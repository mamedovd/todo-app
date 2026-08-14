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

Modernes Sidebar-Layout mit drei Ansichten:

- **Aktive Aufgaben**: Aufgabe über das Eingabefeld hinzufügen (Enter oder Button),
  per Einzelklick auf das Kästchen in der Liste (oder über den Button) als erledigt/offen
  markieren, archivieren oder in den Papierkorb verschieben. Über die Checkbox in der
  Spaltenüberschrift lassen sich alle sichtbaren Aufgaben auf einmal markieren/entmarkieren.
  Checkbox „Nur offene Aufgaben anzeigen“ zum Filtern.
- **Archiv**: zur Seite gelegte Aufgaben. Können wiederhergestellt (zurück zu Aktiv),
  in den Papierkorb verschoben oder über „Archiv leeren“ komplett endgültig gelöscht werden.
- **Papierkorb**: gelöschte Aufgaben. Können wiederhergestellt, einzeln endgültig
  gelöscht oder über „Papierkorb leeren“ komplett entfernt werden.

Die Sidebar zeigt jeweils die Anzahl der Aufgaben pro Ansicht an.

## Archiv- und Papierkorb-Konzept

- **Aktiv**: normale, laufende Aufgaben.
- **Archiv**: bewusst zur Seite gelegte Aufgaben (nicht gelöscht, aber aus dem
  aktiven Blickfeld entfernt).
- **Papierkorb**: gelöschte Aufgaben, die noch wiederhergestellt werden können,
  bevor sie endgültig entfernt werden.

Endgültiges Löschen ist immer ein separater, bestätigter Schritt (einzelne Aufgabe
über „Endgültig löschen“, oder komplett über „Papierkorb leeren“ / „Archiv leeren“).

## Kommandozeile (CLI)

```bash
# Aufgabe hinzufügen
python todo.py add "Einkaufen gehen"

# Aufgaben anzeigen (Ansicht: active | archived | trash, Standard: active)
python todo.py list
python todo.py list --view archived
python todo.py list --view trash

# Nur offene Aufgaben anzeigen (nur in --view active)
python todo.py list --open

# Aufgabe als erledigt / wieder offen markieren
python todo.py done 1
python todo.py reopen 1

# Archivieren / aus dem Archiv zurückholen
python todo.py archive 1
python todo.py unarchive 1

# In den Papierkorb verschieben / wiederherstellen
python todo.py trash 1
python todo.py restore 1

# Einzelne Aufgabe endgültig löschen
python todo.py purge 1

# Papierkorb bzw. Archiv komplett endgültig leeren
python todo.py empty-trash
python todo.py empty-archive

# Alle erledigten aktiven Aufgaben endgültig löschen
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
