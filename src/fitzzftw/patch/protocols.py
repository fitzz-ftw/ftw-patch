# File: src/fitzzftw/patch/protocols.py
# Author: Fitzz TeXnik Welt
# Email: FitzzTeXnikWelt@t-online.de
# License: LGPLv2 or above

"""
Structural Protocols and Type Hints
===================================

This module defines the structural interfaces (Protocols) used for static
type checking and runtime validation throughout the fitzzftw framework.

Core Protocols:
---------------
* **LineLike**:
    The primary protocol for terminal output. It ensures that an object
    provides the necessary metadata for semantic coloring.
* **ArgParsOptions & Friends**:
    A hierarchy of protocols that define the expected structure for
    configuration objects, ranging from whitespace rules to backup settings.

Key Features:
-------------
* **Runtime Validation**:
    Utilizes :py:func:`@runtime_checkable <typing.runtime_checkable>` for 
    protocols like :class:`LineLike`
    to enable safe :func:`~python:isinstance()` checks in mixins.
* **Granular Configuration**:
    Splits application options into logical units (e.g., :class:`BackupOptions`,
    :class:`WhitespaceOptions`) to allow for flexible dependency injection.
"""

from pathlib import Path
from typing import (
    Protocol,
    runtime_checkable,
)

from fitzzftw.patch.static import ColorKey

# SECTION - Typehints only Protocols


class HunkCompareOptions(Protocol):
    """Interface for options governing how hunks are compared during matching."""

    ignore_blank_lines: bool
    ignore_all_space: bool
    ignore_space_change: bool


class DiffCodeOptions(HunkCompareOptions, Protocol):
    """Extension of comparison options to include file-level strip counts."""

    strip_count: int


class BackupOptions(Protocol):
    """Interface for file backup configuration."""

    backup: bool
    backup_ext: str


class FtwPatchApplyOptions(DiffCodeOptions, BackupOptions):
    """Combined protocol for the core patch application logic."""

    ...


class CommonOptions(Protocol):
    """Global framework options for logging and execution mode."""

    verbose: int
    dry_run: bool


class WhitespaceOptions(Protocol):
    """Specialized options for whitespace normalization rules."""

    normalize_whitespace: bool
    ignore_all_whitespace: bool


class ArgParsOptions(
    FtwPatchApplyOptions,
    WhitespaceOptions,
    CommonOptions,
):
    """
    Comprehensive protocol representing all CLI-provided arguments.

    This acts as the master interface for the main application controller.
    """

    patch_file: Path
    target_directory: Path


# !SECTION

# SECTION - Type Protocols runtime_checkable
# Can be used in isinstace()


@runtime_checkable
class LineLike(Protocol):
    """
    Protocol defining the minimal interface for a line object to be printable.

    Objects implementing this protocol are compatible with the
    :meth:`.TerminalColorMixin.print` and can be processed by
    the framework's diagnostic output tools.
    """
    _color_map: dict[str, ColorKey]
    """Dictionary mapping prefixes to semantic color keys."""
    prefix: str | None
    """
    The lookup key for the :attr:`._color_map`.
    """
    orig_line: str
    """The actual string content that will be output to the terminal."""


#!SECTION


if __name__ == "__main__":  # pragma: no cover
    from doctest import FAIL_FAST, testfile

    be_verbose = False
    be_verbose = True
    option_flags = 0
    option_flags = FAIL_FAST
    test_sum = 0
    test_failed = 0

    # Pfad zu den dokumentierenden Tests
    testfiles_dir = Path(__file__).parents[3] / "doc/source/devel"
    test_file = testfiles_dir / "get_started_protocols.rst"

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
