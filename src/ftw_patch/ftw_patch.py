"""
FTW Patch
===============================

| File: ftw_patch/ftw_patch.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de

Ein Unicode resistenter Ersatz für patch.


"""
from argparse import ArgumentParser, Namespace
from collections import namedtuple
from pathlib import Path
from dataclasses import dataclass 
import sys
from typing import ClassVar, Iterator, Literal, TextIO
import re

### Temporäre Funktionen
# oldprint=print

# def print(*values: object, 
#           sep: str | None = " ", 
#           end: str | None = "\n", 
#           file: str| None = None, 
#           flush: Literal[False] = False):
#     pass

def dp(*args):
    # oldprint(*args, flush=True)
    pass

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
        return f"{self.__class__.__name__}()"


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
        return f"{self.__class__.__name__}(message={self.args[0]!r})"

class FileLine:
    """"""

    _INTERNAL_WS_RE: ClassVar[re.Pattern] = re.compile(r'([ \t\f\v]+)')
    _ALL_WS_RE: ClassVar[re.Pattern] = re.compile(r'\s+')
    _TRAIL_WS_RE: ClassVar[re.Pattern] = re.compile(r"([ \t\f\v]+)[\n\r]*$")

    def __init__(self, raw_line:str):
        
        self._prefix: str = ""
        line_content = raw_line
        clean_content = line_content.removesuffix('\\ No newline at end of file\n').removesuffix('\\ No newline at end of file\r\n')
        self._has_trailing_whitespace: bool = bool(self._TRAIL_WS_RE.search(clean_content))
        self._content: str = clean_content.rstrip('\n\r')

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
        content = self._content
        
        # 1. Finde den Index des ersten Nicht-Whitespace-Zeichens und trenne
        # Lstrip gibt den String ohne führenden Whitespace zurück.
        stripped_content = content.lstrip(' \t\f\v')
        first_non_ws_index = len(content) - len(stripped_content)
        
        # 2. Extrahiere den führenden Whitespace (muss erhalten bleiben)
        leading_ws = content[:first_non_ws_index]
        
        # 3. Wende die Normalisierung (Collapse) auf den REST der Zeile an
        # Nur interner Whitespace wird ersetzt.
        collapsed_content = self._INTERNAL_WS_RE.sub(' ', stripped_content)
        
        # 4. Entferne nachgestellten Whitespace (vom Ende der collapsed_content)
        final_content = collapsed_content.rstrip(' \t\f\v')
        
        # 5. Führenden Whitespace wieder anhängen und zurückgeben
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
        Indicates if the original raw line contained trailing whitespace before the newline **(ro)**.
        
        :returns: Boolean value.
        """
        return self._has_trailing_whitespace

    def is_empty(self):
        if self.content:
            return False
        else:
            return True

    # @property
    # def is_context(self) -> bool:
    #     """Returns True if the line is a context line (' ') **(ro)**.
        
    #     :returns: Boolean value.
    #     """
    #     return self._prefix == ' '
        
    # @property
    # def is_addition(self) -> bool:
    #     """Returns True if the line is an addition line ('+') **(ro)**.
        
    #     :returns: Boolean value.
    #     """
    #     return self._prefix == '+'
        
    # @property
    # def is_deletion(self) -> bool:
    #     """Returns True if the line is a deletion line ('-') **(ro)**.
        
    #     :returns: Boolean value.
    #     """
    #     return self._prefix == '-'


class HunkLine(FileLine):
    """
    Represents a single content line within a hunk block of a unified diff.

    The class parses the raw diff line upon instantiation and provides 
    dynamically calculated, read-only content properties for different 
    levels of whitespace normalization.
    """
    
    # _INTERNAL_WS_RE: ClassVar[re.Pattern] = re.compile(r'([ \t\f\v]+)')
    # _ALL_WS_RE: ClassVar[re.Pattern] = re.compile(r'\s+')
    # _TRAIL_WS_RE: ClassVar[re.Pattern] = re.compile(r"([ \t\f\v]+)[\n\r]*$")
    
    def __init__(self, raw_line: str) -> None:
        """
        Initializes the HunkLine by parsing the raw line.

        The raw line must start with a valid diff prefix (' ', '+', or '-'). 
        The content is stored without the final newline character.
        
        :param raw_line: The raw line from the patch file (including prefix).
        :raises PatchParseError: If the prefix is invalid or missing.
        """
        # if not raw_line or len(raw_line) < 2 or raw_line[0] not in (' ', '+', '-'):
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
    
    # @property
    # def content(self) -> str:
    #     """
    #     The raw line content, stripped of the diff prefix and trailing newline **(ro)**.
        
    #     This value is used for standard matching when no whitespace flags are set.

    #     :returns: The cleaned line content as a string.
    #     """
    #     return self._content
    
    # @property
    # def normalized_ws_content(self) -> str:
    #     """
    #     The line content, dynamically normalized according to the --normalize-ws rule **(ro)**.
        
    #     Internal whitespace runs collapse to a single space; trailing 
    #     whitespace is removed; leading whitespace is preserved.

    #     :returns: The normalized string used for matches.
    #     """
    #     content = self._content
        
    #     # 1. Finde den Index des ersten Nicht-Whitespace-Zeichens und trenne
    #     # Lstrip gibt den String ohne führenden Whitespace zurück.
    #     stripped_content = content.lstrip(' \t\f\v')
    #     first_non_ws_index = len(content) - len(stripped_content)
        
    #     # 2. Extrahiere den führenden Whitespace (muss erhalten bleiben)
    #     leading_ws = content[:first_non_ws_index]
        
    #     # 3. Wende die Normalisierung (Collapse) auf den REST der Zeile an
    #     # Nur interner Whitespace wird ersetzt.
    #     collapsed_content = self._INTERNAL_WS_RE.sub(' ', stripped_content)
        
    #     # 4. Entferne nachgestellten Whitespace (vom Ende der collapsed_content)
    #     final_content = collapsed_content.rstrip(' \t\f\v')
        
    #     # 5. Führenden Whitespace wieder anhängen und zurückgeben
    #     return leading_ws + final_content

    # @property
    # def ignore_all_ws_content(self) -> str:
    #     """
    #     The line content, dynamically normalized according to the --ignore-all-ws rule **(ro)**.
        
    #     All forms of whitespace (leading, internal, trailing) are removed from the string.

    #     :returns: The string content with all whitespace removed.
    #     """
    #     return self._ALL_WS_RE.sub('', self._content)

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
        Indicates if the original raw line contained trailing whitespace before the newline **(ro)**.
        
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
# --- Parser ---

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

# Innerhalb der PatchParser-Klasse

    # Statische Regex für Hunk Header (einmalige Kompilierung)
    _HUNK_HEADER_RE = re.compile(
        r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
    )

# Assuming these methods are part of the PatchParser class.

    def _peek_line(self) -> str:
        """
        Looks ahead at the next raw line in the patch stream without consuming it.
        
        This mechanism is crucial for correctly identifying the end of a hunk 
        or the next file/hunk header without discarding the separator line.
        
        Returns:
            The raw line as a string (including the newline '\\n').
            Returns the empty string '' if End-Of-File (EOF) is reached.
        """
        if self._current_line is None:
            # Read the next raw line from the file handle and store it.
            # This can be 'Content\\n', '\\n', or '' (EOF).
            self._current_line = self.file_handle.readline() 
            
        return self._current_line 


    def _read_line(self) -> str:
        """
        Consumes and returns the next line from the patch stream.
        
        It uses '_peek_line' to ensure the buffer is populated and then
        clears the lookahead buffer to signal that the line has been consumed.

        Returns:
            The raw, consumed line as a string (including the newline '\\n').
            Returns the empty string '' if End-Of-File (EOF) is reached.
        """
        # Call _peek_line to populate self._current_line if it is None
        line = self._peek_line() 
        
        # Consume the line by emptying the buffer.
        self._current_line = None 
            
        return line

    def _parse_hunk_metadata(self, line: str) -> tuple[int, int, int, int]:
        """
        Parses the Hunk header line (starting with '@@ ') to extract start and length 
        metadata for the original and new files.
        
        :param line: The raw Hunk header line read from the patch file stream.
        :raises PatchParseError: If the Hunk header line is malformed or does not 
                                 match the expected unified diff format.
        :returns: A tuple containing the parsed metadata: 
                  (original_start, original_length, new_start, new_length).
        """
        match = self._HUNK_HEADER_RE.match(line)
        
        if not match:
            raise PatchParseError(f"Malformed Hunk header: {line.strip()!r}")
            
        # Extrahieren der Gruppen (als Strings oder None, wenn die Länge fehlt)
        o_start_str, o_len_str, n_start_str, n_len_str = match.groups()
        
        # Konvertieren in int, wobei die Länge standardmäßig 1 ist, falls nicht vorhanden
        original_start = int(o_start_str)
        original_length = int(o_len_str) if o_len_str else 1
        new_start = int(n_start_str)
        new_length = int(n_len_str) if n_len_str else 1
        
        return original_start, original_length, new_start, new_length

    # def _parse_hunk_content(self, expected_line_count: int) -> tuple[list['HunkLine'], bool, bool]:
    #     """
    #     Reads the content lines of a hunk and checks for the 'No newline' marker.

    #     This method consumes the lines containing the actual changes ('+', '-', ' ').
    #     It also handles the special "No newline at end of file" marker.

    #     :param expected_line_count: The total number of expected '+', '-', and ' ' lines.
    #     :raises PatchParseError: On unexpected EOF or malformed content lines.
    #     :returns: A tuple containing:
    #               1. list['HunkLine']: The parsed content lines.
    #               2. bool: original_has_newline (False if marker found for original file).
    #               3. bool: new_has_newline (False if marker found for new file).
    #     """
    #     lines: list[HunkLine] = []
    #     original_has_newline: bool = True
    #     new_has_newline: bool = True
    #     print("Linecounter: ", expected_line_count)
    #     # 1. Reading the expected content lines
    #     for _ in range(expected_line_count):
    #         line = self.file_handle.readline()
    #         if not line:
    #             raise PatchParseError("Unexpected EOF while reading expected hunk content lines.")
            
    #         try:
    #             hunk_line = HunkLine(line)
    #             lines.append(hunk_line)
    #         except PatchParseError as e:
    #             raise PatchParseError(f"Error parsing hunk content line {len(lines) + 1}: {e}")
        
    #     # 2. Checking the Newline Marker
    #     current_position = self.file_handle.tell()
    #     next_line_peek = self.file_handle.readline()
        
    #     if next_line_peek and next_line_peek.startswith('\\ No newline at end of file'):
    #         # Marker found: change status and consume the line.
    #         if lines:
    #             last_line = lines[-1]
    #             if last_line.is_context or last_line.is_deletion:
    #                 original_has_newline = False
    #             if last_line.is_context or last_line.is_addition:
    #                 new_has_newline = False
            
    #         # The file pointer is now correctly positioned after the marker.
    #     else:
    #         # No marker, we must reset the file pointer to re-read the line 
    #         # in the next iter_files loop iteration.
    #         self.file_handle.seek(current_position)
            
    #     return HunkContentData(lines, 
    #                            original_has_newline, 
    #                            new_has_newline)

################################
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
            dp(f"DEBUG: _peek_line {line=}")
            # Check for EOF first. An empty string means EOF.
            if not line:
                # EOF reached prematurely is an error if we haven't found a valid end marker yet.
                # raise PatchParseError("Unexpected EOF while reading expected hunk content lines.")
                break

            # KORRIGIERTE LOGIK: Explicitly check for next block headers before checking the prefix.
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
            dp(f"DEBUG: {line_to_process}")
            try:
                hunk_line = HunkLine(line_to_process)
                lines.append(hunk_line)
            except PatchParseError as e:
                raise PatchParseError(f"Error parsing hunk content line {len(lines) + 1}: {e}")
            except Exception as e: 
                # Dies fängt Fehler wie IndexError (z.B. wenn HunkLine[0] fehlschlägt) ab
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

        dp(f"DEBUG_HUNK: Successfully reached return. Lines found: {len(lines)}")    
        
        return HunkContentData(lines, 
                            original_has_newline, 
                            new_has_newline)


# Innerhalb der PatchParser-Klasse

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
             # Fehler: '+++' fehlt nach '---'. PatchFile ist fehlerhaft.
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


    def _strip_patch_path(self, path: str) -> str:
        """
        Strips 'a/', 'b/', and applies strip_count logic (which is assumed to be 0 
        in tests if not explicitly passed).
        """
        # 1. Strip 'a/' or 'b/' prefix (Standard Unified Diff Format)
        # if path.startswith("a/") or path.startswith("b/"):
        #     path = path[2:]
        
        # 2. Apply strip_count logic (optional, aber muss vorhanden sein)
        # Da der PatchParser das strip_count Argument nicht kennt, 
        # gehen wir davon aus, dass es hier nur um das b/ / a/ stripping geht.

        return path


# Innerhalb der PatchParser-Klasse

    def iter_files(self) -> Iterator[tuple[Path, Path, list[Hunk]]]:
        """
        Parses the patch file and yields the results for each file block.
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
                next_line: str | None = None 

                while True:
                    
                    # 1. FILE HEADER LOGIC: Extracts '---' and '+++'
                    o_path_str, n_path_str, found_file_block = self._parse_file_headers()

                    dp(f"DEBUG: {found_file_block=}")

                    if not found_file_block:
                        if hunks:
                            yield original_file_path, new_file_path, hunks
                        return  # EOF reached

                    # If we have hunks from the previous file block, yield them
                    dp(f"DEBUG: before yield {hunks=}")
                    if hunks:
                        yield original_file_path, new_file_path, hunks
                        hunks = [] # Reset for the new file block
                    
                    # Set the paths for the new file block
                    original_file_path = Path(o_path_str)
                    new_file_path = Path(n_path_str)                    

                    # 2. HUNK BLOCK LOGIC: Process '@@' headers
                    
                    # line = next_line or self._read_line()
                    # next_line = None
                    # line = self._peek_line()
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

                        dp(f"DEBUG: After parsing Hunkmetadata {self._current_line=}")


                        # b) Parse content lines (using helper method)
                        hunk_line_count = o_len + n_len
                        hunk_content_data = self._parse_hunk_content()

                        dp(f"DEBUG_ITER: Hunk content data received: {hunk_content_data}")

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
                if hunks:
                    yield original_file_path, new_file_path, hunks

        except FtwPatchError:
            raise
        except Exception as e:
            raise FtwPatchError(f"An unexpected error occurred during patch file parsing: {e}")

# --- FtwPatch (Main Application) ---

# Konstante für den /dev/null-Pfad, der von _clean_patch_path mit strip=0 
# zurückgegeben wird. Dieser Pfad muss vom Betriebssystem unabhängig sein.
DEV_NULL_PATH = Path("/dev/null") 


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

        # Proaktive Prüfung der Existenz der Patch-Datei
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

#ANCHOR - _nomalize_line
    def _normalize_line(self, file_line: FileLine, strip_prefix: bool = False) -> str:
        """
        Applies whitespace normalization rules based on CLI arguments.
        
        :param line: The line content from the file or the patch.
        :param strip_prefix: If True, strips the diff prefix (' ', '+', '-') 
                             from the patch line.
        :returns: The normalized line.
        """
        # Strip the diff prefix if present and requested
        #line = " ".join([file_line.prefix, file_line.content])
        line = "".join([file_line.prefix, file_line.content])
        if strip_prefix:
            line = file_line.content
        
        # Dominante Option: --ignore-all-ws
        if self.ignore_all_whitespace:
            # Remove all whitespace characters (including newlines, tabs, and spaces)
            # return "".join(line.split())
            return file_line.ignore_all_ws_content
        
        # Secondary options: --normalize-ws and --ignore-bl
        
        # Remove newline and carriage return at the end
        line = line.strip('\n\r') 

        # Ignore Blank Lines: If line is now empty after stripping, return empty string
        if self.ignore_blank_lines and not file_line.content.strip():
            return ''
        
        # Normalize non-leading whitespace
        if self.normalize_whitespace:
            # # We use re.match for leading whitespace and process the rest.
            # match = re.match(r'^\s*', line)
            # leading_ws = match.group(0) if match else ''
            # rest = line[len(leading_ws):]
            # # Normalize the rest: replace sequences of internal whitespace 
            # # with a single space.
            # rest_normalized = re.sub(r'[ \t\f\v]+', ' ', rest)
            # line = leading_ws + rest_normalized
            line = file_line.normalized_ws_content
        
        return line

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
        if patch_path == DEV_NULL_PATH:
            return DEV_NULL_PATH

        if strip_count >= len(cleaned_parts):
            raise FtwPatchError(
                f"Strip count ({strip_count}) is greater than or equal to the "
                f"number of pacleaned_th components ({len(cleaned_parts)}) in '{patch_path}'."
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
        dp("DEBUG: _apply_hunk_to_file start")
        # A. Initial checks and setup (omitted)
        
        # B. Hunk Application
        new_file_content = []
        # file_current_index is 0-based index corresponding to line number (hunk.original_start) - 1
        file_current_index = hunk.original_start - 1
        lines_consumed_in_original = 0
        
        # FINAL FIX 4a: NEW STATE for skip suppression (for test_ignore_bl_no_skip_on_blank_line_context)
        last_line_was_explicit_blank = False 
        
        hunk_line_index = 0
        
        dp(f"DEBUG: {hunk=}")

        for hunk_line in hunk.lines:
            #prefix = hunk_line[0]
            dp(f"DEBUG: for {hunk_line}")
            # 1. Check for Addition
            if hunk_line.is_addition:  # Addition line
                new_line_content = hunk_line.content
                
                # Ensure the line has a trailing newline if not present
                if not new_line_content.endswith(('\n', '\r')):
                    new_line_content += '\n'
                    
                new_file_content.append(new_line_content)
                dp(f"DEBUG: addition: {new_line_content}")
                dp(f"DEBUG: addition: {new_file_content}")
                # FINAL FIX 4b: Reset state, addition breaks context chain
                last_line_was_explicit_blank = False 

            # 2. Check for Deletion
            elif hunk_line.is_deletion:  # Deletion line
                #ANCHOR - hunklines
                # Normalize lines for comparison
                norm_hunk_line=self._normalize_line(hunk_line, True)
                #norm_hunk_line = self._normalize_line(hunk_line, strip_prefix=True)
                # if self.ignore_all_whitespace:
                #     norm_hunk_line = hunk_line.ignore_all_ws_content
                # elif self.ignore_blank_lines:
                #     norm_hunk_line = ''
                # elif self.normalize_whitespace:
                #     norm_hunk_line = hunk_line.normalized_ws_content


                # FINAL FIX 4b: Reset state, deletion breaks context chain
                last_line_was_explicit_blank = False 
                
                # FINAL FIX 3a: BLANK LINE SKIP LOGIC (for Deletion)
                # Skip only if ignore-bl is active AND the hunk expects a 
                # non-blank line to be deleted.
                if self.ignore_blank_lines and norm_hunk_line != '':
                    while file_current_index < len(original_lines) and original_lines[file_current_index].strip() == '':
                        # DO NOT append skipped line to new_file_content 
                        file_current_index += 1
                        lines_consumed_in_original += 1
                
                # --- MATCH CHECK ---
                if file_current_index >= len(original_lines):
                    raise FtwPatchError(f"Hunk mismatch on deletion line {hunk_line!r}: Found 'EOF'.")

                original_line = original_lines[file_current_index]
                norm_original_line = self._normalize_line(FileLine(original_line))
                # print("HO:", norm_hunk_line, flush=True)
                # print("NO:",norm_original_line, flush=True)
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
                norm_hunk_line = self._normalize_line(hunk_line, strip_prefix=True)
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

            else:
                # Should be caught by PatchParser.iter_files.
                raise PatchParseError(
                    f"Unexpected line prefix in hunk line: {hunk_line!r}"
                )
            
            hunk_line_index += 1

        # C. Append remaining lines
        new_file_content.extend(original_lines[file_current_index:])

        # D. Newline status correction
        if new_file_content and not hunk.new_has_newline:
            # rstrip removes '\n' or '\r\n'
            last_line = new_file_content[-1]
            new_file_content[-1] = last_line.rstrip('\n\r')
        dp(f"DEBUG: Before return {new_file_content=}")
        return new_file_content

    def run(self) -> int:
        """
        Main entry point for the patch application. 
        
        It encapsulates the core logic (apply_patch) and handles exceptions 
        to return the appropriate exit code.
        
        :returns: The exit code (0 for success, non-zero otherwise).
        """
        try:
            # Die gesamte Logik wurde in apply_patch ausgelagert
            return self.apply_patch(dry_run=self.dry_run)
            
        except FtwPatchError as e:
            # Wir gehen davon aus, dass FtwPatchError für Patch-Fehler
            # und Hunk-Mismatches verwendet wird, was zu einem Exit-Code 1 führen sollte.
            print(f"\nPatch failed: {e}")
            return 1
            
        except FileNotFoundError as e:
            # Behandelt Fehler, wenn eine Zieldatei während der Anwendung fehlt.
            print(f"\nFile Error during patching: {e}")
            return 1
            
        except Exception as e:
            # Allgemeine Fehlerbehandlung (z.B. IO-Fehler beim Schreiben)
            print(f"\nAn unexpected error occurred: {e}")
            return 2

    def apply_patch(self, dry_run: bool = False) -> int:
        """
        Applies the loaded patch to the target files.

        :param dry_run: If :py:obj:`True`, only simulate the patching process.
        :raises builtins.IOError: If an I/O error occurs during patch file reading or writing.
        :raises PatchParseError: If the patch file content is malformed.
        :raises FtwPatchError: If an error occurs during the application of the patch or path stripping.
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
        
        # 1. Iteriere über die geparsten Dateiblöcke und wende Hunks an
        for original_path, new_path, hunks in parser.iter_files():
            dp(f"DEBUG: return of iter_files: {hunks=}")
            # 2. Pfadbereinigung und Zielpfad-Ermittlung
            target_original_path = self._clean_patch_path(original_path)
            target_new_path = self._clean_patch_path(new_path)
            
            # Vollständige Pfade relativ zum Zielverzeichnis
            full_original_path = self.target_directory / target_original_path
            full_new_path = self.target_directory / target_new_path
            
            # Ausgabe der Dateiinformationen
            print(
                f"\n--- Processing file: {target_original_path!r} -> "
                f"{target_new_path!r} ({len(hunks)} hunks)"
            )
            
            # --- Spezialfall: Löschung (Original exists, New is /dev/null)
            if target_new_path == DEV_NULL_PATH:
                if not full_original_path.is_file():
                    raise FtwPatchError(
                        f"File to be deleted not found: {full_original_path!r}"
                    )
                # Markiere zur Löschung (keine Anwendung von Hunks notwendig)
                files_to_delete.append(full_original_path)
                applied_file_count += 1
                print(" -> Marked for deletion.")
                continue

            # --- Spezialfall: Erstellung (Original is /dev/null)
            if target_original_path == DEV_NULL_PATH:
                # Da die Datei nicht existiert, starten wir mit einem leeren Array
                # Die Hunks bestehen nur aus '+'-Zeilen und Kontext (' ').
                original_lines = []
            
            # --- Standardfall: Modifikation
            else:
                # Prüfe, ob die Originaldatei existiert
                if not full_original_path.is_file():
                    raise FtwPatchError(
                        f"Original file not found for patching: "
                        f"{full_original_path!r}"
                    )
                # Datei-Inhalt lesen
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

            # 4. Hunks sequenziell im Speicher anwenden
            current_lines = original_lines
            dp(f"DEBUG: {hunks=}")
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
            dp(f"DEBUG: {current_lines=}")
            # 5. Ergebnis im Speicher zwischenspeichern (nur wenn keine # Löschung)
            if target_new_path != DEV_NULL_PATH:
                patched_file_storage[full_new_path] = current_lines
                applied_file_count += 1
                print(
                    " -> Patch successfully verified and stored in "
                    f"memory ({len(current_lines)} lines)."
                )

        # ENDE DER ITERATION: Wenn wir hier ankommen, war der gesamte 
        # Patch-Vorgang fehlerfrei.
        
        # 6. Dateien schreiben und löschen (All-or-Nothing-Schreibphase)
        if not dry_run:
            print("\nStarting write/delete phase: Applying changes to " "file system...")
            
            # Zuerst Löschungen durchführen
            for file_path in files_to_delete:
                file_path.unlink()
                print(f" -> Successfully deleted {file_path!r}.")

            # Dann Änderungen schreiben
            for full_new_path, final_content in patched_file_storage.items():
                try:
                    # Sicherstellen, dass das übergeordnete Verzeichnis existiert
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
        else:
            print("\nDry run completed. No files were modified.")
        
        print(f"\nSuccessfully processed {applied_file_count} file changes.")
        return 0


# --- CLI Entry Point ---

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
    # 1. Argument Parser initialisieren (Annahme: _get_argparser() ist definiert)
    parser = _get_argparser() 
    
    # 2. Argumente parsen
    args = parser.parse_args()

    # 3. Fehlerbehandlung und Ausführung
    try:
        # Das 'dry_run' Argument muss korrekt aus args extrahiert werden
        dry_run = getattr(args, 'dry_run', False)

        # Die FtwPatch-Klasse kapselt die gesamte Logik
        patcher = FtwPatch(args=args)
        
        # apply_patch() führt die gesamte Patch-Logik aus
        exit_code = patcher.apply_patch(dry_run=dry_run)
        
        return exit_code
        
    except FileNotFoundError as e:
        # Fehler bei nicht gefundenen Dateien (Patch- oder Target-Datei)
        print(f"File System Error: {e}", file=sys.stderr)
        return 1
        
    except FtwPatchError as e:
        # Anwendungsinterne Fehler (z.B. Parse Error, Hunk Mismatch, Strip Count)
        print(f"An ftw_patch error occurred: {e}", file=sys.stderr)
        return 1
        
    except Exception as e:
        # Unerwartete Fehler
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    from doctest import testfile, FAIL_FAST
    from pathlib import Path
    # Fügt das Root-Verzeichnis des Projekts (das Modul-Quellverzeichnis)
    # am Anfang von sys.path hinzu.
    project_root = Path(__file__).resolve().parent.parent
    print(project_root)
    sys.path.insert(0, str(project_root))    
    be_verbose=False
    be_verbose=True
    option_flags= 0
    option_flags= FAIL_FAST
    testfilesbasedir = Path("../../doc/source/devel")
    test_sum = 0
    test_failed = 0
    dt_file = str(testfilesbasedir / "get_started_ftw_patch.rst")
    # dt_file = str(testfilesbasedir / "temp_test.rst")
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