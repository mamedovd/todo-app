"""Unit-Tests für die ToDo-App."""

import json
from pathlib import Path

import pytest

from todo import TodoStore


@pytest.fixture
def store(tmp_path: Path) -> TodoStore:
    db_path = tmp_path / "todos.json"
    return TodoStore(db_path=db_path)


def test_add_todo(store: TodoStore):
    todo = store.add("Einkaufen gehen")
    assert todo.id == 1
    assert todo.text == "Einkaufen gehen"
    assert todo.done is False
    assert store.db_path.exists()


def test_list_todos(store: TodoStore):
    store.add("Aufgabe 1")
    store.add("Aufgabe 2")
    todos = store.list()
    assert len(todos) == 2
    assert [t.text for t in todos] == ["Aufgabe 1", "Aufgabe 2"]


def test_complete_todo(store: TodoStore):
    todo = store.add("Aufgabe")
    assert store.complete(todo.id) is True
    assert store.list()[0].done is True
    assert store.complete(999) is False


def test_list_open_only(store: TodoStore):
    t1 = store.add("Offen")
    t2 = store.add("Erledigt")
    store.complete(t2.id)
    open_todos = store.list(show_all=False)
    assert len(open_todos) == 1
    assert open_todos[0].id == t1.id


def test_remove_todo(store: TodoStore):
    todo = store.add("Zu löschen")
    assert store.remove(todo.id) is True
    assert store.list() == []
    assert store.remove(todo.id) is False


def test_clear_completed(store: TodoStore):
    store.add("Offen")
    t2 = store.add("Erledigt 1")
    t3 = store.add("Erledigt 2")
    store.complete(t2.id)
    store.complete(t3.id)
    removed = store.clear_completed()
    assert removed == 2
    assert len(store.list()) == 1


def test_persistence(tmp_path: Path):
    db_path = tmp_path / "todos.json"
    store1 = TodoStore(db_path=db_path)
    store1.add("Persistente Aufgabe")

    store2 = TodoStore(db_path=db_path)
    assert len(store2.list()) == 1
    assert store2.list()[0].text == "Persistente Aufgabe"


def test_next_id_after_removal(store: TodoStore):
    t1 = store.add("A")
    store.add("B")
    store.remove(t1.id)
    t3 = store.add("C")
    assert t3.id == 3
