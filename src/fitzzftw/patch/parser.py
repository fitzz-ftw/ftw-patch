"""
cli
===============================

| File: src/fitzzftw/patch/cli.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de
| License: LGPLv2 or above

Modul cli documentation
"""

from pathlib import Path
from typing import Generator, Iterable

from fitzzftw.patch.container import DiffCodeFile, Hunk
from fitzzftw.patch.exceptions import FtwPatchError, PatchParseError
from fitzzftw.patch.lines import HeadLine, HunkHeadLine, HunkLine, PatchLine


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
    test_file = testfiles_dir / "get_started_cli.rst"
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
