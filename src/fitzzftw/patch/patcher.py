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
:class:`~.protocols.ArgParsOptions` protocol and call :meth:`~.FtwPatch.run`.

"""

from datetime import datetime
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
    """
    Collector for patch execution metrics and file operation statistics.

    Tracks modified, created, and deleted files during a patch process and
    aggregates line-level changes (additions/removals). It supports colorized
    terminal output based on the configured verbosity level.

    :cvar _color_map: Mapping of operation types to terminal colors.
    :ivar _verbosity: Controls the detail level of the statistical output.
    :ivar _modified: List of DiffCodeFile objects identifying modified files.
    :ivar _created: List of DiffCodeFile objects identifying new files.
    :ivar _deleted: List of DiffCodeFile objects identifying removed files.
    """
    _color_map={"del":"red", "create":"green", "modified":"yellow"}
    def __init__(self, verbosity:int=0) -> None:
        """
        Initializes the statistics collector.

        :param verbosity: Output detail level. 0 for minimal, 1 for extended info.
        """
        super().__init__()
        self._verbosity = verbosity
        self._start_time:datetime|None=None
        self._modified:list[DiffCodeFile] = []
        self._created: list[DiffCodeFile] = []
        self._deleted: list[DiffCodeFile] = []
        self._lines_added:int = 0
        self._lines_removed:int = 0
    # SECTION - Properties
    @property
    def verbosity(self)->int:
        """
        Returns the current verbosity level.

        :return: Verbosity level.
        """
        return self._verbosity
    @property
    def total_files(self)->int:
        """
        Returns the total number of files affected by the patch.

        :return: Count of all processed files.
        """
        return len(self._created)+len(self._deleted)+len(self._modified)
    @property
    def lines_added(self)->int:
        """
        Returns the cumulative count of lines added across all files.

        :return: Total lines added.
        """
        return self._lines_added
    @property
    def lines_removed(self)->int:
        """
        Returns the cumulative count of lines removed across all files.

        :return: Total lines removed.
        """
        return self._lines_removed
    @property
    def files_modified(self)->int:
        """
        Returns the count of existing files that were changed.

        :return: Count of modified files.
        """
        return len(self._modified)
    @property
    def files_created(self)-> int:
        """
        Returns the count of files newly created by the patch.

        :return: Count of created files.
        """
        return len(self._created)
    @property
    def files_deleted(self)->int:
        """
        Returns the count of files removed by the patch.

        :return: Count of deleted files.
        """
        return len(self._deleted)
    
    @property
    def start_time(self)->datetime|None:
        return self._start_time
    
    @start_time.setter
    def start_time(self, value:datetime) -> None:
        self._start_time= value
    
    #!SECTION

    #METHOD - add_file
    def add_file(self, file:DiffCodeFile)-> None:
        """
        Categorizes a processed file and updates aggregate line counters.

        Analyzes the original and new headers to determine if the file was
        created, deleted, or modified.

        :param file: The processed file object containing diff data.
        :raises FtwPatchError: If the file object lacks a valid new header.
        """
        if file.new_header is None:
            raise FtwPatchError("New Header not found!")
        new_header:HeadLine = cast(HeadLine,file.new_header)
        if file.orig_header.is_null_path and not new_header.is_null_path:
            self._created.append(file)
            status, color, path = "CREATED ", "green", file.get_target_path()
        elif not file.orig_header.is_null_path and new_header.is_null_path:
            self._deleted.append(file)
            status, color, path = "DELETED ", "red", file.get_source_path()
        else:
            self._modified.append(file)
            status, color, path = "MODIFIED", "yellow", file.get_target_path()

        self._lines_added += file.addedlines
        self._lines_removed += file.deletedlines
        if self._verbosity >= 6:
            # Format: STATUS Path (+ins, -del)
            stats = f"(+{file.addedlines}, -{file.deletedlines})"
            self.colorize(f"{status} {path.as_posix()} {stats}", color)

    #!METHOD

    #METHOD - print
    def print(self) -> None:
        """
        Prints a colorized summary of the collected statistics to the terminal.

        Output detail varies by 'verbosity' level:
        - Level 0: Total files processed.
        - Level 1: Total files and sum of added/removed lines.
        """
        match self._verbosity:
            case 1:
                self.colorize((f"Files processed: {self.total_files}\n"
                              f"Lines processed: {self.lines_removed+self.lines_added}")
                              ,"terminal")
            case 2:
                self.colorize(f"Files created:  {self.files_created}", "green")
                self.colorize(f"Files modified: {self.files_modified}", "yellow")
                self.colorize(f"Files deleted:  {self.files_deleted}", "red")
            case 3:
                self.colorize(f"Files created:   {self.files_created}", "green")
                self.colorize(f"Files modified:  {self.files_modified}", "yellow")
                self.colorize(f"Files deleted:   {self.files_deleted}", "red")
                self.colorize(f"Lines processed: {self.lines_removed + self.lines_added}"
                    ,"terminal",)
            case 4:
                if self.files_created:
                    tmp_str = ",\n".join([x.get_target_path().as_posix() for x in self._created])
                    self.colorize(f"Files created:   {tmp_str}", "green")
                if self.files_modified:
                    tmp_str = ",\n".join([x.get_target_path().as_posix() for x in self._modified])
                    self.colorize(f"Files modified:  {tmp_str}", "yellow")
                if self.files_deleted:
                    tmp_str = ",\n".join([x.get_source_path().as_posix() for x in self._deleted])
                    self.colorize(f"Files deleted:   {tmp_str}", "red")
            case 5:
                for df in self._created:
                    self.colorize(f"File created:   {df.get_target_path().as_posix()}", "green")
                    self.colorize(f"\tLines added: {df.addedlines}", "green")
                for df in self._modified:
                    self.colorize(f"File modified:   {df.get_target_path().as_posix()}", "yellow")
                    self.colorize(f"\tLines added: {df.addedlines}", "green")
                    self.colorize(f"\tLines deleted: {df.deletedlines}", "red")
                for df in self._deleted:
                    self.colorize(f"File deleted:   {df.get_source_path().as_posix()}", "red")
                    self.colorize(f"\tLines deleted: {df.deletedlines}", "red")
            case _:
                self.colorize(f"Files processed: {self.total_files}", "terminal")
        
        time_delta = datetime.now() - (self.start_time if self.start_time else datetime.now())
        self.colorize(f"Runtime: {time_delta.total_seconds():.2f} s","terminal")

    #!METHOD
    #METHOD - __repr__
    def __repr__(self) -> str:
        """
        Returns a developer-friendly string representation of the instance.

        :return: String representation.
        """
        return f"{self.__class__.__name__}(verbosity: {self._verbosity})"
    #!METHOD
#!CLASS


# CLASS - FtwPatch
class FtwPatch:
    """
    Main class for the ``ftwpatch`` program.

    Implements the PIMPLE idiom by storing the parsed :class:`python:argparse.Namespace` object
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
        self._patch_files:list|None = None
        self._files2delete:list[Path]=[]
        self._statistics= PatchStatistics(args.verbose)
        # Proactive check for the existence of the patch file
        if not self._args.patch_file.is_file():
            raise FileNotFoundError(f"Patch file not found at {self._args.patch_file!r}")

    def __repr__(self) -> str:
        """
        Return a machine-readable representation of the instance.
        :returns: A string containing the class name and its state.
        """
        # Nutzung von self.__class__.__name__ wie vorgeschrieben
        return (f"{self.__class__.__name__}(backup_ext='{self.backup_ext}', "
                f"backup_path='{self.backup_path.as_posix()}')")

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
    def verbose(self) -> int:
        """Get the verbosity level for console output **(ro)**.
        
        :returns: The verbosity level ranging from 0 to 3.
        """
        return self._args.verbose

    @property
    def backup_ext(self)->str:
        """
        Get the normalized backup file extension **(ro)**.

        This property returns the extension including the dot and the
        optional timestamp if a keyword was used during initialization.

        :returns: The backup extension string.
        """
        return self._args.backup_ext

    @property
    def backup_path(self)->Path:
        """
        Get the base directory for backup files **(ro)**.

        This path is resolved and contains the processed timestamp if
        any keywords were present in the initial configuration.

        :returns: The Path object for the backup directory.
        """
        return self._args.backup_path

    @property
    def start_time(self) -> datetime:
        """
        Get the global reference timestamp for this session **(ro)**.

        This timestamp is fixed at program start to ensure consistency
        between directory names and file extensions.

        :returns: The reference datetime.datetime object.
        """
        return self._args.dt_now

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
        if getattr(self, "_patch_files", None) is None:
            self._parse()
        return self._patch_files  # pyright: ignore[reportReturnType]

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
        self._patch_files=[]
        
        with self._get_patch_stream() as stream:
            for diff_file in parser.iter_files(stream):
                self._statistics.add_file(diff_file)
                self._patch_files.append(diff_file)

            # self._patch_files = list(parser.iter_files(stream))

    def run(self) -> int|None:
        """
        Execute the patching process and handle high-level errors.

        :returns: Exit code (0 for success, 1 or 2 for errors).
        """
        try:
            ret= self.apply(self._args)
            self._statistics.start_time = self.start_time
            self._statistics.print()
            return ret
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
        self, file_paths: list[Path], extension: str = ".ftwBak", backup_dir: Path = Path(".")
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
        base_anchor_len = len(Path.cwd().resolve().parts)
        try:
            for original in file_paths:
                # if backup_dir:
                #     backup_dir.mkdir(parents=True, exist_ok=True)
                #     # bak_path = backup_dir / (original.name + extension)
                #     bak_path = backup_dir / original.with_suffix(original.suffix + extension)
                # else:
                #     bak_path = original.with_suffix(original.suffix + extension)
                if not original.exists():
                    continue
                abs_parts = original.resolve().parts
                rel_parts = abs_parts[base_anchor_len:]
                rel_path_with_ext = Path(*rel_parts).with_suffix(original.suffix + extension)
                bak_path = backup_dir / rel_path_with_ext
                bak_path.parent.mkdir(parents=True, exist_ok=True)
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
            backup_dir=getattr(options, "backup_path", Path().cwd()),
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
    # test_file = testfiles_dir / "debug_patcher.txt"
    
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
