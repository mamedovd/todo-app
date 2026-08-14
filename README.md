# ToDo App

Eine einfache Kommandozeilen-ToDo-App in Python ohne externe Abhängigkeiten.
Die Aufgaben werden persistent als JSON-Datei gespeichert (Standard: `~/.todo_app/todos.json`).

## Voraussetzungen

- Python 3.10+

## Verwendung

```bash
# Aufgabe hinzufügen
python todo.py add "Einkaufen gehen"

# Alle Aufgaben anzeigen
python todo.py list

# Nur offene Aufgaben anzeigen
python todo.py list --open

# Aufgabe als erledigt markieren (ID aus der Liste)
python todo.py done 1

# Aufgabe löschen
python todo.py rm 1

# Alle erledigten Aufgaben entfernen
python todo.py clear
```

Mit `--db PFAD` kann ein alternativer Speicherort für die Aufgaben angegeben werden:

```bash
python todo.py --db ./meine_todos.json list
```

## Tests

```bash
pip install pytest
pytest
```
