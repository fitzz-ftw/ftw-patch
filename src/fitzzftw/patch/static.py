"""
static
===============================

| File: src/fitzzftw/patch/static.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de
| License: LGPLv2 or above

Static shared resources for the ftw-patch project.

This module provides global access to color management via a pre-instantiated
singleton-like object.
"""

from ast import mod
from pathlib import Path
from typing import Literal, TypeAlias, TypeVar, get_args

_T = TypeVar("_T")

ColorModes: TypeAlias = Literal["NORMAL", "PLAIN", "TEST"]

class _Color:
    """
    Internal class for color and style management in terminal output.

    Controls whether ANSI escape sequences, plain text, or semantic tags
    (test mode) are returned. This class should not be instantiated directly;
    use the provided 'colors' instance instead.
    """

    _VALID_MODES:tuple[ColorModes] = get_args(ColorModes)

    def __init__(self):
        """
        Initializes the color manager with default mode 'NORMAL'.
        """
        self._mode: ColorModes = "NORMAL"
        self._codes = {
            "RED": ("\033[31m", "red>"),
            "GREEN": ("\033[32m", "grn>"),
            "YELLOW": ("\033[33m", "ylw>"),
            "CYAN": ("\033[36m", "cyn>"),
            "RESET": ("\033[0m", "<reset"),
            "BOLD": ("\033[1m", "bold."),
        }

    @property
    def mode(self) -> ColorModes:
        """
        Get or set the current output mode.

        :returns: The current mode ('NORMAL', 'PLAIN', or 'TEST').
        :raises ValueError: If the assigned mode is not in allowed.
        """
        return self._mode

    @mode.setter
    def mode(self, value: ColorModes) -> None:
        """
        Set the current output mode.

        :param value: The mode ('NORMAL', 'PLAIN', or 'TEST').
        :raises ValueError: If the assigned mode is not allowed.
        """
        normalized = value.upper()
        if normalized not in self._VALID_MODES:
            raise ValueError(f"Invalid mode '{value}'. Must be one of {self._VALID_MODES}")
        self._mode = normalized

    @property
    def defined_colors(self):
        return [c.lower() for c in self._codes if c not in ["RESET", "BOLD"]]

    def switch_to_testmode(self, enabled: bool = True):
        """
        Convenience method to toggle between TEST and NORMAL mode.

        :param enabled: If True, sets mode to 'TEST', otherwise to 'NORMAL'.
        """
        self.mode = "TEST" if enabled else "NORMAL"

    def _get_value(self, name: str) -> str:
        """
        Returns the appropriate string representation for a style name
        based on the current mode.

        :param name: The name of the color or style.
        :returns: ANSI code, test marker, or empty string.
        """
        if self._mode == "PLAIN":
            return ""

        color, test = self._codes.get(name, ("",""))
        return test if self._mode == "TEST" else color

    @property
    def RED(self) -> str:
        """
        The ANSI sequence or marker for red.

        :returns: Red style string.
        """
        return self._get_value("RED")

    @property
    def GREEN(self) -> str:
        """
        The ANSI sequence or marker for green.

        :returns: Green style string.
        """
        return self._get_value("GREEN")

    @property
    def YELLOW(self) -> str:
        """The ANSI sequence or marker for dark yellow."""
        return self._get_value("YELLOW")

    @property
    def CYAN(self) -> str:
        """
        The ANSI sequence or marker for cyan.

        :returns: Cyan style string.
        :rtype: str
        """
        return self._get_value("CYAN")

    @property
    def RESET(self) -> str:
        """
        The ANSI sequence or marker to reset styling.

        :returns: Reset style string.
        :rtype: str
        """
        return self._get_value("RESET")

    @property
    def BOLD(self) -> str:
        """
        The ANSI sequence or marker for bold text.

        :returns: Bold style string.
        """
        return self._get_value("BOLD")

    def __getitem__(self, key: str) -> str:
        """
        Enables dictionary-like access for style names.

        :param key: Style name (e.g., 'red', 'bold').
        :returns: The corresponding ANSI code, marker, or empty string.
        """
        return self._get_value(key.upper())
    
    def get(self, color:str, default:_T=None) -> _T|str:
        """
        Get a color value by key with a fallback default.

        :param key: The name of the color (e.g., 'red').
        :param default: The value to return if the key is not found.
        :returns: The color string or the default value.
        """
        if self._mode == "PLAIN":
            return ""
        return self._get_value(color.upper())
        


Color: TypeAlias = _Color
"""Type alias for the color provider class."""




ColorKey: TypeAlias = Literal["red", "green", "yellow", "cyan"]


colors:Color = _Color()
"""Global instance for project-wide use."""




if __debug__: #pragma: no cover
    def _check_colors() -> None:
        actual_keys = set(_Color().defined_colors)
        literal_keys = set(get_args(ColorKey))

        if actual_keys != literal_keys:
            missing = actual_keys - literal_keys
            extra = literal_keys - actual_keys

            error_msg = ["Update ColorKey-Literal:"]
            if missing:
                error_msg.append(f"  - Missing in Literal: {missing}")
            if extra:
                error_msg.append(f"  - Extra in Literal (obsolete): {extra}")

            print("\n".join(error_msg))
    _check_colors()


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
    test_file = testfiles_dir / "get_started_static.rst"
    
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
