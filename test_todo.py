"""Unit-Tests für die ToDo-App (CLI-Kernlogik: TodoStore)."""

from pathlib import Path

import pytest

from todo import TodoStore


@pytest.fixture
def store(tmp_path: Path) -> TodoStore:
    db_path = tmp_path / "todos.json"
    return TodoStore(db_path=db_path)


# ----------------------------------------------------------------------
# Grundfunktionen
# ----------------------------------------------------------------------

def test_add_todo(store: TodoStore):
    todo = store.add("Einkaufen gehen")
    assert todo.id == 1
    assert todo.text == "Einkaufen gehen"
    assert todo.done is False
    assert todo.archived is False
    assert todo.deleted is False
    assert store.db_path.exists()


def test_list_active_default(store: TodoStore):
    store.add("Aufgabe 1")
    store.add("Aufgabe 2")
    todos = store.list()
    assert [t.text for t in todos] == ["Aufgabe 1", "Aufgabe 2"]


def test_complete_and_reopen(store: TodoStore):
    todo = store.add("Aufgabe")
    assert store.complete(todo.id) is True
    assert store.list()[0].done is True
    assert store.reopen(todo.id) is True
    assert store.list()[0].done is False
    assert store.complete(999) is False
    assert store.reopen(999) is False


def test_list_open_only(store: TodoStore):
    t1 = store.add("Offen")
    t2 = store.add("Erledigt")
    store.complete(t2.id)
    open_todos = store.list(view="active", open_only=True)
    assert len(open_todos) == 1
    assert open_todos[0].id == t1.id


def test_persistence(tmp_path: Path):
    db_path = tmp_path / "todos.json"
    store1 = TodoStore(db_path=db_path)
    store1.add("Persistente Aufgabe")

    store2 = TodoStore(db_path=db_path)
    assert len(store2.list()) == 1
    assert store2.list()[0].text == "Persistente Aufgabe"


def test_next_id_after_purge(store: TodoStore):
    t1 = store.add("A")
    store.add("B")
    store.purge(t1.id)
    t3 = store.add("C")
    assert t3.id == 3


def test_clear_completed(store: TodoStore):
    store.add("Offen")
    t2 = store.add("Erledigt 1")
    t3 = store.add("Erledigt 2")
    store.complete(t2.id)
    store.complete(t3.id)
    removed = store.clear_completed()
    assert removed == 2
    assert len(store.list()) == 1


# ----------------------------------------------------------------------
# Archiv
# ----------------------------------------------------------------------

def test_archive_moves_out_of_active_list(store: TodoStore):
    todo = store.add("Zum Archivieren")
    assert store.archive(todo.id) is True
    assert store.list(view="active") == []
    archived = store.list(view="archived")
    assert len(archived) == 1
    assert archived[0].id == todo.id
    assert archived[0].archived is True
    assert archived[0].archived_at is not None


def test_archive_twice_fails(store: TodoStore):
    todo = store.add("A")
    assert store.archive(todo.id) is True
    assert store.archive(todo.id) is False


def test_unarchive_restores_to_active(store: TodoStore):
    todo = store.add("A")
    store.archive(todo.id)
    assert store.unarchive(todo.id) is True
    assert store.list(view="archived") == []
    active = store.list(view="active")
    assert len(active) == 1
    assert active[0].archived is False
    assert active[0].archived_at is None


def test_empty_archive_removes_only_archived(store: TodoStore):
    t1 = store.add("Aktiv")
    t2 = store.add("Archiviert 1")
    t3 = store.add("Archiviert 2")
    store.archive(t2.id)
    store.archive(t3.id)
    removed = store.empty_archive()
    assert removed == 2
    assert [t.id for t in store.list(view="active")] == [t1.id]
    assert store.list(view="archived") == []


# ----------------------------------------------------------------------
# Papierkorb
# ----------------------------------------------------------------------

def test_trash_moves_out_of_active_list(store: TodoStore):
    todo = store.add("Zum Löschen")
    assert store.trash(todo.id) is True
    assert store.list(view="active") == []
    trashed = store.list(view="trash")
    assert len(trashed) == 1
    assert trashed[0].deleted is True
    assert trashed[0].deleted_at is not None


def test_trash_from_archive(store: TodoStore):
    todo = store.add("Archiviert dann gelöscht")
    store.archive(todo.id)
    assert store.trash(todo.id) is True
    assert store.list(view="archived") == []
    assert len(store.list(view="trash")) == 1


def test_restore_from_trash_to_active(store: TodoStore):
    todo = store.add("Aufgabe")
    store.trash(todo.id)
    assert store.restore(todo.id) is True
    assert store.list(view="trash") == []
    active = store.list(view="active")
    assert len(active) == 1
    assert active[0].deleted is False
    assert active[0].deleted_at is None


def test_restore_from_trash_keeps_archived_flag(store: TodoStore):
    todo = store.add("Aufgabe")
    store.archive(todo.id)
    store.trash(todo.id)
    store.restore(todo.id)
    archived = store.list(view="archived")
    assert len(archived) == 1
    assert archived[0].id == todo.id


def test_purge_removes_permanently(store: TodoStore):
    todo = store.add("Endgültig")
    store.trash(todo.id)
    assert store.purge(todo.id) is True
    assert store.list(view="trash") == []
    assert store.purge(todo.id) is False


def test_empty_trash_removes_only_deleted(store: TodoStore):
    t1 = store.add("Aktiv")
    t2 = store.add("Gelöscht 1")
    t3 = store.add("Gelöscht 2")
    store.trash(t2.id)
    store.trash(t3.id)
    removed = store.empty_trash()
    assert removed == 2
    assert [t.id for t in store.list(view="active")] == [t1.id]
    assert store.list(view="trash") == []


def test_double_trash_fails(store: TodoStore):
    todo = store.add("A")
    assert store.trash(todo.id) is True
    assert store.trash(todo.id) is False


def test_restore_non_deleted_fails(store: TodoStore):
    todo = store.add("A")
    assert store.restore(todo.id) is False
