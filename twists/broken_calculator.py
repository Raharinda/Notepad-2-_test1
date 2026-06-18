import tkinter as tk
import random

from utils import gemini_client
from utils.toast import ToastManager


class BrokenCalculatorTwist:
    """
    Broken Calculator — versi upgrade dengan toast notification.

    Penambahan dibanding versi lama:
      - Angka soal (dividend/divisor) makin besar seiring difficulty.
      - Pada difficulty tinggi, tombol "=" punya kemungkinan FAKE —
        menampilkan hasil yang salah secara sengaja.
      - Toast slide-in muncul saat jawaban salah, dan sesekali random
        saat user diam lama memikirkan jawaban.
      - Visual: header gradasi oranye/merah ("rusak"), tombol dengan
        warna acak tiap reshuffle untuk efek "calculator gila".
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

        answer_range, divisor_range = self._ranges_for_difficulty(difficulty)

        self.answer = random.randint(*answer_range)
        self.divisor = random.randint(*divisor_range)
        self.dividend = self.answer * self.divisor
        self.correct_answer = self.answer

        self.expression = ""
        self.wrong_attempts = 0

        self.fake_equals_chance = min(
            0.0 if difficulty < 1 else 0.20 + difficulty * 0.08, 0.55
        )

        self.idle_taunts = [
            "The calculator is judging your hesitation.",
            "Still staring at the screen?",
            "Division isn't going to solve itself by waiting.",
            "I'm not broken. You're just slow.",
            "Tick tock, this calculator has trust issues.",
        ]

        self._last_input_len = 0
        self._idle_ms_accumulated = 0
        self.idle_taunt_threshold_ms = max(3000, 6500 - difficulty * 400)
        self.idle_check_job = None
        self.finished = False

        self.overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.toast = ToastManager(self.overlay_frame)

        self.build_ui()
        self._schedule_idle_check()

    @staticmethod
    def _ranges_for_difficulty(difficulty: int):
        if difficulty >= 5:
            return (300, 1000), (60, 250)
        if difficulty >= 3:
            return (100, 600), (30, 200)
        if difficulty >= 1:
            return (50, 400), (20, 150)
        return (10, 200), (10, 99)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def build_ui(self):

        self.header_canvas = tk.Canvas(
            self.overlay_frame, height=70, highlightthickness=0
        )
        self.header_canvas.pack(fill="x")
        self.header_canvas.after(10, self._draw_header_gradient)
        self.header_canvas.bind("<Configure>", lambda e: self._draw_header_gradient())

        answer_frame = tk.Frame(self.overlay_frame, bg="#1c1c1c")
        answer_frame.pack(fill="x")

        tk.Label(
            answer_frame, text="Your answer:", bg="#1c1c1c", fg="#cccccc",
            font=("Arial", 10),
        ).pack(side="left", padx=(15, 5), pady=10)

        self.answer_entry = tk.Entry(answer_frame, width=14, font=("Consolas", 12))
        self.answer_entry.pack(side="left", pady=10)

        tk.Button(
            answer_frame, text="Submit", command=self.check_answer,
            bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
            relief="flat", padx=12,
        ).pack(side="left", padx=10, pady=10)

        self.hint_label = tk.Label(
            self.overlay_frame, text="", font=("Arial", 9, "italic"),
            bg="#1c1c1c", fg="#999",
        )
        self.hint_label.pack(fill="x")

        self.display_label = tk.Label(
            self.overlay_frame,
            text="",
            bg="#0d0d0d",
            fg="#ff8c69",
            anchor="e",
            font=("Consolas", 18),
            padx=15,
            pady=12,
        )
        self.display_label.pack(fill="x")

        self.button_frame = tk.Frame(self.overlay_frame, bg="#111")
        self.button_frame.pack(fill="both", expand=True)

        self.create_buttons()

    def _draw_header_gradient(self):
        if not hasattr(self, "header_canvas") or not self.header_canvas.winfo_exists():
            return

        self.header_canvas.delete("all")
        width = self.header_canvas.winfo_width() or 800
        height = 70

        steps = 30
        for i in range(steps):
            ratio = i / steps
            r = int(120 + ratio * 100)
            g = int(40 + ratio * 20)
            b = int(20 + ratio * 10)
            color = f"#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}"
            self.header_canvas.create_rectangle(
                int(width * i / steps), 0, int(width * (i + 1) / steps), height,
                fill=color, outline=color,
            )

        self.header_canvas.create_text(
            width / 2, height / 2,
            text=f"{self.dividend} ÷ {self.divisor} = ?",
            font=("Arial", 20, "bold"),
            fill="white",
        )

    def create_buttons(self):
        buttons = [
            "7", "8", "9", "/",
            "4", "5", "6", "*",
            "1", "2", "3", "-",
            "0", "C", "=", "+",
        ]

        random.shuffle(buttons)

        for col in range(4):
            self.button_frame.grid_columnconfigure(col, weight=1)
        for row in range(4):
            self.button_frame.grid_rowconfigure(row, weight=1)

        row, col = 0, 0
        glitch_palette = ["#2c2c2c", "#34281f", "#3a1f1f", "#2c2c3a"]

        for text in buttons:
            is_op = text in "/*-+="
            btn = tk.Button(
                self.button_frame,
                text=text,
                font=("Arial", 18, "bold"),
                bg="#c0392b" if is_op else random.choice(glitch_palette),
                fg="white",
                activebackground="#e74c3c",
                relief="flat",
                command=lambda t=text: self.button_pressed(t),
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

            col += 1
            if col > 3:
                col = 0
                row += 1

    def shuffle_buttons(self):
        try:
            for widget in list(self.button_frame.winfo_children()):
                if widget.winfo_exists():
                    widget.destroy()
        except tk.TclError:
            pass

        self.create_buttons()

    def _get_random_taunt(self):
        """Generate random taunt using Gemini or fallback to pool."""
        if not gemini_client.is_available():
            return random.choice(self.idle_taunts)
        
        try:
            prompt = "Generate a single short sarcastic taunt about a broken calculator or someone's slow math skills. Make it witty and under 10 words. Reply with ONLY the taunt."
            taunt = gemini_client.generate_text(prompt)
            if taunt and isinstance(taunt, str) and len(taunt.strip()) > 3:
                return taunt.strip()[:80]  # Limit to 80 chars
        except Exception:
            pass
        
        return random.choice(self.idle_taunts)

    # ------------------------------------------------------------------
    # Idle taunt
    # ------------------------------------------------------------------

    def _schedule_idle_check(self):
        if self.finished:
            return

        self.idle_check_job = self.overlay_frame.after(800, self._check_idle)

    def _check_idle(self):
        if self.finished:
            return

        current_len = len(self.expression) + len(self.answer_entry.get())

        if current_len == self._last_input_len:
            self._idle_ms_accumulated += 800
        else:
            self._idle_ms_accumulated = 0
            self._last_input_len = current_len

        if self._idle_ms_accumulated >= self.idle_taunt_threshold_ms:
            self.toast.show(self._get_random_taunt(), kind="roast")
            self._idle_ms_accumulated = 0

        self._schedule_idle_check()

    # ------------------------------------------------------------------
    # Calculator logic
    # ------------------------------------------------------------------

    def button_pressed(self, value):
        if value == "C":
            self.expression = ""
        elif value == "=":
            self.calculate()
        else:
            self.expression += value

        self.refresh_display()
        self.shuffle_buttons()

    def refresh_display(self):
        self.display_label.config(text=self.expression)

    def calculate(self):
        try:
            real_result = eval(self.expression)

            if random.random() < self.fake_equals_chance:
                fake_result = real_result + random.choice([-3, -2, -1, 1, 2, 3])
                self.expression = str(fake_result)
                self.hint_label.config(
                    text="(this calculator may be lying to you...)"
                )
            else:
                self.expression = str(real_result)
                self.hint_label.config(text="")

        except Exception:
            self.expression = "ERROR"

        self.refresh_display()

    def check_answer(self):
        try:
            user_answer = int(self.answer_entry.get())

            if user_answer == self.correct_answer:
                self._cleanup_and_finish()
            else:
                self.wrong_attempts += 1
                self.toast.show(
                    f"Wrong. That's attempt #{self.wrong_attempts}.", kind="roast"
                )

                if self.wrong_attempts >= 3:
                    self.hint_label.config(
                        text=f"Hint: try computing {self.dividend} ÷ {self.divisor} by hand."
                    )

        except Exception:
            self.toast.show("Invalid input. Numbers only.", kind="roast")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _cleanup_and_finish(self):
        self.finished = True

        if self.idle_check_job is not None:
            try:
                self.overlay_frame.after_cancel(self.idle_check_job)
            except (ValueError, tk.TclError):
                pass

        self.toast.cancel_all()

        try:
            for widget in list(self.overlay_frame.winfo_children()):
                if widget.winfo_exists():
                    widget.destroy()
        except tk.TclError:
            pass

        self.finish_callback()