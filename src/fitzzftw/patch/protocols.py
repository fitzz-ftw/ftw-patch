"""
protocolls
===============================

| File: src/fitzzftw/patch/protocolls.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de
| License: LGPLv2 or above

Protocolls used by ftwpatch.
"""

from pathlib import Path
from typing import (
    Protocol,
    runtime_checkable,
)

from fitzzftw.patch.static import ColorKey

# SECTION - Typehints only Protocols


class HunkCompareOptions(Protocol):
    ignore_blank_lines: bool
    ignore_all_space: bool
    ignore_space_change: bool

class DiffCodeOptions(HunkCompareOptions,Protocol):
    strip_count: int
    

# !SECTION 

# SECTION - Type Protocols runtime_checkable
# Can be used in isinstace()

@runtime_checkable
class LineLike(Protocol):
    """Protocol defining the minimal interface for a line object."""

    _color_map: dict[str, ColorKey]
    """Map from prefix to color"""
    prefix: str|None
    """Used as index for the _color_map"""
    orig_line: str
    """Text to be colored."""


#!SECTION



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
    test_file = testfiles_dir / "get_started_protocolls.rst"
    
    if test_file.exists():
        print(f"--- Running Doctest for {test_file.name} ---")
        doctestresult = testfile(
            str(test_file),
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
