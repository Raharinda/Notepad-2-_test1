import tkinter as tk

from controller import twist_registry


class TwistOrchestratorMixin:
    """
    Mixin untuk semua logika twist di sisi View:
    trigger, warning overlay, launch via registry, finish, retry,
    dan victory screen.

    Bergantung pada: self.root, self.overlay_frame, self.text_area,
                     self.twist_manager, self.status_label,
                     self.twist_active
    """

    # ------------------------------------------------------------------
    # Trigger
    # ------------------------------------------------------------------

    def on_text_changed(self, event=None):
        if self.twist_active:
            return
        if self.twist_manager.all_completed():
            return

        char_count = len(self.text_area.get("1.0", "end-1c"))

        if self.twist_manager.should_trigger_twist(char_count):
            self._trigger_twist()

    def _trigger_twist(self):
        self.twist_active = True
        twist_name = self.twist_manager.get_current_twist()
        objective = self.twist_manager.get_current_objective()
        self._show_warning_overlay(twist_name, objective)

    # ------------------------------------------------------------------
    # Warning Overlay  (2 detik sebelum twist dimulai)
    # ------------------------------------------------------------------

    def _show_warning_overlay(self, twist_name: str, objective: str):
        self.overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        tk.Label(
            self.overlay_frame,
            text="⚠ WARNING ⚠",
            font=("Arial", 24, "bold"),
            fg="red",
            bg="#202020",
        ).place(relx=0.5, rely=0.3, anchor="center")

        tk.Label(
            self.overlay_frame,
            text=twist_name,
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#202020",
        ).place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(
            self.overlay_frame,
            text=objective,
            font=("Arial", 12),
            fg="white",
            bg="#202020",
        ).place(relx=0.5, rely=0.6, anchor="center")

        self.root.after(2000, self._launch_current_twist)

    def _launch_current_twist(self):
        for widget in self.overlay_frame.winfo_children():
            widget.destroy()

        twist_name = self.twist_manager.get_current_twist()

        launched = twist_registry.launch(
            twist_name,
            main_view=self,
            finish_callback=self.finish_twist,
            retry_callback=self.retry_current_twist,
        )

        if not launched:
            # Twist terdaftar di TwistManager tapi belum ada implementasinya
            print(f"[TwistOrchestrator] '{twist_name}' not implemented yet — skipping.")
            self.finish_twist()

    # ------------------------------------------------------------------
    # Finish / Retry
    # ------------------------------------------------------------------

    def finish_twist(self):
        self.twist_active = False
        self.twist_manager.complete_current_twist()

        completed = self.twist_manager.completed_twists
        self.update_twist_progress(completed)
        self.hide_overlay()

        if self.twist_manager.all_completed():
            self._show_victory_screen()

    def retry_current_twist(self):
        self.twist_active = True

        for widget in self.overlay_frame.winfo_children():
            widget.destroy()

        twist_name = self.twist_manager.get_current_twist()
        objective = self.twist_manager.get_current_objective()
        self._show_warning_overlay(twist_name, objective)

    # ------------------------------------------------------------------
    # Overlay helpers
    # ------------------------------------------------------------------

    def hide_overlay(self):
        self.overlay_frame.place_forget()

    def update_twist_progress(self, completed: int):
        self.status_label.config(text=f"Twists Completed: {completed}/3")

    # ------------------------------------------------------------------
    # Victory Screen
    # ------------------------------------------------------------------

    def _show_victory_screen(self):
        self.overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        victory_text = (
            "\n"
            "    =================================\n\n"
            "    CONGRATULATIONS\n\n"
            "    You survived Notepad.\n\n"
            "    The notebook seems satisfied...\n"
            "    for now.\n\n"
            "    [ENTER] Continue writing\n"
            "    [ESC]   Close session\n\n"
            "    =================================\n"
        )

        tk.Label(
            self.overlay_frame,
            text=victory_text,
            font=("Consolas", 14),
            bg="#202020",
            fg="white",
            justify="center",
        ).place(relx=0.5, rely=0.5, anchor="center")

        self.root.bind("<Return>", self._continue_after_victory)
        self.root.bind("<Escape>", self._close_session)

    def _continue_after_victory(self, event=None):
        self.root.unbind("<Return>")
        self.root.unbind("<Escape>")
        self.hide_overlay()

    def _close_session(self, event=None):
        self.root.destroy()

