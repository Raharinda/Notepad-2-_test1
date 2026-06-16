import tkinter as tk
from tkinter import font as tkfont


class FormatActionsMixin:
    """
    Mixin untuk Format menu:
    Word Wrap, Font dialog, Zoom (in/out/reset).
    Bergantung pada: self.text_area, self.root, self.word_wrap_var,
                     self.text_font, self.base_font_family,
                     self.base_font_size, self.zoom_percent,
                     self.zoom_label
    """

    # ------------------------------------------------------------------
    # Word Wrap
    # ------------------------------------------------------------------

    def toggle_word_wrap(self):
        self.text_area.config(wrap="word" if self.word_wrap_var.get() else "none")

    # ------------------------------------------------------------------
    # Font Dialog
    # ------------------------------------------------------------------

    def open_font_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Font")
        dialog.resizable(False, False)
        dialog.transient(self.root)

        # ---- Font family ----
        tk.Label(dialog, text="Font:").grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 0)
        )

        families = sorted(set(tkfont.families()))
        family_var = tk.StringVar(value=self.text_font.actual("family"))

        family_list = tk.Listbox(dialog, height=8, exportselection=False)
        for fam in families:
            family_list.insert("end", fam)

        try:
            idx = families.index(family_var.get())
            family_list.selection_set(idx)
            family_list.see(idx)
        except ValueError:
            pass

        family_list.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # ---- Font size ----
        tk.Label(dialog, text="Size:").grid(
            row=0, column=1, sticky="w", padx=10, pady=(10, 0)
        )

        size_var = tk.IntVar(value=self.text_font.actual("size"))
        size_spin = tk.Spinbox(dialog, from_=6, to=72, textvariable=size_var, width=5)
        size_spin.grid(row=1, column=1, padx=10, pady=5, sticky="nw")

        # ---- Preview ----
        preview_label = tk.Label(
            dialog, text="AaBbYyZz 0123", relief="solid", bd=1, padx=10, pady=10
        )
        preview_label.grid(
            row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew"
        )

        def update_preview(*_):
            sel = family_list.curselection()
            family = family_list.get(sel[0]) if sel else family_var.get()
            try:
                size = size_var.get()
            except tk.TclError:
                size = self.base_font_size
            preview_label.config(font=(family, max(6, min(72, size))))

        family_list.bind("<<ListboxSelect>>", update_preview)
        size_spin.bind("<KeyRelease>", update_preview)
        size_spin.bind("<<Increment>>", update_preview)
        size_spin.bind("<<Decrement>>", update_preview)
        update_preview()

        # ---- Buttons ----
        button_frame = tk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))

        def apply_font():
            sel = family_list.curselection()
            family = family_list.get(sel[0]) if sel else family_var.get()
            try:
                size = size_var.get()
            except tk.TclError:
                size = self.base_font_size
            size = max(6, min(72, size))
            self.base_font_family = family
            self.base_font_size = size
            self.zoom_percent = 100
            self.text_font.config(family=family, size=size)
            self.zoom_label.config(text="100%")
            dialog.destroy()

        tk.Button(button_frame, text="OK", command=apply_font).pack(
            side="left", padx=5
        )
        tk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(
            side="left", padx=5
        )

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------

    def on_ctrl_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        self.zoom_percent = min(400, self.zoom_percent + 10)
        self._apply_zoom()

    def zoom_out(self):
        self.zoom_percent = max(20, self.zoom_percent - 10)
        self._apply_zoom()

    def zoom_reset(self):
        self.zoom_percent = 100
        self._apply_zoom()

    def _apply_zoom(self):
        new_size = max(1, int(self.base_font_size * self.zoom_percent / 100))
        self.text_font.config(size=new_size)
        self.zoom_label.config(text=f"{self.zoom_percent}%")

