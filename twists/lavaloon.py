import tkinter as tk
import random

from utils import gemini_client


class LavaloonTwist:
    """
    Lavaloon — versi upgrade dengan cloning system + visual effects.

    Penambahan dibanding versi lama:
      - Bola lavaloon meng-clone diri secara otomatis tiap interval
        waktu tertentu (interval makin pendek = makin sering seiring
        difficulty). Tiap clone sedikit lebih lambat dari induknya
        agar tetap winnable, dan jumlah musuh dibatasi (cap) supaya
        tidak unplayable.
      - Trail/particle effect: setiap bola meninggalkan jejak titik
        yang fade out, memberi kesan gerakan lebih hidup.
      - Screen shake ringan (canvas bergeser cepat) saat player
        kehilangan nyawa, untuk memberi feedback dampak yang lebih
        terasa.
      - Progress fill rate menurun & drain rate naik di level tinggi.
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

        self.mouse_x = 0
        self.mouse_y = 0

        self.base_speed = min(3 + difficulty * 0.6, 8.0)

        self.lives = 3 if difficulty < 2 else 2
        self.invincible = False

        self.progress = 0
        self.hovering = False

        self.fill_rate = max(0.4, 1.0 - difficulty * 0.08)
        self.drain_rate = min(0.3 + difficulty * 0.04, 0.7)

        # Clone interval makin pendek seiring difficulty (lebih sering clone)
        # difficulty 0 = 9000ms, difficulty 3 = 6900ms, difficulty 5 = 5500ms
        self.clone_interval_ms = max(3000, 9000 - difficulty * 800)

        self.hold_button_shifts = difficulty >= 2

        # Dynamically increase max enemies at high difficulty
        self.max_enemies = min(5 + difficulty, 10)

        self.clone_job = None
        self.progress_job = None
        self.move_job = None
        self.shift_job = None
        self.shake_job = None
        self.message_job = None

        self.overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self.overlay_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._canvas_base_x = 0
        self._canvas_base_y = 0

        self.lives_label = tk.Label(
            self.overlay_frame, text="", font=("Arial", 16), bg="black", fg="white"
        )
        self.lives_label.place(relx=0.02, rely=0.02)
        self.update_lives_display()

        self.enemy_count_label = tk.Label(
            self.overlay_frame, text="", font=("Arial", 11), bg="black", fg="#e67e22"
        )
        self.enemy_count_label.place(relx=0.02, rely=0.08)

        self.message_label = tk.Label(
            self.overlay_frame, text="", font=("Arial", 12), bg="black", fg="#ecf0f1"
        )
        self.message_label.place(relx=0.5, rely=0.5, anchor="center")

        self.progress_label = tk.Label(
            self.overlay_frame, text="Progress", bg="black", fg="white"
        )
        self.progress_label.place(relx=0.4, rely=0.02)

        self.progress_bar = tk.Canvas(
            self.overlay_frame, width=300, height=20, bg="gray20", highlightthickness=1
        )
        self.progress_bar.place(relx=0.5, rely=0.02, anchor="n")

        self.progress_fill = self.progress_bar.create_rectangle(
            0, 0, 0, 20, fill="#27ae60"
        )

        self.hold_button = tk.Label(
            self.overlay_frame,
            text="HOLD HERE",
            font=("Arial", 14, "bold"),
            bg="white",
            padx=20,
            pady=10,
        )
        self.hold_button.place(relx=0.5, rely=0.85, anchor="center")
        self.hold_button.bind("<Enter>", self.start_hover)
        self.hold_button.bind("<Leave>", self.stop_hover)

        # Sistem multi-enemy: setiap enemy adalah dict
        # {canvas_id, speed, trail: [list of trail dot ids]}
        self.enemies = []
        first = self._spawn_enemy(100, 100, self.base_speed, color="red")
        self.enemies.append(first)

        self.canvas.bind("<Motion>", self.mouse_moved)

        self.game_over = False

        self.move_enemies()
        self.update_progress()
        self._schedule_clone()

        if self.hold_button_shifts:
            self._schedule_button_shift()

        self._schedule_messages()

    def _get_random_message(self):
        """Generate random encouragement or warning using Gemini or fallback."""
        messages = [
            "Hold steady!",
            "Keep going!",
            "Don't let go!",
            "Push harder!",
            "They're getting closer!",
            "You can do this!",
            "Focus!",
            "Almost there!",
            "Watch out!",
            "Keep holding!",
        ]
        
        if not gemini_client.is_available():
            return random.choice(messages)
        
        try:
            context = "survival game with approaching enemies" 
            prompt = f"Generate a single short motivational or warning phrase (under 4 words) for a {context}. Make it intense. Reply with ONLY the phrase."
            msg = gemini_client.generate_text(prompt)
            if msg and isinstance(msg, str) and len(msg.strip()) > 2:
                return msg.strip()[:50]
        except Exception:
            pass
        
        return random.choice(messages)

    def _schedule_messages(self):
        if self.game_over:
            return
        
        delay = random.randint(1500, 3500)
        msg = self._get_random_message()
        self.message_label.config(text=msg)
        
        self.message_job = self.overlay_frame.after(delay, self._schedule_messages)

    # ------------------------------------------------------------------
    # Enemy spawning / cloning
    # ------------------------------------------------------------------

    def _spawn_enemy(self, x, y, speed, color="red"):
        oval_id = self.canvas.create_oval(
            x, y, x + 50, y + 50, fill=color, outline=""
        )
        glow_id = self.canvas.create_oval(
            x - 5, y - 5, x + 55, y + 55, outline=color, width=1
        )
        self.canvas.tag_lower(glow_id, oval_id)

        return {
            "id": oval_id,
            "glow_id": glow_id,
            "speed": speed,
            "color": color,
            "trail": [],
        }

    def _schedule_clone(self):
        if self.game_over:
            return

        self.clone_job = self.overlay_frame.after(
            self.clone_interval_ms, self._do_clone
        )

    def _do_clone(self):
        if self.game_over or not self.canvas.winfo_exists():
            return

        if len(self.enemies) < self.max_enemies:
            parent = random.choice(self.enemies)
            try:
                coords = self.canvas.coords(parent["id"])
            except tk.TclError:
                coords = None

            if coords:
                x1, y1, x2, y2 = coords
                # Clone sedikit lebih lambat dari induk (tetap winnable)
                clone_speed = max(1.5, parent["speed"] * 0.85)

                offset = random.randint(-40, 40)
                clone = self._spawn_enemy(
                    x1 + offset, y1 + offset, clone_speed, color="#ff6347"
                )
                self.enemies.append(clone)

                self._flash_clone_warning()

        self.enemy_count_label.config(text=f"Threats: {len(self.enemies)}")
        self._schedule_clone()

    def _flash_clone_warning(self):
        warning = tk.Label(
            self.overlay_frame,
            text="⚠ IT SPLIT! ⚠",
            font=("Arial", 16, "bold"),
            bg="black",
            fg="#ff4444",
        )
        warning.place(relx=0.5, rely=0.12, anchor="center")
        self.overlay_frame.after(900, warning.destroy)

    # ------------------------------------------------------------------
    # Hover / mouse tracking
    # ------------------------------------------------------------------

    def start_hover(self, event):
        self.hovering = True

    def stop_hover(self, event):
        self.hovering = False

    def mouse_moved(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    # ------------------------------------------------------------------
    # Lives
    # ------------------------------------------------------------------

    def update_lives_display(self):
        if self.lives == 3:
            text = "♥ ♥ ♥"
        elif self.lives == 2:
            text = "♥ ♥ ♡"
        elif self.lives == 1:
            text = "♥ ♡ ♡"
        else:
            text = "♡ ♡ ♡"

        self.lives_label.config(text=text, fg="red")

    def lose_life(self):
        if self.invincible:
            return

        self.lives -= 1
        self.update_lives_display()
        self.invincible = True

        self._screen_shake()

        if not self.game_over:
            self.overlay_frame.after(1000, self.end_invincibility)

        if self.lives <= 0:
            self.display_game_over()

    def end_invincibility(self):
        self.invincible = False

    def _screen_shake(self, frames: int = 8):
        if self.game_over or not self.canvas.winfo_exists():
            self.shake_job = None
            return
        
        if frames <= 0:
            try:
                self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
            except tk.TclError:
                pass
            self.shake_job = None
            return

        offset_x = random.randint(-8, 8)
        offset_y = random.randint(-8, 8)
        try:
            self.canvas.place(x=offset_x, y=offset_y, relwidth=1, relheight=1)
        except tk.TclError:
            self.shake_job = None
            return

        self.shake_job = self.overlay_frame.after(30, lambda: self._screen_shake(frames - 1))

    def display_game_over(self):
        if self.game_over:
            return

        self.game_over = True
        self._cancel_scheduled_jobs()

        try:
            for widget in list(self.overlay_frame.winfo_children()):
                if widget.winfo_exists():
                    widget.destroy()
        except tk.TclError:
            pass

        game_over = tk.Label(
            self.overlay_frame,
            text="LAVALOON GOT YOU\n\n[R] Retry",
            font=("Arial", 24, "bold"),
            bg="black",
            fg="red",
        )
        game_over.place(relx=0.5, rely=0.5, anchor="center")

        self.overlay_frame.bind_all("<r>", self.retry)
        self.overlay_frame.bind_all("<R>", self.retry)

    # ------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------

    def update_progress(self):
        if self.game_over:
            return

        if self.hovering:
            self.progress += self.fill_rate
        else:
            self.progress -= self.drain_rate

        self.progress = max(0, min(100, self.progress))

        width = self.progress * 3
        color = "#27ae60" if self.progress >= 60 else ("#f1c40f" if self.progress >= 25 else "#e74c3c")
        self.progress_bar.coords(self.progress_fill, 0, 0, width, 20)
        self.progress_bar.itemconfig(self.progress_fill, fill=color)

        if self.progress >= 100:
            self.game_over = True
            self._cancel_scheduled_jobs()
            # Destroy widgets safely (iterate over copy to avoid modification during iteration)
            try:
                for widget in list(self.overlay_frame.winfo_children()):
                    if widget.winfo_exists():
                        widget.destroy()
            except tk.TclError:
                pass
            self.finish_callback()
            return

        self.progress_job = self.overlay_frame.after(50, self.update_progress)

    # ------------------------------------------------------------------
    # Enemy movement (semua enemy digerakkan dalam satu loop)
    # ------------------------------------------------------------------

    def move_enemies(self):
        if self.game_over or not self.canvas.winfo_exists():
            return

        for enemy in self.enemies:
            try:
                coords = self.canvas.coords(enemy["id"])
            except tk.TclError:
                continue
            if not coords:
                continue

            x1, y1, x2, y2 = coords
            circle_x = (x1 + x2) / 2
            circle_y = (y1 + y2) / 2

            dx = self.mouse_x - circle_x
            dy = self.mouse_y - circle_y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance > 0:
                move_x = (dx / distance) * enemy["speed"]
                move_y = (dy / distance) * enemy["speed"]
                self.canvas.move(enemy["id"], move_x, move_y)
                self.canvas.move(enemy["glow_id"], move_x, move_y)

            # Trail effect: tinggalkan jejak titik fade
            self._leave_trail(enemy, circle_x, circle_y)

            if distance < 25:
                self.lose_life()

        self.move_job = self.canvas.after(30, self.move_enemies)

    def _leave_trail(self, enemy, x, y):
        dot = self.canvas.create_oval(
            x - 4, y - 4, x + 4, y + 4, fill=enemy["color"], outline=""
        )
        self.canvas.tag_lower(dot, enemy["glow_id"])
        enemy["trail"].append(dot)

        # Batasi panjang trail & fade out dengan menghapus dot lama
        if len(enemy["trail"]) > 6:
            old_dot = enemy["trail"].pop(0)
            try:
                self.canvas.delete(old_dot)
            except tk.TclError:
                pass

    # ------------------------------------------------------------------
    # Hold button shifting (difficulty >= 5)
    # ------------------------------------------------------------------

    def _schedule_button_shift(self):
        if self.game_over:
            return

        delay = random.randint(2500, 4500)
        self.shift_job = self.overlay_frame.after(delay, self._shift_hold_button)

    def _shift_hold_button(self):
        if self.game_over or not self.overlay_frame.winfo_exists():
            return

        new_relx = 0.5 + random.uniform(-0.08, 0.08)
        new_rely = 0.85 + random.uniform(-0.05, 0.03)

        try:
            self.hold_button.place(relx=new_relx, rely=new_rely, anchor="center")
        except tk.TclError:
            return

        self._schedule_button_shift()

    def _cancel_scheduled_jobs(self):
        for job_id in (self.clone_job, self.progress_job, self.move_job, self.shift_job, self.shake_job, self.message_job):
            if job_id is not None:
                try:
                    self.overlay_frame.after_cancel(job_id)
                except Exception:
                    pass

        self.clone_job = None
        self.progress_job = None
        self.move_job = None
        self.shift_job = None
        self.shake_job = None
        self.message_job = None

    # ------------------------------------------------------------------
    # Retry
    # ------------------------------------------------------------------

    def retry(self, event=None):
        self.overlay_frame.unbind_all("<r>")
        self.overlay_frame.unbind_all("<R>")
        self.game_over = True
        self._cancel_scheduled_jobs()
        self.retry_callback()