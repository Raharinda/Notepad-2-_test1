import threading
import tkinter as tk
from tkinter import messagebox

from utils import gemini_client


class AIActionsMixin:
    """
    Mixin untuk fitur AI (Gemini):
    Rewrite, Summarize, Translate, Continue Writing.
    Bergantung pada: self.text_area, self.root,
                     self.status_label, self.twist_manager
    """

    def run_ai_action(self, action: str):
        if not gemini_client.is_available():
            messagebox.showwarning(
                "AI Feature Unavailable",
                "Gemini belum dikonfigurasi.\n\n"
                "Install: pip install google-generativeai\n"
                "Lalu set environment variable GEMINI_API_KEY.",
            )
            return

        try:
            text = self.text_area.get("sel.first", "sel.last")
            has_selection = True
        except tk.TclError:
            text = self.text_area.get("1.0", "end-1c")
            has_selection = False

        if not text.strip():
            messagebox.showinfo("AI", "Tidak ada teks untuk diproses.")
            return

        self.status_label.config(text="AI is thinking...")

        threading.Thread(
            target=self._ai_worker,
            args=(action, text, has_selection),
            daemon=True,
        ).start()

    def _ai_worker(self, action: str, text: str, has_selection: bool):
        dispatch = {
            "rewrite": gemini_client.rewrite_text,
            "summarize": gemini_client.summarize_text,
            "translate": lambda t: gemini_client.translate_text(t, "English"),
            "continue": gemini_client.continue_text,
        }
        result = dispatch[action](text) if action in dispatch else None

        self.root.after(
            0, lambda: self._ai_apply_result(action, result, has_selection)
        )

    def _ai_apply_result(self, action: str, result, has_selection: bool):
        # Restore status bar setelah AI selesai
        completed = self.twist_manager.completed_twists
        self.update_twist_progress(completed)

        if result is None:
            error_message = getattr(gemini_client, 'get_last_error', lambda: None)()
            if error_message and ('RESOURCE_EXHAUSTED' in error_message or '429' in error_message):
                user_message = (
                    "Quota Gemini terlampaui. Periksa plan/billing dan tunggu beberapa saat sebelum mencoba lagi."
                )
            else:
                user_message = (
                    "Gagal mendapatkan respons dari Gemini. Cek koneksi / API key."
                )

            messagebox.showerror(
                "AI Error",
                user_message,
            )
            return

        if action == "rewrite" and has_selection:
            self.text_area.delete("sel.first", "sel.last")
            self.text_area.insert("insert", result)
        elif action == "continue":
            self.text_area.insert("end", " " + result)
        else:
            self._show_ai_result_dialog(action, result)

    def _show_ai_result_dialog(self, action: str, result: str):
        titles = {
            "rewrite": "Rewritten Text",
            "summarize": "Summary",
            "translate": "Translation",
            "continue": "Continuation",
        }

        dialog = tk.Toplevel(self.root)
        dialog.title(titles.get(action, "AI Result"))
        dialog.geometry("400x300")
        dialog.transient(self.root)

        text_widget = tk.Text(dialog, wrap="word")
        text_widget.pack(expand=True, fill="both", padx=10, pady=10)
        text_widget.insert("1.0", result)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        def insert_into_notepad():
            self.text_area.insert("insert", result)
            dialog.destroy()

        tk.Button(btn_frame, text="Insert into Notepad", command=insert_into_notepad).pack(
            side="left"
        )
        tk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side="right")

