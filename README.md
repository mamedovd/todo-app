# ToDo App

Eine einfache ToDo-App in Python ohne externe Abhängigkeiten – wahlweise über die
Kommandozeile (`todo.py`) oder mit grafischer Oberfläche (`todo_gui.py`, Tkinter).
Die Aufgaben werden persistent als JSON-Datei gespeichert (Standard: `~/.todo_app/todos.json`).
Beide Varianten teilen sich dieselbe Datenbasis (`TodoStore` aus `todo.py`).

## Voraussetzungen

- Python 3.10+
- Für die GUI: Tkinter (bei den meisten Python-Installationen bereits enthalten)

## Grafische Oberfläche (GUI)

```bash
python todo_gui.py
```

Funktionen im Fenster:
- Neue Aufgabe über das Eingabefeld hinzufügen (Enter oder Button „Hinzufügen“)
- Aufgabe auswählen und per Doppelklick oder Button „Erledigt“ als erledigt markieren/zurücksetzen
- Ausgewählte Aufgabe löschen
- Alle erledigten Aufgaben auf einmal entfernen
- Checkbox „Nur offene anzeigen“ zum Filtern der Liste

## Kommandozeile (CLI)

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
