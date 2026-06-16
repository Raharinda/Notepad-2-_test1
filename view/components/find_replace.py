import tkinter as tk
from tkinter import messagebox


class FindReplaceMixin:
    """
    Mixin untuk fitur Find & Replace.
    Bergantung pada: self.text_area, self.root,
                     self.find_dialog, self.last_search_index
    """

    def open_find_dialog(self):
        self._open_search_dialog(show_replace=False)

    def open_replace_dialog(self):
        self._open_search_dialog(show_replace=True)

    def _open_search_dialog(self, show_replace: bool):
        # Jika dialog sudah terbuka, cukup fokus ulang
        if self.find_dialog is not None and self.find_dialog.winfo_exists():
            self.find_dialog.lift()
            self.find_entry.focus_set()
            if show_replace:
                self.replace_frame.pack(fill="x", padx=10, pady=(0, 5))
            return

        self.find_dialog = tk.Toplevel(self.root)
        self.find_dialog.title("Replace" if show_replace else "Find")
        self.find_dialog.resizable(False, False)
        self.find_dialog.transient(self.root)

        # ---- Find row ----
        find_frame = tk.Frame(self.find_dialog)
        find_frame.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(find_frame, text="Find:", width=10, anchor="w").pack(side="left")

        self.find_entry = tk.Entry(find_frame, width=30)
        self.find_entry.pack(side="left", fill="x", expand=True)
        self.find_entry.focus_set()

        # ---- Replace row ----
        self.replace_frame = tk.Frame(self.find_dialog)

        tk.Label(
            self.replace_frame, text="Replace with:", width=10, anchor="w"
        ).pack(side="left")

        self.replace_entry = tk.Entry(self.replace_frame, width=30)
        self.replace_entry.pack(side="left", fill="x", expand=True)

        if show_replace:
            self.replace_frame.pack(fill="x", padx=10, pady=(0, 5))

        # ---- Buttons row ----
        button_frame = tk.Frame(self.find_dialog)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(button_frame, text="Find Next", command=self.find_next).pack(
            side="left", padx=2
        )

        if show_replace:
            tk.Button(
                button_frame, text="Replace", command=self.replace_current
            ).pack(side="left", padx=2)
            tk.Button(
                button_frame, text="Replace All", command=self.replace_all
            ).pack(side="left", padx=2)

        tk.Button(
            button_frame, text="Close", command=self.close_find_dialog
        ).pack(side="right", padx=2)

        self.find_entry.bind("<Return>", lambda e: self.find_next())
        self.find_dialog.bind("<Escape>", lambda e: self.close_find_dialog())

        self.last_search_index = "1.0"

    def close_find_dialog(self):
        if self.find_dialog is not None:
            self.text_area.tag_remove("search_highlight", "1.0", "end")
            self.find_dialog.destroy()
            self.find_dialog = None

    def find_next(self):
        query = self.find_entry.get()
        if not query:
            return

        self.text_area.tag_remove("search_highlight", "1.0", "end")

        start_index = self.text_area.search(
            query, self.last_search_index, stopindex="end", nocase=True
        )

        # Wrap around
        if not start_index:
            start_index = self.text_area.search(
                query, "1.0", stopindex="end", nocase=True
            )

        if not start_index:
            messagebox.showinfo("Find", f'Cannot find "{query}".')
            return

        end_index = f"{start_index}+{len(query)}c"
        self.text_area.tag_add("search_highlight", start_index, end_index)
        self.text_area.mark_set("insert", end_index)
        self.text_area.see(start_index)
        self.last_search_index = end_index

    def replace_current(self):
        query = self.find_entry.get()
        replacement = self.replace_entry.get()
        if not query:
            return

        ranges = self.text_area.tag_ranges("search_highlight")
        if ranges:
            start, end = ranges[0], ranges[1]
            self.text_area.delete(start, end)
            self.text_area.insert(start, replacement)
            self.last_search_index = f"{start}+{len(replacement)}c"

        self.find_next()

    def replace_all(self):
        query = self.find_entry.get()
        replacement = self.replace_entry.get()
        if not query:
            return

        content = self.text_area.get("1.0", "end-1c")
        count = content.lower().count(query.lower())

        if count == 0:
            messagebox.showinfo("Replace All", f'Cannot find "{query}".')
            return

        new_content = content.replace(query, replacement)
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", new_content)
        self.last_search_index = "1.0"

        messagebox.showinfo("Replace All", f"Replaced {count} occurrence(s).")

