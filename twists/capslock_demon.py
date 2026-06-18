import tkinter as tk
import random

from utils import gemini_client


class CapslockDemonTwist:
    """
    Capslock Demon — versi upgrade.

    Penambahan dibanding versi lama:
      - Interval toggle capslock makin cepat seiring difficulty.
      - Pool kalimat makin panjang/aneh pada difficulty tinggi.
      - Toggle ritme dibuat sedikit acak (jitter), bukan benar-benar
        konstan tiap 1 detik, supaya tidak bisa dihafal timing-nya.
      - Indikator karakter real-time: setiap ketikan yang salah
        ditandai dengan warna merah pada label status sesaat.
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

        self.capslock_on = False

        easy_sentences = [
            "the moon watches silently",
            "this notepad is perfectly normal",
            "something is behind you",
            "the demon loves uppercase",
            "keep typing and do not stop",
        ]

        hard_sentences = [
            "i should not trust this program but i keep typing anyway",
            "the demon counts every letter you mistype without mercy",
            "uppercase and lowercase are both equally cursed tonight",
            "this sentence grows longer the more you anger the demon",
            "do not blink the capslock demon is reading your every word",
            "each keystroke echoes with a terrible uncertainty",
            "your punctuation will be your undoing in this realm",
        ]

        pool = easy_sentences if difficulty < 2 else hard_sentences
        self.target_sentence = self._get_random_sentence(pool, difficulty)

        # Interval toggle makin cepat & makin tidak konsisten (jitter)
        self.base_interval_ms = max(300, 1000 - difficulty * 120)
        self.jitter_ms = min(100 + difficulty * 50, 400)

        # Mulai difficulty 2, kadang toggle dobel beruntun
        self.double_toggle_chance = min(0.0 if difficulty < 2 else 0.05 + difficulty * 0.06, 0.5)

        self.finished = False
        self.toggle_job = None

        # Time limit: difficulty naik, waktu berkurang
        self.time_limit_ms = max(15000, 45000 - difficulty * 5000)  # 45s → 15s
        self.time_remaining_ms = self.time_limit_ms
        self.timer_job = None

        self.overlay_frame.place(
            relx=0, rely=0, relwidth=1, relheight=1
        )

        self.build_ui()
        self.toggle_capslock()
        self._start_timer()

    def build_ui(self):
        self.title_label = tk.Label(
            self.overlay_frame, text="CAPSLOCK DEMON", font=("Arial", 18, "bold")
        )
        self.title_label.pack(pady=10)

        # Timer display
        self.timer_label = tk.Label(
            self.overlay_frame, text="", font=("Arial", 12, "bold"), fg="#e74c3c"
        )
        self.timer_label.pack()

        self.state_label = tk.Label(
            self.overlay_frame, text="CAPSLOCK: OFF", font=("Arial", 14)
        )
        self.state_label.pack(pady=5)

        # Sentence label dengan wrapping untuk teks panjang
        self.sentence_label = tk.Label(
            self.overlay_frame, text=self.target_sentence, font=("Arial", 13),
            wraplength=600, justify="center"
        )
        self.sentence_label.pack(pady=15)

        # Text widget untuk input yang lebih luas (bisa multiline)
        text_frame = tk.Frame(self.overlay_frame)
        text_frame.pack(pady=10, padx=20, fill="both", expand=False)

        self.entry = tk.Text(
            text_frame, width=70, height=4, font=("Arial", 11),
            wrap="word", relief="solid", borderwidth=1
        )
        self.entry.pack(side="left", fill="both", expand=True)
        self.entry.bind("<KeyRelease>", self.process_input)
        self.entry.focus_set()

        # Scrollbar untuk Text widget
        scrollbar = tk.Scrollbar(text_frame, command=self.entry.yview)
        scrollbar.pack(side="right", fill="y")
        self.entry.config(yscrollcommand=scrollbar.set)

        self.feedback_label = tk.Label(
            self.overlay_frame, text="", font=("Arial", 10), fg="#c0392b"
        )
        self.feedback_label.pack()

    def _start_timer(self):
        """Start the countdown timer."""
        self.time_remaining_ms = self.time_limit_ms
        self._update_timer_display()

    def _update_timer_display(self):
        """Update timer display and check if time's up."""
        if self.finished or not self.overlay_frame.winfo_exists():
            return

        # Update display
        seconds = max(0, self.time_remaining_ms // 1000)
        self.timer_label.config(text=f"⏱️ Time: {seconds}s")

        # Color warning: red when < 5 seconds
        if seconds < 5:
            self.timer_label.config(fg="#c0392b")
        else:
            self.timer_label.config(fg="#e74c3c")

        # Time's up - restart twist
        if self.time_remaining_ms <= 0:
            self._retry_twist()
            return

        # Tick every 100ms for smooth countdown
        self.time_remaining_ms -= 100
        self.timer_job = self.overlay_frame.after(100, self._update_timer_display)

    def _retry_twist(self):
        """Restart the twist with a new sentence when time runs out."""
        # Generate new sentence
        easy_sentences = [
            "the moon watches silently",
            "this notepad is perfectly normal",
            "something is behind you",
            "the demon loves uppercase",
            "keep typing and do not stop",
        ]
        hard_sentences = [
            "i should not trust this program but i keep typing anyway",
            "the demon counts every letter you mistype without mercy",
            "uppercase and lowercase are both equally cursed tonight",
            "this sentence grows longer the more you anger the demon",
            "do not blink the capslock demon is reading your every word",
            "each keystroke echoes with a terrible uncertainty",
            "your punctuation will be your undoing in this realm",
        ]
        pool = easy_sentences if self.difficulty < 2 else hard_sentences
        self.target_sentence = self._get_random_sentence(pool, self.difficulty)
        
        # Reset text entry
        self.entry.delete("1.0", tk.END)
        self.entry.focus_set()
        
        # Reset timer
        self.time_remaining_ms = self.time_limit_ms
        
        # Reset capslock state
        self.capslock_on = False
        self.state_label.config(text="CAPSLOCK: OFF")
        self.sentence_label.config(text=self.target_sentence.lower())

    def _get_random_sentence(self, fallback_pool, difficulty):
        """Generate random sentence using Gemini or fallback to pool."""
        if not gemini_client.is_available():
            return random.choice(fallback_pool)
        
        try:
            context = "creepy but short" if difficulty < 2 else "longer and more unsettling"
            prompt = f"Generate a single short sentence ({context}) about a cursed notepad and capslock demon. Make it eerie. Reply with ONLY the sentence, no quotes."
            sentence = gemini_client.generate_text(prompt)
            if sentence and isinstance(sentence, str) and len(sentence.strip()) > 5:
                return sentence.strip().lower()[:100]  # Limit to 100 chars
        except Exception:
            pass
        
        return random.choice(fallback_pool)

    def _next_interval(self):
        return self.base_interval_ms + random.randint(
            -self.jitter_ms, self.jitter_ms
        )

    def toggle_capslock(self):
        if self.finished or not self.overlay_frame.winfo_exists():
            return

        self.capslock_on = not self.capslock_on

        current_text = self.entry.get("1.0", tk.END)
        if current_text.endswith("\n"):
            current_text = current_text[:-1]
        
        # Preserve cursor position
        try:
            cursor_pos = self.entry.index(tk.INSERT)
        except tk.TclError:
            cursor_pos = "1.0"

        try:
            if self.capslock_on:
                self.state_label.config(text="CAPSLOCK: ON")
                self.sentence_label.config(text=self.target_sentence.upper())
                transformed = current_text.upper()
            else:
                self.state_label.config(text="CAPSLOCK: OFF")
                self.sentence_label.config(text=self.target_sentence.lower())
                transformed = current_text.lower()

            self.entry.delete("1.0", tk.END)  # Text widget: delete all
            self.entry.insert("1.0", transformed)  # Text widget: insert at beginning
            
            # Restore cursor position
            try:
                self.entry.mark_set(tk.INSERT, cursor_pos)
            except tk.TclError:
                pass
        except tk.TclError:
            return

        next_delay = self._next_interval()

        if random.random() < self.double_toggle_chance:
            # Toggle lagi dengan delay singkat (jebakan ritme)
            next_delay = max(180, next_delay // 3)

        self.toggle_job = self.overlay_frame.after(next_delay, self.toggle_capslock)

    def process_input(self, event):
        current_text = self.entry.get("1.0", tk.END)
        if current_text.endswith("\n"):
            current_text = current_text[:-1]

        # Store cursor position to preserve it
        try:
            cursor_pos = self.entry.index(tk.INSERT)
        except tk.TclError:
            cursor_pos = "1.0"

        transformed = (
            current_text.upper() if self.capslock_on else current_text.lower()
        )

        # Update Text widget if needed
        if transformed != current_text:
            self.entry.delete("1.0", tk.END)
            self.entry.insert("1.0", transformed)
            # Restore cursor position
            try:
                self.entry.mark_set(tk.INSERT, cursor_pos)
            except tk.TclError:
                pass

        self._update_feedback(transformed)
        self.check_answer()

    def _update_feedback(self, current_text):
        target = (
            self.target_sentence.upper()
            if self.capslock_on
            else self.target_sentence.lower()
        )

        typed = current_text.strip()

        if not target.startswith(typed) and typed != "":
            self.feedback_label.config(text="typo detected — keep going")
        else:
            self.feedback_label.config(text="")

    def check_answer(self):
        user_text = self.entry.get("1.0", tk.END).strip()  # Text widget

        if user_text.lower() == self.target_sentence.lower():
            self.finished = True
            
            # Cancel all scheduled jobs
            if self.toggle_job is not None:
                try:
                    self.overlay_frame.after_cancel(self.toggle_job)
                except (ValueError, tk.TclError):
                    pass
            if self.timer_job is not None:
                try:
                    self.overlay_frame.after_cancel(self.timer_job)
                except (ValueError, tk.TclError):
                    pass

            try:
                for widget in list(self.overlay_frame.winfo_children()):
                    if widget.winfo_exists():
                        widget.destroy()
            except tk.TclError:
                pass

            self.finish_callback()