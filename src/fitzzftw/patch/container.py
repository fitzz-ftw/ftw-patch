"""
container
===============================

| File: src/fitzzftw/patch/container.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de
| License: LGPLv2 or above

Modul container documentation
"""

import tempfile
from argparse import Namespace
from pathlib import Path

from fitzzftw.patch.exceptions import PatchParseError
from fitzzftw.patch.lines import FileLine, HeadLine, HunkHeadLine, HunkLine

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

# Hier den Code einfügen

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
    test_file = testfiles_dir / "get_started_container.rst"
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
