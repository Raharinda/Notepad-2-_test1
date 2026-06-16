import tkinter as tk
from tkinter import font as tkfont

from view.components import (
    MenuBuilderMixin,
    FileActionsMixin,
    EditActionsMixin,
    FindReplaceMixin,
    FormatActionsMixin,
    AIActionsMixin,
    ExcuseActionsMixin,
    TwistOrchestratorMixin,
)


class MainView(
    MenuBuilderMixin,
    FileActionsMixin,
    EditActionsMixin,
    FindReplaceMixin,
    FormatActionsMixin,
    AIActionsMixin,
    ExcuseActionsMixin,
    TwistOrchestratorMixin,
):
    """
    View utama Trolling Notepad.

    Kelas ini hanya bertanggung jawab atas:
      - Inisialisasi state
      - Pembuatan widget (text area, status bar, overlay)
      - Binding event utama

    Semua logika bisnis/UI didelegasikan ke mixin masing-masing.
    """

    def __init__(self, root: tk.Tk, twist_manager):
        self.root = root
        self.twist_manager = twist_manager

        self.root.title("Notepad")
        self.root.geometry("800x600")

        # ── State ──────────────────────────────────────────────────────
        self.twist_active: bool = False
        self.current_file_path: str | None = None

        self.base_font_family = "Consolas"
        self.base_font_size = 12
        self.zoom_percent = 100

        self.text_font = tkfont.Font(
            family=self.base_font_family,
            size=self.base_font_size,
        )

        self.word_wrap_var = tk.BooleanVar(value=True)
        self.find_dialog: tk.Toplevel | None = None
        self.last_search_index = "1.0"

        # ── Widgets ────────────────────────────────────────────────────
        self.build_menu_bar()
        self._build_text_area()
        self._build_status_bar()
        self._build_overlay()
        self._bind_events()

        # ── Initial state ──────────────────────────────────────────────
        self.update_title()
        self.update_cursor_position()

    # ------------------------------------------------------------------
    # Widget builders (layout only — no logic)
    # ------------------------------------------------------------------

    def _build_text_area(self):
        self.text_area = tk.Text(
            self.root,
            font=self.text_font,
            wrap="word",
            undo=True,
            autoseparators=True,
            maxundo=-1,
        )
        self.text_area.pack(expand=True, fill="both")

        self.text_area.tag_configure(
            "search_highlight",
            background="#ffd54f",
            foreground="black",
        )

    def _build_status_bar(self):
        self.status_bar = tk.Frame(self.root)
        self.status_bar.pack(fill="x", side="bottom")

        # Kiri: progres twist (direferensikan langsung oleh BloodmoonTwist)
        self.status_label = tk.Label(
            self.status_bar,
            text="Twists Completed: 0/3",
            anchor="w",
        )
        self.status_label.pack(side="left", padx=8)

        # Kanan: zoom %
        self.zoom_label = tk.Label(
            self.status_bar,
            text="100%",
            anchor="e",
            width=6,
        )
        self.zoom_label.pack(side="right", padx=8)

        # Kanan: posisi kursor
        self.position_label = tk.Label(
            self.status_bar,
            text="Ln 1, Col 1",
            anchor="e",
            width=15,
        )
        self.position_label.pack(side="right", padx=8)

    def _build_overlay(self):
        """Frame transparan yang di-place di atas text_area saat twist aktif."""
        self.overlay_frame = tk.Frame(self.root, bg="#202020")

    def _bind_events(self):
        ta = self.text_area

        # Twist trigger + cursor position (keduanya pada KeyRelease)
        ta.bind("<KeyRelease>", self.on_text_changed)
        ta.bind("<KeyRelease>", self.update_cursor_position, add="+")
        ta.bind("<ButtonRelease-1>", self.update_cursor_position)

        # Zoom via Ctrl+scroll (Windows/macOS dan Linux)
        ta.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)
        ta.bind("<Control-Button-4>", lambda e: self.zoom_in())
        ta.bind("<Control-Button-5>", lambda e: self.zoom_out())

    # ------------------------------------------------------------------
    # Status bar helper (dipakai oleh mixin lain)
    # ------------------------------------------------------------------

    def update_cursor_position(self, event=None):
        try:
            line, col = self.text_area.index("insert").split(".")
            self.position_label.config(text=f"Ln {line}, Col {int(col) + 1}")
        except tk.TclError:
            pass
