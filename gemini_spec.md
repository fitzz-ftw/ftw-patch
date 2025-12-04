# 📦 Entwicklungsumgebung Spezifikation

## 1. Projektbeschreibung
* Diese Projekt soll das Programm patch abbilden, da dieses Probleme
  mit UTF-8 und wechselnden/unterschiedlichen Zeilenenden in den diff
  Texten und den Sourcecodedateien hat.
  
* Die mindest Version von Python ist Python 3.13.



## 2. Paketstruktur (Aktuelles Projekt)

Dies beschreibt die Verzeichnisstruktur des Projekts/Pakets, an dem ich gerade arbeite ('FTW-Patch'), und ist für korrekte interne Imports essenziell.
Das Paket ist mit `pip install -e .` in die locale virtuele Pythonumgebung
installiert.

FTW-Patch
├── doc
│   ├── source
│   │   ├── _static
│   │   ├── _templates
│   │   │   ├── autosummary
│   │   │   │   ├── class_extended.rst
│   │   │   │   ├── module_extended.rst
│   │   │   │   └── package.rst
│   │   │   └── mymodul.html
│   │   ├── devel
│   │   │   ├── ftw_patch_module.rst
│   │   │   └── get_started_ftw_patch.rst
│   │   ├── user
│   │   │   └── use_ftwpatch.rst
│   │   ├── api_json_exporter.py
│   │   ├── conf.py
│   │   └── index.rst
│   └── Makefile
├── src
│   └── ftw_patch
│       ├── __init__.py
│       └── ftw_patch.py
├── tests
│   └── __init__.py
├── gemini_spec.md
├── Makefile
├── pyproject.toml
└── README.md
---

## 3. Bevorzugte Pythonmodule 
Bestimmte Module aus der Standardlibrary sollen wenn möglich verwendet
werden:
* **pathlib** vor os, os.path


## 4. Erlaubte PyPI-Pakete (Externe Abhängigkeiten)

Dies ist die limitierte Liste der öffentlichen PyPI-Pakete, die in jeder Datei importiert werden dürfen.

* **Keine**, frage nach.


## 5. Erlaubte PyPI-Pakete zur Entwicklung (Externe Entwicklungs Abhängigkeiten)
Dies ist die limitierte Liste der öffentlichen PyPI-Pakete, die zur
Entwicklung verwendet werden dürfen.

* **pytest**


---

## 6. Lokale private Pakete (Interne Abhängigkeiten)

Dies ist die Liste Ihrer selbstentwickelten Pakete, die sich außerhalb des aktuellen Projekts befinden, aber im Code importiert werden dürfen (z.B. 'import custom_logging').

* **Keine**

---

## 7. Dokumentations-Artefakte (Wissensbasis)

Dies ist eine Checkliste der JSON-Dateien, die die API-Schnittstellen der privaten Pakete (Abschnitt 3) enthalten und in die Wissensanweisung hochgeladen werden MÜSSEN.

* **Keine**
