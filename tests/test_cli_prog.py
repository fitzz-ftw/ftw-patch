from pathlib import Path
import pytest
import sys

# ANNAHME: Importiere die Hauptfunktion und FtwPatch aus dem Modul
# WICHTIG: BITTE 'prog_ftw_patch' durch den tatsächlichen Namen Ihrer Hauptfunktion ersetzen!
from ftw_patch.ftw_patch import FtwPatch, FtwPatchError, prog_ftw_patch 

# Dies ist Ihre Hauptfunktion, die die Zeilen 1271-1342 repräsentiert
prog_entrypoint = prog_ftw_patch 


def test_cli_entrypoint_success(tmp_path: Path, mocker):
    """
    Testet den Haupt-Einstiegspunkt der CLI. 
    Deckt die Argumentverarbeitung, FtwPatch-Instanziierung und den Aufruf von apply_patch() ab 
    (betrifft die fehlenden Zeilen 1271-1342).
    """
    
    # 1. Setup der Testdateien (Patch und Target)
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    # Erstellen der Originaldatei, die vom Patch benötigt wird
    target_file = target_dir / "file.txt"
    target_file.write_text("Old content\n") 
    
    patch_file = tmp_path / "test.patch"
    # Ein einfacher Patch, damit der Code erfolgreich die Argumente parsen kann
    patch_file.write_text(
        "--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-Old content\n+New content\n"
    )

    # 2. Mocking: Simulieren der Kommandozeilenargumente in sys.argv
    # Wir übergeben minimale, gültige Argumente
    mock_argv = [
        "ftw_patch_script",                 # sys.argv[0]
        str(patch_file.resolve()),          # Patch file path
        "-d", str(target_dir.resolve()),
        "-p", "1",
    ]
    # Patch sys.argv für die Dauer des Tests
    mocker.patch('sys.argv', mock_argv)
    
    # 3. Mocking: Verhindern der tatsächlichen Ausführung der FtwPatch-Logik
    # Wir ersetzen FtwPatch durch einen Mock, der nur die Aufrufe zählt (Spying).
    mock_patcher = mocker.Mock()
    mock_FtwPatch_class = mocker.patch(
        'ftw_patch.ftw_patch.FtwPatch', 
        return_value=mock_patcher
    )
    
    # 4. Ausführung der CLI-Funktion
    try:
        prog_entrypoint() 
    except SystemExit as e:
        # Bei erfolgreicher Ausführung ruft argparse.ArgumentParser oft sys.exit(0) auf
        assert e.code == 0
        
    # 5. Überprüfung: Bestätigen, dass die CLI-Funktion die korrekten Schritte ausgeführt hat
    
    # Prüfen, ob FtwPatch mit den geparsten Argumenten aufgerufen wurde
    mock_FtwPatch_class.assert_called_once()
    
    # Prüfen, ob apply_patch() auf der Instanz aufgerufen wurde
    mock_patcher.apply_patch.assert_called_once()


def test_cli_entrypoint_ftw_patch_error(tmp_path: Path, mocker):
    """
    Testet die Fehlerbehandlung (Exception-Handling) in prog_ftw_patch 
    durch Auslösen eines FtwPatchError und Überprüfung des Rückgabewertes (1).
    (Deckt die Exception-Behandlung in Zeilen 1289-1302 ab).
    """
    # ... Setup-Code (mock_argv, mocker.patch von FtwPatch) ...
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    patch_file = tmp_path / "test.patch"
    patch_file.write_text("irrelevant content")

    mock_argv = [
        "ftw_patch_script", str(patch_file.resolve()),
        "-d", str(target_dir.resolve()), 
        "-p", "1",
    ]
    mocker.patch('sys.argv', mock_argv)

    mock_patcher = mocker.Mock()
    # Mock FtwPatch.apply_patch, um den Fehler auszulösen
    mock_patcher.apply_patch.side_effect = FtwPatchError("Simulierter FtwPatch Anwendungsfehler.")
    
    mocker.patch(
        'ftw_patch.ftw_patch.FtwPatch', 
        return_value=mock_patcher
    )
    
    # Führen Sie die CLI-Funktion aus und überprüfen Sie den Rückgabewert
    # Wir erwarten den Fehlercode 1
    return_code = prog_ftw_patch() 
    
    assert return_code == 1


def test_cli_entrypoint_file_not_found(tmp_path: Path, mocker):
    """
    Testet die Abdeckung des FileNotFoundError-Pfades in prog_ftw_patch.
    Dies wird ausgelöst, wenn die Patch-Datei nicht existiert.
    """
    
    # 1. Patch-Datei, die NICHT existiert
    non_existent_patch_file = tmp_path / "non_existent.patch"
    
    # 2. Mock sys.argv mit dem Pfad zur nicht existierenden Datei
    mock_argv = [
        "ftw_patch_script", str(non_existent_patch_file.resolve()),
        "-d", str(tmp_path / "target"), 
        "-p", "1",
    ]
    mocker.patch('sys.argv', mock_argv)

    # 3. Ausführung der CLI-Funktion
    # FileNotFoundError wird beim Versuch, die Patch-Datei zu lesen (z.B. im FtwPatch-Konstruktor oder Parser), ausgelöst.
    return_code = prog_ftw_patch() 
    
    # 4. Überprüfung: Erwarteter Rückgabewert ist 1 bei einem Fehler
    assert return_code == 1


def test_cli_entrypoint_generic_exception(tmp_path: Path, mocker):
    """
    Testet die Abdeckung des generischen 'except Exception:'-Pfades in prog_ftw_patch
    durch Auslösen einer unvorhergesehenen Exception.
    """
    
    # Setup für gültige Argumente
    target_dir = tmp_path / "target"
    target_dir.mkdir()
    patch_file = tmp_path / "test.patch"
    patch_file.write_text("irrelevant content")

    mock_argv = [
        "ftw_patch_script", str(patch_file.resolve()),
        "-d", str(target_dir.resolve()), 
        "-p", "1",
    ]
    mocker.patch('sys.argv', mock_argv)

    # Mock FtwPatch.apply_patch, um eine nicht abgefangene Standard-Exception auszulösen
    mock_patcher = mocker.Mock()
    mock_patcher.apply_patch.side_effect = ValueError("Simulierter unhandled interner Fehler.")
    
    mocker.patch(
        'ftw_patch.ftw_patch.FtwPatch', 
        return_value=mock_patcher
    )
    
    # Ausführung und Überprüfung des Rückgabewerts (1 für Fehler)
    return_code = prog_ftw_patch() 
    
    # Erwarteter Rückgabewert ist 1
    assert return_code == 1