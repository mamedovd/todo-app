#!/usr/bin/env python3
"""Grafische Oberfläche (Tkinter) für die ToDo-App.

Nutzt die bestehende Logik aus todo.py (TodoStore) und stellt sie
über ein einfaches Desktop-Fenster dar.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from todo import DEFAULT_DB_PATH, Todo, TodoStore


class TodoGUI(tk.Tk):
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        super().__init__()
        self.store = TodoStore(db_path=db_path)
        self.show_all = True

        self.title("ToDo App")
        self.geometry("480x520")
        self.minsize(360, 400)

        self._build_widgets()
        self._refresh_list()

    def _build_widgets(self) -> None:
        # Eingabezeile zum Hinzufügen neuer Aufgaben
        input_frame = ttk.Frame(self, padding=10)
        input_frame.pack(fill="x")

        self.entry_var = tk.StringVar()
        entry = ttk.Entry(input_frame, textvariable=self.entry_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _event: self._add_todo())
        entry.focus_set()

        add_btn = ttk.Button(input_frame, text="Hinzufügen", command=self._add_todo)
        add_btn.pack(side="left", padx=(8, 0))

        # Liste der Aufgaben
        list_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode="browse",
            activestyle="none",
            font=("Segoe UI", 11),
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", lambda _event: self._toggle_done())

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        # Aktions-Buttons
        action_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        action_frame.pack(fill="x")

        ttk.Button(action_frame, text="Erledigt", command=self._toggle_done).pack(
            side="left"
        )
        ttk.Button(action_frame, text="Löschen", command=self._remove_todo).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(action_frame, text="Erledigte entfernen", command=self._clear_completed).pack(
            side="left", padx=(8, 0)
        )

        self.filter_var = tk.BooleanVar(value=False)
        filter_check = ttk.Checkbutton(
            action_frame,
            text="Nur offene anzeigen",
            variable=self.filter_var,
            command=self._on_filter_toggle,
        )
        filter_check.pack(side="right")

        # Statusleiste
        self.status_var = tk.StringVar(value="")
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor="w", padding=(10, 4))
        status_bar.pack(fill="x")

    def _current_todos(self) -> list[Todo]:
        return self.store.list(show_all=not self.filter_var.get())

    def _refresh_list(self) -> None:
        self.listbox.delete(0, tk.END)
        todos = self._current_todos()
        for todo in todos:
            prefix = "☑" if todo.done else "☐"
            self.listbox.insert(tk.END, f"{prefix}  #{todo.id}  {todo.text}")
            if todo.done:
                index = self.listbox.size() - 1
                self.listbox.itemconfig(index, fg="gray")

        open_count = sum(1 for t in self.store.list() if not t.done)
        total = len(self.store.list())
        self.status_var.set(f"{open_count} offen / {total} gesamt · Speicherort: {self.store.db_path}")

    def _selected_todo(self) -> Todo | None:
        selection = self.listbox.curselection()
        if not selection:
            return None
        todos = self._current_todos()
        index = selection[0]
        if index >= len(todos):
            return None
        return todos[index]

    def _add_todo(self) -> None:
        text = self.entry_var.get().strip()
        if not text:
            return
        self.store.add(text)
        self.entry_var.set("")
        self._refresh_list()

    def _toggle_done(self) -> None:
        todo = self._selected_todo()
        if todo is None:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Aufgabe auswählen.")
            return
        if todo.done:
            todo.done = False
            todo.completed_at = None
            self.store._save()  # noqa: SLF001 - interner Store-Zugriff
        else:
            self.store.complete(todo.id)
        self._refresh_list()

    def _remove_todo(self) -> None:
        todo = self._selected_todo()
        if todo is None:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Aufgabe auswählen.")
            return
        if messagebox.askyesno("Löschen bestätigen", f"Aufgabe '{todo.text}' wirklich löschen?"):
            self.store.remove(todo.id)
            self._refresh_list()

    def _clear_completed(self) -> None:
        removed = self.store.clear_completed()
        self._refresh_list()
        if removed:
            messagebox.showinfo("Erledigt", f"{removed} erledigte Aufgabe(n) entfernt.")

    def _on_filter_toggle(self) -> None:
        self._refresh_list()


def main() -> None:
    app = TodoGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
