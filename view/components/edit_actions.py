import tkinter as tk


class EditActionsMixin:
    """
    Mixin untuk semua aksi Edit menu:
    Undo, Redo, Cut, Copy, Paste.
    """

    def undo_action(self):
        try:
            self.text_area.edit_undo()
        except tk.TclError:
            pass

    def redo_action(self):
        try:
            self.text_area.edit_redo()
        except tk.TclError:
            pass

    def cut_action(self):
        try:
            self.text_area.event_generate("<<Cut>>")
        except tk.TclError:
            pass

    def copy_action(self):
        try:
            self.text_area.event_generate("<<Copy>>")
        except tk.TclError:
            pass

    def paste_action(self):
        try:
            self.text_area.event_generate("<<Paste>>")
        except tk.TclError:
            pass

