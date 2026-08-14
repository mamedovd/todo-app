#!/usr/bin/env python3
"""Moderne grafische Oberfläche (Tkinter) für die ToDo-App.

Nutzt die Logik aus todo.py (TodoStore) und bietet drei Ansichten:
- Aktiv:   normale, laufende Aufgaben
- Archiv:  zur Seite gelegte Aufgaben
- Papierkorb: gelöschte Aufgaben, wiederherstellbar oder endgültig entfernbar
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from todo import DEFAULT_DB_PATH, Todo, TodoStore, View

# ---------------------------------------------------------------------------
# Farbschema ("modernes" flaches Dark/Light-Design)
# ---------------------------------------------------------------------------
COLOR_BG = "#f4f5f9"           # Haupt-Hintergrund (hell)
COLOR_SIDEBAR = "#1f2233"      # Sidebar-Hintergrund (dunkel)
COLOR_SIDEBAR_ACTIVE = "#3b5bfd"  # aktive Ansicht in der Sidebar
COLOR_SIDEBAR_TEXT = "#c7c9d9"
COLOR_SIDEBAR_TEXT_ACTIVE = "#ffffff"
COLOR_ACCENT = "#3b5bfd"       # Akzentfarbe für primäre Buttons
COLOR_ACCENT_HOVER = "#2d47d6"
COLOR_CARD = "#ffffff"
COLOR_TEXT = "#20223a"
COLOR_MUTED = "#8b8fa3"
COLOR_DANGER = "#e5484d"
COLOR_DANGER_HOVER = "#c8393d"
COLOR_BORDER = "#e3e5ee"

FONT_FAMILY = "Segoe UI"


class RoundishButton(tk.Label):
    """Ein einfacher, moderner "Button" auf Basis von tk.Label mit Hover-Effekt.

    ttk-Buttons lassen sich unter Windows farblich kaum anpassen; ein Label
    mit Klick-/Hover-Bindings wirkt auf allen Plattformen einheitlich modern.
    """

    def __init__(
        self,
        master: tk.Widget,
        text: str,
        command,
        bg: str = COLOR_ACCENT,
        hover_bg: str = COLOR_ACCENT_HOVER,
        fg: str = "#ffffff",
        padx: int = 14,
        pady: int = 8,
        font_size: int = 10,
        **kwargs,
    ):
        super().__init__(
            master,
            text=text,
            bg=bg,
            fg=fg,
            font=(FONT_FAMILY, font_size, "bold"),
            padx=padx,
            pady=pady,
            cursor="hand2",
            **kwargs,
        )
        self._bg = bg
        self._hover_bg = hover_bg
        self._command = command
        self.bind("<Button-1>", lambda _e: self._command())
        self.bind("<Enter>", lambda _e: self.configure(bg=self._hover_bg))
        self.bind("<Leave>", lambda _e: self.configure(bg=self._bg))


class SidebarItem(tk.Frame):
    """Ein Eintrag in der Sidebar (Aktiv / Archiv / Papierkorb)."""

    def __init__(self, master: tk.Widget, icon: str, label: str, command, **kwargs):
        super().__init__(master, bg=COLOR_SIDEBAR, cursor="hand2", **kwargs)
        self._command = command
        self._active = False

        self.icon_label = tk.Label(
            self, text=icon, bg=COLOR_SIDEBAR, fg=COLOR_SIDEBAR_TEXT,
            font=(FONT_FAMILY, 13),
        )
        self.icon_label.pack(side="left", padx=(18, 10), pady=10)

        self.text_label = tk.Label(
            self, text=label, bg=COLOR_SIDEBAR, fg=COLOR_SIDEBAR_TEXT,
            font=(FONT_FAMILY, 11), anchor="w",
        )
        self.text_label.pack(side="left", fill="x", expand=True, pady=10)

        self.count_label = tk.Label(
            self, text="", bg=COLOR_SIDEBAR, fg=COLOR_MUTED,
            font=(FONT_FAMILY, 9), anchor="e",
        )
        self.count_label.pack(side="right", padx=(0, 16), pady=10)

        for widget in (self, self.icon_label, self.text_label, self.count_label):
            widget.bind("<Button-1>", lambda _e: self._command())
            if not self._active:
                widget.bind("<Enter>", self._on_enter)
                widget.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event=None) -> None:
        if not self._active:
            self._set_colors(bg="#2a2d42")

    def _on_leave(self, _event=None) -> None:
        if not self._active:
            self._set_colors(bg=COLOR_SIDEBAR)

    def _set_colors(self, bg: str, fg: str | None = None) -> None:
        widgets = (self, self.icon_label, self.text_label)
        for widget in widgets:
            widget.configure(bg=bg)
        self.count_label.configure(bg=bg)
        if fg:
            self.icon_label.configure(fg=fg)
            self.text_label.configure(fg=fg)

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self._set_colors(bg=COLOR_SIDEBAR_ACTIVE, fg=COLOR_SIDEBAR_TEXT_ACTIVE)
            self.count_label.configure(fg="#dbe1ff")
        else:
            self._set_colors(bg=COLOR_SIDEBAR, fg=COLOR_SIDEBAR_TEXT)
            self.count_label.configure(fg=COLOR_MUTED)

    def set_count(self, count: int) -> None:
        self.count_label.configure(text=str(count) if count else "")


class TodoGUI(tk.Tk):
    VIEWS: list[tuple[View, str, str]] = [
        ("active", "📋", "Aktive Aufgaben"),
        ("archived", "🗄", "Archiv"),
        ("trash", "🗑", "Papierkorb"),
    ]

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        super().__init__()
        self.store = TodoStore(db_path=db_path)
        self.current_view: View = "active"
        self.open_only = False

        self.title("ToDo App")
        self.geometry("760x560")
        self.minsize(620, 440)
        self.configure(bg=COLOR_BG)

        self._setup_style()
        self._build_layout()
        self._refresh()

    # ------------------------------------------------------------------
    # Aufbau
    # ------------------------------------------------------------------

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background=COLOR_CARD,
            fieldbackground=COLOR_CARD,
            foreground=COLOR_TEXT,
            rowheight=32,
            borderwidth=0,
            font=(FONT_FAMILY, 10),
        )
        style.configure(
            "Treeview.Heading",
            background=COLOR_BG,
            foreground=COLOR_MUTED,
            font=(FONT_FAMILY, 9, "bold"),
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", "#e7ecff")],
            foreground=[("selected", COLOR_TEXT)],
        )
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        style.configure("Modern.TEntry", padding=8, relief="flat")

    def _build_layout(self) -> None:
        root = tk.Frame(self, bg=COLOR_BG)
        root.pack(fill="both", expand=True)

        self._build_sidebar(root)
        self._build_content(root)

    def _build_sidebar(self, root: tk.Widget) -> None:
        sidebar = tk.Frame(root, bg=COLOR_SIDEBAR, width=210)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        title = tk.Label(
            sidebar, text="✓  ToDo", bg=COLOR_SIDEBAR, fg="#ffffff",
            font=(FONT_FAMILY, 15, "bold"), anchor="w",
        )
        title.pack(fill="x", padx=18, pady=(22, 18))

        self.sidebar_items: dict[View, SidebarItem] = {}
        for view, icon, label in self.VIEWS:
            item = SidebarItem(sidebar, icon, label, command=lambda v=view: self._switch_view(v))
            item.pack(fill="x")
            self.sidebar_items[view] = item

        spacer = tk.Frame(sidebar, bg=COLOR_SIDEBAR)
        spacer.pack(fill="both", expand=True)

        footer = tk.Label(
            sidebar,
            text=f"Speicherort:\n{self.store.db_path}",
            bg=COLOR_SIDEBAR,
            fg="#5c6086",
            font=(FONT_FAMILY, 8),
            anchor="w",
            justify="left",
            wraplength=190,
        )
        footer.pack(fill="x", padx=18, pady=14)

    def _build_content(self, root: tk.Widget) -> None:
        content = tk.Frame(root, bg=COLOR_BG)
        content.pack(side="left", fill="both", expand=True)

        # Kopfbereich: Titel + Ansicht-spezifische Aktionen (z. B. leeren)
        header = tk.Frame(content, bg=COLOR_BG)
        header.pack(fill="x", padx=24, pady=(22, 10))

        self.view_title = tk.Label(
            header, text="", bg=COLOR_BG, fg=COLOR_TEXT,
            font=(FONT_FAMILY, 18, "bold"), anchor="w",
        )
        self.view_title.pack(side="left")

        self.header_actions = tk.Frame(header, bg=COLOR_BG)
        self.header_actions.pack(side="right")

        # Eingabezeile (nur im aktiven View sichtbar)
        self.input_frame = tk.Frame(content, bg=COLOR_BG)
        self.input_frame.pack(fill="x", padx=24, pady=(0, 14))

        entry_card = tk.Frame(self.input_frame, bg=COLOR_CARD, highlightthickness=1,
                               highlightbackground=COLOR_BORDER)
        entry_card.pack(fill="x")

        self.entry_var = tk.StringVar()
        entry = tk.Entry(
            entry_card,
            textvariable=self.entry_var,
            font=(FONT_FAMILY, 11),
            relief="flat",
            bg=COLOR_CARD,
            fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT,
        )
        entry.pack(side="left", fill="x", expand=True, padx=12, pady=10)
        entry.bind("<Return>", lambda _e: self._add_todo())
        entry.focus_set()
        self.entry_widget = entry

        RoundishButton(entry_card, "+  Hinzufügen", self._add_todo).pack(
            side="right", padx=6, pady=6
        )

        # Filter-Checkbox (nur aktive Ansicht)
        self.filter_frame = tk.Frame(content, bg=COLOR_BG)
        self.filter_frame.pack(fill="x", padx=24)
        self.open_only_var = tk.BooleanVar(value=False)
        self.filter_check = tk.Checkbutton(
            self.filter_frame,
            text="Nur offene Aufgaben anzeigen",
            variable=self.open_only_var,
            command=self._on_filter_toggle,
            bg=COLOR_BG,
            fg=COLOR_MUTED,
            activebackground=COLOR_BG,
            font=(FONT_FAMILY, 9),
            selectcolor=COLOR_CARD,
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        self.filter_check.pack(anchor="w", pady=(0, 8))

        # Liste
        list_card = tk.Frame(content, bg=COLOR_CARD, highlightthickness=1,
                              highlightbackground=COLOR_BORDER)
        list_card.pack(fill="both", expand=True, padx=24, pady=(0, 12))

        columns = ("status", "text", "meta")
        self.tree = ttk.Treeview(
            list_card, columns=columns, show="headings", selectmode="browse"
        )
        self.tree.heading("status", text="")
        self.tree.heading("text", text="AUFGABE")
        self.tree.heading("meta", text="INFO")
        self.tree.column("status", width=40, anchor="center", stretch=False)
        self.tree.column("text", width=380, anchor="w")
        self.tree.column("meta", width=170, anchor="e", stretch=False)
        self.tree.tag_configure("done", foreground=COLOR_MUTED)
        self.tree.pack(side="left", fill="both", expand=True, padx=(1, 0), pady=1)
        self.tree.bind("<Double-Button-1>", lambda _e: self._on_double_click())

        scrollbar = ttk.Scrollbar(list_card, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Aktionsleiste (ansicht-abhängig)
        self.action_bar = tk.Frame(content, bg=COLOR_BG)
        self.action_bar.pack(fill="x", padx=24, pady=(0, 10))

        # Statusleiste
        self.status_var = tk.StringVar(value="")
        status_bar = tk.Label(
            content, textvariable=self.status_var, bg=COLOR_BG, fg=COLOR_MUTED,
            font=(FONT_FAMILY, 9), anchor="w",
        )
        status_bar.pack(fill="x", padx=24, pady=(0, 14))

    # ------------------------------------------------------------------
    # Ansicht wechseln
    # ------------------------------------------------------------------

    def _switch_view(self, view: View) -> None:
        self.current_view = view
        for v, item in self.sidebar_items.items():
            item.set_active(v == view)
        self._refresh()

    # ------------------------------------------------------------------
    # Daten holen / Liste zeichnen
    # ------------------------------------------------------------------

    def _current_todos(self) -> list[Todo]:
        if self.current_view == "active":
            return self.store.list(view="active", open_only=self.open_only_var.get())
        return self.store.list(view=self.current_view)

    def _refresh(self) -> None:
        # Kopfzeile / Titel
        titles = {"active": "Aktive Aufgaben", "archived": "Archiv", "trash": "Papierkorb"}
        self.view_title.configure(text=titles[self.current_view])

        # Eingabe- und Filterzeile nur im aktiven View zeigen
        if self.current_view == "active":
            self.input_frame.pack(fill="x", padx=24, pady=(0, 14))
            self.filter_frame.pack(fill="x", padx=24)
        else:
            self.input_frame.pack_forget()
            self.filter_frame.pack_forget()

        self._build_header_actions()
        self._build_action_bar()

        # Liste befüllen
        for row in self.tree.get_children():
            self.tree.delete(row)

        todos = self._current_todos()
        for todo in todos:
            status_icon = "☑" if todo.done else "☐"
            meta = self._meta_text(todo)
            tags = ("done",) if todo.done else ()
            self.tree.insert(
                "", "end", iid=str(todo.id),
                values=(status_icon, todo.text, meta), tags=tags,
            )

        # Sidebar-Zähler aktualisieren
        self.sidebar_items["active"].set_count(
            len(self.store.list(view="active"))
        )
        self.sidebar_items["archived"].set_count(len(self.store.list(view="archived")))
        self.sidebar_items["trash"].set_count(len(self.store.list(view="trash")))

        total_active = len(self.store.list(view="active"))
        open_active = len(self.store.list(view="active", open_only=True))
        self.status_var.set(
            f"{open_active} offen / {total_active} aktiv insgesamt   ·   "
            f"{len(self.store.list(view='archived'))} im Archiv   ·   "
            f"{len(self.store.list(view='trash'))} im Papierkorb"
        )

    def _meta_text(self, todo: Todo) -> str:
        if self.current_view == "trash":
            return f"gelöscht {self._short_date(todo.deleted_at)}"
        if self.current_view == "archived":
            return f"archiviert {self._short_date(todo.archived_at)}"
        return f"erstellt {self._short_date(todo.created_at)}"

    @staticmethod
    def _short_date(value: str | None) -> str:
        if not value:
            return ""
        return value.replace("T", " ")

    # ------------------------------------------------------------------
    # Ansicht-abhängige Buttons
    # ------------------------------------------------------------------

    def _build_header_actions(self) -> None:
        for widget in self.header_actions.winfo_children():
            widget.destroy()

        if self.current_view == "archived":
            RoundishButton(
                self.header_actions, "Archiv leeren", self._empty_archive,
                bg=COLOR_DANGER, hover_bg=COLOR_DANGER_HOVER, font_size=9,
            ).pack(side="right")
        elif self.current_view == "trash":
            RoundishButton(
                self.header_actions, "Papierkorb leeren", self._empty_trash,
                bg=COLOR_DANGER, hover_bg=COLOR_DANGER_HOVER, font_size=9,
            ).pack(side="right")

    def _build_action_bar(self) -> None:
        for widget in self.action_bar.winfo_children():
            widget.destroy()

        if self.current_view == "active":
            RoundishButton(
                self.action_bar, "✓ Erledigt / Offen", self._toggle_done,
                bg="#20223a", hover_bg="#31344d", font_size=9,
            ).pack(side="left")
            RoundishButton(
                self.action_bar, "🗄 Archivieren", self._archive_selected,
                bg="#5b6079", hover_bg="#474b60", font_size=9,
            ).pack(side="left", padx=(8, 0))
            RoundishButton(
                self.action_bar, "🗑 In Papierkorb", self._trash_selected,
                bg=COLOR_DANGER, hover_bg=COLOR_DANGER_HOVER, font_size=9,
            ).pack(side="left", padx=(8, 0))

        elif self.current_view == "archived":
            RoundishButton(
                self.action_bar, "↩ Wiederherstellen", self._unarchive_selected,
                bg="#5b6079", hover_bg="#474b60", font_size=9,
            ).pack(side="left")
            RoundishButton(
                self.action_bar, "🗑 In Papierkorb", self._trash_selected,
                bg=COLOR_DANGER, hover_bg=COLOR_DANGER_HOVER, font_size=9,
            ).pack(side="left", padx=(8, 0))

        elif self.current_view == "trash":
            RoundishButton(
                self.action_bar, "↩ Wiederherstellen", self._restore_selected,
                bg="#5b6079", hover_bg="#474b60", font_size=9,
            ).pack(side="left")
            RoundishButton(
                self.action_bar, "✕ Endgültig löschen", self._purge_selected,
                bg=COLOR_DANGER, hover_bg=COLOR_DANGER_HOVER, font_size=9,
            ).pack(side="left", padx=(8, 0))

    # ------------------------------------------------------------------
    # Auswahl-Hilfsfunktion
    # ------------------------------------------------------------------

    def _selected_id(self) -> int | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _require_selection(self) -> int | None:
        todo_id = self._selected_id()
        if todo_id is None:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Aufgabe auswählen.")
            return None
        return todo_id

    def _on_double_click(self) -> None:
        if self.current_view == "active":
            self._toggle_done()

    # ------------------------------------------------------------------
    # Aktionen: hinzufügen / erledigt / offen
    # ------------------------------------------------------------------

    def _add_todo(self) -> None:
        text = self.entry_var.get().strip()
        if not text:
            return
        self.store.add(text)
        self.entry_var.set("")
        self._refresh()

    def _toggle_done(self) -> None:
        todo_id = self._require_selection()
        if todo_id is None:
            return
        todo = self.store._find(todo_id)  # noqa: SLF001
        if todo is None:
            return
        if todo.done:
            self.store.reopen(todo_id)
        else:
            self.store.complete(todo_id)
        self._refresh()

    def _on_filter_toggle(self) -> None:
        self._refresh()

    # ------------------------------------------------------------------
    # Aktionen: Archiv
    # ------------------------------------------------------------------

    def _archive_selected(self) -> None:
        todo_id = self._require_selection()
        if todo_id is None:
            return
        self.store.archive(todo_id)
        self._refresh()

    def _unarchive_selected(self) -> None:
        todo_id = self._require_selection()
        if todo_id is None:
            return
        self.store.unarchive(todo_id)
        self._refresh()

    def _empty_archive(self) -> None:
        if not self.store.list(view="archived"):
            return
        if messagebox.askyesno(
            "Archiv leeren", "Alle archivierten Aufgaben endgültig löschen?"
        ):
            removed = self.store.empty_archive()
            self._refresh()
            messagebox.showinfo("Archiv geleert", f"{removed} Aufgabe(n) endgültig gelöscht.")

    # ------------------------------------------------------------------
    # Aktionen: Papierkorb
    # ------------------------------------------------------------------

    def _trash_selected(self) -> None:
        todo_id = self._require_selection()
        if todo_id is None:
            return
        self.store.trash(todo_id)
        self._refresh()

    def _restore_selected(self) -> None:
        todo_id = self._require_selection()
        if todo_id is None:
            return
        self.store.restore(todo_id)
        self._refresh()

    def _purge_selected(self) -> None:
        todo_id = self._require_selection()
        if todo_id is None:
            return
        if messagebox.askyesno(
            "Endgültig löschen", "Diese Aufgabe unwiderruflich löschen?"
        ):
            self.store.purge(todo_id)
            self._refresh()

    def _empty_trash(self) -> None:
        if not self.store.list(view="trash"):
            return
        if messagebox.askyesno(
            "Papierkorb leeren", "Alle Aufgaben im Papierkorb endgültig löschen?"
        ):
            removed = self.store.empty_trash()
            self._refresh()
            messagebox.showinfo("Papierkorb geleert", f"{removed} Aufgabe(n) endgültig gelöscht.")


def main() -> None:
    app = TodoGUI()
    app.sidebar_items["active"].set_active(True)
    app.mainloop()


if __name__ == "__main__":
    main()
