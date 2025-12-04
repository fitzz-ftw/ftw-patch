from pathlib import Path
import pytest
# Annahme: Das Paket ftw_patch liegt nun im src/ Verzeichnis
from ftw_patch.ftw_patch import PatchParser, PatchParseError, Hunk, DEV_NULL_PATH


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
    """Erstellt eine Patch-Datei mit der Markierung '\ No newline at end of file'."""
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

    assert len(parsed_files) == 3

    # --- 1. Geänderte Datei: src/old_file.py -> src/new_file.py ---
    old_path_1, new_path_1, hunks_1 = parsed_files[0]
    assert old_path_1 == Path("src/old_file.py")
    assert new_path_1 == Path("src/new_file.py")
    assert len(hunks_1) == 2

    # Hunk 1
    hunk_1_1 = hunks_1[0]
    assert hunk_1_1.original_start == 1
    assert hunk_1_1.original_length == 5
    assert hunk_1_1.new_start == 1
    assert hunk_1_1.new_length == 6
    assert len(hunk_1_1.lines) == 5 # 2 Context, 1 Deletion, 2 Addition
    assert hunk_1_1.lines[1].startswith('-')
    assert hunk_1_1.lines[2].startswith('+')

    # Hunk 2
    hunk_1_2 = hunks_1[1]
    assert hunk_1_2.original_start == 10
    assert hunk_1_2.original_length == 3
    assert hunk_1_2.new_start == 11
    assert hunk_1_2.new_length == 4
    assert len(hunk_1_2.lines) == 4
    assert hunk_1_2.lines[-1].startswith('+')

    # --- 2. Gelöschte Datei: data/deleted_file.txt -> /dev/null ---
    old_path_2, new_path_2, hunks_2 = parsed_files[1]
    assert old_path_2 == Path("data/deleted_file.txt")
    assert new_path_2 == DEV_NULL_PATH
    assert len(hunks_2) == 1

    # Hunk 1 (Deletion)
    hunk_2_1 = hunks_2[0]
    assert hunk_2_1.original_start == 1
    assert hunk_2_1.original_length == 3
    assert hunk_2_1.new_start == 0
    assert hunk_2_1.new_length == 0
    assert len(hunk_2_1.lines) == 3 # 3 Deletions
    assert hunk_2_1.lines[0].startswith('-')
    # Prüfen auf korrekte no_newline-Markierung
    assert hunk_2_1.original_has_newline == False 
    assert hunk_2_1.new_has_newline == True # In der neuen Datei gibt es keinen Inhalt, also ist der Newline-Status für 'new' irrelevant (oder standardmäßig True)

    # --- 3. Erstellte Datei: /dev/null -> data/created_file.txt ---
    old_path_3, new_path_3, hunks_3 = parsed_files[2]
    assert old_path_3 == DEV_NULL_PATH
    assert new_path_3 == Path("data/created_file.txt")
    assert len(hunks_3) == 1

    # Hunk 1 (Creation)
    hunk_3_1 = hunks_3[0]
    assert hunk_3_1.original_start == 0
    assert hunk_3_1.original_length == 0
    assert hunk_3_1.new_start == 1
    assert hunk_3_1.new_length == 2
    assert len(hunk_3_1.lines) == 2 # 2 Additions
    assert hunk_3_1.lines[0].startswith('+')


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
    # 1. Die ORIGINALDATEI hatte keinen Newline (weil es gelöschte Zeilen gab)
    # 2. Die NEUE DATEI hat keinen Newline (weil die hinzugefügte/geänderte Zeile die letzte ist)
    
    assert len(hunk.lines) == 6 # 2 Context, 2 Deletion, 2 Addition
    assert hunk.original_has_newline == False
    assert hunk.new_has_newline == False
    
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
    with pytest.raises(PatchParseError) as excinfo:
        list(parser.iter_files())
        
    assert "Malformed hunk header found" in str(excinfo.value)