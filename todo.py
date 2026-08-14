#!/usr/bin/env python3
"""Einfache Kommandozeilen-ToDo-App.

Speichert Aufgaben persistent in einer JSON-Datei und bietet Befehle
zum Hinzufügen, Auflisten, Erledigen, Archivieren, Löschen (Papierkorb)
und endgültigen Entfernen von Aufgaben.

Konzept:
- Aktive Aufgaben: weder archiviert noch im Papierkorb.
- Archiv: Aufgaben, die bewusst "zur Seite gelegt" wurden (z. B. erledigte
  Projekte), aber nicht endgültig gelöscht sind.
- Papierkorb: Aufgaben, die gelöscht wurden, aber noch wiederhergestellt
  werden können, bevor sie endgültig entfernt werden.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Literal

DEFAULT_DB_PATH = Path.home() / ".todo_app" / "todos.json"

View = Literal["active", "archived", "trash"]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class Todo:
    id: int
    text: str
    done: bool = False
    created_at: str = field(default_factory=_now)
    completed_at: str | None = None
    archived: bool = False
    archived_at: str | None = None
    deleted: bool = False
    deleted_at: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Todo":
        return Todo(
            id=data["id"],
            text=data["text"],
            done=data.get("done", False),
            created_at=data.get("created_at", ""),
            completed_at=data.get("completed_at"),
            archived=data.get("archived", False),
            archived_at=data.get("archived_at"),
            deleted=data.get("deleted", False),
            deleted_at=data.get("deleted_at"),
        )


class TodoStore:
    """Verwaltet das Laden und Speichern der ToDo-Liste."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.todos: List[Todo] = []
        self._load()

    def _load(self) -> None:
        if self.db_path.exists():
            try:
                raw = json.loads(self.db_path.read_text(encoding="utf-8"))
                self.todos = [Todo.from_dict(item) for item in raw]
            except (json.JSONDecodeError, KeyError):
                self.todos = []
        else:
            self.todos = []

    def _save(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        data = [t.to_dict() for t in self.todos]
        self.db_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _next_id(self) -> int:
        return max((t.id for t in self.todos), default=0) + 1

    def _find(self, todo_id: int) -> Todo | None:
        for t in self.todos:
            if t.id == todo_id:
                return t
        return None

    # ------------------------------------------------------------------
    # Erstellen / Anzeigen
    # ------------------------------------------------------------------

    def add(self, text: str) -> Todo:
        todo = Todo(id=self._next_id(), text=text)
        self.todos.append(todo)
        self._save()
        return todo

    def list(self, view: View = "active", open_only: bool = False) -> List[Todo]:
        if view == "active":
            items = (t for t in self.todos if not t.archived and not t.deleted)
            if open_only:
                items = (t for t in items if not t.done)
        elif view == "archived":
            items = (t for t in self.todos if t.archived and not t.deleted)
        elif view == "trash":
            items = (t for t in self.todos if t.deleted)
        else:
            raise ValueError(f"Unbekannte Ansicht: {view}")
        return sorted(items, key=lambda t: t.id)

    # ------------------------------------------------------------------
    # Erledigt / Offen
    # ------------------------------------------------------------------

    def complete(self, todo_id: int) -> bool:
        todo = self._find(todo_id)
        if todo is None or todo.deleted:
            return False
        todo.done = True
        todo.completed_at = _now()
        self._save()
        return True

    def reopen(self, todo_id: int) -> bool:
        todo = self._find(todo_id)
        if todo is None or todo.deleted:
            return False
        todo.done = False
        todo.completed_at = None
        self._save()
        return True

    # ------------------------------------------------------------------
    # Archiv
    # ------------------------------------------------------------------

    def archive(self, todo_id: int) -> bool:
        todo = self._find(todo_id)
        if todo is None or todo.deleted or todo.archived:
            return False
        todo.archived = True
        todo.archived_at = _now()
        self._save()
        return True

    def unarchive(self, todo_id: int) -> bool:
        """Stellt eine archivierte Aufgabe zurück in die aktive Liste."""
        todo = self._find(todo_id)
        if todo is None or todo.deleted or not todo.archived:
            return False
        todo.archived = False
        todo.archived_at = None
        self._save()
        return True

    def empty_archive(self) -> int:
        """Löscht alle archivierten (nicht gelöschten) Aufgaben endgültig."""
        before = len(self.todos)
        self.todos = [t for t in self.todos if not (t.archived and not t.deleted)]
        removed = before - len(self.todos)
        if removed:
            self._save()
        return removed

    # ------------------------------------------------------------------
    # Papierkorb
    # ------------------------------------------------------------------

    def trash(self, todo_id: int) -> bool:
        """Verschiebt eine Aufgabe (aktiv oder archiviert) in den Papierkorb."""
        todo = self._find(todo_id)
        if todo is None or todo.deleted:
            return False
        todo.deleted = True
        todo.deleted_at = _now()
        self._save()
        return True

    def restore(self, todo_id: int) -> bool:
        """Stellt eine Aufgabe aus dem Papierkorb wieder her."""
        todo = self._find(todo_id)
        if todo is None or not todo.deleted:
            return False
        todo.deleted = False
        todo.deleted_at = None
        self._save()
        return True

    def purge(self, todo_id: int) -> bool:
        """Entfernt eine einzelne Aufgabe endgültig (unabhängig vom Status)."""
        before = len(self.todos)
        self.todos = [t for t in self.todos if t.id != todo_id]
        if len(self.todos) != before:
            self._save()
            return True
        return False

    def empty_trash(self) -> int:
        """Entfernt alle Aufgaben im Papierkorb endgültig."""
        before = len(self.todos)
        self.todos = [t for t in self.todos if not t.deleted]
        removed = before - len(self.todos)
        if removed:
            self._save()
        return removed

    # ------------------------------------------------------------------
    # Sonstiges
    # ------------------------------------------------------------------

    def clear_completed(self) -> int:
        """Löscht alle erledigten, aktiven (nicht archivierten/gelöschten) Aufgaben endgültig."""
        before = len(self.todos)
        self.todos = [
            t for t in self.todos if not (t.done and not t.archived and not t.deleted)
        ]
        removed = before - len(self.todos)
        if removed:
            self._save()
        return removed


def format_todo(todo: Todo) -> str:
    status = "x" if todo.done else " "
    tags = []
    if todo.archived:
        tags.append("archiviert")
    if todo.deleted:
        tags.append("im Papierkorb")
    suffix = f"  ({', '.join(tags)})" if tags else ""
    return f"[{status}] #{todo.id:<3} {todo.text}{suffix}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Einfache ToDo-App")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Pfad zur Speicherdatei (Standard: {DEFAULT_DB_PATH})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_p = subparsers.add_parser("add", help="Neue Aufgabe hinzufügen")
    add_p.add_argument("text", nargs="+", help="Text der Aufgabe")

    list_p = subparsers.add_parser("list", help="Aufgaben anzeigen")
    list_p.add_argument(
        "--view",
        choices=["active", "archived", "trash"],
        default="active",
        help="Welche Ansicht angezeigt werden soll (Standard: active)",
    )
    list_p.add_argument(
        "--open", action="store_true", help="Nur offene (nicht erledigte) Aufgaben anzeigen (nur bei --view active)"
    )

    done_p = subparsers.add_parser("done", help="Aufgabe als erledigt markieren")
    done_p.add_argument("id", type=int, help="ID der Aufgabe")

    reopen_p = subparsers.add_parser("reopen", help="Aufgabe als offen markieren")
    reopen_p.add_argument("id", type=int, help="ID der Aufgabe")

    archive_p = subparsers.add_parser("archive", help="Aufgabe archivieren")
    archive_p.add_argument("id", type=int, help="ID der Aufgabe")

    unarchive_p = subparsers.add_parser("unarchive", help="Aufgabe aus dem Archiv zurückholen")
    unarchive_p.add_argument("id", type=int, help="ID der Aufgabe")

    trash_p = subparsers.add_parser("trash", help="Aufgabe in den Papierkorb verschieben")
    trash_p.add_argument("id", type=int, help="ID der Aufgabe")

    restore_p = subparsers.add_parser("restore", help="Aufgabe aus dem Papierkorb wiederherstellen")
    restore_p.add_argument("id", type=int, help="ID der Aufgabe")

    purge_p = subparsers.add_parser("purge", help="Aufgabe endgültig löschen")
    purge_p.add_argument("id", type=int, help="ID der Aufgabe")

    subparsers.add_parser("empty-trash", help="Papierkorb endgültig leeren")
    subparsers.add_parser("empty-archive", help="Archiv endgültig leeren")
    subparsers.add_parser("clear", help="Alle erledigten aktiven Aufgaben endgültig löschen")

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = TodoStore(db_path=args.db)

    def fail(todo_id: int) -> int:
        print(f"Aufgabe #{todo_id} nicht gefunden oder Aktion nicht möglich.", file=sys.stderr)
        return 1

    if args.command == "add":
        text = " ".join(args.text)
        todo = store.add(text)
        print(f"Aufgabe hinzugefügt: {format_todo(todo)}")

    elif args.command == "list":
        todos = store.list(view=args.view, open_only=args.open)
        if not todos:
            print("Keine Aufgaben vorhanden.")
        for t in todos:
            print(format_todo(t))

    elif args.command == "done":
        if not store.complete(args.id):
            return fail(args.id)
        print(f"Aufgabe #{args.id} als erledigt markiert.")

    elif args.command == "reopen":
        if not store.reopen(args.id):
            return fail(args.id)
        print(f"Aufgabe #{args.id} als offen markiert.")

    elif args.command == "archive":
        if not store.archive(args.id):
            return fail(args.id)
        print(f"Aufgabe #{args.id} archiviert.")

    elif args.command == "unarchive":
        if not store.unarchive(args.id):
            return fail(args.id)
        print(f"Aufgabe #{args.id} aus dem Archiv zurückgeholt.")

    elif args.command == "trash":
        if not store.trash(args.id):
            return fail(args.id)
        print(f"Aufgabe #{args.id} in den Papierkorb verschoben.")

    elif args.command == "restore":
        if not store.restore(args.id):
            return fail(args.id)
        print(f"Aufgabe #{args.id} aus dem Papierkorb wiederhergestellt.")

    elif args.command == "purge":
        if not store.purge(args.id):
            return fail(args.id)
        print(f"Aufgabe #{args.id} endgültig gelöscht.")

    elif args.command == "empty-trash":
        removed = store.empty_trash()
        print(f"Papierkorb geleert: {removed} Aufgabe(n) endgültig gelöscht.")

    elif args.command == "empty-archive":
        removed = store.empty_archive()
        print(f"Archiv geleert: {removed} Aufgabe(n) endgültig gelöscht.")

    elif args.command == "clear":
        removed = store.clear_completed()
        print(f"{removed} erledigte Aufgabe(n) entfernt.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
