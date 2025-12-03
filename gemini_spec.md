# 📦 Entwicklungsumgebung Spezifikation

## 1. Projektbeschreibung
* Diese Projekt soll das Programm patch abbilden, da dieses Probleme
  mit UTF-8 und wechselnden/unterschiedlichen Zeilenenden in den diff
  Texten und den Sourcecodedateien hat.
  
* Die mindest Version von Python ist Python 3.13.



## 2. Paketstruktur (Aktuelles Projekt)

Dies beschreibt die Verzeichnisstruktur des Pakets, an dem ich gerade arbeite ('ftw_patch'), und ist für korrekte interne Imports essenziell.

ftw_patch/
    ├── __init__.py
    └── ftw_patch.py

---

## 3. Bevorzugte Pythonmodule 
Bestimmte Module aus der Standardlibrary sollen wenn möglich verwendet
werden:
* **pathlib** vor os, os.path


## 4. Erlaubte PyPI-Pakete (Externe Abhängigkeiten)

Dies ist die limitierte Liste der öffentlichen PyPI-Pakete, die in jeder Datei importiert werden dürfen.

* **Keine**, frage nach.

---

## 5. Lokale private Pakete (Interne Abhängigkeiten)

Dies ist die Liste Ihrer selbstentwickelten Pakete, die sich außerhalb des aktuellen Projekts befinden, aber im Code importiert werden dürfen (z.B. 'import custom_logging').

* **Keine**

---

## 6. Dokumentations-Artefakte (Wissensbasis)

Dies ist eine Checkliste der JSON-Dateien, die die API-Schnittstellen der privaten Pakete (Abschnitt 3) enthalten und in die Wissensanweisung hochgeladen werden MÜSSEN.

* **Keine**
