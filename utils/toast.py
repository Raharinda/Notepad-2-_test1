"""
Toast Notification Helper
==========================
Komponen kecil reusable untuk menampilkan notifikasi ala OS popup
(slide-in dari pojok kanan atas, auto-dismiss) di atas sebuah parent
widget Tkinter (biasanya overlay_frame milik sebuah twist).

Dipakai oleh: SelfAwareCalculatorTwist, BrokenCalculatorTwist, dan
twist lain yang ingin menampilkan pesan singkat tanpa mengganggu
layout utama.

Pemakaian:
    from utils.toast import ToastManager

    self.toast = ToastManager(self.overlay_frame)
    self.toast.show("Wrong answer, genius.", kind="roast")
    ...
    self.toast.cancel_all()   # panggil ini saat twist dibersihkan
"""

import tkinter as tk


_KIND_STYLES = {
    "roast": {"bg": "#c0392b", "fg": "white", "title": "CALCULATOR SAYS"},
    "warning": {"bg": "#e67e22", "fg": "white", "title": "WARNING"},
    "info": {"bg": "#2c3e50", "fg": "white", "title": "NOTICE"},
}


class ToastManager:
    """Mengelola satu atau beberapa toast yang slide-in/out di pojok kanan atas."""

    def __init__(self, parent: tk.Widget, max_visible: int = 3):
        self.parent = parent
        self.max_visible = max_visible
        self._active_toasts: list[dict] = []
        self._pending_jobs: list[tuple] = []  # (widget_or_None, job_id)

    def show(self, message: str, kind: str = "info", duration_ms: int = 2600):
        style = _KIND_STYLES.get(kind, _KIND_STYLES["info"])

        toast_frame = tk.Frame(
            self.parent,
            bg=style["bg"],
            highlightthickness=1,
            highlightbackground="#000000",
        )

        tk.Label(
            toast_frame,
            text=style["title"],
            bg=style["bg"],
            fg=style["fg"],
            font=("Arial", 8, "bold"),
            anchor="w",
        ).pack(fill="x", padx=10, pady=(6, 0))

        tk.Label(
            toast_frame,
            text=message,
            bg=style["bg"],
            fg=style["fg"],
            font=("Arial", 10),
            anchor="w",
            justify="left",
            wraplength=240,
        ).pack(fill="x", padx=10, pady=(0, 8))

        # Posisi awal: start dari luar layar (kanan), lalu slide-in
        toast_frame.place(relx=1.05, rely=0.04, anchor="ne")

        entry = {"frame": toast_frame, "target_rely": None}
        self._reflow_targets(new_entry=entry)
        self._active_toasts.append(entry)

        self._slide_in(entry)

        dismiss_job = self.parent.after(
            duration_ms, lambda: self._dismiss(entry)
        )
        self._pending_jobs.append((toast_frame, dismiss_job))

        # Batasi jumlah toast aktif biar tidak menumpuk tak terkendali
        while len(self._active_toasts) > self.max_visible:
            oldest = self._active_toasts[0]
            self._dismiss(oldest)

    # ------------------------------------------------------------------
    # Internal animation
    # ------------------------------------------------------------------

    def _reflow_targets(self, new_entry=None):
        """Hitung ulang posisi rely tiap toast aktif (stack vertikal)."""
        entries = self._active_toasts + ([new_entry] if new_entry else [])

        for i, entry in enumerate(entries):
            entry["target_rely"] = 0.04 + i * 0.12

    def _slide_in(self, entry, step: int = 0):
        if entry["frame"] not in self._frame_alive_check():
            return

        target_relx = 0.985
        current_x = 1.05 - (step * 0.03)

        if current_x <= target_relx:
            entry["frame"].place(
                relx=target_relx, rely=entry["target_rely"], anchor="ne"
            )
            return

        entry["frame"].place(relx=current_x, rely=entry["target_rely"], anchor="ne")
        self.parent.after(12, lambda: self._slide_in(entry, step + 1))

    def _frame_alive_check(self):
        # Helper kecil supaya tidak crash kalau frame sudah destroyed
        alive = []
        for entry in self._active_toasts:
            try:
                if entry["frame"].winfo_exists():
                    alive.append(entry["frame"])
            except tk.TclError:
                pass
        return alive

    def _dismiss(self, entry):
        if entry not in self._active_toasts:
            return

        try:
            if entry["frame"].winfo_exists():
                entry["frame"].destroy()
        except tk.TclError:
            pass

        self._active_toasts.remove(entry)
        self._reflow_targets()

        # Re-posisikan toast yang masih aktif ke target baru
        for remaining in self._active_toasts:
            try:
                if remaining["frame"].winfo_exists():
                    remaining["frame"].place(
                        relx=0.985, rely=remaining["target_rely"], anchor="ne"
                    )
            except tk.TclError:
                pass

    def cancel_all(self):
        """Panggil ini saat twist dibersihkan, supaya tidak ada after() job nyangkut."""
        for widget, job_id in self._pending_jobs:
            try:
                self.parent.after_cancel(job_id)
            except (tk.TclError, ValueError):
                pass

        for entry in list(self._active_toasts):
            try:
                if entry["frame"].winfo_exists():
                    entry["frame"].destroy()
            except tk.TclError:
                pass

        self._active_toasts.clear()
        self._pending_jobs.clear()