from pathlib import Path

from ftw.patch.ftw_patch import is_null_path

# Angenommen, Sie haben is_null_path und die Konstanten NULL_PATHS_POSIX/WIN_UPPER
# in Ihrem Modul importiert.

def test_is_null_path_posix_standard():
    """Prüft den standardmäßigen POSIX Null-Pfad ('/dev/null')."""
    # Muss exakt case-sensitiv übereinstimmen
    assert is_null_path("/dev/null") is True
    assert is_null_path(Path("/dev/null")) is True

def test_is_null_path_posix_case_mismatch():
    """Prüft, ob POSIX-Pfade bei falscher Großschreibung fehlschlagen 
    (wegen case-sensitiver Natur)."""
    assert is_null_path("/DEV/NULL") is False
    assert is_null_path(Path("/DEV/NULL")) is False

def test_is_null_path_windows_standard_and_case_insensitive():
    """Prüft den Windows Null-Pfad ('NUL') und dessen case-insensitive Behandlung."""
    # Standard (Upper)
    assert is_null_path("NUL") is True
    assert is_null_path(Path("NUL")) is True
    
    # Lowercase und gemischt
    assert is_null_path("nul") is True
    assert is_null_path("NuL") is True

def test_is_null_path_negative_cases():
    """Prüft, ob normale Pfade fälschlicherweise als Null-Pfade erkannt werden."""
    assert is_null_path("/path/to/file.txt") is False
    assert is_null_path("null") is False
    assert is_null_path("DEV_NULL") is False
    assert is_null_path("") is False
