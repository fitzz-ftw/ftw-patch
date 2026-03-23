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
from argparse import ArgumentError, ArgumentParser
from pathlib import Path
from tomllib import TOMLDecodeError
from typing import cast

from fitzzftw.baselib.converter import str2bool
from fitzzftw.patch.base import TerminalColorMixin, color_terminal_check
from fitzzftw.patch.container import DiffCodeFile, Hunk
from fitzzftw.patch.exceptions import FtwPatchError, PatchParseError
from fitzzftw.patch.lines import FileLine, HeadLine, HunkHeadLine, HunkLine, PatchLine
from fitzzftw.patch.parser import PatchParser
from fitzzftw.patch.patcher import FtwPatch
from fitzzftw.patch.protocols import ArgParsOptions, BackupOptions, FtwPatchApplyOptions
from fitzzftw.patch.utils import get_backup_extension, get_merged_config

__all__ = [
    "FileLine",
    "Hunk",
    "HeadLine",
    "HunkHeadLine",
    "HunkLine",
    "PatchLine",
    "TerminalColorMixin",
    "DiffCodeFile",
    "PatchParseError",
    "PatchParser",
    "BackupOptions",
    "FtwPatchApplyOptions",
] 



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
        args:ArgParsOptions = cast(ArgParsOptions, parser.parse_args())


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

#!SECTION

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


