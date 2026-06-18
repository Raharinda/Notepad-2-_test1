import threading
import tkinter as tk
from tkinter import messagebox

from utils import gemini_client
from utils.excuse_generator import generate_ai_excuse


class ExcuseActionsMixin:
    """Aksi untuk Excuse Generator di menu bar."""

    def generate_excuse(self):
        if not gemini_client.is_available():
            messagebox.showwarning(
                "Excuse Generator Unavailable",
                "Gemini belum dikonfigurasi.\n\n"
                "Install: pip install google-genai\n"
                "Lalu set environment variable GEMINI_API_KEY.",
            )
            return

        try:
            selected_context = self.text_area.get("sel.first", "sel.last")
        except tk.TclError:
            selected_context = ""

        context = self._prompt_excuse_context(selected_context)
        if context is None:
            return

        category = self.excuse_category_var.get()
        tone = self.excuse_tone_var.get()

        self._show_excuse_dialog("Generating excuse...", loading=True)
        self.status_label.config(text="Generating excuse...")
        self._set_excuse_button_state("disabled")

        threading.Thread(
            target=self._excuse_worker,
            args=(category, tone, context),
            daemon=True,
        ).start()

    def _prompt_excuse_context(self, initial_context: str) -> str | None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Konteks Excuse")
        dialog.geometry("480x260")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text=(
                "Masukkan konteks singkat untuk excuse.\n"
                "Contoh: 'Telat kerja karena macet', 'Belum selesai tugas kantor', atau 'Minta perpanjangan deadline'."
            ),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=10, pady=(10, 0))

        context_text = tk.Text(dialog, wrap="word", height=8)
        context_text.pack(expand=True, fill="both", padx=10, pady=10)
        if initial_context.strip():
            context_text.insert("1.0", initial_context.strip())

        result = {"value": None}

        def on_generate():
            result["value"] = context_text.get("1.0", "end-1c").strip()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = tk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(button_frame, text="Generate", command=on_generate).pack(side="right")
        tk.Button(button_frame, text="Cancel", command=on_cancel).pack(side="right", padx=(0, 8))

        context_text.focus_set()
        dialog.wait_window()
        return result["value"]

    def _excuse_worker(self, category, tone, context):
        result = generate_ai_excuse(
            category=category,
            tone=tone,
            context=context,
        )

        self.root.after(0, lambda: self._apply_excuse_result(result))

    def _apply_excuse_result(self, result):
        self._set_excuse_button_state("normal")
        self.update_twist_progress(self.twist_manager.completed_twists)

        if result is None:
            error_message = getattr(gemini_client, 'get_last_error', lambda: None)()
            if error_message and ('RESOURCE_EXHAUSTED' in error_message or '429' in error_message):
                user_message = (
                    "Quota Gemini terlampaui. Periksa plan/billing dan tunggu beberapa saat sebelum mencoba lagi."
                )
            else:
                user_message = (
                    "Gagal membuat excuse dari Gemini. Cek koneksi atau API key."
                )

            self._show_excuse_dialog(user_message, loading=False)
            messagebox.showerror(
                "Excuse Generator Error",
                user_message,
            )
            return

        self._show_excuse_dialog(result)

    def _show_excuse_dialog(self, excuse, loading=False):
        if (
            getattr(self, "excuse_dialog", None) is None
            or not self.excuse_dialog.winfo_exists()
        ):
            self._build_excuse_dialog()

        self.current_excuse = "" if loading else excuse
        self.excuse_text_widget.config(state="normal")
        self.excuse_text_widget.delete("1.0", "end")
        self.excuse_text_widget.insert("1.0", excuse)
        self.excuse_text_widget.config(state="disabled")
        self.insert_excuse_button.config(state="disabled" if loading else "normal")

        self.excuse_dialog.lift()
        self.excuse_dialog.focus_force()

    def _build_excuse_dialog(self):
        self.excuse_dialog = tk.Toplevel(self.root)
        self.excuse_dialog.title("Excuse Generator")
        self.excuse_dialog.geometry("420x220")
        self.excuse_dialog.transient(self.root)

        self.excuse_text_widget = tk.Text(
            self.excuse_dialog,
            wrap="word",
            height=6,
        )
        self.excuse_text_widget.pack(expand=True, fill="both", padx=10, pady=10)

        button_frame = tk.Frame(self.excuse_dialog)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        def insert_into_notepad():
            self.text_area.insert("insert", self.current_excuse)
            self.excuse_dialog.destroy()

        self.insert_excuse_button = tk.Button(
            button_frame,
            text="Insert into Notepad",
            command=insert_into_notepad,
        )
        self.insert_excuse_button.pack(side="left")

        tk.Button(
            button_frame,
            text="Close",
            command=self.excuse_dialog.destroy,
        ).pack(side="right")

    def _set_excuse_button_state(self, state):
        if hasattr(self, "excuse_button"):
            self.excuse_button.config(state=state)
