import pytest
from pathlib import Path
from argparse import Namespace
# Annahme: Das Paket ftw_patch liegt nun im src/ Verzeichnis
from ftw.patch.ftw_patch import FtwPatch, Hunk, FtwPatchError, HunkLine

# --- Fixture für Mock FtwPatch Instanz ---

def create_mock_ftw_patch(
    normalize_ws: bool = False, 
    ignore_bl: bool = False, 
    ignore_all_ws: bool = False
) -> FtwPatch:
    """Erstellt eine Mock-Instanz von FtwPatch mit spezifischen CLI-Optionen."""
    mock_args = Namespace(
        patch_file=Path("dummy.diff"),
        strip_count=0,
        target_directory=Path("."),
        normalize_whitespace=normalize_ws,
        ignore_blank_lines=ignore_bl,
        ignore_all_whitespace=ignore_all_ws,
    )
    # Da wir nur die Logik von _apply_hunk_to_file testen, ist die 
    # dummy.diff-Datei nicht notwendig, aber die Path-Prüfung erfordert eine 
    # existierende Datei. Wir müssen hier die `_args`-Prüfung umgehen oder 
    # einen Dummy erstellen.
    # Da FtwPatch proaktiv prüft, erstellen wir einen Dummy-Patch.
    dummy_patch = Path("dummy.diff")
    dummy_patch.touch()
    
    # Temporäre Korrektur des Namespace für FtwPatch
    mock_args.patch_file = dummy_patch
    
    # FtwPatch Instanz erstellen
    patcher = FtwPatch(args=mock_args)
    
    # Den Dummy wieder löschen, da er nicht für die Tests verwendet wird
    dummy_patch.unlink() 
    return patcher


# --- Testfälle für Standardanwendung ---

def test_hunk_application_basic_change():
    """Testet einen einfachen Hunk mit Löschung und Hinzufügung."""
    patcher = create_mock_ftw_patch()
    
    original_lines = [
        "Line 1: Context\n",
        "Line 2: Delete me\n",
        "Line 3: Context\n",
    ]
    
    hunk = Hunk(
        original_start=1,
        original_length=3,
        new_start=1,
        new_length=3,
        lines=[
            HunkLine(" Line 1: Context\n"),
            HunkLine("-Line 2: Delete me\n"),
            HunkLine("+Line 2: Added instead\n"),
            HunkLine(" Line 3: Context\n"),
        ]
    )
    
    new_content = patcher._apply_hunk_to_file(
        Path("test.txt"), hunk, original_lines
    )
    
    expected = [
        "Line 1: Context\n",
        "Line 2: Added instead\n",
        "Line 3: Context\n",
    ]
    assert new_content == expected


def test_hunk_application_mismatch():
    """Testet, ob ein Context Mismatch korrekt FtwPatchError auslöst."""
    patcher = create_mock_ftw_patch()
    
    original_lines = [
        "Line 1: Correct Context\n",
        "Line 2: WRONG content\n", # <-- Mismatch hier
        "Line 3: Context\n",
    ]
    
    hunk = Hunk(
        original_start=1,
        original_length=3,
        new_start=1,
        new_length=3,
        lines=[
            HunkLine(" Line 1: Correct Context\n"),
            HunkLine(" Line 2: Expected content\n"),
            HunkLine(" Line 3: Context\n"),
        ]
    )
    
    with pytest.raises(FtwPatchError) as excinfo:
        patcher._apply_hunk_to_file(Path("test.txt"), hunk, original_lines)
        
    assert "Context mismatch" in str(excinfo.value)
    assert "line 2" in str(excinfo.value)


def test_hunk_application_no_newline_handling():
    """Testet das Entfernen des Newlines bei hunk.new_has_newline=False."""
    patcher = create_mock_ftw_patch()
    
    original_lines = [
        "Last line with newline\n",
    ]
    
    # Fügt eine neue Zeile hinzu und markiert, dass die letzte Zeile keinen 
    # Newline haben soll
    hunk = Hunk(
        original_start=1,
        original_length=1,
        new_start=1,
        new_length=2,
        lines=[
            HunkLine("-Last line with newline\n"),
            HunkLine("+New last line"),
        ],
        new_has_newline=False
    )
    
    new_content = patcher._apply_hunk_to_file(
        Path("test.txt"), hunk, original_lines
    )
    
    # Erwartet, dass die letzte Zeile KEIN \n enthält
    expected = [
        "New last line",
    ]
    assert new_content == expected


# --- Testfälle für Whitespace-Optionen ---

def test_normalize_ws_success():
    """Testet --normalize-ws: Normalisiert inneren Whitespace."""
    patcher = create_mock_ftw_patch(normalize_ws=True)
    
    original_lines = [
        "def   some_func(arg): \n", # Mehrere Leerzeichen
    ]
    
    hunk = Hunk(
        original_start=1,
        original_length=1,
        new_start=1,
        new_length=1,
        lines=[
            HunkLine(" def some_func(arg): \n"), # Nur ein Leerzeichen (normalisiert)
        ]
    )
    
    new_content = patcher._apply_hunk_to_file(
        Path("test.txt"), hunk, original_lines
    )
    
    # Die Originalzeile wird beibehalten (kein Unterschied im Context)
    assert new_content == original_lines


def test_ignore_all_ws_success():
    """Testet --ignore-all-ws: Ignoriert jeglichen Whitespace."""
    patcher = create_mock_ftw_patch(ignore_all_ws=True)
    
    original_lines = [
        "    if (x == 1) {\n",
    ]
    
    hunk = Hunk(
        original_start=1,
        original_length=1,
        new_start=1,
        new_length=1,
        lines=[
            HunkLine(" if(x==1){"), # Im Hunk fehlen Spaces und Einrückung
        ]
    )
    
    new_content = patcher._apply_hunk_to_file(
        Path("test.txt"), hunk, original_lines
    )
    
    # Trotz unterschiedlicher Whitespace-Menge im Original und im Hunk (im Hunk 
    # ist der Whitespace komplett entfernt), gilt der Match
    assert new_content == original_lines
    
    # Testen der Löschung:
    original_lines = [
        "    delete me;\n",
    ]
    hunk_delete = Hunk(
        original_start=1,
        original_length=1,
        new_start=1,
        new_length=0,
        lines=[
            HunkLine("-delete me;"), # Der Hunk erwartet keine Einrückung
        ]
    )
    new_content = patcher._apply_hunk_to_file(
        Path("test.txt"), hunk_delete, original_lines
    )
    assert new_content == []


# --- Testfälle für Blank Line Ignore (--ignore-bl) ---

def test_ignore_bl_collapse_context():
    """
    Testet --ignore-bl: Überspringt (collapsed) Leerzeilen im Original, 
    wenn der Hunk dies nicht erwartet (1 Leerzeile im Hunk vs. 2 im Original).
    """
    patcher = create_mock_ftw_patch(ignore_bl=True)
    
    original_lines = [
        "Line 1: Start\n",
        "\n", # Leerzeile 1 im Original (wird übersprungen)
        "\n", # Leerzeile 2 im Original (wird übersprungen)
        "Line 4: Match Context\n", # Die Zeile, die matchen muss
        "Line 5: End\n",
    ]
    
    # Der Hunk erwartet nur eine leere Zeile (oder gar keine) zwischen den 
    # Inhaltszeilen.
    hunk = Hunk(
        original_start=1,
        # original_length=4, # Gesamtlänge des Kontextes im Original
        original_length=5, # Gesamtlänge des Kontextes im Original
        new_start=1,
        new_length=3,
        lines=[
            HunkLine(" Line 1: Start\n"),
            # " \n", # Eine Leerzeile im Hunk
            HunkLine(" Line 4: Match Context\n"), # Die nächste Inhaltszeile
            HunkLine(" Line 5: End\n"),
        ]
    )
    
    new_content = patcher._apply_hunk_to_file(
        Path("test.txt"), hunk, original_lines
    )
    
    # Im neuen Inhalt bleiben alle Zeilen des Originals erhalten (einschließlich 
    # der übersprungenen Leerzeilen, da es ein Context-Match war).
    assert new_content == original_lines


def test_ignore_bl_skip_deletion():
    """
    Testet --ignore-bl: Überspringt Leerzeilen im Original, wenn der Hunk 
    eine Inhaltszeile zur Löschung erwartet.
    """
    patcher = create_mock_ftw_patch(ignore_bl=True)
    
    original_lines = [
        "Line 1: Context\n",
        "\n", # Leerzeile im Original (wird übersprungen)
        "Line 3: Delete me\n", # Wird gelöscht
        "Line 4: Context\n",
    ]
    
    # Der Hunk erwartet eine Inhaltszeile zur Löschung
    hunk = Hunk(
        original_start=1,
        original_length=4,
        new_start=1,
        new_length=3,
        lines=[
            HunkLine(" Line 1: Context\n"),
            HunkLine("-Line 3: Delete me\n"), # Löschung der Inhaltszeile
            HunkLine(" Line 4: Context\n"),
        ]
    )
    
    new_content = patcher._apply_hunk_to_file(
        Path("test.txt"), hunk, original_lines
    )
    
    # Erwartet: Leerzeile 2 wurde NICHT in den neuen Inhalt übernommen (sie wurde 
    # ignoriert/übersprungen und zählt nicht zum Context).
    expected = [
        "Line 1: Context\n",
        "Line 4: Context\n",
    ]
    assert new_content == expected


def test_ignore_bl_no_skip_on_blank_line_context():
    """
    Testet --ignore-bl: Führt KEINEN Skip aus, wenn die Hunk-Zeile selbst 
    eine leere Zeile (nur \n) ist. Der Match muss exakt sein.
    """
    patcher = create_mock_ftw_patch(ignore_bl=True)
    
    original_lines = [
        "Line 1: Context\n",
        "\n", # Leerzeile im Original 
        "\n", # Eine zweite Leerzeile
        "Line 4: Context\n",
    ]
    
    # Der Hunk erwartet eine leere Zeile, gefolgt von der nächsten Inhaltszeile.
    hunk = Hunk(
        original_start=1,
        original_length=4,
        new_start=1,
        new_length=4,
        lines=[
            HunkLine(" Line 1: Context\n"),
            HunkLine(" \n"), # Hunk erwartet EINE Leerzeile
            HunkLine(" Line 4: Context\n"),
        ]
    )
    
    # Hier muss der Skip aufhören, da die Hunk-Zeile '\n' ist (normiert zu '')
    # Beim Lesen von Original Lines 2 ('\n') wird der Skip NICHT ausgeführt,
    # da die Hunk-Zeile `norm_hunk_line == ''` ist.
    # ABER: Die normale Match-Logik würde hier fehlschlagen, da die 
    # Match-Logik in `_normalize_line` die Hunk-Zeile zu '' und die 
    # Originalzeile zu '' normalisiert, d.h. sie matchen. 
    # Wenn wir zwei Leerzeilen im Original haben und eine im Hunk, sollte 
    # der Match trotzdem fehlschlagen, wenn wir nicht skippen.
    
    # Da die Hunk-Logik im Code so implementiert ist, dass sie nur skippt, 
    # wenn der Hunk eine **Inhaltszeile** erwartet (`norm_hunk_line != ''`), 
    # führt die zweite Leerzeile im Original zu einem Mismatch, 
    # da die nächste Hunk-Zeile " Line 4: Context\n" matchen muss,
    # während die nächste Original-Zeile noch "\n" ist.
    # Hier prüfen wir den Fehlerfall:
    with pytest.raises(FtwPatchError) as excinfo:
        patcher._apply_hunk_to_file(Path("test.txt"), hunk, original_lines)
    
    # Hier tritt der Mismatch auf, weil " Line 4: Context" nicht mit "\n" matched,
    # nachdem die erste Leerzeile matchen durfte.
    assert "Context mismatch" in str(excinfo.value)
#    assert "line 4" in str(excinfo.value)
    assert "line 3" in str(excinfo.value)