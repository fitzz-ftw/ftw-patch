"""
base
===============================

| File: src/fitzzftw/patch/base.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de
| License: LGPLv2 or above

Modul base documentation
"""

from pathlib import Path
from typing import ClassVar

from fitzzftw.patch.static import Color, ColorKey, colors

#SECTION - MixinClasses

#CLASS - ColorMixin
class ColorMixin:
    """
    Provides colorization capabilities for CLI output.

    The mixin provides a :meth:`~ColorMixin.colorize` method to encapsulate strings with ANSI
    color codes and bold styling.
    """

    # ANSI Terminal Codes
    _ANSI:Color = colors
    """Internal mapping of semantic names to ANSI escape sequences. 
    Can be overridden for testing purposes. 
    """

    use_colors: ClassVar[bool] = True
    """Global toggle to enable or disable colorized output. 
    Defaults to True; should be set explicitly based on CLI flags.
    """

    def colorize(self, text: str, color_key: ColorKey ,#Literal["red","green","cyan","yellow"], 
                 bold:bool=False) -> str:
        """
        Colorizes the text using ANSI escape sequences.

        :param text: The string to colorize.
        :param color_key: The color to use ('red', 'green', 'cyan').
        :param bold: Whether to make the output bold.
        :returns: Colorized string or plain text if colors are disabled.
        """
        if not self.use_colors:
            return text

        prefix = self._ANSI.get("bold", "\033[1m") if bold else ""
        prefix += self._ANSI.get(color_key, "")
        suffix = self._ANSI.get("reset", "\033[0m")

        return f"{prefix}{text}{suffix}"

#!CLASS

#!SECTION
def color_terminal_check() -> None:
    """
    Performs a visual diagnostic of ANSI color support in the current terminal.

    This function prints a structured test pattern showcasing 'green', 'red',
    and 'cyan' in both standard and bold variations. It then repeats the
    pattern with colors disabled to verify the fallback mechanism.

    **Usage via CLI:**

    .. code-block:: bash

        $ ftw-terminal-color

    **Visual Output:**
    - A header 'Visual Terminal Color Check' centered in a 39-character block.
    - An 'Enabled' row showing colorized and bold tags.
    - A 'Disabled' row showing plain text tags.
    """
    row_length=49
    print("=" * row_length)
    print(" Visual Terminal Color Check ".center(row_length, "="))
    colmix = ColorMixin()

    # Testreihe 1: Colors ON
    print("Enabled :", end=" ")
    print(colmix.colorize("GRN", "green"), end="|")
    print(colmix.colorize("GRN-B", "green", True), end="|")
    print(colmix.colorize("RED", "red"), end="|")
    print(colmix.colorize("RED-B", "red", True), end="|")
    print(colmix.colorize("CYN", "cyan"), end="|")
    print(colmix.colorize("CYN-B", "cyan", True), end="|")
    print(colmix.colorize("YLW", "yellow"), end="|")
    print(colmix.colorize("YLW-B", "yellow", True))

    # Testreihe 2: Colors OFF
    colmix.use_colors = False  # pyright: ignore[reportAttributeAccessIssue]
    print("Disabled:", end=" ")
    print(colmix.colorize("GRN", "green"), end="|")
    print(colmix.colorize("GRN-B", "green", True), end="|")
    print(colmix.colorize("RED", "red"), end="|")
    print(colmix.colorize("RED-B", "red", True), end="|")
    print(colmix.colorize("CYN", "cyan"), end="|")
    print(colmix.colorize("CYN-B", "cyan", True), end="|")
    print(colmix.colorize("YLW", "yellow"), end="|")
    print(colmix.colorize("YLW-B", "yellow", True))
    print("=" * row_length)



if __name__ == "__main__": # pragma: no cover
    from doctest import FAIL_FAST, testfile
    
    be_verbose = False
    # be_verbose = True
    option_flags = 0
    option_flags = FAIL_FAST
    test_sum = 0
    test_failed = 0
    
    # Pfad zu den dokumentierenden Tests
    testfiles_dir = Path(__file__).parents[3] / "doc/source/devel"
    test_file = testfiles_dir / "get_started_base.rst"
    # test_file = testfiles_dir / "get_started_ftw_patch.rst"

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
