import tkinter as tk
import random
import math


class BlackHoleTwist:
    """
    Black Hole — versi upgrade.

    Penambahan dibanding versi lama:
      - Growth rate black hole naik seiring difficulty (lebih cepat
        membesar = waktu lebih sempit).
      - Player spawn lebih jauh dari finish line di difficulty tinggi.
      - Mulai difficulty 3, ada gravitasi parsial: player ditarik
        sedikit ke arah black hole tiap frame, jadi user harus aktif
        melawan tarikan, bukan cuma diam di tempat aman.
    """

    def __init__(
        self,
        overlay_frame,
        finish_callback,
        retry_callback,
        difficulty: int = 0,
    ):

        self.overlay_frame = overlay_frame
        self.finish_callback = finish_callback
        self.retry_callback = retry_callback
        self.difficulty = difficulty

        self.growth_rate = min(0.60 + difficulty * 0.10, 1.4)
        self.gravity_pull = 0.0 if difficulty < 1 else min(0.020 + difficulty * 0.007, 0.08)

        self.overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self.overlay_frame, bg="#3d6db5", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.update()

        self.width = self.canvas.winfo_width()
        self.height = self.canvas.winfo_height()

        self.game_over = False
        self.player_speed = 4

        direction = random.choice(["right", "left", "top", "bottom"])
        self.direction = direction

        # Spawn distance dari tengah makin jauh di difficulty tinggi
        spawn_offset = min(100 + difficulty * 15, 220)

        if direction == "right":
            self.player_x = max(40, self.width / 2 - spawn_offset)
            self.player_y = self.height / 2
            self.hole_x = self.width / 2
            self.hole_y = self.height / 2
            self.create_vertical_finish(self.width - 40)

        elif direction == "left":
            self.player_x = min(self.width - 40, self.width / 2 + spawn_offset)
            self.player_y = self.height / 2
            self.hole_x = self.width / 2
            self.hole_y = self.height / 2
            self.create_vertical_finish(0)

        elif direction == "top":
            self.player_x = self.width / 2
            self.player_y = min(self.height - 40, self.height / 2 + spawn_offset)
            self.hole_x = self.width / 2
            self.hole_y = self.height / 2
            self.create_horizontal_finish(0)

        else:
            self.player_x = self.width / 2
            self.player_y = max(40, self.height / 2 - spawn_offset)
            self.hole_x = self.width / 2
            self.hole_y = self.height / 2
            self.create_horizontal_finish(self.height - 40)

        self.player = self.canvas.create_oval(
            self.player_x - 15, self.player_y - 15,
            self.player_x + 15, self.player_y + 15,
            fill="yellow",
        )

        self.player_label = self.canvas.create_text(
            self.player_x, self.player_y - 25,
            text="YOU", fill="white", font=("Arial", 10, "bold"),
        )

        self.hole_radius = 40

        self.black_hole = self.canvas.create_oval(
            self.hole_x - self.hole_radius, self.hole_y - self.hole_radius,
            self.hole_x + self.hole_radius, self.hole_y + self.hole_radius,
            fill="black", outline="black",
        )

        self.mouse_x = self.width / 2
        self.mouse_y = self.height / 2

        self.canvas.bind("<Motion>", self.mouse_moved)

        self.move_player()
        self.expand_black_hole()

    # ------------------------------------------------------------------
    # Finish line
    # ------------------------------------------------------------------

    def create_vertical_finish(self, x):
        size = 20
        for y in range(0, self.height, size):
            for col in range(2):
                color = "white" if (y // size + col) % 2 == 0 else "black"
                self.canvas.create_rectangle(
                    x + col * size, y, x + (col + 1) * size, y + size,
                    fill=color, outline=color,
                )

    def create_horizontal_finish(self, y):
        size = 20
        for x in range(0, self.width, size):
            for row in range(2):
                color = "white" if (x // size + row) % 2 == 0 else "black"
                self.canvas.create_rectangle(
                    x, y + row * size, x + size, y + (row + 1) * size,
                    fill=color, outline=color,
                )

    # ------------------------------------------------------------------
    # Mouse / movement
    # ------------------------------------------------------------------

    def mouse_moved(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def move_player(self):
        if self.game_over or not self.canvas.winfo_exists():
            return

        center_x = self.width / 2
        center_y = self.height / 2

        dx = self.mouse_x - center_x
        dy = self.mouse_y - center_y

        self.player_x += dx * 0.01
        self.player_y += dy * 0.01

        # Gravitasi parsial: tarikan kecil ke arah black hole
        if self.gravity_pull > 0:
            gx = self.hole_x - self.player_x
            gy = self.hole_y - self.player_y
            gdist = max(1, (gx ** 2 + gy ** 2) ** 0.5)
            self.player_x += (gx / gdist) * self.gravity_pull * gdist * 0.02
            self.player_y += (gy / gdist) * self.gravity_pull * gdist * 0.02

        self.player_x = max(15, min(self.width - 15, self.player_x))
        self.player_y = max(15, min(self.height - 15, self.player_y))

        self.canvas.coords(
            self.player,
            self.player_x - 15, self.player_y - 15,
            self.player_x + 15, self.player_y + 15,
        )
        self.canvas.coords(self.player_label, self.player_x, self.player_y - 25)

        self.check_finish()
        self.check_black_hole()

        self.canvas.after(16, self.move_player)

    # ------------------------------------------------------------------
    # Black hole growth
    # ------------------------------------------------------------------

    def expand_black_hole(self):
        if self.game_over or not self.canvas.winfo_exists():
            return

        self.hole_radius += self.growth_rate

        try:
            self.canvas.coords(
                self.black_hole,
                self.hole_x - self.hole_radius, self.hole_y - self.hole_radius,
                self.hole_x + self.hole_radius, self.hole_y + self.hole_radius,
            )
        except tk.TclError:
            return

        self.canvas.after(16, self.expand_black_hole)

    def check_black_hole(self):
        distance = math.sqrt(
            (self.player_x - self.hole_x) ** 2 + (self.player_y - self.hole_y) ** 2
        )

        if distance <= self.hole_radius:
            self.display_game_over()

    # ------------------------------------------------------------------
    # Win / lose
    # ------------------------------------------------------------------

    def check_finish(self):
        if self.direction == "right" and self.player_x >= self.width - 40:
            self.win()
        elif self.direction == "left" and self.player_x <= 40:
            self.win()
        elif self.direction == "top" and self.player_y <= 40:
            self.win()
        elif self.direction == "bottom" and self.player_y >= self.height - 40:
            self.win()

    def win(self):
        self.game_over = True
        try:
            for widget in list(self.overlay_frame.winfo_children()):
                if widget.winfo_exists():
                    widget.destroy()
        except tk.TclError:
            pass
        self.finish_callback()

    def display_game_over(self):
        if self.game_over:
            return

        self.game_over = True

        try:
            for widget in list(self.overlay_frame.winfo_children()):
                if widget.winfo_exists():
                    widget.destroy()
        except tk.TclError:
            pass

        label = tk.Label(
            self.overlay_frame,
            text="CONSUMED BY THE BLACK HOLE\n\n[R] Retry",
            font=("Arial", 24, "bold"),
            bg="#3d6db5",
            fg="yellow",
        )
        label.place(relx=0.5, rely=0.5, anchor="center")

        self.overlay_frame.bind_all("<r>", self.retry)
        self.overlay_frame.bind_all("<R>", self.retry)

    def retry(self, event=None):
        self.overlay_frame.unbind_all("<r>")
        self.overlay_frame.unbind_all("<R>")
        self.retry_callback()