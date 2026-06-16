import tkinter as tk

from utils.excuse_generator import get_all_categories


class MenuBuilderMixin:
    """
    Mixin yang membangun seluruh menu bar dan keyboard shortcuts.
    Dipanggil sekali dari MainView.__init__().
    """

    def build_menu_bar(self):
        menu_bar = tk.Menu(self.root)

        menu_bar.add_cascade(label="File",   menu=self._build_file_menu(menu_bar))
        menu_bar.add_cascade(label="Edit",   menu=self._build_edit_menu(menu_bar))
        menu_bar.add_cascade(label="Format", menu=self._build_format_menu(menu_bar))
        menu_bar.add_cascade(label="AI",     menu=self._build_ai_menu(menu_bar))
        menu_bar.add_cascade(label="Excuse", menu=self._build_excuse_menu(menu_bar))

        self.root.config(menu=menu_bar)
        self._bind_shortcuts()

    # ------------------------------------------------------------------
    # Sub-menus
    # ------------------------------------------------------------------

    def _build_file_menu(self, parent: tk.Menu) -> tk.Menu:
        m = tk.Menu(parent, tearoff=0)
        m.add_command(label="New",       accelerator="Ctrl+N", command=self.new_file)
        m.add_command(label="Open...",   accelerator="Ctrl+O", command=self.open_file)
        m.add_command(label="Save",      accelerator="Ctrl+S", command=self.save_file)
        m.add_command(label="Save As...",accelerator="Ctrl+Shift+S", command=self.save_file_as)
        m.add_separator()
        m.add_command(label="Exit", command=self.exit_app)
        return m

    def _build_edit_menu(self, parent: tk.Menu) -> tk.Menu:
        m = tk.Menu(parent, tearoff=0)
        m.add_command(label="Undo",    accelerator="Ctrl+Z", command=self.undo_action)
        m.add_command(label="Redo",    accelerator="Ctrl+Y", command=self.redo_action)
        m.add_separator()
        m.add_command(label="Cut",     accelerator="Ctrl+X", command=self.cut_action)
        m.add_command(label="Copy",    accelerator="Ctrl+C", command=self.copy_action)
        m.add_command(label="Paste",   accelerator="Ctrl+V", command=self.paste_action)
        m.add_separator()
        m.add_command(label="Find...",    accelerator="Ctrl+F", command=self.open_find_dialog)
        m.add_command(label="Replace...", accelerator="Ctrl+H", command=self.open_replace_dialog)
        return m

    def _build_format_menu(self, parent: tk.Menu) -> tk.Menu:
        m = tk.Menu(parent, tearoff=0)
        m.add_checkbutton(
            label="Word Wrap",
            variable=self.word_wrap_var,
            command=self.toggle_word_wrap,
        )
        m.add_command(label="Font...", command=self.open_font_dialog)
        return m

    def _build_ai_menu(self, parent: tk.Menu) -> tk.Menu:
        m = tk.Menu(parent, tearoff=0)
        m.add_command(label="Rewrite Selection",   command=lambda: self.run_ai_action("rewrite"))
        m.add_command(label="Summarize",           command=lambda: self.run_ai_action("summarize"))
        m.add_command(label="Translate to English",command=lambda: self.run_ai_action("translate"))
        m.add_command(label="Continue Writing",    command=lambda: self.run_ai_action("continue"))
        return m

    def _build_excuse_menu(self, parent: tk.Menu) -> tk.Menu:
        if not hasattr(self, "excuse_category_var"):
            self.excuse_category_var = tk.StringVar(value="auto")

        if not hasattr(self, "excuse_tone_var"):
            self.excuse_tone_var = tk.StringVar(value="normal")

        m = tk.Menu(parent, tearoff=0)

        category_menu = tk.Menu(m, tearoff=0)
        for category in ["auto"] + get_all_categories():
            category_menu.add_radiobutton(
                label=category,
                variable=self.excuse_category_var,
                value=category,
            )

        tone_menu = tk.Menu(m, tearoff=0)
        for tone in ("normal", "serious", "absurd"):
            tone_menu.add_radiobutton(
                label=tone,
                variable=self.excuse_tone_var,
                value=tone,
            )

        m.add_cascade(label="Category", menu=category_menu)
        m.add_cascade(label="Tone", menu=tone_menu)
        m.add_separator()
        m.add_command(label="Generate Excuse", command=self.generate_excuse)

        return m

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def _bind_shortcuts(self):
        bind = self.root.bind

        for seq in ("<Control-n>", "<Control-N>"):
            bind(seq, lambda e: self.new_file())
        for seq in ("<Control-o>", "<Control-O>"):
            bind(seq, lambda e: self.open_file())
        for seq in ("<Control-s>", "<Control-S>"):
            bind(seq, lambda e: self.save_file())
        for seq in ("<Control-Shift-s>", "<Control-Shift-S>"):
            bind(seq, lambda e: self.save_file_as())
        for seq in ("<Control-z>", "<Control-Z>"):
            bind(seq, lambda e: self.undo_action())
        for seq in ("<Control-y>", "<Control-Y>"):
            bind(seq, lambda e: self.redo_action())
        for seq in ("<Control-f>", "<Control-F>"):
            bind(seq, lambda e: self.open_find_dialog())
        for seq in ("<Control-h>", "<Control-H>"):
            bind(seq, lambda e: self.open_replace_dialog())

        bind("<Control-plus>",  lambda e: self.zoom_in())
        bind("<Control-equal>", lambda e: self.zoom_in())
        bind("<Control-minus>", lambda e: self.zoom_out())
        bind("<Control-0>",     lambda e: self.zoom_reset())

