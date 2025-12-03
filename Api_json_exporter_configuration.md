Gerne\! Hier sind die notwendigen Änderungen, die Sie in Ihrer **conf.py** vornehmen müssen, um den **api\_json\_exporter.py** erfolgreich in Sphinx zu registrieren und zu laden.

Die Änderungen bestehen aus zwei Teilen:

1. **Erweiterung des sys.path**: Stellt sicher, dass Python die Datei findet.  
2. **Registrierung in extensions**: Aktiviert die Erweiterung für Sphinx.

## ---

**🐍 Änderungen in conf.py**

Stellen Sie sicher, dass die Datei **api\_json\_exporter.py** im selben Verzeichnis wie Ihre **conf.py** liegt (z.B. im docs oder source Ordner).

Python

\# conf.py

import os  
import sys

\# 1\. ERWEITERUNG DES SYSTEMPFADES  
\# Fügt das Verzeichnis, in dem conf.py liegt, zum Python-Suchpfad hinzu.  
\# Dies ist notwendig, damit Sphinx/Python Ihre lokale Erweiterungsdatei findet.  
sys.path.insert(0, os.path.abspath('.'))   
\# Oder, falls die conf.py im 'source'-Ordner liegt:  
\# sys.path.insert(0, os.path.abspath('./source')) 

\# \--- Allgemeine Konfigurationen \---

\# ... andere Einstellungen ...

\# 2\. REGISTRIERUNG DER ERWEITERUNG  
extensions \= \[  
    'sphinx.ext.autodoc',  
    'sphinx.ext.coverage', \# Wenn Sie coverage verwenden  
    \# ... andere Extensions ...  
      
    \# HIER FÜGEN SIE IHRE ERWEITERUNG HINZU:  
    'api_json_exporter'  # Name der Python-Datei (ohne .py Endung)  
\]

Nachdem Sie diese Änderungen gespeichert haben, kann die Erweiterung beim nächsten Aufruf von make html-coverage-full oder make api-json geladen werden.