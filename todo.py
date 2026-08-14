#!/usr/bin/env python3
"""Einfache Kommandozeilen-ToDo-App.

Speichert Aufgaben persistent in einer JSON-Datei und bietet Befehle
zum Hinzufügen, Auflisten, Erledigen und Löschen von Aufgaben.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List

DEFAULT_DB_PATH = Path.home() / ".todo_app" / "todos.json"


@dataclass
class Todo:
    id: int
    text: str
    done: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    completed_at: str | None = None

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

    def add(self, text: str) -> Todo:
        todo = Todo(id=self._next_id(), text=text)
        self.todos.append(todo)
        self._save()
        return todo

    def list(self, show_all: bool = True) -> List[Todo]:
        if show_all:
            return sorted(self.todos, key=lambda t: t.id)
        return sorted((t for t in self.todos if not t.done), key=lambda t: t.id)

    def complete(self, todo_id: int) -> bool:
        for t in self.todos:
            if t.id == todo_id:
                t.done = True
                t.completed_at = datetime.now().isoformat(timespec="seconds")
                self._save()
                return True
        return False

    def remove(self, todo_id: int) -> bool:
        before = len(self.todos)
        self.todos = [t for t in self.todos if t.id != todo_id]
        if len(self.todos) != before:
            self._save()
            return True
        return False

    def clear_completed(self) -> int:
        before = len(self.todos)
        self.todos = [t for t in self.todos if not t.done]
        removed = before - len(self.todos)
        if removed:
            self._save()
        return removed


def format_todo(todo: Todo) -> str:
    status = "x" if todo.done else " "
    return f"[{status}] #{todo.id:<3} {todo.text}"


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
        "--open", action="store_true", help="Nur offene (nicht erledigte) Aufgaben anzeigen"
    )

    done_p = subparsers.add_parser("done", help="Aufgabe als erledigt markieren")
    done_p.add_argument("id", type=int, help="ID der Aufgabe")

    rm_p = subparsers.add_parser("rm", help="Aufgabe löschen")
    rm_p.add_argument("id", type=int, help="ID der Aufgabe")

    subparsers.add_parser("clear", help="Alle erledigten Aufgaben löschen")

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = TodoStore(db_path=args.db)

    if args.command == "add":
        text = " ".join(args.text)
        todo = store.add(text)
        print(f"Aufgabe hinzugefügt: {format_todo(todo)}")

    elif args.command == "list":
        todos = store.list(show_all=not args.open)
        if not todos:
            print("Keine Aufgaben vorhanden.")
        for t in todos:
            print(format_todo(t))

    elif args.command == "done":
        if store.complete(args.id):
            print(f"Aufgabe #{args.id} als erledigt markiert.")
        else:
            print(f"Aufgabe #{args.id} nicht gefunden.", file=sys.stderr)
            return 1

    elif args.command == "rm":
        if store.remove(args.id):
            print(f"Aufgabe #{args.id} gelöscht.")
        else:
            print(f"Aufgabe #{args.id} nicht gefunden.", file=sys.stderr)
            return 1

    elif args.command == "clear":
        removed = store.clear_completed()
        print(f"{removed} erledigte Aufgabe(n) entfernt.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
