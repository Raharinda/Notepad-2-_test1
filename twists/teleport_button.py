import tkinter as tk
import random

from utils import gemini_client
from utils.toast import ToastManager


class TeleportButtonTwist:
    """
    "Chaos Click" — versi upgrade dari Teleporting Button.

    Penambahan dibanding versi lama:
      - Tombol mengecil seiring difficulty naik.
      - Ada decoy button (merah) yang muncul acak — klik decoy MENAMBAH
        sisa klik yang dibutuhkan, bukan mengurangi.
      - Tombol asli punya kemungkinan "lari" menjauh dari cursor saat
        didekati, bukan langsung diam menunggu klik.
      - Time pressure: kalau tombol asli tidak diklik dalam waktu
        tertentu, ia melompat sendiri ke posisi baru (memberi tekanan
        tapi tidak menambah beban — supaya tetap fair).
    """

    def __init__(
        self,
        overlay_frame,
        finish_callback,
        difficulty: int = 0,
    ):

        self.overlay_frame = overlay_frame
        self.finish_callback = finish_callback
        self.difficulty = difficulty

        base_clicks = random.randint(15, 25)
        # Tiap difficulty naik, tambah beberapa klik wajib (cap supaya tidak gila)
        extra_clicks = min(difficulty * 3, 25)
        self.teleports_remaining = base_clicks + extra_clicks

        # Ukuran tombol mengecil seiring difficulty, dengan batas bawah
        self.button_size = max(40, 110 - difficulty * 8)

        # Probabilitas decoy muncul & probabilitas tombol "lari" saat didekati
        self.decoy_chance = min(0.20 + difficulty * 0.06, 0.65)
        self.flee_chance = min(0.15 + difficulty * 0.08, 0.75)

        # Auto-jump timer: makin sulit, makin cepat tombol pindah sendiri
        self.auto_jump_ms = max(1000, 3000 - difficulty * 200)

        self.decoy_button = None
        self.decoy_job = None
        self.auto_jump_job = None
        self.finished = False

        self.overlay_frame.place(
            relx=0, rely=0, relwidth=1, relheight=1
        )

        self.canvas = tk.Canvas(
            self.overlay_frame,
            bg="#101010",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.update()

        self.width = self.canvas.winfo_width()
        self.height = self.canvas.winfo_height()

        self.toast = ToastManager(self.overlay_frame)

        self.counter_label = tk.Label(
            self.overlay_frame,
            text="",
            font=("Arial", 14, "bold"),
            bg="#101010",
            fg="white",
        )
        self.counter_label.place(relx=0.02, rely=0.02)
        self._refresh_counter()

        self.button = tk.Button(
            self.overlay_frame,
            text="CLICK ME",
            font=("Arial", 11, "bold"),
            bg="#3aa65a",
            command=self.button_clicked,
        )
        self.button.bind("<Enter>", self._maybe_flee)

        self.move_button()
        self._schedule_decoy()
        self._schedule_auto_jump()

    def _get_random_taunt(self):
        """Generate random taunt when button teleports using Gemini or fallback."""
        taunts = [
            "Too slow!",
            "Missed me!",
            "Can't catch me!",
            "Try again!",
            "Better luck next time!",
            "Did you really think you could grab me?",
            "I'm faster than your reflexes!",
        ]
        
        if not gemini_client.is_available():
            return random.choice(taunts)
        
        try:
            prompt = "Generate a single short taunting phrase (under 5 words) when an evasive button avoids being clicked. Make it cheeky. Reply with ONLY the phrase."
            taunt = gemini_client.generate_text(prompt)
            if taunt and isinstance(taunt, str) and len(taunt.strip()) > 2:
                return taunt.strip()[:60]
        except Exception:
            pass
        
        return random.choice(taunts)

    # ------------------------------------------------------------------
    # Real button movement
    # ------------------------------------------------------------------

    def move_button(self):
        if self.finished:
            return

        x = random.randint(20, max(21, self.width - self.button_size - 20))
        y = random.randint(20, max(21, self.height - self.button_size - 40))

        self.button.place(
            x=x, y=y, width=self.button_size, height=self.button_size
        )
        
        # Show random taunt when button teleports
        if random.random() < 0.4:  # 40% chance to taunt
            self.toast.show(self._get_random_taunt(), kind="info")

    def _maybe_flee(self, event=None):
        """Saat cursor mendekat (hover), tombol punya chance untuk lari."""
        if self.finished:
            return

        if random.random() < self.flee_chance:
            self.move_button()

    def _schedule_auto_jump(self):
        if self.finished:
            return

        self.move_button()

        self.auto_jump_job = self.overlay_frame.after(
            self.auto_jump_ms, self._schedule_auto_jump
        )

    # ------------------------------------------------------------------
    # Decoy button
    # ------------------------------------------------------------------

    def _schedule_decoy(self):
        if self.finished:
            return

        delay = random.randint(1200, 2600)
        self.decoy_job = self.overlay_frame.after(delay, self._maybe_spawn_decoy)

    def _maybe_spawn_decoy(self):
        if self.finished:
            return

        if self.decoy_button is None and random.random() < self.decoy_chance:
            self._spawn_decoy()

        self._schedule_decoy()

    def _spawn_decoy(self):
        size = self.button_size

        x = random.randint(20, max(21, self.width - size - 20))
        y = random.randint(20, max(21, self.height - size - 40))

        self.decoy_button = tk.Button(
            self.overlay_frame,
            text="CLICK ME",
            font=("Arial", 11, "bold"),
            bg="#c0392b",
            command=self._decoy_clicked,
        )
        self.decoy_button.place(x=x, y=y, width=size, height=size)

        # Decoy hilang sendiri kalau tidak diklik dalam 1.5 detik
        self.overlay_frame.after(1500, self._despawn_decoy)

    def _despawn_decoy(self):
        if self.decoy_button is not None:
            self.decoy_button.destroy()
            self.decoy_button = None

    def _decoy_clicked(self):
        if self.finished:
            return

        self.teleports_remaining += 2
        self._refresh_counter()
        self._despawn_decoy()

    # ------------------------------------------------------------------
    # Real button click
    # ------------------------------------------------------------------

    def button_clicked(self):
        if self.finished:
            return

        self.teleports_remaining -= 1
        self._refresh_counter()

        if self.teleports_remaining > 0:
            self.move_button()
        else:
            self._cleanup_and_finish()

    def _refresh_counter(self):
        self.counter_label.config(
            text=f"Clicks remaining: {self.teleports_remaining}"
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _cleanup_and_finish(self):
        self.finished = True

        if self.decoy_job is not None:
            try:
                self.overlay_frame.after_cancel(self.decoy_job)
            except (ValueError, tk.TclError):
                pass
        if self.auto_jump_job is not None:
            try:
                self.overlay_frame.after_cancel(self.auto_jump_job)
            except (ValueError, tk.TclError):
                pass

        try:
            for widget in list(self.overlay_frame.winfo_children()):
                if widget.winfo_exists():
                    widget.destroy()
        except tk.TclError:
            pass

        self.finish_callback()