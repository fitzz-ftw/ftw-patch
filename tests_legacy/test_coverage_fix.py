from argparse import Namespace
from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from ftw.patch.ftw_patch import FtwPatch, HunkLine, PatchParseError, PatchParser


def test_coverage_branch_562_addition_no_newline(tmp_path):
    """
    Fixes Partial Branch 562->573.
    
    This test creates a patch where the last line of a hunk is an ADDITION (+),
    followed by the '\\ No newline' marker.
    - line.is_context is False
    - line.is_deletion is False
    -> The first if-block (Line 562) is skipped.
    - line.is_addition is True
    -> The second if-block is entered.
    """
    patch_path = tmp_path / "addition_no_newline.patch"
    
    # Der entscheidende Part: Das '+' am Ende vor dem Marker
    patch_content = (
        "--- a/old.txt\n"
        "+++ b/new.txt\n"
        "@@ -1,1 +1,2 @@\n"
        " context line\n"
        "+added line without newline\n"
        "\\ No newline at end of file\n"
    )
    patch_path.write_text(patch_content)

    parser = PatchParser(patch_path)
    files = list(parser.iter_files())
    
    assert len(files) == 1
    hunks = files[0][2]
    hunk = hunks[0]
    
    # Verifikation der Logik:
    # 1. Die Original-Datei hatte ein Newline (da die letzte Zeile des Hunks ein '+' ist)
    assert hunk.original_has_newline is True
    # 2. Die neue Datei hat KEIN Newline (wegen des Markers nach dem '+')
    assert hunk.new_has_newline is False
    
    # Bonus: Prüfen, ob die letzte Zeile wirklich eine Addition ist
    assert hunk.lines[-1].is_addition is True
    assert hunk.lines[-1].is_context is False
    assert hunk.lines[-1].is_deletion is False

def test_coverage_branch_562_empty_lines(tmp_path):
    """
    Zusatz-Check: Deckt den Fall ab, falls 'if lines:' selbst 
    False ist (theoretisches Sicherheitsnetz im Code).
    """
    patch_path = tmp_path / "empty_hunk.patch"
    # Ein Hunk-Header ohne Linien (untypisch, aber triggert 'if lines' == False)
    patch_content = (
        "--- a/old.txt\n"
        "+++ b/new.txt\n"
        "@@ -0,0 +0,0 @@\n"
    )
    patch_path.write_text(patch_content)

    parser = PatchParser(patch_path)
    files = list(parser.iter_files())
    hunks = files[0][2]
    assert len(hunks[0].lines) == 0

def test_coverage_loop_exit_via_sentinel(tmp_path):
    """
    Fixes Branch 1206->1139.
    Creates a hunk that ends naturally with EOF (no break triggered).
    """
    # Ein Patch, der mitten im Hunk einfach aufhört (EOF)
    p = tmp_path / "eof.patch"
    p.write_text("--- a/f\n+++ b/f\n@@ -1,1 +1,1 @@\n ")
    
    parser = PatchParser(p)
    # iter_files triggert _parse_hunk_content
    files = list(parser.iter_files())
    assert len(files) == 1

def test_coverage_marker_without_lines(tmp_path):
    """
    Fixes Branch 551->562.
    Forces 'if lines:' to be False by having a marker immediately after header.
    """
    p = tmp_path / "no_lines.patch"
    p.write_text("--- a/f\n+++ b/f\n@@ -1,1 +1,1 @@\n\\ No newline at end of file\n")
    
    parser = PatchParser(p)
    files = list(parser.iter_files())
    # This ensures the code path where 'lines' is empty is executed
    assert len(files[0][2][0].lines) == 0

def test_coverage_unexpected_exception_hunkline(mocker, tmp_path):
    """
    Fixes Branch 973->976 (The generic Exception catch).
    """
    p = tmp_path / "error.patch"
    p.write_text("--- a/f\n+++ b/f\n@@ -1,1 +1,1 @@\n+line\n")
    
    # We force HunkLine to throw a weird error (not a PatchParseError)
    mocker.patch("ftw.patch.ftw_patch.HunkLine", side_effect=IndexError("Simulated Index Error"))
    
    parser = PatchParser(p)
    with pytest.raises(PatchParseError, match="Unexpected error processing HunkLine content"):
        list(parser.iter_files())

def test_coverage_parser_sentinel_exit(tmp_path, mocker):
    """
    Simulates an empty file/EOF to ensure the iter() loop 
    terminates naturally (covering the False branch of the loop).
    """
    from ftw.patch.ftw_patch import PatchParser
    
    # We create a dummy file
    p = tmp_path / "empty.patch"
    p.write_text("")
    
    parser = PatchParser(p)
    
    # We mock _peek_line so it immediately returns the sentinel ""
    # even if there were content, the loop would now terminate.
    mocker.patch.object(parser, '_peek_line', return_value="")
    
    # This call now hits the 'False' branch of the for-loop immediately
    lines, orig_nl, new_nl = parser._parse_hunk_content()
    
    assert lines == []
    assert orig_nl is True

def test_coverage_natural_loop_exit(tmp_path):
    # Ein Patch, der exakt nach der letzten Zeile des Hunks endet.
    # Kein Marker, kein neuer Header, einfach EOF.
    patch_content = (
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1,1 +1,1 @@\n"
        " context line" # Wichtig: Kein \n am Ende, damit EOF sofort kommt
    )
    p = tmp_path / "natural_exit.patch"
    p.write_text(patch_content)
    
    parser = PatchParser(p)
    # iter_files -> _parse_hunk_content
    # Die Schleife liest " context line", springt hoch, 
    # _peek_line liefert "", iter() bricht ab.
    list(parser.iter_files())

def test_coverage_force_loop_back_and_exit(mocker, tmp_path):
    from ftw.patch.ftw_patch import PatchParser
    
    # Datei mit einer Zeile
    p = tmp_path / "final_boss.patch"
    p.write_text("--- a/f\n+++ b/f\n@@ -1,1 +1,1 @@\n ")
    
    parser = PatchParser(p)
    
    # Wir faken die Rückgabewerte von _peek_line:
    # 1. Aufruf: " " (Gültiger Content, Schleife läuft)
    # 2. Aufruf: ""  (Sentinel, Schleife muss beenden)
    mocker.patch.object(parser, '_peek_line', side_effect=[" ", "",""])
    
    # Wir müssen auch _read_line mocken, damit der Parser nicht abstürzt
    mocker.patch.object(parser, '_read_line', return_value=" ")

    # Ausführen
    parser._parse_hunk_content()

def test_coverage_apply_patch_multi_file_full_cycle(tmp_path):
    """
    Achieves 100% branch coverage for the main apply loop (1206->1139).
    By processing two separate files, we force a complete back-edge jump
    and a subsequent natural loop termination.
    """
    # 1. Setup target directory and original files
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    file1 = target_dir / "file1.txt"
    file2 = target_dir / "file2.txt"
    file1.write_text("aaa\n", encoding="utf-8")
    file2.write_text("bbb\n", encoding="utf-8")
    
    # 2. Create a patch file modifying both files
    patch_content = (
        "--- file1.txt\n+++ file1.txt\n@@ -1,1 +1,1 @@\n-aaa\n+AAA\n"
        "--- file2.txt\n+++ file2.txt\n@@ -1,1 +1,1 @@\n-bbb\n+BBB\n"
    )
    patch_file = tmp_path / "multi.patch"
    patch_file.write_text(patch_content, encoding="utf-8")
    
    # 3. Mock the Namespace (PIMPLE)
    # Ensure all attributes required by your FtwPatch.__init__ are present
    args = Namespace(
        patch_file=patch_file,
        target_directory=target_dir,
        strip_count=0,
        normalize_whitespace=False,
        ignore_blank_lines=False,
        ignore_all_whitespace=False
    )
    
    # 4. Execute the logic
    patcher = FtwPatch(args)
    patcher.apply_patch() # Triggers the loop in question

    # Verification (optional but good for a robust test)
    assert (target_dir / "file1.txt").read_text() == "AAA\n"
    assert (target_dir / "file2.txt").read_text() == "BBB\n"



def test_coverage_loop_back_edges_saturated(tmp_path):
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    
    # Drei saubere, unterschiedliche Dateien
    # (target_dir / "mod1.txt").write_text("line1\n", encoding="utf-8")
    # (target_dir / "mod2.txt").write_text("line2\n", encoding="utf-8")
    # (target_dir / "del1.txt").write_text("line3\n", encoding="utf-8")
    
    # # Ein Patch, der genau 3 verschiedene Datei-Sektionen hat
    # # Wichtig: Keine doppelten Pfade!
    # patch_content = (
    #     "--- del1.txt\n+++ /dev/null\n@@ -1,1 +0,0 @@\n-line3\n"
    #     "--- mod1.txt\n+++ mod1.txt\n@@ -1,1 +1,1 @@\n-line1\n+MOD1\n"
    #     "--- mod2.txt\n+++ mod2.txt\n@@ -1,1 +1,1 @@\n-line2\n+MOD2\n"
    # )

    (target_dir / "mod1.txt").write_text("line1\nline2\nline3\nline4\nline5\n")

    patch_content = (
        "--- mod1.txt\n+++ mod1.txt\n"
        "@@ -1,1 +1,1 @@\n-line1\n+MOD1\n"  # Hunk 1
        "@@ -4,1 +4,1 @@\n-line4\n+MOD4\n"  # Hunk 2 -> Erzwingt den Rücksprung zu 1194!
    )

    patch_file = tmp_path / "multi.patch"
    patch_file.write_text(patch_content, encoding="utf-8")
    
    args = Namespace(
        patch_file=patch_file,
        target_directory=target_dir,
        strip_count=0,
        dry_run=False,
        normalize_whitespace=False,
        ignore_blank_lines=False,
        ignore_all_whitespace=False
    )
    
    patcher = FtwPatch(args)
    
    # Wir fangen Fehler ab, falls das File-System oder der Parser 
    # doch noch eine Überraschung bereitstellen, damit die 
    # Coverage-Daten trotzdem geschrieben werden.
    try:
        patcher.apply_patch()
    except Exception as e:
        print(f"DEBUG: Exception caught: {e}")
        # Wir lassen den Test trotzdem scheitern, 
        # aber wir sehen die Coverage.
        raise 

    # Überprüfung
    assert (target_dir / "mod1.txt").read_text() == "MOD1\n"
    assert (target_dir / "mod2.txt").read_text() == "MOD2\n"
    assert not (target_dir / "del1.txt").exists()
