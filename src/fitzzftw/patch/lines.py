"""
lines
===============================

| File: src/fitzzftw/patch/lines.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de
| License: LGPLv2 or above

Modul lines documentation
"""

import re
from pathlib import Path
from typing import ClassVar

from fitzzftw.patch.exceptions import PatchParseError


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

# Hier den Code einfügen

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
    test_file = testfiles_dir / "get_started_lines.rst"
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
