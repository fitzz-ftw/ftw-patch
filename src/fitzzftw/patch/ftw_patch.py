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

import re
import sys
import tempfile
from argparse import ArgumentError, ArgumentParser, Namespace
from pathlib import Path
from shutil import copy2, move
from tempfile import TemporaryDirectory
from tomllib import TOMLDecodeError
from tomllib import load as tomlload
from typing import ClassVar, Generator, Iterable

from platformdirs import user_config_path

from fitzzftw.baselib.converter import str2bool

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


# CLASS - PatchLine
class PatchLine:
    """
    Base class for structural patch lines.

    This class serves as the foundation for all specialized line types within
    a patch (e.g., HeadLine, FileLine). It handles the initial sanitization
    of the raw input stream.
    """

    _TRAIL_WS_RE: ClassVar[re.Pattern] = re.compile(r"([ \t\f\v]+)[\n\r]*$")

    def __init__(self, raw_line: str):
        """
        Initializes a PatchLine instance by sanitizing the input.

        The raw line is stripped of trailing carriage returns and newlines.
        Additionally, it removes the specialized 'No newline at end of file'
        markers that can appear in Unified Diff format to ensure the
        content property contains only the actual text data.

        :param raw_line: The unmodified string read directly from the patch source.
        """
        # Strict type check to ensure the input is a string
        if not isinstance(raw_line, str):
            raise PatchParseError(
                f"PatchLine expected a string, but received {type(raw_line).__name__}."
            )

        # Remove standard 'No newline' markers found in diffs
        # These markers would otherwise interfere with matching/patching logic.
        clean_content = raw_line.removesuffix("\\ No newline at end of file\n").removesuffix(
            "\\ No newline at end of file\r\n"
        )
        self._has_trailing_whitespace: bool = bool(self._TRAIL_WS_RE.search(clean_content))

        # Strip trailing newline characters (\n or \r\n)
        self._content: str = clean_content.rstrip("\n\r")

    @property
    def content(self) -> str:
        """
        The cleaned content of the line without trailing newlines (ro).

        :returns: A string representing the text content of the line.
        """
        return self._content

    @property
    def has_trailing_whitespace(self) -> bool:
        # TODO: Docstring
        return self._has_trailing_whitespace

    def __repr__(self):
        return "".join([self.__class__.__name__, f"(Content: {self.content!r})"])


#!CLASS - PatchLine


# CLASS - HeadLine
class HeadLine(PatchLine):
    """
    Represents a file header line within a patch (starting with '--- ' or '+++ ').

    This class specializes :py:class:`PatchLine` to handle file-level metadata.
    It isolates the file path from the unified diff prefix and provides
    convenience methods to identify the role of the file (original vs. new)
    within a transition.
    """

    def __init__(self, raw_line: str):
        """
        Initializes the HeadLine by extracting the prefix and path content.

        The first four characters are used to identify the header type.
        The remainder of the line is passed to the base class to ensure
        consistent sanitization of the path string.

        :param raw_line: The complete, unmodified header line from the patch.
        """
        prefix_candidate = raw_line[:4]
        if prefix_candidate not in ("--- ", "+++ "):
            raise ValueError(
                f"Invalid HeadLine: Expected '--- ' or '+++ ', got {repr(raw_line[:4])}"
            )

        self._prefix: str = prefix_candidate
        parts = raw_line[4:].split("\t", 1)
        if len(parts) > 1:
            content_candidate = parts[0].rstrip(" ")
            super().__init__(parts[1])
            self._info = self.content
            self._content = content_candidate
        else:
            super().__init__(parts[0])
            self._info = None

    @property
    def prefix(self)->str:
        """
        The diff prefix ('--- ' or '+++ ') identified at the start of the line **(ro)**.

        :returns: The prefix string.
        """
        return self._prefix

    @property
    def is_orig(self)->bool:
        """
        Indicates if this line represents the original (source) file path **(ro)**.

        :returns: True if the prefix is '--- ', False otherwise.
        """
        return self._prefix == "--- "

    @property
    def is_new(self)->bool:
        """
        Indicates if this line represents the new (target) file path **(ro)**.

        :returns: True if the prefix is '+++ ', False otherwise.
        """
        return self._prefix == "+++ "

    @property
    def is_null_path(self)->bool:
        """
        Checks if the file path points to a null device (e.g., /dev/null) **(ro)**.

        This property uses the static method :py:meth:`~HeadLine.check_is_null_path` to perform the 
        null-path check.

        :returns: True if the content matches a null path pattern.
        """
        return self.check_is_null_path(self.content)

    @property
    def info(self) -> str | None:
        """
        Returns the metadata found after the file path (e.g., timestamps) **(ro)**.

        This contains everything that was separated by a tab character
        from the path. Returns an empty string or None if no metadata
        was present.

        :returns: The metadata string or None.
        """

        return self._info

    def get_path(self, strip_count: int) -> Path:
        """
        Returns the path as a Path object, stripped of N leading segments.

        :param strip_count: Number of leading path components to remove.
        :raises ValueError: If strip_count is too high for the available segments or is negative.
        :returns: A Path object of the remaining segments.
        """
        p = Path(self.content)
        segments = p.parts

        if strip_count < 0:
            raise ValueError(f"Strip count must be non-negative, got {strip_count}")

        if strip_count >= len(segments):
            raise ValueError(
                f"Strip level -p{strip_count} is too high for path '{self.content}' "
                f"(only {len(segments)} segments available)."
            )

        return Path(*segments[strip_count:])

    @staticmethod
    def check_is_null_path(path: Path | str) -> bool:
        """Check if the given path represents a null path marker.

        This function detects special paths used in patch files to signify
        file deletion or creation, specifically:
        1. '/dev/null' (POSIX standard, case-sensitive).
        2. 'NUL' (Windows standard, case-insensitive).

        The implementation is hard-coded for maximum performance and stability,
        as these standards are highly unlikely to change.

        :param path: The path object or string to check.
        :returns: :py:obj:`True` if the path matches a known null path
                marker, :py:obj:`False` otherwise.
        """
        if isinstance(path, Path):
            path_str = path.as_posix()
        elif isinstance(path, str):
            path_str = path
        else:
            return False

        # 1. POSIX Check: Must match '/dev/null' exactly (case-sensitive).
        # This ensures correctness on POSIX filesystems.
        if path_str == "/dev/null":
            return True

        # 2. Windows Check: Must match 'NUL' (case-insensitive).
        # This handles patches created on Windows/DOS systems (e.g., 'nul', 'NuL').
        if path_str.upper() == "NUL":
            return True

        return False

    def __repr__(self):
        return "".join(
            [self.__class__.__name__, f"(Content: {self.content!r}, Prefix: {self.prefix!r})"]
        )


#!CLASS - HeadLine
# CLASS -  HunkHead


class HunkHeadLine(PatchLine):
    """
    Represents a hunk header line within a patch (starting with '@@ ').

    This class specializes :py:class:`PatchLine` to handle coordinate metadata.
    It isolates the range information from optional context info (like function names)
    and provides parsed access to the line numbers.
    """

    _HUNK_RE: ClassVar[re.Pattern] = re.compile(
        r"^-(?P<old_start>\d+)(?:,(?P<old_len>\d+))? "
        r"\+(?P<new_start>\d+)(?:,(?P<new_len>\d+))?"
    )

    def __init__(self, raw_line: str):
        """
        Initializes the HunkHeadLine by extracting coordinates and optional info.

        :param raw_line: The complete, unmodified hunk header line.
        :raises ValueError: If the prefix or the coordinates are invalid.
        """
        # Strict type check to ensure the input is a string
        if not isinstance(raw_line, str):
            raise PatchParseError(
                f"PatchLine expected a string, but received {type(raw_line).__name__}."
            )

        if not raw_line.startswith("@@ "):
            raise ValueError(f"Invalid HunkHeadLine: Expected '@@ ', got {repr(raw_line[:3])}")

        self._prefix = "@@ "

        # Split beim schließenden " @@", um Koordinaten von Info zu trennen
        parts = raw_line[3:].split(" @@", 1)
        if len(parts) < 2:
            raise ValueError(f"Invalid HunkHeader: Missing closing ' @@' in {repr(raw_line)}")
        if parts[1].strip():
            # Fall: @@ -l,s +l,s @@ Context-Info
            coord_candidate = parts[0]
            super().__init__(parts[1])
            self._info = self.content
            self._content = coord_candidate
            self._suffix_marker = " @@"
        else:
            # Fall: Nur @@ -l,s +l,s @@
            super().__init__(parts[0])
            self._info = None
            self._suffix_marker = " @@"

        # Koordinaten-Validierung auf dem isolierten Koordinaten-String
        match = self._HUNK_RE.match(self.content)
        if not match:
            raise ValueError(f"Invalid Hunk coordinates: {repr(self.content)}")

        # Integer-Konvertierung
        self._old_start = int(match.group("old_start"))
        self._old_len = int(match.group("old_len")) if match.group("old_len") else 1
        self._new_start = int(match.group("new_start"))
        self._new_len = int(match.group("new_len")) if match.group("new_len") else 1

    @property
    def prefix(self) -> str:
        """The '@@ ' prefix at the start of the line **(ro)**."""
        return self._prefix

    @property
    def info(self) -> str | None:
        """The optional context information after the coordinates **(ro)**."""
        return self._info

    @property
    def old_start(self) -> int:
        """The starting line number in the original file **(ro)**."""
        return self._old_start

    @property
    def old_len(self) -> int:
        """The number of lines affected in the original file **(ro)**."""
        return self._old_len

    @property
    def new_start(self) -> int:
        """The starting line number in the new file **(ro)**."""
        return self._new_start

    @property
    def new_len(self) -> int:
        """The number of lines in the new hunk **(ro)**."""
        return self._new_len

    @property
    def coords(self) -> tuple[int, int, int, int]:
        """All coordinates as a tuple: (old_start, old_len, new_start, new_len) **(ro)**."""
        return self._old_start, self._old_len, self._new_start, self._new_len

    def __repr__(self):
        # info_part = f" | Info: {self._info}" if self._info else ""
        return "".join(
            [
                self.__class__.__name__,
                # f"(Content: {self.prefix}{self.content}{self._suffix_marker}{info_part})"
                f"(Content: {self.content!r}, Prefix: {self.prefix!r})",
            ]
        )


#!CLASS -  HunkHead


# CLASS - FileLine
class FileLine(PatchLine):
    """
    Represents a single line read from a file or contained within a patch hunk.

    The primary responsibility is to handle the line content and its associated
    prefix (if it comes from a patch) consistently, especially by immediately
    stripping the trailing newline character upon initialization.

    The actual content, free of the trailing newline, is exposed via the
    :py:attr:`~FileLine.content` property.
    """

    _INTERNAL_WS_RE: ClassVar[re.Pattern] = re.compile(r"([ \t\f\v]+)")
    _ALL_WS_RE: ClassVar[re.Pattern] = re.compile(r"\s+")
    # _TRAIL_WS_RE: ClassVar[re.Pattern] = re.compile(r"([ \t\f\v]+)[\n\r]*$")

    def __init__(self, raw_line: str):
        """
        Initializes the FileLine instance.

        The raw line content is processed immediately: the trailing newline
        character is removed, and the cleaned content is stored internally.
        This prevents issues where the newline character interferes with
        hunk application logic.

        :param raw_line: The complete, unmodified line string, typically including
                         a trailing newline.
        """
        self._prefix: str = ""
        super().__init__(raw_line)
        self._has_newline = raw_line.endswith("\n")

    def __repr__(self):
        return "".join(
            [
                self.__class__.__name__,
                # f"(Content: {self.prefix}{self.content})",
                f"(Content: {self.content!r}, Prefix: {self.prefix!r})",
            ]
        )

    # --- Content Properties ---

    @property
    def content(self) -> str:
        """
        The raw line content, stripped of the diff prefix and trailing newline **(ro)**.

        This value is used for standard matching when no whitespace flags are set.

        :returns: The cleaned line content as a string.
        """
        return self._content

    @property
    def normalized_ws_content(self) -> str:
        """
        The line content, dynamically normalized according to the --normalize-ws rule **(ro)**.

        Internal whitespace runs collapse to a single space; trailing
        whitespace is removed; leading whitespace is preserved.

        :returns: The normalized string used for matches.
        """
        content = self._content.replace("\xa0", " ")

        # 1. Find the index of the first non-whitespace character and separate
        # Lstrip returns the string without leading whitespace.
        stripped_content = content.lstrip(" \t\f\v")
        first_non_ws_index = len(content) - len(stripped_content)

        # 2. Extract the leading whitespace (must be preserved)
        leading_ws = content[:first_non_ws_index]

        # 3. Apply normalization (collapse) to the REST of the line
        # Only internal whitespace is replaced.
        collapsed_content = self._INTERNAL_WS_RE.sub(" ", stripped_content)

        # 4. Remove trailing whitespace (from the end of collapsed_content)
        final_content = collapsed_content.rstrip(" \t\f\v")

        # 5. Re-append leading whitespace and return
        return leading_ws + final_content

    @property
    def ignore_all_ws_content(self) -> str:
        """
        The line content, dynamically normalized according to the --ignore-all-ws rule **(ro)**.

        All forms of whitespace (leading, internal, trailing) are removed from the string.

        :returns: The string content with all whitespace removed.
        """
        return self._ALL_WS_RE.sub("", self._content)

    # --- Metadata & Convenience Properties ---

    @property
    def prefix(self) -> str:
        """
        The diff prefix character (' ', '+', or '-') **(ro)**.

        :returns: The prefix character.
        """
        return self._prefix

    @property
    def has_trailing_whitespace(self) -> bool:
        """
        Indicates if the original raw line contained trailing whitespace before the newline
        **(ro)**.

        :returns: Boolean value.
        """
        return self._has_trailing_whitespace

    @property
    def is_empty(self) -> bool:
        """
        Checks if the line content is an empty string **(ro)**.

        :returns: True if the line content is empty, False otherwise.
        """
        if self.content:
            return False
        else:
            return True

    @property
    def line_string(self) -> str:
        """
        Get the processed line for filesystem output **(ro)**.

        The returned string includes the original line terminator only if the
        source line had one. This ensures that files without a trailing
        newline (e.g., at the end of the file) are reconstructed identically
        to their original or patched state.

        :returns: The content string, optionally suffixed with a newline.
        """
        return self.content + ("\n" if self.has_newline else "")

    @property
    def has_newline(self) -> bool:
        """
        State of the newline termination at the end of the line (**(rw)**).

        :param value: Set to False if the line lacks a trailing newline.
        :returns: True if the line ends with a newline, False otherwise.
        """
        return self._has_newline

    @has_newline.setter
    def has_newline(self, value: bool) -> None:
        """
        State of the newline termination at the end of the line.

        :param value: Set to False if the line lacks a trailing newline.
        """
        self._has_newline = value


#!CLASS FileLine


# CLASS - HunkLine
class HunkLine(FileLine):
    """
    Represents a single content line within a hunk block of a unified diff.

    The class parses the raw diff line upon instantiation and provides
    dynamically calculated, read-only content properties for different
    levels of whitespace normalization.
    """

    def __init__(self, raw_line: str) -> None:
        """
        Initializes the HunkLine by parsing the raw line.

        The raw line must start with a valid diff prefix (' ', '+', or '-').
        The content is stored without the final newline character.

        :param raw_line: The raw line from the patch file (including prefix).
        :raises PatchParseError: If the prefix is invalid or missing.
        """
        if not raw_line or raw_line[0] not in (" ", "+", "-"):
            raise PatchParseError(
                f"Hunk content line missing valid prefix (' ', '+', '-') or is empty: {raw_line!r}"
            )

        super().__init__(raw_line[1:])
        self._prefix: str = raw_line[0]
        self._has_newline: bool = True  # Default to POSIX standard

    def __repr__(self):
        return "".join(
            [
                self.__class__.__name__,
                # f"(Content: {self.prefix}{self.content})",
                f"(Content: {self.content!r}, Prefix: {self.prefix!r})",
            ]
        )

    # --- Content Properties ---
    @property
    def prefix(self) -> str:
        """
        The diff prefix character (' ', '+', or '-') **(ro)**.

        :returns: The prefix character.
        """
        return self._prefix

    # @property
    # def has_trailing_whitespace(self) -> bool:
    #     """
    #     Indicates if the original raw line contained trailing whitespace before the newline
    #     **(ro)**.

    #     :returns: Boolean value.
    #     """
    #     return self._has_trailing_whitespace

    @property
    def is_context(self) -> bool:
        """Returns True if the line is a context line (' ') **(ro)**.

        :returns: Boolean value.
        """
        return self._prefix == " "

    @property
    def is_addition(self) -> bool:
        """Returns True if the line is an addition line ('+') **(ro)**.

        :returns: Boolean value.
        """
        return self._prefix == "+"

    @property
    def is_deletion(self) -> bool:
        """Returns True if the line is a deletion line ('-') **(ro)**.

        :returns: Boolean value.
        """
        return self._prefix == "-"

    # @property
    # def has_newline(self) -> bool:
    #     """
    #     State of the newline termination at the end of the line (**(rw)**).

    #     :param value: Set to False if the line lacks a trailing newline.
    #     :returns: True if the line ends with a newline, False otherwise.
    #     """
    #     return self._has_newline

    # @has_newline.setter
    # def has_newline(self, value: bool) -> None:
    #     """
    #     State of the newline termination at the end of the line.

    #     :param value: Set to False if the line lacks a trailing newline.
    #     """
    #     self._has_newline = value


#!CLASS HunkLine

# CLASS - Hunks


class Hunk:
    """
    Container for a single change block within a file.

    This class stores the coordinate information from the hunk header and
    the actual content lines. It ensures that only valid HunkHeadLine objects
    are used as headers.
    """

    def __init__(self, header: HunkHeadLine) -> None:
        """
        Initializes a new Hunk with coordinate metadata.

        :param header: The '@@' coordinate header line object.
        :raises TypeError: If header is not a HunkHeadLine instance.
        """
        if not isinstance(header, HunkHeadLine):
            raise TypeError(f"header must be HunkHeadLine, got {type(header).__name__}")

        self._header = header
        self._lines: list[HunkLine] = []

    @property
    def lines(self) -> list[HunkLine]:
        """
        Returns a list of all HunkLine objects within this hunk **(ro)**.

        :returns: A list containing specialized HunkLine objects.
        """
        return self._lines

    @property
    def old_start(self) -> int:
        """
        The starting line number in the original file **(ro)**.

        :returns: The 1-based start line index from the header.
        """
        return self._header.old_start

    @property
    def new_start(self) -> int:
        """
        The starting line number in the new file **(ro)**.

        :returns: The 1-based start line index for the target state.
        """
        return self._header.new_start

    def add_line(self, line: HunkLine) -> None:
        """
        Adds a single content line to the hunk.

        :param line: The HunkLine object to append.
        """
        self.lines.append(line)

    def _compare_context(
        self, expected: list[HunkLine], actual: list[FileLine], options: Namespace
    ) -> bool:
        """
        Compare hunk context against file content using specialized properties.

        This method acts as a dispatcher that selects the appropriate comparison
        property from the FileLine/HunkLine objects based on the provided
        whitespace options.

        :param expected: Lines from the hunk (context or deleted).
        :param actual: Corresponding lines from the actual file.
        :param options: Configuration for whitespace and blankline handling.
        :returns: True if all lines match according to the selected rules.
        """
        if len(expected) != len(actual):
            return False

        for exp, act in zip(expected, actual, strict=False):
            # 1. Option: --ignore-blank-lines
            if getattr(options, "ignore_blank_lines", False):
                if exp.is_empty and act.is_empty:
                    continue

            # 2. Vergleich basierend auf den Whitespace-Regeln
            if getattr(options, "ignore_all_space", False):
                if exp.ignore_all_ws_content != act.ignore_all_ws_content:
                    return False

            elif getattr(options, "ignore_space_change", False):
                if exp.normalized_ws_content != act.normalized_ws_content:
                    return False

            else:
                if exp.content != act.content:
                    return False

        return True

    def apply(self, lines: list[FileLine], options: Namespace) -> list[FileLine]:
        """
        Apply the hunk's changes to a list of FileLine objects.

        This method validates the context of the target lines against the
        expected hunk context. If the validation passes (considering whitespace
        options), it performs the replacement/insertion and returns the new
        state of the lines.

        :param lines: Current file content as a list of FileLine objects.
        :param options: Command line arguments for whitespace and comparison.
        :raises FtwPatchError: If the context check fails or the index is out of bounds.
        :returns: A modified list of FileLine objects.
        """
        # 1. Indizierung vorbereiten (old_start aus dem Unified Diff Header)
        # Wir korrigieren auf 0-basierten Index
        start_idx = self.old_start - 1

        # 2. Erwarteten Kontext extrahieren
        expected_hunk_lines = [lin for lin in self.lines if not lin.is_addition]

        # 3. Validierung der Grenzen
        if start_idx < 0 or (start_idx + len(expected_hunk_lines)) > len(lines):
            raise PatchParseError(
                f"Hunk starting at line {self.old_start} exceeds file bounds. "
                f"File has {len(lines)} lines."
            )

        actual_file_lines = lines[start_idx : start_idx + len(expected_hunk_lines)]

        # 4. Inhalts-Check mit Whitespace-Logik (ruft interne Methode auf)
        if not self._compare_context(expected_hunk_lines, actual_file_lines, options):
            raise PatchParseError(
                f"Hunk mismatch at line {self.old_start}. "
                "The actual file content does not match the hunk's context."
            )

        # 5. Rekonstruktion der Zeilenliste
        new_lines = lines[:start_idx]

        for h_line in self.lines:
            # Kontext behalten, Additions einfügen, Deletions weglassen
            if h_line.is_context or h_line.is_addition:
                new_lines.append(FileLine(h_line.line_string))

        new_lines.extend(lines[start_idx + len(expected_hunk_lines) :])

        return new_lines

    def __getitem__(self, index: int) -> HunkLine:
        """
        Provides access to hunk lines by their position.

        :param index: Zero-based index of the line.
        :returns: The HunkLine object at the given index.
        """
        return self.lines[index]

    def __len__(self) -> int:
        """
        Returns the count of lines in this hunk.

        :returns: The total number of HunkLine objects.
        """
        return len(self.lines)

    def __iter__(self):
        """
        Provides an iterator for the hunk's lines.

        :returns: A list iterator for the internal line collection.
        """
        return iter(self.lines)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(header={self._header.coords}, lines={len(self.lines)})"


#!CLASS - Hunks


# CLASS - DiffCodeFile


class DiffCodeFile:
    """
    Stateful container for a single file's modifications within a patch.

    This class serves as the central assembly point for a file-level patch. It
    ensures that only valid HeadLine objects are used for headers. It manages
    a collection of Hunks and provides indexed and iterative access to them.

    Attributes:
        hunks (list[Hunk]): The collection of change blocks for this file.
    """

    def __init__(self, orig_header: HeadLine) -> None:
        """
        Initializes a new DiffCodeFile with a mandatory original file header.

        :param orig_header: The '---' header line object.
        :raises TypeError: If orig_header is not a HeadLine instance.
        """
        if not isinstance(orig_header, HeadLine):
            raise TypeError(f"orig_header must be HeadLine, got {type(orig_header).__name__}")

        if not orig_header.is_orig:
            msg_info = "".join(
                [
                    f"{orig_header.prefix}",
                    f"{orig_header.content}",
                    f"{orig_header.info if orig_header.info else ''}",
                ]
            )
            raise PatchParseError(
                f"DiffCodeFile must start with an original header (---), got '{msg_info}'"
            )

        self._orig_header = orig_header
        self._new_header: HeadLine | None = None
        self._hunks: list[Hunk] = []

    @property
    def hunks(self) -> list[Hunk]:
        """
        Returns a list of all Hunk objects associated with this file **(ro)**.

        :returns: A list containing specialized Hunk containers.
        """
        return self._hunks

    @property
    def orig_header(self) -> HeadLine:
        """
        The original file header (---) **(ro)**.

        :returns: The HeadLine object representing the source file state.
        """
        return self._orig_header

    @property
    def new_header(self) -> HeadLine | None:
        """
        The new file header (+++) **(rw)**.

        :param value: The HeadLine object to set as the target file state.
        :raises TypeError: If the value is not a HeadLine instance (Setter).
        :returns: The HeadLine object representing the target file state or None.
        """
        return self._new_header

    @new_header.setter
    def new_header(self, value: HeadLine) -> None:
        """
        The new file header (+++) **(rw)**.

        :param value: The HeadLine object to set as the target file state.
        :raises TypeError: If the value is not a HeadLine instance.
        """
        if not isinstance(value, HeadLine):
            raise TypeError(f"new_header must be HeadLine, got {type(value).__name__}")
        self._new_header = value

    def __getitem__(self, index: int) -> "Hunk":
        """
        Enables indexed access to the stored hunks.

        :param index: Zero-based index of the hunk.
        :returns: The Hunk object at the specified position.
        """
        return self.hunks[index]

    def __len__(self) -> int:
        """
        Provides the total count of hunks.

        :returns: The number of hunks in the internal list.
        """
        return len(self.hunks)

    def __iter__(self):
        """
        Returns an independent iterator over the hunks.

        :returns: A list iterator object for the hunk collection.
        """
        return iter(self.hunks)

    def add_hunk(self, hunk: "Hunk") -> None:
        """
        Appends a Hunk to the internal collection.

        :param hunk: The Hunk object to add.
        """
        self.hunks.append(hunk)

    def apply(self, options: Namespace) -> list[FileLine]:
        """
        Apply hunks to the file content and return the resulting lines.

        This method is purely logical and does not perform any write operations.

        :param options: Command line arguments for comparison.
        :returns: A new list of FileLine objects representing the patched state.
        :raises FtwPatchError: If any hunk fails to apply.
        """
        # 1. Datei einlesen (Lesender Zugriff)
        current_lines = self._read_file(self.get_source_path(strip=options.strip_count))

        # 2. Hunks sortieren (wie besprochen: rückwärts)
        sorted_hunks = sorted(self.hunks, key=lambda h: h.old_start, reverse=True)

        # 3. Transformation
        for hunk in sorted_hunks:
            current_lines = hunk.apply(current_lines, options)

        # Wir geben die fertigen Objekte einfach an den Controller zurück
        return current_lines

    def get_source_path(self, strip: int = 0) -> Path:
        """
        Determine the source file path based on the header and strip level.

        :param strip: Number of path components to remove from the start.
        :returns: A Path object for the source file.
        """
        # Wir delegieren die Arbeit an das HeadLine-Objekt
        return Path(self.orig_header.get_path(strip))

    @property
    def _temp_path(self) -> Path:
        """
        Generates a unique path for the staging file **(ro)**.

        The path is located in the system's temporary directory and includes
        the object's ID to avoid collisions during concurrent processing.

        :returns: A Path object for a temporary staging file.
        """
        return Path(tempfile.gettempdir()) / f"ftw_patch_{id(self)}.tmp"

    def _read_file(self, path: Path) -> list[FileLine]:
        """
        Read a file and convert its lines into FileLine objects.

        Uses universal newline support to normalize line endings during
        reading, ensuring the patch logic operates on consistent content.

        :param path: The path to the source file.
        :returns: A list of FileLine instances.
        :raises FtwPatchError: If the file cannot be read.
        """
        try:
            with path.open("r", encoding="utf-8") as f:
                return [FileLine(line) for line in f]
        except (OSError, IOError) as e:
            raise PatchParseError(f"Could not read file {path}: {e}")

    def _write_to_staging(self, lines: list[FileLine]) -> Path:
        """
        Write the patched lines to a temporary file in the staging area.

        Reconstructs the file by writing each FileLine. Python's universal
        newline handling ensures the output matches the system's standard
        line endings.

        :param lines: List of patched FileLine objects.
        :returns: The Path to the generated temporary file.
        :raises FtwPatchError: If writing to the staging area fails.
        """
        temp_file = self._temp_path

        try:
            with temp_file.open("w", encoding="utf-8") as f:
                for line in lines:
                    f.write(line.line_string)
            return temp_file
        except (OSError, IOError) as e:
            raise PatchParseError(f"Could not write to staging file {temp_file}: {e}")

    def __repr__(self) -> str:
        return " ".join(
            [
                f"{self.__class__.__name__}(orig={self._orig_header.content},",
                f"hunks={len(self.hunks)})",
            ]
        )


#!CLASS - DiffCodeFile


# SECTION - --- Parser ---
# CLASS - PatchParser
class PatchParser:
    """
    Handles the parsing of the diff or patch file content.

    This class is responsible for reading the file, handling potential
    encoding issues, and iterating over the hunks and files defined
    in the patch.
    """

    def __init__(self) -> None:
        """
        Initializes the PatchParser instance.

        """
        super().__init__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    @staticmethod
    def create_line(raw_line: str) -> PatchLine:
        """
        Factory method that maps a raw patch line to its specialized class.

        This method analyzes the line prefix to determine the semantic role
        of the line (Header, Hunk, or Data). It is designed to be the
        central entry point for line instantiation to ensure consistent
        parsing and high testability.

        :param raw_line: The complete, unmodified line from the input stream.
        :returns: A specialized instance (HeadLine, HunkHeadLine, or FileLine).
                  Returns a generic PatchLine for unknown metadata or comments.
        """
        # 1. Datei-Header
        if raw_line.startswith(("--- ", "+++ ")):
            return HeadLine(raw_line)

        # 2. Hunk-Header
        elif raw_line.startswith("@@ "):
            return HunkHeadLine(raw_line)

        # 3. Inhaltszeilen
        elif raw_line.startswith(("+", "-", " ")):
            return HunkLine(raw_line)

        # 4. Fallback für alles andere
        else:
            return PatchLine(raw_line)

    @classmethod
    def get_lines(cls, stream: Iterable[str]) -> Generator[PatchLine, None, None]:
        """
        A generator that transforms a stream of raw strings into PatchLine objects.

        :param stream: Any iterable of strings (e.g., file handle, list, or generator).
        :yields: Specialized PatchLine objects.
        """
        for raw_line in stream:
            # Wir strippen hier nur das Newline am Ende,
            # damit PatchLine die internen Leerzeichen behält.
            yield cls.create_line(raw_line)

    def iter_files(self, stream: Iterable[str]) -> Generator[DiffCodeFile, None, None]:
        """
        Iterates over all file-level patches within the provided stream.

        This method acts as a high-speed state machine, assembling objects
        directly from raw strings using an efficient if-elif-else sieve.

        :param stream: An iterable source of raw patch strings.
        :raises FtwPatchError: If the diff sequence is invalid or corrupted.
        :returns: A generator yielding complete DiffCodeFile objects.
        """
        current_file: DiffCodeFile | None = None
        current_hunk: Hunk | None = None
        line_no = 0
        try:
            for line_no, raw_line in enumerate(stream, start=1):
                # --- THE SIEVE (Inline for maximum performance) ---
                # 1. Handle File Headers
                if raw_line.startswith(("--- ", "+++ ")):
                    line = HeadLine(raw_line)
                    if line.is_orig:
                        # Yield the previously assembled file before starting a new one
                        if current_file:
                            yield current_file
                        current_file = DiffCodeFile(line)
                        current_hunk = None
                        continue

                    elif line.is_new:
                        if current_file is None:
                            raise PatchParseError(f"Line {line_no}: Found '+++' before '---'")
                        current_file.new_header = line
                        continue
                    else:
                        pass  # pragma: no cover

                # 2. Handle Hunk Headers
                elif raw_line.startswith("@@ "):
                    if current_file is None:
                        raise PatchParseError(f"Line {line_no}: Found '@@ ' before file headers")

                    current_hunk = Hunk(HunkHeadLine(raw_line))
                    current_file.add_hunk(current_hunk)

                # 3. Handle Valid Content Lines
                elif raw_line.startswith(("+", "-", " ")):
                    if current_hunk is None:
                        raise PatchParseError(
                            f"Line {line_no}: Found content line before '@@' header"
                        )  # noqa: E501

                    current_hunk.add_line(HunkLine(raw_line))

                # 4. Handle Metadata and Noise
                else:
                    # STRICT RULE: No unrecognized lines allowed inside a hunk block
                    if current_hunk is not None:
                        raise PatchParseError(
                            f"Line {line_no}: Invalid line within hunk. Missing prefix (' ', '+', '-')."  # noqa: E501
                        )
                    # Lines outside of hunks (Git metadata, empty lines) are safely ignored
                    continue

            # Yield the final file in the stream
            if current_file:
                yield current_file

        except FtwPatchError:
            # Re-raise known validation errors
            raise
        except Exception as e:
            # Wrap any unexpected low-level errors
            raise PatchParseError(f"Unexpected error at line {line_no}: {str(e)}")


#!CLASS - PatchParser
#!SECTION - Parsers


# SECTION -  --- FtwPatch (Main Application) ---

# Constant for the /dev/null path, which is returned by _clean_patch_path with strip=0.
# This path must be independent of the operating system.
# DEV_NULL_PATH = Path(os.devnull)


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
        return self._patch_files

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

    def run(self) -> int:
        """
        Execute the patching process and handle high-level errors.

        :returns: Exit code (0 for success, 1 or 2 for errors).
        """
        try:
            return self.apply()
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

def get_backup_extension(ext: str) -> str:
    """
    Normalizes the backup extension and handles dynamic keywords.

    Input is cleaned by removing outer whitespace and dots. If a keyword is 
    detected, it is replaced by an ISO 8601 compliant timestamp.

    :param ext: The extension string or keyword ('date', 'time', 'datetime', 'auto', 'timestamp').
    :returns: A normalized string starting with a dot. Keywords result 
              in the format: '.bak_YYYY-MM-DDTHHMMSS'.
    """
    ext = ext.strip().strip(".").strip()
    
    # Aliases for the full ISO 8601 timestamp
    if ext in ('auto', 'date', 'time', 'datetime', 'timestamp'):
        import datetime
        ext = f"bak_{datetime.datetime.now().strftime('%Y-%m-%dT%H%M%S')}"
    
    return f".{ext}"

def get_merged_config(app_name: str = "ftw", manual_user_cfg: str = None) -> dict:
    """
    Merge configuration from hierarchical sources into a single dictionary.
    
    This function implements the configuration layering logic before the 
    Pimple-object (args) is fully initialized. It resolves the 'chicken-and-egg' 
    problem of locating the user configuration file via CLI before parsing 
    the remaining arguments.

    The priority order for settings (highest to lowest):

    1. Project Configuration: Defined in 'pyproject.toml' under [tool.fitzzftw.patch].
       This level ensures project-specific standards (e.g., .gitignore compliance) 
       always override global user preferences.       
    2. Manual User Configuration: A TOML file specified via the '--userconfig' flag.
    3. Platform User Configuration: The default OS-specific path 
       (e.g., ~/.config/ftw/patch.toml on Linux).

    :param app_name: The application namespace used for platformdirs resolution.
    :param manual_user_cfg: Optional filesystem path to a custom TOML config.
    :raises tomllib.TOMLDecodeError: If any encountered TOML file is syntactically invalid.
    :raises OSError: If there are permission issues accessing the configuration files.
    :returns: A dictionary containing the effective configuration defaults.
    """ 
    config = {}
    
    # 1. User level
    if manual_user_cfg:
        user_cfg_file = Path(manual_user_cfg)
    else:
        user_cfg_file = user_config_path(app_name) / "patch.toml"
    
    if user_cfg_file.exists():
        with open(user_cfg_file, "rb") as f:
            config.update(tomlload(f))
            
    # 2. Project level (always wins over user level)
    project_cfg_file = Path("pyproject.toml")
    if project_cfg_file.exists():
        with open(project_cfg_file, "rb") as f:
            data = tomlload(f)
            project_cfg = data.get("tool", {}).get(app_name, {}).get("patch", {})
            config.update(project_cfg)
            
    return config

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
        dry_run = getattr(args, "dry_run", False)

        # The FtwPatch class encapsulates the entire logic
        patcher = FtwPatch(args=args)

        # apply_patch() executes the entire patch logic
        exit_code = patcher.apply_patch(dry_run=dry_run)

        return exit_code

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
    be_verbose = True
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
        print(f"DocTests passed without errors, {test_sum} tests.")
    else:
        print(f"DocTests failed: {test_failed} tests.")
