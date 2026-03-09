"""
exceptions
===============================

| File: src/fitzzftw/patch/exceptions.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de
| License: LGPLv2 or above

Modul exceptions documentation
"""

from pathlib import Path

# --- Exceptions ---


class FtwPatchError(Exception):  
    """
    Base exception for all errors raised by the :py:mod:`ftw_patch`
    module.

    **Inheritance Hierarchy**
        * :py:class:`FtwPatchError`
        * :py:class:`Exception`
    """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)!r})"


class PatchParseError(FtwPatchError):  
    """
    Exception raised when an error occurs during the parsing of the
    patch file content.

    **Inheritance Hierarchy**
        * :py:class:`PatchParseError`
        * :py:class:`FtwPatchError`
        * :py:class:`Exception`
    """

    def __init__(self, message: str) -> None:
        """
        Initializes the PatchParseError.

        :param message: The error message.
        """
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str(self)!r})"
        # return f"{self.__class__.__name__}(message={self.args[0]!r})"



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
    test_file = testfiles_dir / "get_started_exceptions.rst"
    test_file = testfiles_dir / "get_started_ftw_patch.rst"

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
