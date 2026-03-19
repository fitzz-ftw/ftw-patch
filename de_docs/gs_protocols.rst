Getting Started: Protocols
==========================

Das Modul :mod:`.protocols` definiert die strukturellen Schnittstellen des Frameworks. 
Anstatt auf starre Vererbung zu setzen, nutzen wir :class:`~python:typing.Protocol`, 
um "Duck Typing" sicher und prüfbar zu machen.

Das LineLike Protokoll
----------------------

Das wichtigste Protokoll ist :class:`.protocols.LineLike`. Es definiert, welche 
Attribute ein Objekt besitzen muss, damit es vom Framework (z. B. durch das 
:class:`.base.TerminalColorMixin`) verarbeitet und farbig ausgegeben werden kann.

Ein Objekt erfüllt das Protokoll, wenn es folgende Attribute besitzt:

1. ``_color_map``: Ein Dictionary, das Präfixe auf Farben abbildet.
2. ``prefix``: Ein String (oder ``None``), der als Index für die Map dient.
3. ``orig_line``: Der eigentliche Textinhalt.

Lass uns das in einem Test verifizieren:

    >>> from fitzzftw.patch.protocols import LineLike
    >>> from fitzzftw.patch.base import TerminalColorMixin

Wir erstellen eine minimale Klasse, die das Protokoll manuell implementiert:

    >>> class MySimpleLine:
    ...     def __init__(self, text):
    ...         self._color_map = {"!": "red"}
    ...         self.prefix = "!"
    ...         self.orig_line = text

Da :class:`LineLike` mit :func:`~python:isinstance` prüfbar ist (dank 
:func:`~python:typing.runtime_checkable`), können wir das sofort testen:

    >>> simple_line = MySimpleLine("Gefahr!")
    >>> isinstance(simple_line, LineLike)
    True

Konfigurations-Protokolle
-------------------------

Neben den Datenobjekten nutzt das Framework Protokolle, um Konfigurationen 
abzubilden. Dies erlaubt es, verschiedene Options-Quellen (wie Argument-Parser 
oder Konfigurationsdateien) austauschbar zu machen.

* :class:`.protocols.BackupOptions`: 
    Regelt, ob und mit welcher Endung Backups erstellt werden.
* :class:`.protocols.WhitespaceOptions`: 
    Definiert Regeln zur Normalisierung von Leerzeichen.
* :class:`.protocols.ArgParsOptions`: 
    Das Master-Protokoll, das alle verfügbaren CLI-Optionen zusammenfasst.

Diese Protokolle werden primär für statische Typprüfungen (Type Hinting) 
verwendet, um sicherzustellen, dass Funktionen nur die Optionen erhalten, 
die sie auch wirklich verarbeiten können.
