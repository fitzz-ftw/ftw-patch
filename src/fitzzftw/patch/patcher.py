# File: src/fitzzftw/patch/patcher.py
# Author: Fitzz TeXnik Welt
# Email: FitzzTeXnikWelt@t-online.de
# License: LGPLv2 or above
"""
Patch Application Engine
========================

This module implements the core orchestration logic for applying patches.
The central class :class:`.FtwPatch` manages the transition from
parsed diff data to actual filesystem modifications.

Core Functionality:
-------------------

* **Staging**:
    Changes are first applied to temporary files to ensure atomicity.

* **Backup Management**:
    Handles mandatory file backups before any write operations occur

* **Transaction Safety**:
    Implements an 'all-or-nothing' commit strategy for multi-file patches.

Usage:
------

Initialize with an options object satisfying the
:class:`~.protocols.ArgParsOptions` protocol and call :meth:`~.FtwPatch.apply`.

"""

from pathlib import Path
from shutil import copy2, move
from tempfile import TemporaryDirectory
from typing import cast

from fitzzftw.patch.base import TerminalColorMixin
from fitzzftw.patch.container import DiffCodeFile
from fitzzftw.patch.exceptions import FtwPatchError, PatchParseError
from fitzzftw.patch.lines import HeadLine
from fitzzftw.patch.parser import PatchParser
from fitzzftw.patch.protocols import ArgParsOptions, BackupOptions, FtwPatchApplyOptions


# CLASS - PatchStatistics
class PatchStatistics(TerminalColorMixin):
    _color_map={"del":"red", "create":"green", "modified":"yellow"}
    def __init__(self, verbosity:int=0) -> None:
        super().__init__()
        self._verbosity = verbosity
        self._modified:list[DiffCodeFile] = []
        self._created: list[DiffCodeFile] = []
        self._deleted: list[DiffCodeFile] = []
        self._lines_added:int = 0
        self._lines_removed:int = 0
    # SECTION - Properties
    @property
    def verbosity(self)->int:
        return self._verbosity
    @property
    def total_files(self)->int:
        return len(self._created)+len(self._deleted)+len(self._modified)
    @property
    def lines_added(self)->int:
        return self._lines_added
    @property
    def lines_removed(self)->int:
        return self._lines_removed
    @property
    def files_modified(self)->int:
        return len(self._modified)
    @property
    def files_created(self)-> int:
        return len(self._created)
    @property
    def files_deleted(self)->int:
        return len(self._deleted)
    #!SECTION

    #METHOD - add_file
    def add_file(self, file:DiffCodeFile)-> None:
        if file.new_header is None:
            raise FtwPatchError("New Header not found!")
        new_header:HeadLine = cast(HeadLine,file.new_header)
        if file.orig_header.is_null_path and not new_header.is_null_path:
            self._created.append(file)
        elif not file.orig_header.is_null_path and new_header.is_null_path:
            self._deleted.append(file)
        else:
            self._modified.append(file)

        self._lines_added += file.addedlines
        self._lines_removed += file.deletedlines

    #!METHOD

    #METHOD - print
    def print(self):
        match self._verbosity:
            case 1:
                self.colorize((f"Files processed: {self.total_files}\n"
                              f"Lines processed: {self.lines_removed+self.lines_added}")
                              ,"terminal")
            case _:
                self.colorize(f"Files processed: {self.total_files}", "terminal")
    #!METHOD
    #METHOD - __repr__
    def __repr__(self):
        return f"{self.__class__.__name__}(verbosity: {self._verbosity})"
    #!METHOD
#!CLASS


# CLASS - FtwPatch
class FtwPatch:
    """
    Main class for the ``ftwpatch`` program.

    Implements the PIMPLE idiom by storing the parsed argparse.Namespace object
    and providing command-line arguments via read-only properties (getters).
    """

    def __init__(self, args: ArgParsOptions) -> None:
        """
        Initializes the FtwPatch instance by storing the parsed command-line
        arguments.

        :param args: The argparse.Namespace object containing command-line arguments.
                     Expected attributes: patch_file, strip_count, target_directory,
                     normalize_whitespace, ignore_blank_lines, ignore_all_whitespace.
        :raises FileNotFoundError: If the patch file does not exist.
        :raises FtwPatchError: If any internal error occurs during setup.
        """
        self._args = args
        self._patch_files = None
        self._files2delete:list[Path]=[]
        # Proactive check for the existence of the patch file
        if not self._args.patch_file.is_file():
            raise FileNotFoundError(f"Patch file not found at {self._args.patch_file!r}")

    def __repr__(self) -> str:
        """
        Return a formal string representation of the FtwPatch instance.

        :returns: String containing the class name and the associated patch file path.
        """
        # self.__class__.__name__ erfüllt die Anforderung für Vererbung
        return f"{self.__class__.__name__}(patch_file={self._args.patch_file!r})"

    #SECTION - Properties
    @property
    def patch_file_path(self) -> Path:
        """
        The path to the patch or diff file **(ro)**.

        :returns: The path object for the patch file.
        """
        return self._args.patch_file

    @property
    def strip_count(self) -> int:
        """
        The number of leading path components to strip from file names **(ro)**.

        :returns: The strip count value.
        """
        return self._args.strip_count

    @property
    def target_directory(self) -> Path:
        """
        The directory containing the files to be patched **(ro)**.

        :returns: The target directory path.
        """
        return self._args.target_directory

    @property
    def normalize_whitespace(self) -> bool:
        """
        Indicates if non-leading whitespace should be normalized **(ro)**.

        :returns: The normalization status.
        """
        return self._args.normalize_whitespace

    @property
    def ignore_blank_lines(self) -> bool:
        """
        Indicates if pure blank lines should be ignored or normalized **(ro)**.

        :returns: The ignore status.
        """
        return self._args.ignore_blank_lines

    @property
    def ignore_all_whitespace(self) -> bool:
        """
        Indicates if all whitespace differences should be completely ignored **(ro)**.

        :returns: The ignore status.
        """
        return self._args.ignore_all_whitespace

    @property
    def dry_run(self) -> bool:
        """
        Indicates whether the patch should only be simulated without writing
        to the file system **(ro)**.

        :returns: The dry run status.
        """
        return self._args.dry_run

    @property
    def parsed_files(self) -> list[DiffCodeFile]:
        """
        Return the list of code files extracted from the patch **(ro)**.

        :raises PatchParseError: If the patch format is invalid **(Indirect)**.
        :raises FileNotFoundError: If the patch file does not exist **(Indirect)**.
        :raises PermissionError: If the patch file cannot be accessed **(Indirect)**.
        :raises OSError: If file access fails during parsing **(Indirect)**.
        :returns: List of DiffCodeFile objects.
        """
        if getattr(self, '_patch_files', None) is None:
            self._parse()
        return self._patch_files # pyright: ignore[reportReturnType]

    @property
    def verbose(self) -> int:
        """Get the verbosity level for console output **(ro)**.
        
        :returns: The verbosity level ranging from 0 to 3.
        """
        return self._args.verbose
    #!SECTION Properties

    def _get_patch_stream(self):
        """
        Open the patch file and return a stream.
        
        :raises FileNotFoundError: If the patch file does not exist **(Indirect)**.
        :raises OSError: If the file cannot be opened **(Indirect)**.
        :returns: A file stream object.
        """
        # self._args.patch_file ist ein Path-Objekt aus argparse
        return self._args.patch_file.open("r", encoding="utf-8")

    def _parse(self) -> None:
        """
        Initialize the parser and load patch data.

        :raises PatchParseError: If the patch format is invalid **(Indirect)**.
        :raises FileNotFoundError: If the patch file does not exist **(Indirect)**.
        :raises PermissionError: If the patch file cannot be accessed **(Indirect)**.
        :raises OSError: If an I/O error occurs during reading **(Indirect)**.
        """
        parser = PatchParser() 
        
        with self._get_patch_stream() as stream:
            self._patch_files = list(parser.iter_files(stream))

    def run(self) -> int|None:
        """
        Execute the patching process and handle high-level errors.

        :returns: Exit code (0 for success, 1 or 2 for errors).
        """
        try:
            return self.apply(self._args)
        except FtwPatchError as e:
            print(f"\nPatch failed: {e}")
            return 1
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            return 2

    def apply(self, options: FtwPatchApplyOptions)->None:
        """
        Orchestrate the staging of changes by applying hunks to temporary files.

        Orchestrates the patching process:
        1. Calculate changes (Logical)
        2. Stage changes (IO - Temporary)
        3. Commit changes (IO - Final)

        :param options: Command line options for patch application.
        :raises PatchParseError: If the patch content is invalid **(Indirect)**.
        :raises OSError: If reading or writing files fails **(Indirect)**.
        """
        staged_results: list[tuple[Path, Path]] = []

        with TemporaryDirectory(prefix="ftw_patch_") as tmp_dir:
            staging_dir = Path(tmp_dir)

            try:
                for code_file in self.parsed_files:
                    # if code_file.new_header and code_file.new_header.is_null_path:
                        # print(f"{code_file.get_source_path(options.strip_count)=}", flush=True)
                        # print(f"{code_file.get_target_path(options.strip_count)=}", flush=True)
                        # print(f"{code_file.new_header.is_null_path=}", flush=True)
                        # continue
                        # ...
                    # SCHRITT 1: Logik (nur lesend auf die Originaldatei)
                    patched_lines = code_file.apply(options)

                    # SCHRITT 2: Staging (Schreibend in den Temp-Bereich)
                    # Wir erzeugen einen sicheren Pfad im Temp-Verzeichnis
                    if code_file.new_header and code_file.new_header.is_null_path:
                        target_path = code_file.get_source_path(options.strip_count)
                        self._files2delete.append(target_path)
                    else:
                        target_path = code_file.get_target_path(options.strip_count) 
                    # name}_{id(code_file)}.tmp
                    tmp_file_name=f"{target_path.name}_{id(code_file)}.tmp"
                    target_tmp_path = target_path.with_name(tmp_file_name)

                    staged_path = staging_dir / target_tmp_path
                    # f"{code_file.get_source_path(options.strip_count).name}_{id(code_file)}.tmp"

                    with staged_path.open("w", encoding="utf-8") as f:
                        for line in patched_lines:
                            f.write(line.line_string)

                    staged_results.append((target_path, staged_path))

                # SCHRITT 3: All-or-Nothing Commit
                if self.dry_run:
                    return 
                self._commit_changes(staged_results, options)

            except FtwPatchError:
                # Fehler passiert? Der Temp-Ordner wird durch 'with' automatisch gelöscht.
                raise

    def _create_backups(
        self, file_paths: list[Path], extension: str = ".ftwBak", backup_dir: Path | None = None
    ) -> list[Path]:
        """
        Create mandatory backups of all files before any modification.

        :param file_paths: List of original file paths.
        :param extension: Extension for the backup files.
        :param backup_dir: Optional directory to store backups.
        :returns: List of created backup file paths.
        :raises FtwPatchError: If a backup fails, removes all previously created backups.
        """
        created_backups = []
        try:
            for original in file_paths:
                if backup_dir:
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    bak_path = backup_dir / (original.name + extension)
                else:
                    bak_path = original.with_suffix(original.suffix + extension)
                if not original.exists():
                    continue
                copy2(original, bak_path)
                created_backups.append(bak_path)
            return created_backups
        except (OSError, IOError) as e:
            # Rollback: delete partial backups if one fails
            for bak in created_backups:
                bak.unlink(missing_ok=True)
            raise PatchParseError(f"Mandatory backup failed: {e}. Aborting before patch.")

    def _commit_changes(self, results: list[tuple[Path, Path]], options: BackupOptions) -> bool:
        """
        Move patched files to their final destination and clean up.

        :param results: List of tuples containing (original_path, staged_path).
        :param options: Command line arguments to check for backup retention.
        :raises OSError: If moving a file fails (Setter).
        :raises FtwPatchError: If the transaction fails and rollback is triggered.
        :returns: True if all files were moved successfully, False otherwise.
        """
        originals = [r[0] for r in results]

        # Phase 1: Create backups (always required)
        backup_paths = self._create_backups(
            originals,
            extension=getattr(options, "backup_ext", ".ftwBak"),
            backup_dir=getattr(options, "backup_dir", None),
        )

        # Phase 2: Overwrite original files
        try:
            for original, patched in results:
                move(str(patched), str(original))
        except (OSError, IOError) as e:
            # If move fails, backups are kept for safety
            raise PatchParseError(
                f"Critical error during file move: {e}. Backups have been preserved for recovery."
            )

        for file_ in self._files2delete:
            file_.unlink()
        # Phase 3: Conditional cleanup
        # Default behavior: delete backups (backup=False)
        keep_backup = getattr(options, "backup", False)

        if not keep_backup:
            for bak_path in backup_paths:
                bak_path.unlink(missing_ok=True)

        return True
#!CLASS - FtwPatch



if __name__ == "__main__": # pragma: no cover
    from doctest import FAIL_FAST, testfile
    
    be_verbose = False
    be_verbose = True
    option_flags = 0
    option_flags = FAIL_FAST
    test_sum = 0
    test_failed = 0
    
    # Pfad zu den dokumentierenden Tests
    testfiles_dir = Path(__file__).parents[3] / "doc/source/devel"
    test_file = testfiles_dir / "get_started_patcher.rst"
    # test_file = testfiles_dir / "debug_patcher.rst"
    
    if test_file.exists():
        print(f"--- Running Doctest for {test_file.name} ---")
        doctestresult = testfile(
            str(test_file),
            module_relative=False,
            verbose=be_verbose,
            optionflags=option_flags,
        )
        test_failed += doctestresult.failed
        test_sum += doctestresult.attempted
        if test_failed == 0:
            print(f"\nDocTests passed without errors, {test_sum} tests.")
        else:
            print(f"\nDocTests failed: {test_failed} tests.")
    else:
        print(f"⚠️ Warning: Test file {test_file.name} not found.")
