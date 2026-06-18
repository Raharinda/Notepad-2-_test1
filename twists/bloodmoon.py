import tkinter as tk
import random

from utils import gemini_client


class BloodmoonTwist:
    """
    Bloodmoon — versi upgrade.

    Penambahan dibanding versi lama:
      - Durasi survive naik seiring difficulty (capped).
      - User WAJIB tetap mengetik di notepad utama; kalau diam lebih
        dari `silence_limit_ms`, layar "menghukum" dengan flash merah
        dan mempercepat siklus pesan (membuatnya makin menegangkan).
      - Random jumpscare flash: border window berkedip terang sebentar
        tanpa peringatan, lalu kembali normal.
      - Pesan makin sering muncul & makin intens seiring waktu berjalan.
    """

    def __init__(
        self,
        main_view,
        finish_callback,
        difficulty: int = 0,
    ):

        self.main_view = main_view
        self.finish_callback = finish_callback
        self.difficulty = difficulty

        self.messages = [
            "The moon is watching.",
            "Keep writing.",
            "Do not look behind you.",
            "Something feels wrong.",
            "The night grows darker.",
            "It sees your notes.",
            "Don't stop typing.",
            "The Bloodmoon hungers.",
            "Why did you stop?",
            "It noticed your silence.",
            "Faster. It's getting closer.",
            "Your words are the only light left.",
            "I can feel your heartbeat.",
            "Stop running. Join us.",
        ]

        # Durasi survive naik dengan difficulty, capped di 35s
        self.duration_ms = min(12000 + difficulty * 2000, 35000)

        # Batas diam sebelum dihukum (makin sulit, makin galak)
        self.silence_limit_ms = max(1500, 4500 - difficulty * 300)

        self.message_interval_ms = max(800, 3000 - difficulty * 200)

        self._last_text_len = len(self.main_view.text_area.get("1.0", "end-1c"))
        self._silent_streak = False

        # Save original colors
        self.old_text_bg = self.main_view.text_area.cget("bg")
        self.old_text_fg = self.main_view.text_area.cget("fg")
        self.old_status_bg = self.main_view.status_label.cget("bg")
        self.old_status_fg = self.main_view.status_label.cget("fg")
        self.old_root_bg = self.main_view.root.cget("bg")

        # Remove warning overlay
        self.main_view.hide_overlay()

        # Apply Bloodmoon theme
        self.main_view.text_area.config(
            bg="#2b0000", fg="#dddddd", insertbackground="white"
        )
        self.main_view.status_label.config(bg="#550000", fg="white")

        # Bind ke KeyRelease textarea utk deteksi aktivitas mengetik
        self._typing_bind_id = self.main_view.text_area.bind(
            "<KeyRelease>", self._on_user_typed, add="+"
        )

        self.message_job = None
        self.silence_check_job = None
        self.jumpscare_job = None
        self.ended = False

        self.update_message()
        self._schedule_silence_check()
        self._schedule_jumpscare()

        self.main_view.root.after(self.duration_ms, self.end_bloodmoon)

    # ------------------------------------------------------------------
    # Typing activity tracking
    # ------------------------------------------------------------------

    def _on_user_typed(self, event=None):
        current_len = len(self.main_view.text_area.get("1.0", "end-1c"))
        self._last_text_len = current_len

        if self._silent_streak:
            self._silent_streak = False
            self.main_view.text_area.config(bg="#2b0000")

    def _schedule_silence_check(self):
        if self.ended:
            return

        self.silence_check_job = self.main_view.root.after(
            self.silence_limit_ms, self._check_silence
        )

    def _check_silence(self):
        if self.ended:
            return

        current_len = len(self.main_view.text_area.get("1.0", "end-1c"))

        if current_len == self._last_text_len:
            # User diam terlalu lama — hukuman visual ringan
            self._silent_streak = True
            self.main_view.text_area.config(bg="#5e0000")
            self.main_view.status_label.config(
                text="STOP STALLING. KEEP WRITING."
            )
        else:
            self._last_text_len = current_len

        self._schedule_silence_check()

    # ------------------------------------------------------------------
    # Ambient messages
    # ------------------------------------------------------------------

    def _get_random_message(self):
        """Generate random eerie message using Gemini or fallback."""
        if not gemini_client.is_available():
            return random.choice(self.messages)
        
        try:
            prompt = "Generate a single short eerie/creepy message (under 6 words) about a bloodmoon and darkness. Make it unsettling. Reply with ONLY the message."
            msg = gemini_client.generate_text(prompt)
            if msg and isinstance(msg, str) and len(msg.strip()) > 3:
                return msg.strip()[:80]
        except Exception:
            pass
        
        return random.choice(self.messages)

    def update_message(self):
        if self.ended:
            return

        self.main_view.status_label.config(text=self._get_random_message())

        self.message_job = self.main_view.root.after(
            self.message_interval_ms, self.update_message
        )

    # ------------------------------------------------------------------
    # Random jumpscare flash
    # ------------------------------------------------------------------

    def _schedule_jumpscare(self):
        if self.ended:
            return

        delay = random.randint(2500, 6000)
        self.jumpscare_job = self.main_view.root.after(delay, self._do_jumpscare)

    def _do_jumpscare(self):
        if self.ended:
            return

        self.main_view.root.config(bg="#ff1111")
        self.main_view.root.after(90, self._end_jumpscare_flash)

    def _end_jumpscare_flash(self):
        if self.ended:
            return

        self.main_view.root.config(bg=self.old_root_bg)
        self._schedule_jumpscare()

    # ------------------------------------------------------------------
    # End
    # ------------------------------------------------------------------

    def end_bloodmoon(self):
        if self.ended:
            return

        self.ended = True

        if self.message_job is not None:
            try:
                self.main_view.root.after_cancel(self.message_job)
            except (ValueError, tk.TclError):
                pass
        if self.silence_check_job is not None:
            try:
                self.main_view.root.after_cancel(self.silence_check_job)
            except (ValueError, tk.TclError):
                pass
        if self.jumpscare_job is not None:
            try:
                self.main_view.root.after_cancel(self.jumpscare_job)
            except (ValueError, tk.TclError):
                pass

        self.main_view.text_area.unbind("<KeyRelease>", self._typing_bind_id)

        self.main_view.text_area.config(
            bg=self.old_text_bg, fg=self.old_text_fg, insertbackground="black"
        )
        self.main_view.status_label.config(
            bg=self.old_status_bg, fg=self.old_status_fg
        )
        self.main_view.root.config(bg=self.old_root_bg)

        self.finish_callback()