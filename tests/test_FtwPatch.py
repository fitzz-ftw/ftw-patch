from argparse import Namespace
from pathlib import Path

import pytest

from ftw.patch.ftw_patch import FtwPatch, FtwPatchError, PatchParseError


class TestFtwPatch:
    """
    Klassengebundene Tests für die FtwPatch-Hauptklasse.
    Deckt Properties, Initialisierung und das Error-Handling der run-Methode ab.
    """

    @pytest.fixture
    def valid_args(self, tmp_path):
        """Erzeugt einen validen Namespace für die Initialisierung."""
        patch_file = tmp_path / "test.patch"
        patch_file.write_text("--- a/file\n+++ b/file\n@@ -1,1 +1,1 @@\n-old\n+new")
        
        return Namespace(
            patch_file=patch_file,
            strip_count=1,
            target_directory=tmp_path,
            normalize_whitespace=True,
            ignore_blank_lines=False,
            ignore_all_whitespace=True,
            dry_run=True
        )

    ## --- Tests für Initialisierung und Properties ---

    def test_initialization_success(self, valid_args):
        """Prüft, ob die Instanz korrekt erstellt wird und die Datei prüft."""
        app = FtwPatch(valid_args)
        assert app.patch_file_path == valid_args.patch_file

    def test_init_raises_file_not_found(self):
        """Prüft den proaktiven Check auf Existenz der Patch-Datei."""
        bad_args = Namespace(patch_file=Path("/tmp/non_existent_patch_123.diff"))
        with pytest.raises(FileNotFoundError) as excinfo:
            FtwPatch(bad_args)
        assert "Patch file not found" in str(excinfo.value)

    def test_all_properties_passthrough(self, valid_args):
        """Verifiziert, dass alle Namespace-Attribute korrekt durchgereicht werden."""
        app = FtwPatch(valid_args)
        
        assert app.strip_count == 1
        assert app.target_directory == valid_args.target_directory
        assert app.normalize_whitespace is True
        assert app.ignore_blank_lines is False
        assert app.ignore_all_whitespace is True
        assert app.dry_run is True

    def test_repr_format(self, valid_args):
        """Prüft die __repr__ Methode für Debugging-Zwecke."""
        app = FtwPatch(valid_args)
        assert "FtwPatch(args=Namespace" in repr(app)

    ## --- Tests für die run() Methode (Error Handling) ---


    def test_run_success_code_zero(self, mocker, valid_args):
        """Prüft, ob run() bei Erfolg 0 zurückgibt."""
        app = FtwPatch(valid_args)
        # Wir mocken 'apply', da dies die Methode ist, die run() aufruft
        mocker.patch.object(app, 'apply', return_value=0)
        
        assert app.run() == 0

    def test_run_known_error_code_one(self, mocker, valid_args):
        """Prüft, ob FtwPatchError (bekannte Fehler) Code 1 liefert."""
        app = FtwPatch(valid_args)
        mocker.patch.object(app, 'apply', side_effect=FtwPatchError("Specific Path Error"))
        
        assert app.run() == 1

    def test_run_unexpected_error_code_two(self, mocker, valid_args):
        """
        Prüft, ob die allgemeine Exception (unvorhergesehene Fehler) 
        abgefangen wird und Code 2 liefert.
        """
        app = FtwPatch(valid_args)
        # Wir werfen die oberste Basis-Exception für Laufzeitfehler
        mocker.patch.object(app, 'apply', side_effect=Exception("Unexpected System Failure"))
        
        assert app.run() == 2

    def test_create_backups_success(self, valid_args, tmp_path):
        """Prüft, ob Backups für mehrere Dateien korrekt erstellt werden."""
        app = FtwPatch(valid_args)
        
        # Testdateien erstellen
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        backup_paths = app._create_backups([file1, file2], extension=".bak")
        
        assert len(backup_paths) == 2
        assert Path(str(file1) + ".bak").exists()
        assert Path(str(file2) + ".bak").read_text() == "content2"

    def test_create_backups_failure_and_cleanup(self, valid_args, tmp_path, mocker):
        """Prüft, ob bei einem Fehler bereits erstellte Backups gelöscht werden."""
        app = FtwPatch(valid_args)
        
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        # Simuliere Fehler beim zweiten Kopier-Vorgang
        # Wir mocken shutil.copy2 (via copy2 im Namespace von ftw_patch)
        import ftw.patch.ftw_patch as patch_module
        mock_copy = mocker.patch.object(patch_module, 'copy2')
        mock_copy.side_effect = [None, OSError("Disk Full")]
        
        with pytest.raises(PatchParseError) as excinfo:
            app._create_backups([file1, file2])
        
        assert "Mandatory backup failed" in str(excinfo.value)
        # Sicherstellen, dass das erste Backup wieder gelöscht wurde (Cleanup)
        assert not Path(str(file1) + ".ftwBak").exists()



    def test_commit_changes_rollback_on_failure(self, valid_args, tmp_path, mocker):
        """
        Tests lines 1401-1429: Verifies that OSError is caught, 
        handled via rollback, and re-raised as FtwPatchError.
        """
        import shutil
        app = FtwPatch(valid_args)
        
        # Setup files
        original = tmp_path / "critical_file.py"
        original.write_text("safe_original_content")
        staged = tmp_path / "staged_changes.tmp"
        staged.write_text("new_buggy_content")
        
        backup_path = Path(str(original) + ".ftwBak")
        shutil.copy2(original, backup_path)
        
        results = [(original, staged)]
        options = Namespace(backup=True)

        # WICHTIG: Patch 'move' direkt in deinem Modul, nicht in shutil!
        mocker.patch("ftw.patch.ftw_patch.move", side_effect=OSError("Disk write protected"))
        
        with pytest.raises(FtwPatchError) as excinfo:
            app._commit_changes(results, options)
        
        # Wir passen den String an deine tatsächliche Fehlermeldung an:
        assert "Critical error during file move" in str(excinfo.value)
        assert "Disk write protected" in str(excinfo.value)
        
        # Verify the rollback
        assert original.read_text() == "safe_original_content"


    def test_create_backups_with_custom_directory(self, valid_args, tmp_path):
        """
        Covers lines 1375-1376: Verifies that a custom backup directory 
        is created and used correctly.
        """
        app = FtwPatch(valid_args)
        
        # Setup: Source file
        original = tmp_path / "source.txt"
        original.write_text("original content")
        
        # Define a non-existent sub-directory for backups
        custom_bak_dir = tmp_path / "sub" / "backups"
        
        # Execution
        backup_paths = app._create_backups(
            [original], 
            extension=".bak", 
            backup_dir=custom_bak_dir
        )
        
        # Assertions
        assert custom_bak_dir.exists()
        expected_path = custom_bak_dir / "source.txt.bak"
        assert expected_path.exists()
        assert expected_path.read_text() == "original content"
        assert backup_paths[0] == expected_path




    def test_commit_changes_cleanup_backups(self, valid_args, tmp_path):
        """
        Covers lines 1423-1427: Default case where backups are deleted.
        """
        app = FtwPatch(valid_args)
        
        # Setup: We need a 'real' file to act as the target for the move
        # and a backup file that should be deleted.
        original = tmp_path / "file.txt"
        original.write_text("current")
        staged = tmp_path / "file.txt.tmp"
        staged.write_text("patched")
        
        # This is the backup file that the cleanup logic will look for
        bak_file = tmp_path / "file.txt.ftwBak"
        bak_file.write_text("backup content")
        
        # The method expects a list of (Path, Path)
        results = [(original, staged)]
        options = Namespace(backup=False) 
        
        # Act
        app._commit_changes(results, options)
        
        # Assert: Cleanup should have removed the backup
        assert not bak_file.exists()

    def test_commit_changes_keep_backups(self, valid_args, tmp_path):
        """
        Covers lines 1423-1429: Ensures backups are preserved if option is True.
        """
        app = FtwPatch(valid_args)
        
        original = tmp_path / "file.txt"
        original.write_text("current")
        staged = tmp_path / "file.txt.tmp"
        staged.write_text("patched")
        
        bak_file = tmp_path / "file.txt.ftwBak"
        bak_file.write_text("backup content")
        
        results = [(original, staged)]
        options = Namespace(backup=True)
        
        app._commit_changes(results, options)
        
        # Assert: Backup must still exist
        assert bak_file.exists()
