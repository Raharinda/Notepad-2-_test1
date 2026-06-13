import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import font as tkfont

from twists.teleport_button import TeleportButtonTwist
from twists.bloodmoon import BloodmoonTwist
from twists.capslock_demon import CapslockDemonTwist
from twists.self_aware_calculator import SelfAwareCalculatorTwist
from twists.broken_calculator import BrokenCalculatorTwist
from twists.lavaloon import LavaloonTwist
from twists.black_hole import BlackHoleTwist


class MainView:

    def __init__(self, root, twist_manager):

        self.root = root
        self.twist_manager = twist_manager

        self.root.title("Notepad")
        self.root.geometry("800x600")

        self.twist_active = False

        # Track currently opened file (for Save vs Save As)
        self.current_file_path = None

        # Font state (for Format > Font and Zoom)
        self.base_font_family = "Consolas"
        self.base_font_size = 12
        self.zoom_percent = 100

        self.text_font = tkfont.Font(
            family=self.base_font_family,
            size=self.base_font_size
        )

        # Word wrap state
        self.word_wrap_var = tk.BooleanVar(value=True)

        # Find/Replace state
        self.find_dialog = None
        self.last_search_index = "1.0"

        # ==================
        # MENU BAR
        # ==================
        self.build_menu_bar()

        # Notepad area
        self.text_area = tk.Text(
            root,
            font=self.text_font,
            wrap="word",
            undo=True,
            autoseparators=True,
            maxundo=-1
        )

        self.text_area.pack(
            expand=True,
            fill="both"
        )

        # Highlight tag for Find/Replace results
        self.text_area.tag_configure(
            "search_highlight",
            background="#ffd54f",
            foreground="black"
        )

        # Overlay (hidden by default)
        self.overlay_frame = tk.Frame(
            self.root,
            bg="#202020"
        )

        # Detect typing
        self.text_area.bind(
            "<KeyRelease>",
            self.on_text_changed
        )

        # Detect cursor movement for Line/Col indicator
        self.text_area.bind(
            "<ButtonRelease-1>",
            self.update_cursor_position
        )

        self.text_area.bind(
            "<KeyRelease>",
            self.update_cursor_position,
            add="+"
        )

        # Zoom with Ctrl + Mouse Wheel (Windows/Mac)
        self.text_area.bind(
            "<Control-MouseWheel>",
            self.on_ctrl_mousewheel
        )

        # Zoom with Ctrl + Mouse Wheel (Linux)
        self.text_area.bind(
            "<Control-Button-4>",
            lambda e: self.zoom_in()
        )

        self.text_area.bind(
            "<Control-Button-5>",
            lambda e: self.zoom_out()
        )

        # ==================
        # STATUS BAR
        # ==================
        self.status_bar = tk.Frame(root)

        self.status_bar.pack(
            fill="x",
            side="bottom"
        )

        # Twist progress (left side) - kept as `status_label`
        # because twists (e.g. Bloodmoon) reference this widget directly.
        self.status_label = tk.Label(
            self.status_bar,
            text="Twists Completed: 0/3",
            anchor="w"
        )

        self.status_label.pack(
            side="left",
            padx=8
        )

        # Zoom indicator (right side)
        self.zoom_label = tk.Label(
            self.status_bar,
            text="100%",
            anchor="e",
            width=6
        )

        self.zoom_label.pack(
            side="right",
            padx=8
        )

        # Line/Column indicator (right side)
        self.position_label = tk.Label(
            self.status_bar,
            text="Ln 1, Col 1",
            anchor="e",
            width=15
        )

        self.position_label.pack(
            side="right",
            padx=8
        )

        # Update window title when file changes
        self.update_title()
        self.update_cursor_position()

    # ==========================================================
    # MENU BAR
    # ==========================================================

    def build_menu_bar(self):

        menu_bar = tk.Menu(self.root)

        # ---------------- File menu ----------------
        file_menu = tk.Menu(menu_bar, tearoff=0)

        file_menu.add_command(
            label="New",
            accelerator="Ctrl+N",
            command=self.new_file
        )

        file_menu.add_command(
            label="Open...",
            accelerator="Ctrl+O",
            command=self.open_file
        )

        file_menu.add_command(
            label="Save",
            accelerator="Ctrl+S",
            command=self.save_file
        )

        file_menu.add_command(
            label="Save As...",
            accelerator="Ctrl+Shift+S",
            command=self.save_file_as
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Exit",
            command=self.exit_app
        )

        menu_bar.add_cascade(
            label="File",
            menu=file_menu
        )

        # ---------------- Edit menu ----------------
        edit_menu = tk.Menu(menu_bar, tearoff=0)

        edit_menu.add_command(
            label="Undo",
            accelerator="Ctrl+Z",
            command=self.undo_action
        )

        edit_menu.add_command(
            label="Redo",
            accelerator="Ctrl+Y",
            command=self.redo_action
        )

        edit_menu.add_separator()

        edit_menu.add_command(
            label="Cut",
            accelerator="Ctrl+X",
            command=self.cut_action
        )

        edit_menu.add_command(
            label="Copy",
            accelerator="Ctrl+C",
            command=self.copy_action
        )

        edit_menu.add_command(
            label="Paste",
            accelerator="Ctrl+V",
            command=self.paste_action
        )

        edit_menu.add_separator()

        edit_menu.add_command(
            label="Find...",
            accelerator="Ctrl+F",
            command=self.open_find_dialog
        )

        edit_menu.add_command(
            label="Replace...",
            accelerator="Ctrl+H",
            command=self.open_replace_dialog
        )

        menu_bar.add_cascade(
            label="Edit",
            menu=edit_menu
        )

        # ---------------- Format menu ----------------
        format_menu = tk.Menu(menu_bar, tearoff=0)

        format_menu.add_checkbutton(
            label="Word Wrap",
            variable=self.word_wrap_var,
            command=self.toggle_word_wrap
        )

        format_menu.add_command(
            label="Font...",
            command=self.open_font_dialog
        )

        menu_bar.add_cascade(
            label="Format",
            menu=format_menu
        )

        self.root.config(menu=menu_bar)

        # ---------------- Keyboard shortcuts ----------------
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-N>", lambda e: self.new_file())

        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-O>", lambda e: self.open_file())

        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-S>", lambda e: self.save_file())

        self.root.bind("<Control-Shift-s>", lambda e: self.save_file_as())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_file_as())

        self.root.bind("<Control-z>", lambda e: self.undo_action())
        self.root.bind("<Control-Z>", lambda e: self.undo_action())

        self.root.bind("<Control-y>", lambda e: self.redo_action())
        self.root.bind("<Control-Y>", lambda e: self.redo_action())

        self.root.bind("<Control-f>", lambda e: self.open_find_dialog())
        self.root.bind("<Control-F>", lambda e: self.open_find_dialog())

        self.root.bind("<Control-h>", lambda e: self.open_replace_dialog())
        self.root.bind("<Control-H>", lambda e: self.open_replace_dialog())

        # Zoom shortcuts (Ctrl + / Ctrl -)
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-equal>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.zoom_reset())

    # ==========================================================
    # FILE ACTIONS
    # ==========================================================

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
                ("All Files", "*.*")
            ]
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

            messagebox.showerror(
                "Error",
                f"Could not open file:\n{e}"
            )

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
                ("All Files", "*.*")
            ]
        )

        if not file_path:
            return

        self.current_file_path = file_path
        self._write_to_file(file_path)

    def _write_to_file(self, file_path):

        try:

            content = self.text_area.get("1.0", "end-1c")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.update_title()

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"Could not save file:\n{e}"
            )

    def exit_app(self):

        self.root.destroy()

    def update_title(self):

        if self.current_file_path:

            import os

            file_name = os.path.basename(self.current_file_path)
            self.root.title(f"{file_name} - Notepad")

        else:

            self.root.title("Untitled - Notepad")

    # ==========================================================
    # EDIT ACTIONS
    # ==========================================================

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

    # ==========================================================
    # FIND & REPLACE
    # ==========================================================

    def open_find_dialog(self):

        self._open_search_dialog(show_replace=False)

    def open_replace_dialog(self):

        self._open_search_dialog(show_replace=True)

    def _open_search_dialog(self, show_replace):

        # If a dialog is already open, just focus it
        if self.find_dialog is not None and self.find_dialog.winfo_exists():
            self.find_dialog.lift()
            self.find_entry.focus_set()

            if show_replace:
                self.replace_frame.pack(
                    fill="x",
                    padx=10,
                    pady=(0, 5)
                )

            return

        self.find_dialog = tk.Toplevel(self.root)
        self.find_dialog.title("Replace" if show_replace else "Find")
        self.find_dialog.resizable(False, False)
        self.find_dialog.transient(self.root)

        # ---- Find row ----
        find_frame = tk.Frame(self.find_dialog)
        find_frame.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(
            find_frame,
            text="Find:",
            width=10,
            anchor="w"
        ).pack(side="left")

        self.find_entry = tk.Entry(find_frame, width=30)
        self.find_entry.pack(side="left", fill="x", expand=True)
        self.find_entry.focus_set()

        # ---- Replace row ----
        self.replace_frame = tk.Frame(self.find_dialog)

        tk.Label(
            self.replace_frame,
            text="Replace with:",
            width=10,
            anchor="w"
        ).pack(side="left")

        self.replace_entry = tk.Entry(self.replace_frame, width=30)
        self.replace_entry.pack(side="left", fill="x", expand=True)

        if show_replace:
            self.replace_frame.pack(fill="x", padx=10, pady=(0, 5))

        # ---- Buttons row ----
        button_frame = tk.Frame(self.find_dialog)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(
            button_frame,
            text="Find Next",
            command=self.find_next
        ).pack(side="left", padx=2)

        if show_replace:

            tk.Button(
                button_frame,
                text="Replace",
                command=self.replace_current
            ).pack(side="left", padx=2)

            tk.Button(
                button_frame,
                text="Replace All",
                command=self.replace_all
            ).pack(side="left", padx=2)

        tk.Button(
            button_frame,
            text="Close",
            command=self.close_find_dialog
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
            query,
            self.last_search_index,
            stopindex="end",
            nocase=True
        )

        # Wrap around to the beginning if nothing found below cursor
        if not start_index:

            start_index = self.text_area.search(
                query,
                "1.0",
                stopindex="end",
                nocase=True
            )

        if not start_index:

            messagebox.showinfo(
                "Find",
                f'Cannot find "{query}".'
            )

            return

        end_index = f"{start_index}+{len(query)}c"

        self.text_area.tag_add(
            "search_highlight",
            start_index,
            end_index
        )

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

            messagebox.showinfo(
                "Replace All",
                f'Cannot find "{query}".'
            )

            return

        # Simple case-sensitive replace for the actual edit
        new_content = content.replace(query, replacement)

        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", new_content)

        self.last_search_index = "1.0"

        messagebox.showinfo(
            "Replace All",
            f"Replaced {count} occurrence(s)."
        )

    # ==========================================================
    # FORMAT: WORD WRAP
    # ==========================================================

    def toggle_word_wrap(self):

        if self.word_wrap_var.get():
            self.text_area.config(wrap="word")
        else:
            self.text_area.config(wrap="none")

    # ==========================================================
    # FORMAT: FONT DIALOG
    # ==========================================================

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
            current_index = families.index(family_var.get())
            family_list.selection_set(current_index)
            family_list.see(current_index)
        except ValueError:
            pass

        family_list.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # ---- Font size ----
        tk.Label(dialog, text="Size:").grid(
            row=0, column=1, sticky="w", padx=10, pady=(10, 0)
        )

        size_var = tk.IntVar(value=self.text_font.actual("size"))

        size_spin = tk.Spinbox(
            dialog,
            from_=6,
            to=72,
            textvariable=size_var,
            width=5
        )

        size_spin.grid(row=1, column=1, padx=10, pady=5, sticky="nw")

        # ---- Preview ----
        preview_label = tk.Label(
            dialog,
            text="AaBbYyZz 0123",
            relief="solid",
            bd=1,
            padx=10,
            pady=10
        )

        preview_label.grid(
            row=2, column=0, columnspan=2,
            padx=10, pady=10, sticky="nsew"
        )

        def update_preview(*_):

            selection = family_list.curselection()

            family = (
                family_list.get(selection[0])
                if selection
                else family_var.get()
            )

            try:
                size = size_var.get()
            except tk.TclError:
                size = self.base_font_size

            preview_label.config(
                font=(family, max(6, min(72, size)))
            )

        family_list.bind("<<ListboxSelect>>", update_preview)
        size_spin.bind("<KeyRelease>", update_preview)
        size_spin.bind("<<Increment>>", update_preview)
        size_spin.bind("<<Decrement>>", update_preview)

        update_preview()

        # ---- Buttons ----
        button_frame = tk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))

        def apply_font():

            selection = family_list.curselection()

            family = (
                family_list.get(selection[0])
                if selection
                else family_var.get()
            )

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

        tk.Button(
            button_frame,
            text="OK",
            command=apply_font
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side="left", padx=5)

    # ==========================================================
    # ZOOM
    # ==========================================================

    def on_ctrl_mousewheel(self, event):

        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):

        self.zoom_percent = min(400, self.zoom_percent + 10)
        self.apply_zoom()

    def zoom_out(self):

        self.zoom_percent = max(20, self.zoom_percent - 10)
        self.apply_zoom()

    def zoom_reset(self):

        self.zoom_percent = 100
        self.apply_zoom()

    def apply_zoom(self):

        new_size = max(
            1,
            int(self.base_font_size * self.zoom_percent / 100)
        )

        self.text_font.config(size=new_size)
        self.zoom_label.config(text=f"{self.zoom_percent}%")

    # ==========================================================
    # STATUS BAR: LINE / COLUMN
    # ==========================================================

    def update_cursor_position(self, event=None):

        try:
            line, col = self.text_area.index("insert").split(".")
            self.position_label.config(
                text=f"Ln {line}, Col {int(col) + 1}"
            )
        except tk.TclError:
            pass

    # ==========================================================
    # TWIST / GAME LOGIC (unchanged)
    # ==========================================================

    def on_text_changed(self, event):

        if self.twist_active:
            return
        
        if (self.twist_manager.completed_twists >= 3):
            return

        current_text = self.text_area.get(
            "1.0",
            "end-1c"
        )

        character_count = len(current_text)

        if self.twist_manager.should_trigger_twist(
            character_count
        ):
            self.trigger_twist()

    def trigger_twist(self):

        self.twist_active = True

        twist_name = (
            self.twist_manager
            .get_current_twist()
        )

        objective = (
            self.twist_manager
            .get_current_objective()
        )

        self.show_warning_overlay(
            twist_name,
            objective
        )

        print(
            f"Starting twist: {twist_name}"
        )

    def fake_twist(self):

        twist_name = (
            self.twist_manager
            .get_current_twist()
        )

        if twist_name == "Teleporting Button":

            TeleportButtonTwist(
                self.overlay_frame,
                self.finish_twist
            )

        elif twist_name == "Bloodmoon":

            BloodmoonTwist(
                self,
                self.finish_twist
            )
        
        elif twist_name == "Capslock Demon":

            CapslockDemonTwist(
                self.overlay_frame,
                self.finish_twist
            )

        elif twist_name == "Self Aware Calculator":

            SelfAwareCalculatorTwist(
                self.overlay_frame,
                self.finish_twist
            )

        elif twist_name == "Broken Calculator":

            BrokenCalculatorTwist(
                self.overlay_frame,
                self.finish_twist
            )
            
        elif twist_name == "Lavaloon":

            LavaloonTwist(
                self.overlay_frame,
                self.finish_twist,
                self.retry_current_twist
            )

        elif twist_name == "Black Hole":

            BlackHoleTwist(
                self.overlay_frame,
                self.finish_twist,
                self.retry_current_twist
            )

        else:

            print(
                f"{twist_name} not implemented yet"
            )

            self.finish_twist()

    def finish_twist(self):

        self.twist_active = False

        self.twist_manager.complete_current_twist()

        completed = (self.twist_manager.completed_twists)
        
        self.update_twist_progress(
            completed
        )

        self.hide_overlay()
        
        if completed >= 3:
            self.show_victory_screen()

    def update_twist_progress(self, completed):

        self.status_label.config(
            text=f"Twists Completed: {completed}/3"
        )

    def show_warning_overlay(
        self,
        twist_name,
        objective
        ):


        self.overlay_frame.place(
            relx=0,
            rely=0,
            relwidth=1,
            relheight=1
        )

        warning_title = tk.Label(
            self.overlay_frame,
            text="⚠ WARNING ⚠",
            font=("Arial", 24, "bold"),
            fg="red",
            bg="#202020"
        )

        warning_title.place(
            relx=0.5,
            rely=0.3,
            anchor="center"
        )

        twist_label = tk.Label(
            self.overlay_frame,
            text=twist_name,
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#202020"
        )

        twist_label.place(
            relx=0.5,
            rely=0.45,
            anchor="center"
        )

        objective_label = tk.Label(
            self.overlay_frame,
            text=objective,
            font=("Arial", 12),
            fg="white",
            bg="#202020"
        )

        objective_label.place(
            relx=0.5,
            rely=0.6,
            anchor="center"
        )

        self.root.after(
            2000,
            self.start_twist_after_warning
        )

    def start_twist_after_warning(self):


        for widget in self.overlay_frame.winfo_children():
            widget.destroy()

        self.fake_twist()


    
    def hide_overlay(self):

        self.overlay_frame.place_forget()
        
    def show_victory_screen(self):

        self.overlay_frame.place(
            relx=0,
            rely=0,
            relwidth=1,
            relheight=1
        )

        victory_text = """

    =================================

    CONGRATULATIONS

    You survived Notepad.

    The notebook seems satisfied...
    for now.

    [ENTER] Continue writing
    [ESC] Close session

    =================================
    """

        label = tk.Label(
            self.overlay_frame,
            text=victory_text,
            font=("Consolas", 14),
            bg="#202020",
            fg="white",
            justify="center"
        )

        label.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        self.root.bind(
            "<Return>",
            self.continue_after_victory
        )

        self.root.bind(
            "<Escape>",
            self.close_session
        )

    def continue_after_victory(
        self,
        event=None
    ):

        self.root.unbind(
            "<Return>"
        )

        self.root.unbind(
            "<Escape>"
        )

        self.hide_overlay()

    def close_session(
        self,
        event=None
    ):

        self.root.destroy()

    def retry_current_twist(self):

        self.twist_active = True

        for widget in (
            self.overlay_frame.winfo_children()
        ):
            widget.destroy()

        twist_name = (
            self.twist_manager
            .get_current_twist()
        )

        objective = (
            self.twist_manager
            .get_current_objective()
        )

        self.show_warning_overlay(
            twist_name,
            objective
        )