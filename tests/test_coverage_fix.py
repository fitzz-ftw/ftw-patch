from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from ftw.patch.ftw_patch import PatchParser


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
