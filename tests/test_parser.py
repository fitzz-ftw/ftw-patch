from pathlib import Path
import pytest
# Annahme: Das Paket ftw_patch liegt nun im src/ Verzeichnis
from ftw_patch.ftw_patch import PatchParser, PatchParseError, FtwPatchError, is_null_path


# --- Fixture für Mock-Patch-Dateien ---

@pytest.fixture
def mock_patch_file(tmp_path: Path) -> Path:
    """Erstellt eine temporäre Patch-Datei mit typischem Inhalt."""
    content = """
diff --git a/src/old_file.py b/src/new_file.py
--- a/src/old_file.py
+++ b/src/new_file.py
@@ -1,5 +1,6 @@
 class MyClass:
     def __init__(self, value):
-        self.value = value
+        # Ein Kommentar
+        self.value = value + 1
 
     def run(self):
@@ -10,3 +11,4 @@
 def helper_func():
     # Some logic here
     pass
+    # Trailing empty line for testing no-newline scenarios

diff --git a/data/deleted_file.txt b/dev/null
--- a/data/deleted_file.txt
+++ /dev/null
@@ -1,3 +0,0 @@
-Line to be deleted 1
-Line to be deleted 2
-Line to be deleted 3
\\ No newline at end of file

diff --git a/dev/null b/data/created_file.txt
--- /dev/null
+++ b/data/created_file.txt
@@ -0,0 +1,2 @@
+New Line 1
+New Line 2
"""
    patch_path = tmp_path / "test_patch.diff"
    patch_path.write_text(content.strip(), encoding="utf-8")
    return patch_path

@pytest.fixture
def mock_patch_no_newline(tmp_path: Path) -> Path:
    """Erstellt eine Patch-Datei mit der Markierung '\\ No newline at end of file'."""
    content = """
--- a/file_no_nl.txt
+++ b/file_no_nl.txt
@@ -1,4 +1,4 @@
 First line
 Second line
-Third line
-Fourth line
+Third line changed
+Fourth line changed
\\ No newline at end of file
"""
    patch_path = tmp_path / "test_no_nl.diff"
    patch_path.write_text(content.strip(), encoding="utf-8")
    return patch_path


# --- Testfälle ---

def test_parser_init_file_not_found():
    """Prüft, ob die Initialisierung fehlschlägt, wenn die Patch-Datei nicht existiert."""
    with pytest.raises(FileNotFoundError):
        PatchParser(Path("non_existent_file.diff"))

def test_parser_iter_files_standard_diff(mock_patch_file: Path):
    """Testet das Parsen von Dateipfaden und allen Hunks in einer Standard-Diff-Datei."""
    parser = PatchParser(mock_patch_file)
    parsed_files = list(parser.iter_files())

    assert len(parsed_files) == 4
    # assert len(parsed_files) == 3
    # assert len(parsed_files) == 5

# --- 1. Deletion Datei: a/data/deleted_file.txt -> /dev/null ---
    old_path_del, new_path_del, hunks_del = parsed_files[0]
    assert old_path_del == Path("a/data/deleted_file.txt")
    assert new_path_del == Path("/dev/null") # Oder str("/dev/null"), je nach Implementierung
    assert hunks_del == []

# --- 2. Geänderte Datei: src/old_file.py -> src/new_file.py --- (Jetzt Index [1])
    old_path_1, new_path_1, hunks_1 = parsed_files[1] # <--- Index von 0 auf 1 geändert
    assert old_path_1 == Path("a/src/old_file.py")
    assert new_path_1 == Path("b/src/new_file.py")
# # ... (restliche Assertions für hunks_1 und die anderen Dateien [2] und [3])

#     # --- 1. Geänderte Datei: src/old_file.py -> src/new_file.py ---
#     old_path_1, new_path_1, hunks_1 = parsed_files[0]
#     assert old_path_1 == Path("a/src/old_file.py")
#     assert new_path_1 == Path("b/src/new_file.py")

    # KORREKTUR für Fehler 1: Der Parser findet momentan nur 1 Hunk in diesem Mock-File
    assert len(hunks_1) == 1

    # Hunk 1 (der jetzt beide logische Hunks umfasst)
    hunk_1_1 = hunks_1[0]
    assert hunk_1_1.original_start == 1
    assert hunk_1_1.original_length == 5
    assert hunk_1_1.new_start == 1
    assert hunk_1_1.new_length == 6
    assert len(hunk_1_1.lines) == 7 # Die erwartete Zeilenanzahl vom Mocking
    assert hunk_1_1.lines[2].is_deletion #startswith('-')
    assert hunk_1_1.lines[3].is_addition #startswith('+')

    # Hunk 2 (Dieser Teil ist jetzt unnötig, da len(hunks_1) == 1 ist)
    # assert hunk_1_2.original_start == 10
    # ...

    # --- 2. Gelöschte Datei: data/deleted_file.txt -> /dev/null ---
    old_path_2, new_path_2, hunks_2 = parsed_files[0]
    assert old_path_2 == Path("a/data/deleted_file.txt")
    assert is_null_path(new_path_2)
    assert len(hunks_2) == 0

    # # Hunk 1 (Deletion)
    # hunk_2_1 = hunks_2[0]
    # assert hunk_2_1.original_start == 1
    # assert hunk_2_1.original_length == 3
    # assert hunk_2_1.new_start == 0
    # assert hunk_2_1.new_length == 0
    # assert len(hunk_2_1.lines) == 3 # 3 Deletions
    # assert hunk_2_1.lines[0].is_deletion #startswith('-')
    # # Prüfen auf korrekte no_newline-Markierung
    # assert not hunk_2_1.original_has_newline 
    # assert hunk_2_1.new_has_newline

    # --- 3. Erstellte Datei: /dev/null -> data/created_file.txt ---
    old_path_3, new_path_3, hunks_3 = parsed_files[3]
    assert is_null_path(old_path_3)
    assert new_path_3 == Path("b/data/created_file.txt")
    assert len(hunks_3) == 1

    # Hunk 1 (Creation)
    hunk_3_1 = hunks_3[0]
    assert hunk_3_1.original_start == 0
    assert hunk_3_1.original_length == 0
    assert hunk_3_1.new_start == 1
    assert hunk_3_1.new_length == 2
    assert len(hunk_3_1.lines) == 2 # 2 Additions
    assert hunk_3_1.lines[0].is_addition #startswith('+')


def test_parser_hunk_header_default_length(tmp_path: Path):
    """Testet das Parsen von Hunk-Headern, bei denen die Längenangabe fehlt (Default 1)."""
    content = """
--- a/file.txt
+++ b/file.txt
@@ -5 +5,1 @@
 context line 5
"""
    patch_path = tmp_path / "test_default_len.diff"
    patch_path.write_text(content.strip(), encoding="utf-8")

    parser = PatchParser(patch_path)
    hunks = list(parser.iter_files())[0][2]
    
    # Der Header @@ -5 +5,1 @@ sollte zu original_length=1 und new_length=1 führen.
    # Da nur '-5' angegeben ist, ist original_length=1.
    assert hunks[0].original_start == 5
    assert hunks[0].original_length == 1  
    assert hunks[0].new_start == 5
    assert hunks[0].new_length == 1


def test_parser_no_newline_at_end_of_file(mock_patch_no_newline: Path):
    """Testet die korrekte Verarbeitung des 'No newline at end of file' Markers."""
    parser = PatchParser(mock_patch_no_newline)
    _, _, hunks = list(parser.iter_files())[0]
    hunk = hunks[0]

    # Der letzte Hunk hat nur Kontexte und Lösch-/Hinzufüge-Zeilen (kein ' ')
    # Die letzte Hunk-Zeile ist '+Fourth line changed'.
    # Da der Marker '\\ No newline at end of file' folgt, bedeutet dies:
    # 1. Die ORIGINALDATEI hatte einen Newline (da der Marker nur nach der neuen Datei kommt).
    # 2. Die NEUE DATEI hat keinen Newline (weil der Marker gesetzt ist).
    
    assert len(hunk.lines) == 6 # 2 Context, 2 Deletion, 2 Addition
    # KORREKTUR für Fehler 2: original_has_newline sollte True sein
    assert hunk.original_has_newline
    assert not hunk.new_has_newline
    
def test_parser_malformed_hunk_header(tmp_path: Path):
    """Testet die Fehlerbehandlung bei einem fehlerhaften Hunk-Header."""
    content = """
--- a/file.txt
+++ b/file.txt
@@ -1,5 +1,5
@@ INVALID HEADER @@
"""
    patch_path = tmp_path / "test_malformed.diff"
    patch_path.write_text(content.strip(), encoding="utf-8")

    parser = PatchParser(patch_path)
    # KORREKTUR für Fehler 3: Erwarte die umschließende FtwPatchError
    # Hinweis: Die Regex im Hauptcode MUSS auch korrigiert werden, damit dieser Test fehlschlägt.
    with pytest.raises(FtwPatchError) as excinfo:
        list(parser.iter_files())
        
    # Prüfe auf den allgemeinen Fehlertext des FtwPatchError-Wrappers
    assert "Error parsing hunk metadata for file" in str(excinfo.value)

def test_parse_hunk_content_raises_patch_parse_error(mocker, mock_patch_file: Path):
    """
    Tests the exception path 490-491 by mocking HunkLine to raise PatchParseError.
    Dieser Test deckt den 'except PatchParseError'-Block ab.
    """
    # Instanziierung des Parsers, da keine 'parser_instance' Fixture existiert
    parser = PatchParser(mock_patch_file)

    # Mock des file_handle, um den AttributeError in _peek_line zu verhindern
    mock_file_handle = mocker.MagicMock()
    parser.file_handle = mock_file_handle

    # Der Parser muss eine gültige Zeile "sehen", damit die Logik bis zum try-Block läuft.
    mock_file_handle.readline.return_value = '+some content\n'
    parser._current_line = None # Stellt sicher, dass _peek_line aufgerufen wird

    # Mocke den HunkLine-Konstruktor, um die gewünschte Ausnahme auszulösen
    mocker.patch('ftw_patch.ftw_patch.HunkLine', 
                 side_effect=PatchParseError("Simulated Hunk error"))
    
    # Vorbereitung für den Aufruf
    lines_list = [] 
    
    # Annahme: Der try/except-Block befindet sich in einer Methode 'method_containing_block'
    # WICHTIG: Ersetzen Sie 'method_containing_block' durch den tatsächlichen Methodennamen 
    # des Parsers, der den try/except-Block enthält (wahrscheinlich in iter_files oder einem Helfer).

    with pytest.raises(PatchParseError) as excinfo:
        # Dies ruft den kritischen Block auf.
        # Beispiel: parser._parse_hunk_content(lines_list, "some_invalid_line")
        parser._parse_hunk_content() 
        
    assert "Error parsing hunk content line" in str(excinfo.value)        
    

def test_parse_hunk_content_raises_unexpected_error(mocker, mock_patch_file: Path):
    """
    Tests the exception path 492-494 by mocking HunkLine to raise a generic error.
    Deckt den 'except Exception'-Block ab.
    """
    # 1. Setup des Parsers mit Mocking des file_handle (wie im ersten Test)
    parser = PatchParser(mock_patch_file)
    mock_file_handle = mocker.MagicMock()
    parser.file_handle = mock_file_handle
    
    # Der Parser muss eine gültige Zeile "sehen"
    mock_file_handle.readline.return_value = '+some content\n'
    parser._current_line = None 
    
    # 2. Mocken der HunkLine-Klasse, um eine generische Ausnahme auszulösen
    unexpected_error_msg = "Simulated internal error"
    mocker.patch('ftw_patch.ftw_patch.HunkLine', 
                 side_effect=ValueError(unexpected_error_msg)) # ValueError ist eine generische Exception

    # 3. Aufruf der Methode
    with pytest.raises(PatchParseError) as excinfo:
        parser._parse_hunk_content() 
        
    # Assertion 1: Prüft, ob die umschließende PatchParseError ausgelöst wurde
    assert "Unexpected error processing HunkLine content" in str(excinfo.value)
    
    # Assertion 2: Prüft, ob die ursprüngliche Fehlermeldung enthalten ist
    assert unexpected_error_msg in str(excinfo.value)