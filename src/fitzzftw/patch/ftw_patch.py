# Copyright (C) 2025 Fitzz TeXnik Welt <FitzzTeXnikWelt@t-online.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
FTW Patch
===============================

| File: fitzzftw.patch/ftw_patch.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de

Ein Unicode resistenter Ersatz für patch.


"""

import sys
from argparse import ArgumentError, ArgumentParser, Namespace
from pathlib import Path
from shutil import copy2, move
from tempfile import TemporaryDirectory
from tomllib import TOMLDecodeError

from fitzzftw.baselib.converter import str2bool
from fitzzftw.patch.base import ColorMixin, color_terminal_check
from fitzzftw.patch.cli import PatchParser
from fitzzftw.patch.container import DiffCodeFile, Hunk
from fitzzftw.patch.exceptions import FtwPatchError, PatchParseError
from fitzzftw.patch.lines import FileLine, HeadLine, HunkHeadLine, HunkLine, PatchLine
from fitzzftw.patch.utils import get_backup_extension, get_merged_config

### Temporary Functions
# oldprint=print

# def print(*values: object,
#           sep: str | None = " ",
#           end: str | None = "\n",
#           file: str| None = None,
#           flush: bool = False):
#     pass

# def dp(*args):
# oldprint(*args, flush=True)
#     pass

__all__ = [FileLine, Hunk, HeadLine,HunkHeadLine, HunkLine, PatchLine, ColorMixin] # type: ignore





# SECTION -  --- FtwPatch (Main Application) ---


# CLASS - FtwPatch
class FtwPatch:
    """
    Main class for the ``ftwpatch`` program.

    Implements the PIMPLE idiom by storing the parsed argparse.Namespace object
    and providing command-line arguments via read-only properties (getters).
    """

    def __init__(self, args: Namespace) -> None:
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
            return self.apply(Namespace())
        except FtwPatchError as e:
            print(f"\nPatch failed: {e}")
            return 1
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            return 2

    def apply(self, options: Namespace)->None:
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
                    # SCHRITT 1: Logik (nur lesend auf die Originaldatei)
                    patched_lines = code_file.apply(options)

                    # SCHRITT 2: Staging (Schreibend in den Temp-Bereich)
                    # Wir erzeugen einen sicheren Pfad im Temp-Verzeichnis
                    source_path = code_file.get_source_path(options.strip_count) 
                    # name}_{id(code_file)}.tmp
                    tmp_file_name=f"{source_path.name}_{id(code_file)}.tmp"
                    source_tmp_path = source_path.with_name(tmp_file_name)

                    staged_path = staging_dir / source_tmp_path
                    # f"{code_file.get_source_path(options.strip_count).name}_{id(code_file)}.tmp"

                    with staged_path.open("w", encoding="utf-8") as f:
                        for line in patched_lines:
                            f.write(line.line_string)

                    staged_results.append((source_path, staged_path))

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

                copy2(original, bak_path)
                created_backups.append(bak_path)
            return created_backups
        except (OSError, IOError) as e:
            # Rollback: delete partial backups if one fails
            for bak in created_backups:
                bak.unlink(missing_ok=True)
            raise PatchParseError(f"Mandatory backup failed: {e}. Aborting before patch.")

    def _commit_changes(self, results: list[tuple[Path, Path]], options: Namespace) -> bool:
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

        # Phase 3: Conditional cleanup
        # Default behavior: delete backups (backup=False)
        keep_backup = getattr(options, "backup", False)

        if not keep_backup:
            for bak_path in backup_paths:
                bak_path.unlink(missing_ok=True)

        return True


#!CLASS - FtwPatch
#!SECTION - FtwPatch


# SECTION -  --- CLI Entry Point ---


def _get_argparser() -> ArgumentParser:
    """
    Creates the final parser by first pre-parsing meta-arguments to load configs.
    
    This encapsulates the 'chicken-and-egg' problem of loading defaults 
    from a file path that is itself a command line argument.

    :returns: The configured ArgumentParser instance.
    """
    # 1. Pre-parsing phase (Internal)
    pre_parser = ArgumentParser(add_help=False, exit_on_error=False)
    pre_parser.add_argument("--userconfig", dest="user_config_path")
    
    # We don't want the script to crash here if other args are present
    pre_args, _ = pre_parser.parse_known_args()

    # 2. Load Configuration (using our previously defined logic)
    # The priority is already handled inside get_merged_config
    cfg = get_merged_config(manual_user_cfg=pre_args.user_config_path)
    # 3. Final Parser Phase
    parser = ArgumentParser(
        prog="ftwpatch",
        description=("A Unicode-safe patch application tool with "
                     "advanced whitespace normalization. "
                     "Patch utility. Settings are loaded from pyproject.toml [tool.fitzzftw.patch] "
                     "or a user config file. Keys in TOML match CLI flags (e.g., 'backupext')."
                     ),
        epilog=(
            "Note: '--userconfig' cannot be set within a config file itself "
            "as it is required to locate the file."
        ),
        exit_on_error=False,
    )

    parser.add_argument(
        "patch_file",
        type=Path,
        # dest="patch_file",
        help="The path to the unified diff or patch file.",
    )

    # Standard patch options
    parser.add_argument(
        "-p",
        "--strip",
        type=int,
        default=cfg.get("strip", 0),
        dest="strip_count",
        help=(
            "Set the number of leading path components to strip from file names "
            "before trying to find the file. (default: %(default)s)"
        ),
    )

    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        default=Path(cfg.get("directory",".")),
        dest="target_directory",
        help=(
            "Change the working directory to <dir> before starting to look for "
            "files to patch. (default: %(default)s)"
        ),
    )

    # FTW Patch specific normalization options
    parser.add_argument(
        "--normalize-ws",
        type=str2bool,
        nargs='?',
        const=True,
        metavar="BOOLEAN",
        # action="store_true",
        default=cfg.get("normalize-ws", False),
        dest="normalize_whitespace",
        help=(
            "Normalize non-leading whitespace (replace sequences of spaces/tabs "
            "with a single space) in context and patch lines before comparison. "
            "Useful for patches with minor formatting differences. (default: %(default)s)"
        ),
    )

    parser.add_argument(
        "--ignore-bl",
        type=str2bool,
        nargs='?',
        const=True,
        metavar="BOOLEAN",
        # action="store_true",
        default=cfg.get("ignore-bl", False),
        dest="ignore_blank_lines",
        help=(
            "Ignore or treat pure blank lines identically during patch matching. "
            "This implements a skip-ahead logic that collapses sequences of "
            "blank lines in the original file to match the blank lines (or lack "
            "thereof) in the patch context. It effectively ignores differences "
            "in the number of consecutive blank lines. (default: %(default)s)"
        ),
    )

    parser.add_argument(
        "--ignore-all-ws",
        type=str2bool,
        nargs='?',
        const=True,
        metavar="BOOLEAN",
        # action="store_true",
        default=cfg.get("ignore-all-ws", False),
        dest="ignore_all_whitespace",
        help=(
            "Ignore all whitespace (leading, non-leading, and blank lines) "
            "during comparison. This option overrides --normalize-ws and "
            "--ignore-bl. (default: %(default)s)"
        ),
    )

    parser.add_argument(
        "--dry-run",
        type=str2bool,
        nargs='?',
        const=True,
        metavar="BOOLEAN",
        # action="store_true",
        default=cfg.get("dry-run", False),
        dest="dry_run",
        help=("Do not write changes to the file system; only simulate the process. "
              "(default: %(default)s)"),
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        dest="verbose",
        default=cfg.get("verbose",0),
        help="Increase output verbosity. Can be specified multiple times (-vvv) "
        "to increase the level of detail. (default: %(default)s)",
    )
    parser.add_argument(
        "-b", "--backup",
        type=str2bool,
        nargs='?',
        const=True,
        metavar="BOOLEAN",
        # action="store_true",
        default=cfg.get("backup", False),
        dest="backup",
        help=("Create a backup of each file before applying patches. "
            "(default: %(default)s)"
        )
    )

    parser.add_argument(
        "--backupext",
        type=str,
        default=cfg.get("backupext", ".bak"),
        dest="backup_ext",
        help=(
            "The extension for backup files (e.g., '.bak' or 'old'). "
            "A leading dot is added automatically if missing. "
            "Special keywords 'date', 'time', or 'datetime' create a timestamped suffix "
            "in ISO 8601 format (e.g., '.bak_2025-12-30T094200'). (default: %(default)s)"
        )
    
    )
    parser.add_argument("--userconfig",
        type=str,
        default="",
        dest="userconfig",
        help="Path to a custom user TOML config (default: %(default)s)"
        )


    return parser


def prog_ftw_patch() -> int:  
    """
    Main entry point for the command line application.

    This function parses the arguments and starts the patching process.
    It is not intended to be called directly within the module (e.g., from __main__.py
    or __init__.py). Instead, it is invoked by the packaging system (via the
    'ftwpatch' entry point defined in pyproject.toml) when the user executes
    the 'ftwpatch' command in the shell.

    :returns: The system exit code (0 for success, 1 for error).
    """
    # 1. Error handling and execution
    try:
        # 2. Initialize Argument Parser (Assumption: _get_argparser() is defined)
        parser = _get_argparser()

        # 3. Parse arguments
        args = parser.parse_args()


        args.backup_ext = get_backup_extension(args.backup_ext)

        # The 'dry_run' argument must be correctly extracted from args
        # dry_run = getattr(args, "dry_run", False)

        # The FtwPatch class encapsulates the entire logic
        patcher = FtwPatch(args=args)

        # apply_patch() executes the entire patch logic
        # exit_code = patcher.apply_patch(dry_run=dry_run)
        # exit_code = patcher.apply(Namespace(dry_run=dry_run))
        exit_code = patcher.apply(args)
        return exit_code if exit_code is not None else 0

    except (ArgumentError, TOMLDecodeError) as e:
        print(f"Initialization error: {e}", file=sys.stderr)
        return 2

    except FileNotFoundError as e:
        # Error for files not found (patch or target file)
        print(f"File System Error: {e}", file=sys.stderr)
        return 1

    except FtwPatchError as e:
        # Internal application errors (e.g., Parse Error, Hunk Mismatch, Strip Count)
        print(f"An ftw_patch error occurred: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        # Unexpected errors
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1



if __name__ == "__main__":  # pragma: no cover
    from doctest import testfile, FAIL_FAST  # noqa: I001
    from pathlib import Path

    # Adds the project's root directory (the module source directory)
    # to the beginning of sys.path.
    project_root = Path(__file__).resolve().parent.parent
    print(project_root)
    sys.path.insert(0, str(project_root))
    be_verbose = False
    # be_verbose = True
    option_flags = 0
    option_flags = FAIL_FAST
    testfilesbasedir = Path("../../../doc/source/devel")
    test_sum = 0
    test_failed = 0
    dt_file = str(testfilesbasedir / "get_started_ftw_patch.rst")
    # dt_file = str(testfilesbasedir / "temp_test.rst")
    # dt_file = str(testfilesbasedir / "test_parser_fix.rst")
    # dt_file = str(testfilesbasedir / "parser_validation.txt")
    print(dt_file)
    doctestresult = testfile(
        dt_file,
        # "../../doc/source/devel/get_started_ftw_patch.rst",
        optionflags=option_flags,
        verbose=be_verbose,
    )
    test_failed += doctestresult.failed
    test_sum += doctestresult.attempted

    # doctestresult = testfile(
    #     str(testfilesbasedir / "ftw_patch.rst"),
    #     optionflags=option_flags,
    #     verbose=be_verbose,
    # )
    # test_failed += doctestresult.failed
    # test_sum += doctestresult.failed

    if test_failed == 0:
        print(f"\nDocTests passed without errors, {test_sum} tests.")
    else:
        print(f"\nDocTests failed: {test_failed} tests.")

    color_terminal_check()


