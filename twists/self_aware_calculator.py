import tkinter as tk
import random

from utils import gemini_client
from utils.toast import ToastManager


class SelfAwareCalculatorTwist:
    """
    Self Aware Calculator — versi upgrade dengan toast roasting.

    Penambahan dibanding versi lama:
      - Angka soal makin besar seiring difficulty.
      - Time limit dengan progress bar yang mengecil; kalau habis,
        soal baru di-generate (lebih sulit).
      - Tombol kalkulator ikut random-shuffle mulai difficulty 3.
      - Toast notification (slide-in dari pojok kanan atas) muncul
        SAAT jawaban salah, dan SESEKALI random saat user diam lama
        memikirkan jawaban (pressure tambahan).
      - Visual: header bergradasi manual, glow pulsing di pertanyaan,
        warna timer berubah dari hijau -> kuning -> merah seiring
        waktu menipis.
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

        digit_range = self._digit_range_for_difficulty(difficulty)
        self.num1 = random.randint(*digit_range)
        self.num2 = random.randint(*digit_range)
        self.correct_answer = self.num1 * self.num2

        self.expression = ""

        self.time_limit_ms = max(8000, 25000 - difficulty * 1800)
        self.time_remaining_ms = self.time_limit_ms

        self.shuffle_buttons_enabled = difficulty >= 1

        self.mild_roasts = [
            "Really?",
            "You needed a calculator for that?",
            "This is embarrassing.",
            "Have you tried thinking?",
            "I believe in you. Actually, no.",
            "You know multiplication exists, right?",
            "I do all the work around here.",
            "Outstanding display of dependency.",
        ]

        self.spicy_roasts = [
            "I wasn't built for this level of disappointment.",
            "Humanity peaked long ago, and it wasn't with you.",
            "You went to school just to use me?",
            "I hope you have a backup calculator in case I break down.",
            "If you were any slower, you'd be going backwards.",
            "At this point I'm doing the math out of pity.",
            "Even your decoy answers are wrong.",
            "Statistically, this is impressive incompetence.",
        ]

        self.idle_taunts = [
            "Still thinking? Bold of you.",
            "I can hear the gears not turning.",
            "Take your time. I have eternity.",
            "Tick tock. I'm judging silently.",
            "This is the slowest multiplication in history.",
        ]

        self.roasts = self.spicy_roasts if difficulty >= 1 else self.mild_roasts

        self.use_ai = gemini_client.is_available()
        self.timer_job = None
        self.idle_check_job = None
        self.glow_job = None
        self.finished = False

        self._last_expression_len = 0
        self._idle_ms_accumulated = 0
        self.idle_taunt_threshold_ms = max(3500, 6000 - difficulty * 300)

        self.overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.toast = ToastManager(self.overlay_frame)

        self.build_ui()
        self._tick_timer()
        self._schedule_idle_check()
        self._pulse_glow()

    @staticmethod
    def _digit_range_for_difficulty(difficulty: int):
        if difficulty >= 5:
            return (100000, 999999)
        if difficulty >= 3:
            return (10000, 99999)
        if difficulty >= 1:
            return (5000, 49999)
        return (1000, 9999)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def build_ui(self):

        # Header dengan gradasi manual (canvas strip warna)
        self.header_canvas = tk.Canvas(
            self.overlay_frame, height=70, highlightthickness=0
        )
        self.header_canvas.pack(fill="x")
        self.overlay_frame.after(10, self._draw_header_gradient)

        self.question_text_id = None
        self.overlay_frame.bind("<Configure>", lambda e: self._draw_header_gradient())

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

        # Timer bar
        self.timer_bar = tk.Canvas(
            self.overlay_frame, height=16, bg="#222", highlightthickness=0
        )
        self.timer_bar.pack(fill="x")
        self.timer_fill = self.timer_bar.create_rectangle(0, 0, 0, 16, fill="#27ae60", width=0)

        self.display_label = tk.Label(
            self.overlay_frame,
            text="",
            bg="#0d0d0d",
            fg="#7fffd4",
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
        self.header_canvas.delete("all")
        width = self.header_canvas.winfo_width() or 800
        height = 70

        steps = 30
        for i in range(steps):
            ratio = i / steps
            r = int(20 + ratio * 40)
            g = int(20 + ratio * 10)
            b = int(60 + ratio * 80)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.header_canvas.create_rectangle(
                int(width * i / steps), 0, int(width * (i + 1) / steps), height,
                fill=color, outline=color,
            )

        self.question_text_id = self.header_canvas.create_text(
            width / 2, height / 2,
            text=f"{self.num1} × {self.num2} = ?",
            font=("Arial", 20, "bold"),
            fill="white",
        )

    def _pulse_glow(self, step: int = 0):
        if self.finished or self.question_text_id is None:
            return

        try:
            phase = (step % 40) / 40
            brightness = 200 + int(55 * abs(0.5 - phase) * 2)
            color = f"#{brightness:02x}{brightness:02x}ff"
            self.header_canvas.itemconfig(self.question_text_id, fill=color)
        except tk.TclError:
            return

        self.glow_job = self.overlay_frame.after(60, lambda: self._pulse_glow(step + 1))

    def create_buttons(self):
        buttons = [
            "7", "8", "9", "/",
            "4", "5", "6", "*",
            "1", "2", "3", "-",
            "0", "C", "=", "+",
        ]

        if self.shuffle_buttons_enabled:
            random.shuffle(buttons)

        for col in range(4):
            self.button_frame.grid_columnconfigure(col, weight=1)
        for row in range(4):
            self.button_frame.grid_rowconfigure(row, weight=1)

        row, col = 0, 0

        for text in buttons:
            is_op = text in "/*-+="
            btn = tk.Button(
                self.button_frame,
                text=text,
                font=("Arial", 18, "bold"),
                bg="#e67e22" if is_op else "#2c2c2c",
                fg="white",
                activebackground="#f39c12" if is_op else "#444",
                relief="flat",
                command=lambda t=text: self.button_pressed(t),
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)

            col += 1
            if col > 3:
                col = 0
                row += 1

    def _reshuffle_buttons(self):
        if not self.shuffle_buttons_enabled:
            return

        try:
            for widget in list(self.button_frame.winfo_children()):
                if widget.winfo_exists():
                    widget.destroy()
        except tk.TclError:
            pass

        self.create_buttons()

    # ------------------------------------------------------------------
    # Timer
    # ------------------------------------------------------------------

    def _tick_timer(self):
        if self.finished:
            return

        self.time_remaining_ms -= 100

        bar_width = self.timer_bar.winfo_width() or 760
        ratio = max(0, self.time_remaining_ms / self.time_limit_ms)

        if ratio > 0.5:
            color = "#27ae60"
        elif ratio > 0.2:
            color = "#f1c40f"
        else:
            color = "#e74c3c"

        self.timer_bar.coords(self.timer_fill, 0, 0, bar_width * ratio, 16)
        self.timer_bar.itemconfig(self.timer_fill, fill=color)

        if self.time_remaining_ms <= 0:
            self._on_time_up()
            return

        self.timer_job = self.overlay_frame.after(100, self._tick_timer)

    def _on_time_up(self):
        harder_digits = self._digit_range_for_difficulty(self.difficulty + 1)
        self.num1 = random.randint(*harder_digits)
        self.num2 = random.randint(*harder_digits)
        self.correct_answer = self.num1 * self.num2

        self.header_canvas.itemconfig(
            self.question_text_id, text=f"{self.num1} × {self.num2} = ?"
        )
        self.toast.show("Too slow. New question. Keep up.", kind="warning")

        self.expression = ""
        self.refresh_display()

        self.time_remaining_ms = self.time_limit_ms
        self._tick_timer()

    # ------------------------------------------------------------------
    # Idle taunt (toast random saat user diam lama)
    # ------------------------------------------------------------------

    def _schedule_idle_check(self):
        if self.finished:
            return

        self.idle_check_job = self.overlay_frame.after(800, self._check_idle)

    def _check_idle(self):
        if self.finished:
            return

        current_len = len(self.expression) + len(self.answer_entry.get())

        if current_len == self._last_expression_len:
            self._idle_ms_accumulated += 800
        else:
            self._idle_ms_accumulated = 0
            self._last_expression_len = current_len

        if self._idle_ms_accumulated >= self.idle_taunt_threshold_ms:
            self.toast.show(random.choice(self.idle_taunts), kind="roast")
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
            self._reshuffle_buttons()
            return
        else:
            self.expression += value

        self.refresh_display()
        self._reshuffle_buttons()

    def refresh_display(self):
        self.display_label.config(text=self.expression)

    def calculate(self):
        try:
            result = eval(self.expression)
            self.expression = str(result)
            self.refresh_display()
        except Exception:
            self.expression = "ERROR"
            self.refresh_display()

    def check_answer(self):
        try:
            user_answer = int(self.answer_entry.get())

            if user_answer == self.correct_answer:
                self._cleanup_and_finish()
            else:
                self.toast.show(
                    "Wrong answer. I literally calculated it for you.",
                    kind="roast",
                )
                self.maybe_show_ai_roast(user_answer)

        except Exception:
            self.toast.show("That doesn't even look like a number.", kind="roast")

    def maybe_show_ai_roast(self, user_answer):
        if not self.use_ai:
            self.toast.show(self._get_random_roast(), kind="roast")
            return

        import threading

        question = f"{self.num1} x {self.num2}"

        def worker():
            roast = gemini_client.generate_roast(
                question, user_answer, self.correct_answer
            )
            if roast:
                self.overlay_frame.after(
                    0, lambda: self.toast.show(roast, kind="roast")
                )

        threading.Thread(target=worker, daemon=True).start()

    def _get_random_roast(self):
        """Generate random roast using Gemini or fallback to pool."""
        try:
            # Try to get a fresh roast from Gemini directly
            prompt = "Generate a single short sarcastic roast about poor math skills or using a calculator wrong. Make it witty and under 10 words. Reply with ONLY the roast."
            roast = gemini_client.generate_text(prompt)
            if roast and isinstance(roast, str) and len(roast.strip()) > 3:
                return roast.strip()[:100]
        except Exception:
            pass
        
        return random.choice(self.roasts)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _cleanup_and_finish(self):
        self.finished = True

        if self.timer_job is not None:
            try:
                self.overlay_frame.after_cancel(self.timer_job)
            except (ValueError, tk.TclError):
                pass
        if self.idle_check_job is not None:
            try:
                self.overlay_frame.after_cancel(self.idle_check_job)
            except (ValueError, tk.TclError):
                pass
        if self.glow_job is not None:
            try:
                self.overlay_frame.after_cancel(self.glow_job)
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