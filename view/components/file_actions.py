import os
import tkinter as tk
from tkinter import filedialog, messagebox


class FileActionsMixin:
    """
    Mixin untuk semua aksi File menu:
    New, Open, Save, Save As, Exit, dan update title.
    """

    def new_file(self):
        if self.twist_active:
            return
        self.text_area.delete("1.0", "end")
        self.current_file_path = None
        self.update_title()
        self.update_cursor_position()

    def open_file(self):
        if self.twist_active:
            return

        file_path = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text Files", "*.txt"),
                ("All Files", "*.*"),
            ],
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", content)
            self.current_file_path = file_path
            self.update_title()
            self.update_cursor_position()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def save_file(self):
        if self.current_file_path:
            self._write_to_file(self.current_file_path)
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text Files", "*.txt"),
                ("All Files", "*.*"),
            ],
        )
        if not file_path:
            return
        self.current_file_path = file_path
        self._write_to_file(file_path)

    def _write_to_file(self, file_path: str):
        try:
            content = self.text_area.get("1.0", "end-1c")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.update_title()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")

    def exit_app(self):
        self.root.destroy()

    def update_title(self):
        if self.current_file_path:
            name = os.path.basename(self.current_file_path)
            self.root.title(f"{name} - Notepad")
        else:
            self.root.title("Untitled - Notepad")

