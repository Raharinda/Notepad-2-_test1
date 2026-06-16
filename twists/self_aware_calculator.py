import tkinter as tk
import random

from utils import gemini_client


class SelfAwareCalculatorTwist:

    def __init__(
        self,
        overlay_frame,
        finish_callback
    ):

        self.overlay_frame = overlay_frame
        self.finish_callback = finish_callback

        self.num1 = random.randint(
            1000,
            9999
        )

        self.num2 = random.randint(
            1000,
            9999
        )

        self.correct_answer = (
            self.num1 * self.num2
        )

        self.expression = ""

        # Fallback roasts kalau Gemini tidak tersedia / gagal
        self.roasts = [
            "Really?",
            "You needed a calculator for that?",
            "This is embarrassing.",
            "Have you tried thinking?",
            "I believe in you. Actually, no.",
            "You know multiplication exists, right?",
            "I do all the work around here.",
            "Outstanding display of dependency.",
            "I wasn't built for this.",
            "Humanity peaked long ago.",
            "You went to school just to use me?",
            "I hope you have a backup calculator in case I break down.",
            "If you were any slower, you'd be going backwards."
        ]

        self.use_ai = gemini_client.is_available()

        self.overlay_frame.place(
            relx=0,
            rely=0,
            relwidth=1,
            relheight=1
        )

        self.build_ui()

    def build_ui(self):

        # ==================
        # TOP ROW
        # ==================

        top_frame = tk.Frame(
            self.overlay_frame,
            relief="solid",
            bd=2
        )

        top_frame.pack(
            fill="x"
        )

        top_frame.grid_columnconfigure(
            0,
            weight=4
        )

        top_frame.grid_columnconfigure(
            1,
            weight=1
        )

        self.question_label = tk.Label(
            top_frame,
            text=f"{self.num1} × {self.num2} = ?",
            font=("Arial", 16, "bold"),
            anchor="w",
            padx=15,
            pady=15
        )

        self.question_label.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        answer_frame = tk.Frame(
            top_frame,
            relief="solid",
            bd=1
        )

        answer_frame.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        tk.Label(
            answer_frame,
            text="Answer"
        ).pack()

        self.answer_entry = tk.Entry(
            answer_frame,
            width=12
        )

        self.answer_entry.pack(
            pady=2
        )

        tk.Button(
            answer_frame,
            text="Submit",
            command=self.check_answer
        ).pack(
            pady=2
        )

        # ==================
        # ROAST AREA
        # ==================

        self.roast_label = tk.Label(
            self.overlay_frame,
            text="",
            relief="solid",
            bd=2,
            anchor="w",
            font=("Arial", 11),
            padx=15,
            pady=12,
            wraplength=760,
            justify="left"
        )

        self.roast_label.pack(
            fill="x"
        )

        # ==================
        # DISPLAY AREA
        # ==================

        self.display_label = tk.Label(
            self.overlay_frame,
            text="",
            relief="solid",
            bd=2,
            anchor="e",
            font=("Consolas", 16),
            padx=15,
            pady=12
        )

        self.display_label.pack(
            fill="x"
        )

        # ==================
        # BUTTON AREA
        # ==================

        button_frame = tk.Frame(
            self.overlay_frame,
            relief="solid",
            bd=2
        )

        button_frame.pack(
            fill="both",
            expand=True
        )

        buttons = [
            "7", "8", "9", "/",
            "4", "5", "6", "*",
            "1", "2", "3", "-",
            "0", "C", "=", "+"
        ]

        for col in range(4):

            button_frame.grid_columnconfigure(
                col,
                weight=1
            )

        for row in range(4):

            button_frame.grid_rowconfigure(
                row,
                weight=1
            )

        row = 0
        col = 0

        for text in buttons:

            btn = tk.Button(
                button_frame,
                text=text,
                font=("Arial", 18),
                command=lambda t=text:
                self.button_pressed(t)
            )

            btn.grid(
                row=row,
                column=col,
                sticky="nsew",
                padx=4,
                pady=4
            )

            col += 1

            if col > 3:
                col = 0
                row += 1

    def button_pressed(self, value):

        # Tampilkan roast statis dulu (instan), AI roast (jika ada)
        # akan menyusul secara async dan menggantikan teks ini.
        self.roast_label.config(
            text=random.choice(self.roasts)
        )

        if value == "C":

            self.expression = ""

        elif value == "=":

            self.calculate()
            return

        else:

            self.expression += value

        self.refresh_display()

    def refresh_display(self):

        self.display_label.config(
            text=self.expression
        )

    def calculate(self):

        try:

            result = eval(
                self.expression
            )

            self.expression = str(
                result
            )

            self.refresh_display()

        except:

            self.expression = "ERROR"

            self.refresh_display()

    def check_answer(self):

        try:

            user_answer = int(
                self.answer_entry.get()
            )

            if (
                user_answer
                ==
                self.correct_answer
            ):

                for widget in (
                    self.overlay_frame
                    .winfo_children()
                ):
                    widget.destroy()

                self.finish_callback()

            else:

                self.roast_label.config(
                    text="Wrong answer. I literally calculated it for you."
                )

                self.maybe_show_ai_roast(user_answer)

        except:

            self.roast_label.config(
                text="That doesn't even look like a number."
            )

    def maybe_show_ai_roast(self, user_answer):
        """
        Generate roast dinamis via Gemini secara async.
        Jika Gemini tidak tersedia, label tetap menampilkan teks
        statis yang sudah di-set sebelumnya.
        """

        if not self.use_ai:
            return

        import threading

        question = f"{self.num1} x {self.num2}"

        def worker():

            roast = gemini_client.generate_roast(
                question,
                user_answer,
                self.correct_answer
            )

            if roast:
                self.overlay_frame.after(
                    0,
                    lambda: self.roast_label.config(text=roast)
                )

        threading.Thread(target=worker, daemon=True).start()