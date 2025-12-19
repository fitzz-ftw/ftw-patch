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

| File: ftw.patch/ftw_patch.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de

Ein Unicode resistenter Ersatz für patch.


"""
import os
import re
import sys
from argparse import ArgumentParser, Namespace
from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Iterator, TextIO

### Temporary Functions
# oldprint=print

# def print(*values: object, 
#           sep: str | None = " ", 
#           end: str | None = "\n", 
#           file: str| None = None, 
#           flush: Literal[False] = False):
#     pass

# def dp(*args):
#     # oldprint(*args, flush=True)
#     pass



def is_null_path(path: Path | str) -> bool:
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
        path_str = str(path)
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

HunkContentData = namedtuple(
    'HunkContentData', 
    ['lines', 'original_has_newline', 'new_has_newline']
)

# --- Core Data Structures for Patch Content ---



@dataclass(frozen=True)
class Hunk:
    """
    Represents a single hunk (block of changes) in a unified diff format.

    :param original_start: Starting line number in the original file.
    :param original_length: Number of lines affected in the original file.
    :param new_start: Starting line number in the new file.
    :param new_length: Number of lines affected in the new file.
    :param lines: The actual content lines (starting with ' ', '+', or '-').
    :param original_has_newline: If False, the last affected line in the 
                                 original file did not have a trailing newline. 
                                 Defaults to True.
    :param new_has_newline: If False, the last affected line in the new file 
                            should not have a trailing newline. Defaults to True.
    """
    original_start: int
    original_length: int
    new_start: int
    new_length: int
    lines: list['HunkLine']
    original_has_newline: bool = True 
    new_has_newline: bool = True 


# --- Exceptions ---

class FtwPatchError(Exception):
    """
    Base exception for all errors raised by the :py:mod:`ftw_patch` 
    module.

    **Inheritance Hierarchy**
        * :py:class:`FtwPatchError`
        * :py:class:`builtins.Exception`
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
        * :py:class:`builtins.Exception`
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


#CLASS - FileLine
class FileLine:
    """
    Represents a single line read from a file or contained within a patch hunk.

    The primary responsibility is to handle the line content and its associated 
    prefix (if it comes from a patch) consistently, especially by immediately 
    stripping the trailing newline character upon initialization.

    The actual content, free of the trailing newline, is exposed via the 
    :py:attr:`~FileLine.content` property.
    """
    _INTERNAL_WS_RE: ClassVar[re.Pattern] = re.compile(r'([ \t\f\v]+)')
    _ALL_WS_RE: ClassVar[re.Pattern] = re.compile(r'\s+')
    _TRAIL_WS_RE: ClassVar[re.Pattern] = re.compile(r"([ \t\f\v]+)[\n\r]*$")

    def __init__(self, raw_line:str):
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
        line_content = raw_line
        clean_content = line_content.removesuffix(
            '\\ No newline at end of file\n').removesuffix(
                '\\ No newline at end of file\r\n')
        self._has_trailing_whitespace: bool = bool(
                        self._TRAIL_WS_RE.search(clean_content))
        self._content: str = clean_content.rstrip('\n\r')

    def __repr__(self):
        return "".join([self.__class__.__name__,
                        f"(Content: {self.prefix}{self.content})"])


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
        content = self._content.replace('\xa0', ' ')
        
        # 1. Find the index of the first non-whitespace character and separate
        # Lstrip returns the string without leading whitespace.
        stripped_content = content.lstrip(' \t\f\v')
        first_non_ws_index = len(content) - len(stripped_content)
        
        # 2. Extract the leading whitespace (must be preserved)
        leading_ws = content[:first_non_ws_index]
        
        # 3. Apply normalization (collapse) to the REST of the line
        # Only internal whitespace is replaced.
        collapsed_content = self._INTERNAL_WS_RE.sub(' ', stripped_content)
        
        # 4. Remove trailing whitespace (from the end of collapsed_content)
        final_content = collapsed_content.rstrip(' \t\f\v')
        
        # 5. Re-append leading whitespace and return
        return leading_ws + final_content

    @property
    def ignore_all_ws_content(self) -> str:
        """
        The line content, dynamically normalized according to the --ignore-all-ws rule **(ro)**.
        
        All forms of whitespace (leading, internal, trailing) are removed from the string.

        :returns: The string content with all whitespace removed.
        """
        return self._ALL_WS_RE.sub('', self._content)

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
#!CLASS FileLine

#CLASS - HunkLine
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
        if not raw_line or raw_line[0] not in (' ', '+', '-'):
             raise PatchParseError(
                 f"Hunk content line missing valid prefix (' ', '+', '-') or is empty: {raw_line!r}"
             )
        
        self._prefix: str = raw_line[0]
        line_content = raw_line[1:]
        
        clean_content = line_content.removesuffix('\\ No newline at end of file\n').removesuffix('\\ No newline at end of file\r\n')
        self._has_trailing_whitespace: bool = bool(self._TRAIL_WS_RE.search(clean_content))
        self._content: str = clean_content.rstrip('\n\r')

    def __repr__(self):
        return "".join([self.__class__.__name__,
                        f"(Content: {self.prefix}{self.content})"])

    # --- Content Properties ---
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
    def is_context(self) -> bool:
        """Returns True if the line is a context line (' ') **(ro)**.
        
        :returns: Boolean value.
        """
        return self._prefix == ' '
        
    @property
    def is_addition(self) -> bool:
        """Returns True if the line is an addition line ('+') **(ro)**.
        
        :returns: Boolean value.
        """
        return self._prefix == '+'
        
    @property
    def is_deletion(self) -> bool:
        """Returns True if the line is a deletion line ('-') **(ro)**.
        
        :returns: Boolean value.
        """
        return self._prefix == '-'
#!CLASS HunkLine

#SECTION - --- Parser ---
#CLASS - PatchParser
class PatchParser:
    """
    Handles the parsing of the diff or patch file content.

    This class is responsible for reading the file, handling potential 
    encoding issues, and iterating over the hunks and files defined 
    in the patch.
    """
    
    # Regex to capture the standard unified hunk header: 
    # @@ -<start>,<len> +<start>,<len> @@ (optional text)
    _HUNK_HEADER_RE = re.compile(
        r"^@@\s*-(\d+)(?:,(\d+))?\s*\+(\d+)(?:,(\d+))?\s*@@.*$"
    )
    
    def __init__(self, patch_file_path: Path) -> None:
        """
        Initializes the PatchParser instance.

        :param patch_file_path: Path to the .diff or .patch file.
        :raises builtins.FileNotFoundError: If the patch file does not 
                                            exist.
        """
        self._current_line: str|None =None

        if not patch_file_path.is_file():
            raise FileNotFoundError(f"Patch file not found: {patch_file_path}")
        
        self._patch_file_path = patch_file_path

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}" \
               f"(patch_file_path={self._patch_file_path!r})"


    # Static Regex for Hunk Header (single compilation)
    _HUNK_HEADER_RE = re.compile(
        r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
    )


    def _peek_line(self) -> str:
        """
        Reads the next line from the file stream into the lookahead buffer 
        (self._current_line) if it is currently empty (None).

        The line remains in the buffer after the call, allowing the consumer 
        to inspect the line without consuming it. An empty string ('') indicates EOF.

        Used by:
        - :py:meth:`~PatchParser._read_line` (to ensure the buffer is populated before consumption)
        - :py:meth:`~PatchParser.iter_files` (to check for next file/hunk headers)
        - :py:meth:`~PatchParser._parse_hunk_content` (to check for hunk termination or newline 
                    markers)

        :returns: The next line, including the newline character, or an empty 
                string if the end of the file is reached.
        """
        if self._current_line is None:
            # Read the next raw line from the file handle and store it.
            # This can be 'Content\\n', '\\n', or '' (EOF).
            self._current_line = self.file_handle.readline() 
            
        return self._current_line 


    def _read_line(self) -> str:
        """
        Consumes and returns the line currently stored in the lookahead buffer 
        (self._current_line).

        This method calls :py:meth:`~PatchParser._peek_line` to ensure the buffer is populated 
        first. After retrieving the line, it explicitly sets self._current_line to None, 
        making the line officially consumed and advancing the parser's position.

        Uses:
        - :py:meth:`~PatchParser._peek_line` (to ensure the buffer is populated before consumption)

        Used by:
        - :py:meth:`~PatchParser.iter_files` (to consume headers like '---', '+++', and '@@')
        - :py:meth:`~PatchParser._parse_hunk_content` (to consume actual content lines and markers)

        :returns: The consumed line, including the newline character.
        """
        # Call _peek_line to populate self._current_line if it is None
        line = self._peek_line() 
        
        # Consume the line by emptying the buffer.
        self._current_line = None 
            
        return line

    def _parse_hunk_metadata(self, line: str) -> tuple[int, int, int, int]:
        """
        Reads and parses the content lines of a single hunk until the block ends.

        Hunk termination is dynamically determined by checking the lookahead buffer 
        for a non-content prefix ('---', '+++', '@@', or EOF), eliminating the need 
        for pre-calculated line counts. This method also handles the special 
        'No newline at end of file' marker.

        Used by:
        - :py:meth:`~PatchParser.iter_files` (after consuming an '@@' header)

        :raises PatchParseError: On unexpected EOF or malformed content lines.

        :returns: A named tuple containing the parsed lines and newline status flags.
        """
        match = self._HUNK_HEADER_RE.match(line)
        
        if not match:
            raise PatchParseError(f"Malformed Hunk header: {line.strip()!r}")
            
        # Extracting the groups (as strings or None if length is missing)
        o_start_str, o_len_str, n_start_str, n_len_str = match.groups()
        
        # Convert to int, where length defaults to 1 if not present
        original_start = int(o_start_str)
        original_length = int(o_len_str) if o_len_str else 1
        new_start = int(n_start_str)
        new_length = int(n_len_str) if n_len_str else 1
        
        return original_start, original_length, new_start, new_length


    def _parse_hunk_content(self) -> tuple[list['HunkLine'], bool, bool]:
        """
        Reads the content lines of a hunk by checking prefixes until the end of the 
        hunk block is found (next header, EOF, or marker).

        This method consumes the lines containing the actual changes ('+', '-', ' ').
        It also handles the special "No newline at end of file" marker using lookahead.

        Returns:
            A tuple containing:
            1. list['HunkLine']: The parsed content lines.
            2. bool: original_has_newline (False if marker found for original file).
            3. bool: new_has_newline (False if marker found for new file).
        
        Raises:
            PatchParseError: On unexpected EOF or malformed content lines.
        """
        lines: list[HunkLine] = []
        original_has_newline: bool = True
        new_has_newline: bool = True
        
        # 1. Read content lines until the hunk ends (prefix check)
        while True:
            line = self._peek_line() # Use lookahead to check prefix without consuming
            # Check for EOF first. An empty string means EOF.
            if not line:
                # EOF reached prematurely is an error if we haven't found a valid end marker yet.
                # raise PatchParseError("Unexpected EOF while reading expected hunk content lines.")
                break

            if line.startswith(("--- ", "+++ ", "@@ ")):
                # The next file header or hunk header is found. The hunk content is finished.
                # The line is left in the buffer for iter_files to handle.
                break

            # The special marker also terminates the hunk content loop
            if line.startswith(r"\ No newline at end of file"):
                break

            # Check if the line is valid hunk content (must start with ' ', '+', or '-').
            # If not, the hunk content block is finished. The line is left in the buffer.
            if line[0] not in (' ', '+', '-'):
                break

            # Consume the line and attempt to parse it as HunkLine
            line_to_process = self._read_line()
            try:
                hunk_line = HunkLine(line_to_process)
                lines.append(hunk_line)
            except PatchParseError as e:
                raise PatchParseError(f"Error parsing hunk content line {len(lines) + 1}: {e}")
            except Exception as e: 
                # This catches errors like IndexError (e.g., if HunkLine[0] fails)
                raise PatchParseError(f"Unexpected error processing HunkLine content (line: {len(lines) + 1}): {e}")
        # 2. Check for the Newline Marker using lookahead (if the hunk was not ended by EOF)
        
        next_line_peek = self._peek_line()
        
        if next_line_peek.startswith(r"\ No newline at end of file"):
            # Marker found: update status flags based on the last line's type
            
            # Consume the marker line to advance the parser
            self._read_line() 
            
            if lines:
                last_line = lines[-1]
                
                # The marker affects the original file if the last line was context or deletion.
                if last_line.is_context or last_line.is_deletion:
                    original_has_newline = False
                    
                # The marker affects the new file if the last line was context or addition.
                if last_line.is_context or last_line.is_addition:
                    new_has_newline = False

        return HunkContentData(lines, 
                            original_has_newline, 
                            new_has_newline)


    def _parse_file_headers(self) -> tuple[str | None, str | None, bool]:
        """
        Reads lines from the file handle until the '---' and '+++' file headers 
        are found. Strips the time/date stamps and extracts the file paths.
        
        :returns: A tuple (original_path, new_path, found_file_block). 
                  (None, None, False) if EOF is hit before finding the headers.
        """
        original_path = None
        new_path = None
        
        # 1. Skip lines until the '---' header is found
        while True:
            line = self._read_line()
            if not line: # EOF reached
                return None, None, False
            if line.startswith('--- '):
                # Found original file header
                original_path = self._clean_path(line[4:].strip())
                break
        
        # 2. Read the subsequent '+++' header
        line = self._read_line()
        if not line or not line.startswith('+++ '):
             # Error: '+++' missing after '---'. PatchFile is malformed.
             raise PatchParseError("Missing '+++' file header after '---'.")

        new_path = self._clean_path(line[4:].strip())
        
        return original_path, new_path, True

    def _clean_path(self, path_line: str) -> str:
        """
        Removes tabs, carriage returns, and optional timestamp/revision info 
        from the file path line. (e.g., '\t2017-01-01 ...' or '\trevision').
        
        This logic currently resides in FtwPatch; it will be moved to 
        PatchContext later, but for now, we simulate the required cleaning.
        """
        if '\t' in path_line:
            path_line = path_line.split('\t', 1)[0]
        if '\r' in path_line:
            path_line = path_line.split('\r', 1)[0]
            
        return path_line


    # def _strip_patch_path(self, path: str) -> str:
    #     """
    #     Strips 'a/', 'b/', and applies strip_count logic (which is assumed to be 0 
    #     in tests if not explicitly passed).
    #     """
    #     # 1. Strip 'a/' or 'b/' prefix (Standard Unified Diff Format)
    #     # if path.startswith("a/") or path.startswith("b/"):
    #     #     path = path[2:]
        
    #     # 2. Apply strip_count logic (optional, aber muss vorhanden sein)
    #     # Da der PatchParser das strip_count Argument nicht kennt, 
    #     # gehen wir davon aus, dass es hier nur um das b/ / a/ stripping geht.

    #     return path


    def iter_files(self) -> Iterator[tuple[Path, Path, list[Hunk]]]:
        """
        Iterates over all file-level patches in the diff file, yielding one Patch 
        object for each modification.

        This method manages the overall parsing flow, handling file headers (--- and +++), 
        and controlling the transition between hunks and files.

        Uses:
        - :py:meth:`~PatchParser._peek_line` (to check for new headers without consuming them)
        - :py:meth:`~PatchParser._read_line` (to consume headers and manage the lookahead buffer)
        - :py:meth:`~PatchParser._parse_hunk_content` (to read the lines belonging to a hunk)
            
        :raises FtwPatchError: On any critical parsing error during file or hunk processing.

        :returns: A Patch object containing all necessary metadata and Hunk objects 
                for a single file modification.
        """
        original_file_path: Path | None = None
        new_file_path: Path | None = None
        hunks: list[Hunk] = []
        
        try:
            file_handle: TextIO
            # Use manual readline for stateful parsing of file/hunk blocks
            with self._patch_file_path.open(
                mode="r", encoding="utf-8", errors="replace"
            ) as file_handle:
                
                # We assign the file_handle to self to allow helper methods 
                # to access the stream state.
                self.file_handle = file_handle

                while True:
                    
                    # 1. FILE HEADER LOGIC: Extracts '---' and '+++'
                    o_path_str, n_path_str, found_file_block = self._parse_file_headers()

                    if is_null_path(n_path_str):
                        yield Path(o_path_str), Path(n_path_str), []

                    if not found_file_block:
                        if hunks:
                            yield original_file_path, new_file_path, hunks
                        return  # EOF reached

                    # If we have hunks from the previous file block, yield them
                    if hunks:
                        yield original_file_path, new_file_path, hunks
                        hunks = [] # Reset for the new file block
                    
                    # Set the paths for the new file block
                    original_file_path = Path(o_path_str)
                    new_file_path = Path(n_path_str)                    

                    # 2. HUNK BLOCK LOGIC: Process '@@' headers
                    
                    line = self._read_line()

                    if not line:
                        break

                    # Identify Hunk Header '@@ ... @@'
                    if line.startswith('@@ '):
                        # a) Parse metadata (using helper method)
                        try:
                            o_start, o_len, n_start, n_len = self._parse_hunk_metadata(line)
                        except PatchParseError as e:
                            raise FtwPatchError(f"Error parsing hunk metadata for file {original_file_path!r}: {e}")



                        # b) Parse content lines (using helper method)
                        hunk_content_data = self._parse_hunk_content()

                        # c) Create and append Hunk
                        hunk = Hunk(
                            original_start=o_start,
                            original_length=o_len,
                            new_start=n_start,
                            new_length=n_len,
                            lines=hunk_content_data.lines,
                            original_has_newline=hunk_content_data.original_has_newline,
                            new_has_newline=hunk_content_data.new_has_newline
                        )
                        hunks.append(hunk)
                        
                    else:
                        # Skip other lines between blocks (e.g., 'Index: ...')
                        continue 
                        
                # End of While loop (EOF)
                # if hunks:
                #     yield original_file_path, new_file_path, hunks

        except FtwPatchError:
            raise
        except Exception as e:
            raise FtwPatchError(f"An unexpected error occurred during patch file parsing: {e}")

#!CLASS - PatchParser
#!SECTION - Parsers


#SECTION -  --- FtwPatch (Main Application) ---

# Constant for the /dev/null path, which is returned by _clean_patch_path with strip=0.
# This path must be independent of the operating system.
# DEV_NULL_PATH = Path(os.devnull) 

#CLASS - FtwPatch
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
        :raises builtins.FileNotFoundError: If the patch file does not exist.
        :raises FtwPatchError: If any internal error occurs during setup.
        """
        self._args = args

        # Proactive check for the existence of the patch file
        if not self._args.patch_file.is_file():
             raise FileNotFoundError(
                 f"Patch file not found at {self._args.patch_file!r}"
             )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(args={self._args!r})"

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

#ANCHOR - alt _nomalize_line
    # def _normalize_line(self, file_line: FileLine, strip_prefix: bool = False) -> str:
    #     """
    #     Applies whitespace normalization rules based on CLI arguments.
        
    #     :param line: The line content from the file or the patch.
    #     :param strip_prefix: If True, strips the diff prefix (' ', '+', '-') 
    #                          from the patch line.
    #     :returns: The normalized line.
    #     """
    #     # Strip the diff prefix if present and requested
    #     #line = " ".join([file_line.prefix, file_line.content])
    #     line = "".join([file_line.prefix, file_line.content])
    #     if strip_prefix:
    #         line = file_line.content
        
    #     # Dominant option: --ignore-all-ws
    #     if self.ignore_all_whitespace:
    #         # Remove all whitespace characters (including newlines, tabs, and spaces)
    #         # return "".join(line.split())
    #         return file_line.ignore_all_ws_content
        
    #     # Secondary options: --normalize-ws and --ignore-bl
        
    #     # Remove newline and carriage return at the end
    #     line = line.strip('\n\r') 

    #     # Ignore Blank Lines: If line is now empty after stripping, return empty string
    #     if self.ignore_blank_lines and not file_line.content.strip():
    #         return ''
        
    #     # Normalize non-leading whitespace
    #     if self.normalize_whitespace:
    #         line = file_line.normalized_ws_content
        
    #     return line

    def _normalize_line(self, file_line: FileLine) -> str:
        """
        Applies whitespace normalization rules based on CLI arguments, 
        dispatching to the correct :py:class:`FileLine` getter method.

        This function acts as the central dispatcher, ensuring that the appropriate 
        comparison logic is used (e.g., ignoring all whitespace, normalizing spaces, 
        or standard comparison). It relies on the :py:class:`FileLine` getters to 
        handle prefix stripping and newline removal, as these methods have been 
        validated to return content suitable for comparison.

        :param file_line: The line content from the file or the patch as 
                          a :py:class:`FileLine` instance.
        :returns: The normalized line content suitable for comparison.
        """
        
        # 1. Dominant Option: --ignore-all-ws
        if self.ignore_all_whitespace:
            # The method returns content with all whitespace removed.
            return file_line.ignore_all_ws_content
        
        # 2. Option: --ignore-bl
        # Checks for an explicit blank line (content is effectively empty after stripping).
        if self.ignore_blank_lines and not file_line.content.strip():
            # If ignore-bl is active and the content is empty, return an empty string for 
            # comparison.
            return ''
            
        # 3. Secondary Option: --normalize-ws
        if self.normalize_whitespace:
            # The method returns content with internal whitespace collapsed, 
            # preserving leading indentation (which may include the patch prefix).
            return file_line.normalized_ws_content
            
        # 4. Standard Mode (No WS options active)
        # For standard comparison, the content part (without prefix and without newline) is 
        # returned.
        return file_line.content



    def _clean_patch_path(self, patch_path: Path) -> Path:
        """
        Applies the strip count to a path found in the patch file and returns 
        the final target path relative to the target directory.

        :param patch_path: The path extracted from the '---' or '+++' line.
        :raises FtwPatchError: If the strip count is too large for the given path.
        :returns: The path to the file relative to the target directory.
        """
        parts = patch_path.parts
        strip_count = self.strip_count
        
        cleaned_parts = [p for p in parts if p and p != '.']

        # Special case /dev/null is always returned without stripping.
        # if patch_path == DEV_NULL_PATH:
        #     return DEV_NULL_PATH
        if is_null_path(patch_path):
            return os.devnull

        if strip_count >= len(cleaned_parts):
            raise FtwPatchError(
                # f"Strip count ({strip_count}) is greater than or equal to the "
                # f"number of pacleaned_th components ({len(cleaned_parts)}) in '{patch_path}'."
                f"Strip count ({strip_count}) is greater than the number of " 
                f"cleaned_path components ({len(cleaned_parts)}) in '{patch_path}'."
            )
        
        cleaned_path = Path(*cleaned_parts[strip_count:])
        return cleaned_path

    def _apply_hunk_to_file(self, file_path: Path, hunk: Hunk, original_lines: list[str]) -> list[str]:
        """
        Applies a single hunk to the content of a file, performing 
        line-by-line validation and transformation.
        
        :param file_path: The Path object of the file being patched.
        :param hunk: The Hunk object containing the changes.
        :param original_lines: The current content of the file as a list of strings (lines).
        :raises FtwPatchError: If a hunk mismatch occurs (context or deletion line does not match).
        :returns: The new content of the file as a list of strings.
        """
        # A. Initial checks and setup (omitted)
        
        # B. Hunk Application
        new_file_content = []
        # file_current_index is 0-based index corresponding to line number (hunk.original_start) - 1
        file_current_index = hunk.original_start - 1
        lines_consumed_in_original = 0
        
        # FINAL FIX 4a: NEW STATE for skip suppression (for 
        # test_ignore_bl_no_skip_on_blank_line_context)
        last_line_was_explicit_blank = False 
        
        hunk_line_index = 0
        
        for hunk_line in hunk.lines:
            # 1. Check for Addition
            if hunk_line.is_addition:  # Addition line
                new_line_content = hunk_line.content
                
                # Ensure the line has a trailing newline if not present
                if not new_line_content.endswith(('\n', '\r')):
                    new_line_content += '\n'
                    
                new_file_content.append(new_line_content)
                # FINAL FIX 4b: Reset state, addition breaks context chain
                last_line_was_explicit_blank = False 

            # 2. Check for Deletion
            elif hunk_line.is_deletion:  # Deletion line
                # Normalize lines for comparison
                norm_hunk_line=self._normalize_line(hunk_line)


                # FINAL FIX 4b: Reset state, deletion breaks context chain
                last_line_was_explicit_blank = False 
                
                # FINAL FIX 3a: BLANK LINE SKIP LOGIC (for Deletion)
                # Skip only if ignore-bl is active AND the hunk expects a 
                # non-blank line to be deleted.
                if self.ignore_blank_lines and norm_hunk_line != '':
                    while file_current_index < len(original_lines) and original_lines[file_current_index].strip() == '':
                        file_current_index += 1
                        lines_consumed_in_original += 1
                
                # --- MATCH CHECK ---
                if file_current_index >= len(original_lines):
                    raise FtwPatchError(f"Hunk mismatch on deletion line {hunk_line!r}: Found 'EOF'.")

                original_line = original_lines[file_current_index]
                norm_original_line = self._normalize_line(FileLine(original_line))
                if norm_original_line != norm_hunk_line:
                    raise FtwPatchError(
                        f"Hunk mismatch on deletion line {hunk_line!r}: "
                        f"Expected '{norm_hunk_line!r}', found '{norm_original_line!r}'."
                    )
                
                # Match successful: Line is removed by skipping append
                file_current_index += 1
                lines_consumed_in_original += 1
                
            # 3. Check for Context
            elif hunk_line.is_context:  # Context line
                
                # 1. Normalize the hunk line and check if it contains content
                norm_hunk_line = self._normalize_line(hunk_line)
                is_hunk_line_content = (norm_hunk_line != '')
                
                # --- FINAL FIX 4c / 3b START: Skip Control and Execution ---
                if self.ignore_blank_lines: 
                    
                    if is_hunk_line_content:
                        # Only skip if no explicit blank line context preceded it (Fix 4c)
                        if not last_line_was_explicit_blank:
                            # Skip logic (Fix 3b: WITH append)
                            while file_current_index < len(original_lines) and original_lines[file_current_index].strip() == '':
                                new_file_content.append(original_lines[file_current_index])
                                file_current_index += 1
                                lines_consumed_in_original += 1
                                
                        # Reset state, as a content line was processed.
                        last_line_was_explicit_blank = False 

                    else: # is_hunk_line_content == False (explicit blank line expected: ' \n')
                        # Set state to suppress the skip check for the next content line.
                        last_line_was_explicit_blank = True 

                else:
                    # Regular processing: no skip-suppression needed
                    last_line_was_explicit_blank = False
                # --- FINAL FIX 4c / 3b END ---
                
                
                # Load the line AFTER the optional skip
                if file_current_index >= len(original_lines):
                     raise FtwPatchError(f"Context mismatch in file '{file_path}': Expected '{norm_hunk_line!r}', found 'EOF'.")

                original_line = original_lines[file_current_index]
                # Normalize original line after loading
                norm_original_line = self._normalize_line(FileLine(original_line)) 
                
                # --- MATCH CHECK ---
                if norm_hunk_line != norm_original_line:
                    raise FtwPatchError(
                        f"Context mismatch in file '{file_path}' at expected line {file_current_index + 1}: "
                        f"Expected '{norm_hunk_line!r}', found '{norm_original_line!r}'."
                    )
                
                # Match successful: Append the original line
                new_file_content.append(original_line)
                file_current_index += 1
                lines_consumed_in_original += 1

            else: # pragma: no cover
                # Should be caught by PatchParser.iter_files.
                raise PatchParseError(
                    f"Unexpected line prefix in hunk line: {hunk_line!r}"
                )
            
            hunk_line_index += 1

        # C. Append remaining lines
        new_file_content.extend(original_lines[file_current_index:])

        # D. Newline status correction
        if new_file_content and not hunk.new_has_newline:
            last_line = new_file_content[-1]
            new_file_content[-1] = last_line.rstrip('\n\r')
        return new_file_content

    def run(self) -> int:
        """
        Main entry point for the patch application.
        
        It encapsulates the core logic (apply_patch) and handles exceptions 
        to return the appropriate exit code.
        
        :returns: The exit code (0 for success, non-zero otherwise).
        """
        try:
            # The entire logic has been delegated to apply_patch
            return self.apply_patch(dry_run=self.dry_run)
            
        except FtwPatchError as e:
            # We assume FtwPatchError is used for patch errors
            # and hunk mismatches, which should lead to an exit code of 1.
            print(f"\nPatch failed: {e}")
            return 1
            
        except FileNotFoundError as e:
            # Handles errors when a target file is missing during application.
            print(f"\nFile Error during patching: {e}")
            return 1
            
        except Exception as e:
            # General error handling (e.g., IO errors during writing)
            print(f"\nAn unexpected error occurred: {e}")
            return 2


    def apply_patch(self, dry_run: bool = False) -> int:
        """
        Applies the loaded patch to the target files.

        :param dry_run: If :py:obj:`True`, only simulate the patching process.
        :raises builtins.IOError: If an I/O error occurs during patch file reading or writing.
        :raises PatchParseError: If the patch file content is malformed.
        :raises FtwPatchError: If an error occurs during the application of the patch or path 
                stripping.
        :returns: The exit code, typically 0 for success.
        """
        parser = PatchParser(self.patch_file_path)
        print(
            f"Applying patch from {self.patch_file_path!r} in directory "
            f"{self.target_directory!r} (strip={self.strip_count}, ws_norm="
            f"{self.normalize_whitespace}, bl_ignore={self.ignore_blank_lines}, "
            f"all_ws_ignore={self.ignore_all_whitespace})."
        )
        
        # Stores the new content of patched files (Path: list[str])
        patched_file_storage: dict[Path, list[str]] = {}
        # Stores files that need to be deleted
        files_to_delete: list[Path] = []
        
        applied_file_count = 0
        
        # 1. Iterate over the parsed file blocks and apply hunks
        for original_path, new_path, hunks in parser.iter_files():
            # 2. Path cleanup and target path determination
            target_original_path = self._clean_patch_path(original_path)
            target_new_path = self._clean_patch_path(new_path)
            
            # Full paths relative to the target directory
            full_original_path = self.target_directory / target_original_path
            full_new_path = self.target_directory / target_new_path
            
            # Output file information
            print(
                f"\n--- Processing file: {target_original_path!r} -> "
                f"{target_new_path!r} ({len(hunks)} hunks)"
            )
            
            # --- Special case: Deletion (Original exists, New is_null_path()=True )
            if is_null_path(target_new_path):
                if not full_original_path.is_file():
                    raise FtwPatchError(
                        f"File to be deleted not found: {full_original_path!r}"
                    )
                # Mark for deletion (no application of hunks necessary)
                files_to_delete.append(full_original_path)
                applied_file_count += 1
                print(" -> Marked for deletion.")
                continue

            # --- Special case: Creation (Original is_null_path()==True)
            if is_null_path(target_original_path):
                # Since the file does not exist, we start with an empty array
                # The hunks only consist of '+' lines and context (' ').
                original_lines = []
            
            # --- Standard case: Modification
            else:
                # Check if the original file exists
                if not full_original_path.is_file():
                    raise FtwPatchError(
                        f"Original file not found for patching: "
                        f"{full_original_path!r}"
                    )
                # Read file content
                try:
                    with full_original_path.open(
                        mode="r", encoding="utf-8", errors="replace"
                    ) as f:
                        original_lines = f.readlines()
                except IOError as e:
                    raise IOError(
                        f"Error reading target file {full_original_path}: "
                        f"{e}"
                    )

            # 4. Sequentially apply hunks in memory
            current_lines = original_lines
            for i, hunk in enumerate(hunks):
                print(
                    f" - Applying Hunk {i+1}/{len(hunks)} "
                    f"(@ Line {hunk.original_start}: "
                    f"{hunk.original_length} -> {hunk.new_length})"
                )
                current_lines = self._apply_hunk_to_file(
                    file_path=full_original_path,
                    hunk=hunk,
                    original_lines=current_lines
                )
            # 5. Cache the result in memory (only if not a deletion)
            if not is_null_path(target_new_path):
                patched_file_storage[full_new_path] = current_lines
                applied_file_count += 1
                print(
                    " -> Patch successfully verified and stored in "
                    f"memory ({len(current_lines)} lines)."
                )

            # END OF HUNK ITERATION: If we reach this point, the entire patch process 
            # for THIS file was error-free. (LOOP CONTINUES)
            
        # 6. WRITE PHASE (All-or-nothing write phase, runs ONCE after all files are 
        #    verified)
        if not dry_run:
            print("\nStarting write/delete phase: Applying changes to " "file system...")
            
            # Perform deletions first
            for file_path in files_to_delete:
                file_path.unlink()
                print(f" -> Successfully deleted {file_path!r}.")

            # Then write changes
            for full_new_path, final_content in patched_file_storage.items():
                try:
                    # Ensure the parent directory exists
                    full_new_path.parent.mkdir(parents=True, exist_ok=True)
                    with full_new_path.open(
                        mode="w", encoding="utf-8", errors="replace"
                    ) as f:
                        f.writelines(final_content)
                    print(f" -> Successfully wrote {full_new_path!r}.")
                except IOError as e:
                    raise IOError(
                        f"Error writing patched file {full_new_path}: {e}"
                    )
        
        else: # Executes if dry_run is True (corresponds to the 'if not dry_run:' above)
            print("\nDry run completed. No files were modified.")
        
        # 7. Summary (runs regardless)
        print(f"\nSuccessfully processed {applied_file_count} file changes.")
        return 0
#!CLASS - FtwPatch
#!SECTION - FtwPatch

#SECTION -  --- CLI Entry Point ---

def _get_argparser() -> ArgumentParser:
    """
    Creates and configures the ArgumentParser for the ftw_patch CLI.

    :returns: The configured ArgumentParser instance.
    """
    parser = ArgumentParser(
        prog="ftwpatch",
        description="A Unicode-safe patch application tool with advanced "
                    "whitespace normalization."
    )
    
    parser.add_argument(
        "patch_file", 
        type=Path,
        # dest="patch_file", 
        help="The path to the unified diff or patch file."
    )
    
    # Standard patch options
    parser.add_argument(
        "-p", 
        "--strip", 
        type=int, 
        default=0,
        dest="strip_count",
        help=(
            "Set the number of leading path components to strip from file names "
            "before trying to find the file. Default is 0."
        ),
    )
    
    parser.add_argument(
        "-d", 
        "--directory", 
        type=Path, 
        default=Path('.'),
        dest="target_directory",
        help=(
            "Change the working directory to <dir> before starting to look for "
            "files to patch. Default is the current working directory ('.')."
        ),
    )
    
    # FTW Patch specific normalization options
    parser.add_argument(
        "--normalize-ws", 
        action="store_true",
        dest="normalize_whitespace",
        help=(
            "Normalize non-leading whitespace (replace sequences of spaces/tabs "
            "with a single space) in context and patch lines before comparison. "
            "Useful for patches with minor formatting differences."
        ),
    )
    
    parser.add_argument(
        "--ignore-bl", 
        action="store_true",
        dest="ignore_blank_lines",
        help=(
            "Ignore or treat pure blank lines identically during patch matching. "
            "This implements a skip-ahead logic that collapses sequences of "
            "blank lines in the original file to match the blank lines (or lack "
            "thereof) in the patch context. It effectively ignores differences "
            "in the number of consecutive blank lines."
        ),
    )
    
    parser.add_argument(
        "--ignore-all-ws", 
        action="store_true",
        dest="ignore_all_whitespace",
        help=(
            "Ignore all whitespace (leading, non-leading, and blank lines) "
            "during comparison. This option overrides --normalize-ws and "
            "--ignore-bl."
        ),
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        dest="dry_run", 
        help="Do not write changes to the file system; only simulate the process."
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        dest = "verbose",
        default=0,
        help="Increase output verbosity. Can be specified multiple times (-vvv) "
             "to increase the level of detail."
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
    # 1. Initialize Argument Parser (Assumption: _get_argparser() is defined)
    parser = _get_argparser() 
    
    # 2. Parse arguments
    args = parser.parse_args()

    # 3. Error handling and execution
    try:
        # The 'dry_run' argument must be correctly extracted from args
        dry_run = getattr(args, 'dry_run', False)

        # The FtwPatch class encapsulates the entire logic
        patcher = FtwPatch(args=args)
        
        # apply_patch() executes the entire patch logic
        exit_code = patcher.apply_patch(dry_run=dry_run)
        
        return exit_code
        
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

if __name__ == "__main__": # pragma: no cover
    from doctest import testfile, FAIL_FAST  # noqa: I001
    from pathlib import Path
    # Adds the project's root directory (the module source directory)
    # to the beginning of sys.path.
    project_root = Path(__file__).resolve().parent.parent
    print(project_root)
    sys.path.insert(0, str(project_root))    
    be_verbose=False
    be_verbose=True
    option_flags= 0
    option_flags= FAIL_FAST
    testfilesbasedir = Path("../../../doc/source/devel")
    test_sum = 0
    test_failed = 0
    dt_file = str(testfilesbasedir / "get_started_ftw_patch.rst")
    # dt_file = str(testfilesbasedir / "temp_test.rst")
    # dt_file = str(testfilesbasedir / "test_parser_fix.rst")
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
    
    if test_failed== 0:
        print(f"DocTests passed without errors, {test_sum} tests.")
    else:
        print(f"DocTests failed: {test_failed} tests.")


