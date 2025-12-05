"""
FTW Patch
===============================

| File: ftw_patch/ftw_patch.py
| Author: Fitzz TeXnik Welt
| Email: FitzzTeXnikWelt@t-online.de

Ein Unicode resistenter Ersatz für patch.


"""
from argparse import ArgumentParser, Namespace
from pathlib import Path
from dataclasses import dataclass 
import sys
from typing import Iterator, TextIO
import re

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
    lines: list[str]
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
        if not patch_file_path.is_file():
            raise FileNotFoundError(f"Patch file not found: {patch_file_path}")
        
        self._patch_file_path = patch_file_path

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}" \
               f"(patch_file_path={self._patch_file_path!r})"


    def _strip_patch_path(self, path: str) -> str:
        """
        Strips 'a/', 'b/', and applies strip_count logic (which is assumed to be 0 
        in tests if not explicitly passed).
        """
        # 1. Strip 'a/' or 'b/' prefix (Standard Unified Diff Format)
        if path.startswith("a/") or path.startswith("b/"):
            path = path[2:]
        
        # 2. Apply strip_count logic (optional, aber muss vorhanden sein)
        # Da der PatchParser das strip_count Argument nicht kennt, 
        # gehen wir davon aus, dass es hier nur um das b/ / a/ stripping geht.

        return path


    def iter_files(self) -> Iterator[tuple[Path, Path, list[Hunk]]]:
        """
        Iterates over the files defined in the patch.

        This method reads the patch file, identifies the file boundaries, 
        collects all hunks for one file change, and yields the result.

        :raises PatchParseError: If the patch file format is invalid.
        :raises builtins.IOError: If an I/O error occurs during file reading.
        :returns: An iterator yielding tuples of (original_path, new_path, 
                  list_of_hunks).
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
                
                # Variable to store a line that was read but belongs to the 
                # next block
                next_line: str | None = None 

                while True:
                    
                    if next_line:
                        line = next_line
                        next_line = None
                    else:
                        line = file_handle.readline()

                    if not line: # EOF reached
                        break
                    # Ignore all lines that start with 'diff ' or '#'
                    if not original_file_path and line.startswith(('diff ', '#', 'index ', '\n')):
                        continue

                    # 1. Identify File Header '---'
                    if line.startswith('--- '):

                        if original_file_path is not None:
                            # Ausgabe des fertigen Blocks
                            yield (
                                original_file_path,  # Path-Objekt
                                new_file_path,       # Path-Objekt
                                hunks,
                            )
                            # Zurücksetzen für den nächsten Block
                            hunks = []
                            
                        # Setze den neuen original_file_path
                        path_str = self._strip_patch_path(line[4:].rstrip('\n\r'))
                        original_file_path = Path(path_str)

                    
                    # 2. Identify File Header '+++'
                    elif line.startswith('+++ '):
                        # Extract new path
                        path_part_raw = line.strip().split(' ', 1)[1].split('\t')[0]
                        # FIX: Pfad strippen, bevor Path-Objekt erstellt wird
                        path_str = self._strip_patch_path(path_part_raw)
                        new_file_path = Path(path_str)
                        
                        if not original_file_path:
                            raise PatchParseError(
                                "Found '+++' line without preceding '---' line."
                            )
                            
                        # Reset hunks list for the new file
                        hunks = [] 
                        continue
                   
                    # 3. Identify Hunk Header '@@ ... @@'
                    elif line.startswith('@@ '):
                        if not new_file_path:
                            raise PatchParseError(
                                "Found hunk header '@@' before '+++' file "
                                "definition."
                            )
                            
                        match = self._HUNK_HEADER_RE.match(line)
                        if not match:
                            raise PatchParseError(
                                f"Malformed hunk header found: {line.strip()}"
                            )
                            
                        # Extract start/length values. Default length to 1 if 
                        # missing
                        o_start, o_len_str, n_start, n_len_str = match.groups()
                        o_len = int(o_len_str or 1)
                        n_len = int(n_len_str or 1)
                        
                        current_hunk_lines: list[str] = []
                        original_has_newline: bool = True
                        new_has_newline: bool = True
                        
                        # --- START HUNK LINE CONSUMPTION ---
                        while True:
                            hunk_line = file_handle.readline()
                            if not hunk_line: # EOF while reading hunk content
                                break
                            
                            # Hunk content lines: context (' '), added ('+'), or 
                            # removed ('-')
                            if hunk_line.startswith((' ', '+', '-')):
                                current_hunk_lines.append(hunk_line)
                            
                            # Special case: No newline at end of file metadata
                            elif hunk_line.startswith(
                                    '\\ No newline at end of file'
                            ):
                                if not current_hunk_lines:
                                    original_has_newline = False
                                    new_has_newline = False
                                else:
                                    # Check if the hunk affected the original or the new file content.
                                    # Check for deletion ('-') or context (' ')
                                    affects_original = any(line.startswith(('-', ' ')) for line in current_hunk_lines)
                                    # Check for addition ('+') or context (' ')
                                    affects_new = any(line.startswith(('+', ' ')) for line in current_hunk_lines)
                                    
                                    if affects_original:
                                        original_has_newline = False
                                        
                                    if affects_new:
                                        new_has_newline = False
                                        
                                continue
                            
                            # Check for the start of the next block: new hunk, 
                            # new file, or end of diff
                            elif hunk_line.startswith(('@@ ', '--- ', 'diff ')):
                                # This line belongs to the next block. Put it 
                                # back for the main loop.
                                next_line = hunk_line
                                break
                            
                            else:
                                # Ignore other metadata lines inside the diff 
                                continue 
                        # --- END HUNK LINE CONSUMPTION ---

                        # Create and append Hunk
                        hunk = Hunk(
                            original_start=int(o_start),
                            original_length=o_len,
                            new_start=int(n_start),
                            new_length=n_len,
                            lines=current_hunk_lines,
                            original_has_newline=original_has_newline,
                            new_has_newline=new_has_newline
                        )
                        hunks.append(hunk)
                        
                        # Start the main loop iteration again (either with 
                        # next_line or a fresh read)
                        continue 


                    # 4. Handle end of a file block (e.g., empty lines or 
                    # other headers before next '---')
                    elif line.startswith('diff ') and new_file_path:
                        # Found the start of the next diff, yield the current 
                        # file's hunks
                        yield original_file_path, new_file_path, hunks
                        # Reset state for the new file block
                        original_file_path = None
                        new_file_path = None
                        hunks = []
                        
                # 5. Handle EOF: Yield the last collected file patch if any 
                # hunks were found
                
                if original_file_path is not None:
                    # Ausgabe des fertigen Blocks
                    yield (
                        original_file_path,
                        new_file_path,      
                        hunks,
                    )
                    # Zurücksetzen für den nächsten Block
                    hunks = []
                    

        except IOError as e:
            # Catch I/O errors (e.g., encoding problems, read errors)
            raise IOError(
                f"Error reading patch file '{self._patch_file_path.name}': {e}"
            )
        except Exception as e:
            # Catch other unexpected parsing issues and wrap them
            if not isinstance(e, PatchParseError):
                 raise PatchParseError(
                     f"Unexpected error during patch parsing: {e}"
                 )
            raise # Re-raise if it was already a PatchParseError

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

    def _normalize_line(self, line: str, strip_prefix: bool = False) -> str:
        """
        Applies whitespace normalization rules based on CLI arguments.
        
        :param line: The line content from the file or the patch.
        :param strip_prefix: If True, strips the diff prefix (' ', '+', '-') 
                             from the patch line.
        :returns: The normalized line.
        """
        # Strip the diff prefix if present and requested
        if strip_prefix and line.startswith((' ', '+', '-')):
            line = line[1:]
        
        # Dominante Option: --ignore-all-ws
        if self.ignore_all_whitespace:
            # Remove all whitespace characters (including newlines, tabs, and spaces)
            return "".join(line.split())
        
        # Secondary options: --normalize-ws and --ignore-bl
        
        # Remove newline and carriage return at the end
        line = line.strip('\n\r') 

        # Ignore Blank Lines: If line is now empty after stripping, return empty string
        if self.ignore_blank_lines and not line.strip():
            return ''
        
        # Normalize non-leading whitespace
        if self.normalize_whitespace:
            # We use re.match for leading whitespace and process the rest.
            match = re.match(r'^\s*', line)
            leading_ws = match.group(0) if match else ''
            rest = line[len(leading_ws):]
            # Normalize the rest: replace sequences of internal whitespace 
            # with a single space.
            rest_normalized = re.sub(r'[ \t\f\v]+', ' ', rest)
            line = leading_ws + rest_normalized
        
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
        
        # Special case /dev/null is always returned without stripping.
        if patch_path == DEV_NULL_PATH:
            return DEV_NULL_PATH

        if strip_count >= len(parts):
            raise FtwPatchError(
                f"Strip count ({strip_count}) is greater than or equal to the "
                f"number of path components ({len(parts)}) in '{patch_path}'."
            )
        
        cleaned_path = Path(*parts[strip_count:])
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
        
        # FINAL FIX 4a: NEW STATE for skip suppression (for test_ignore_bl_no_skip_on_blank_line_context)
        last_line_was_explicit_blank = False 
        
        hunk_line_index = 0
        for hunk_line in hunk.lines:
            prefix = hunk_line[0]
            
            # 1. Check for Addition
            if prefix == '+':  # Addition line
                new_line_content = hunk_line[1:]
                
                # Ensure the line has a trailing newline if not present
                if not new_line_content.endswith(('\n', '\r')):
                    new_line_content += '\n'
                    
                new_file_content.append(new_line_content)
                
                # FINAL FIX 4b: Reset state, addition breaks context chain
                last_line_was_explicit_blank = False 

            # 2. Check for Deletion
            elif prefix == '-':  # Deletion line
                
                # Normalize lines for comparison
                norm_hunk_line = self._normalize_line(hunk_line, strip_prefix=True)

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
                norm_original_line = self._normalize_line(original_line)
                
                if norm_original_line != norm_hunk_line:
                    raise FtwPatchError(
                        f"Hunk mismatch on deletion line {hunk_line!r}: "
                        f"Expected '{norm_hunk_line!r}', found '{norm_original_line!r}'."
                    )
                
                # Match successful: Line is removed by skipping append
                file_current_index += 1
                lines_consumed_in_original += 1
                
            # 3. Check for Context
            elif prefix == ' ':  # Context line
                
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
                norm_original_line = self._normalize_line(original_line) 
                
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

        return new_file_content

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
        help="Do not write changes to the file system; only simulate the process."
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
    be_verbose=False
    be_verbose=True
    option_flags= 0
    option_flags= FAIL_FAST
    testfilesbasedir = Path("../../docs/source/devel")
    test_sum = 0
    doctestresult = testfile(
        str(testfilesbasedir / "get_argparser.rst"),
        optionflags=option_flags,
        verbose=be_verbose,
    )
    test_sum += doctestresult.failed
    
    doctestresult = testfile(
        str(testfilesbasedir / "ftw_patch.rst"),
        optionflags=option_flags,
        verbose=be_verbose,
    )
    test_sum += doctestresult.failed
    
    if test_sum == 0:
        print(f"DocTests passed without errors, {test_sum} tests.")
    else:
        print(f"DocTests failed: {test_sum} tests.")