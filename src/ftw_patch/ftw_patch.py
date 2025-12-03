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
        original_file_path: Path = Path()
        new_file_path: Path = Path()
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

                    # 1. Identify File Header '---'
                    if line.startswith('--- '):
                        # Extract original path
                        path_part = line.strip().split(' ', 1)[1].split('\t')[0]
                        original_file_path = Path(path_part)
                        continue
                    
                    # 2. Identify File Header '+++'
                    elif line.startswith('+++ '):
                        # Extract new path
                        path_part = line.strip().split(' ', 1)[1].split('\t')[0]
                        new_file_path = Path(path_part)
                        
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
                                    # Sollte in einem wohlgeformten Diff nicht 
                                    # vorkommen.
                                    original_has_newline = False
                                    new_has_newline = False
                                else:
                                    last_prefix = current_hunk_lines[-1][0]
                                    
                                    # Wenn die letzte Zeile eine Löschung ('-') 
                                    # oder Kontext (' ') war, fehlte der Newline 
                                    # in der ORIGINALDATEI.
                                    if last_prefix in ('-', ' '):
                                        original_has_newline = False
                                        
                                    # Wenn die letzte Zeile eine Hinzufügung ('+') 
                                    # oder Kontext (' ') war, fehlt der Newline 
                                    # in der NEUEN DATEI.
                                    if last_prefix in ('+', ' '):
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
                        original_file_path = Path()
                        new_file_path = Path()
                        hunks = []
                        
                # 5. Handle EOF: Yield the last collected file patch if any 
                # hunks were found
                if new_file_path and hunks:
                    yield original_file_path, new_file_path, hunks

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

    Es implementiert das PIMPLE-Idiom, indem es das Namespace-Objekt
    speichert und die Argumente über Getter bereitstellt.
    """
    def __init__(self, args: Namespace) -> None:
        """
        Initializes the FtwPatch instance by storing the parsed command-line 
        arguments.

        :param args: The Namespace object returned by 
                     :py:func:`argparse.ArgumentParser.parse_args()`.
                     Must contain attributes: patch_file (Path), strip_count 
                     (int), target_directory (Path), normalize_whitespace 
                     (bool), ignore_blank_lines (bool), 
                     ignore_all_whitespace (bool).
        :raises builtins.FileNotFoundError: If the patch file does not exist 
                                            (checked proaktiv).
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
        The path to the patch or diff file (**ro**).

        :returns: The path object for the patch file.
        """
        return self._args.patch_file

    @property
    def strip_count(self) -> int:
        """
        The number of leading path components to strip from file names (**ro**).

        :returns: The strip count value.
        """
        return self._args.strip_count

    @property
    def target_directory(self) -> Path:
        """
        The directory containing the files to be patched (**ro**).

        :returns: The target directory path.
        """
        return self._args.target_directory
    
    @property
    def normalize_whitespace(self) -> bool:
        """
        Indicates if non-leading whitespace should be normalized (**ro**).

        :returns: The normalization status.
        """
        return self._args.normalize_whitespace
    
    @property
    def ignore_blank_lines(self) -> bool:
        """
        Indicates if pure blank lines should be ignored or normalized (**ro**).

        :returns: The ignore status.
        """
        return self._args.ignore_blank_lines

    @property
    def ignore_all_whitespace(self) -> bool:
        """
        Indicates if all whitespace differences should be completely ignored 
        (**ro**).

        :returns: The ignore status.
        """
        return self._args.ignore_all_whitespace

    def _normalize_line(self, line: str, strip_prefix: bool = False) -> str:
        """
        Applies whitespace normalization rules based on CLI arguments.
        
        :param line: The line content from the file or the patch.
        :param strip_prefix: If True, strips the diff prefix (' ', '+', '-') 
                             from the patch line.
                             Default is False, da dies die Normalisierung von 
                             Zieldateizeilen erleichtert.
        :returns: The normalized line.
        """
        # Strip the diff prefix if present and requested
        if strip_prefix and line.startswith((' ', '+', '-')):
            line = line[1:]
        
        # Dominante Option: --ignore-all-ws
        if self.ignore_all_whitespace:
            # Entferne alle Whitespace-Zeichen (einschließlich Newlines, Tabs 
            # und Leerzeichen)
            return "".join(line.split())
        
        # Sekundäre Optionen: --normalize-ws und --ignore-bl
        
        # Newline und Carriage Return am Ende entfernen
        line = line.strip('\n\r') 

        # Ignore Blank Lines
        if self.ignore_blank_lines and not line.strip():
            # Eine leere Zeile wird zu einem leeren String normalisiert (''). 
            # Dies ist das Token, das im Hunk-Matching verwendet wird, um 
            # alle Leerzeilen als identisch zu behandeln, was die Toleranz 
            # für die Anzahl aufeinanderfolgender Leerzeilen ermöglicht.
            return ''
             
        # Whitespace Normalization (außer führender Whitespace)
        if self.normalize_whitespace:
            # Wir verwenden re.split für Whitespace am Anfang und verarbeiten 
            # dann den Rest.
            match = re.match(r'^\s*', line)
            leading_ws = match.group(0) if match else ''
            rest = line[len(leading_ws):]
            
            # Normalisiere den Rest: Ersetze alle inneren Whitespace-Sequenzen 
            # durch ein einzelnes Leerzeichen.
            rest_normalized = re.sub(r'[ \t\f\v]+', ' ', rest)
            line = leading_ws + rest_normalized
        
        return line

    def _clean_patch_path(self, patch_path: Path) -> Path:
        """
        Applies the strip count to a path found in the patch file and returns 
        the final target path relative to the target directory.

        :param patch_path: The path extracted from the '---' or '+++' line.
        :raises FtwPatchError: If the strip count is too large for the given 
                               path.
        :returns: The path to the file relative to the target directory.
        """
        parts = patch_path.parts
        strip_count = self.strip_count
        
        # Sonderfall /dev/null wird immer ohne Stripping zurückgegeben.
        if patch_path == DEV_NULL_PATH:
            return DEV_NULL_PATH
            
        if strip_count >= len(parts):
            raise FtwPatchError(
                f"Strip count ({strip_count}) is greater than or equal to the "
                f"number of path components ({len(parts)}) in '{patch_path}'."
            )
            
        cleaned_path = Path(*parts[strip_count:])
        return cleaned_path
        
    def _apply_hunk_to_file(self, 
                            file_path: Path, 
                            hunk: Hunk, 
                            original_lines: list[str]) -> list[str]:
        """
        Applies a single hunk's changes to the provided list of file lines.

        :param file_path: The full path to the file being patched (for error 
                          messages).
        :param hunk: The Hunk object containing the change details.
        :param original_lines: The list of lines (content) of the original 
                               file.
        :raises FtwPatchError: If the hunk cannot be applied (e.g., context 
                               mismatch or line number out of bounds).
        :returns: The modified list of lines after applying the hunk.
        """
        
        # Hunk-Zeilennummern sind 1-basiert, Listenindizes sind 0-basiert.
        hunk_start_index = hunk.original_start - 1
        
        if hunk_start_index < 0 or \
           hunk_start_index + hunk.original_length > len(original_lines):
            raise FtwPatchError(
                f"Hunk (starts at line {hunk.original_start}, length "
                f"{hunk.original_length}) is out of bounds for file "
                f"'{file_path}' (length {len(original_lines)})."
            )

        # 1. Kontext- und Deletions-Prüfung (Matching)
        hunk_line_index = 0
        file_current_index = hunk_start_index
        
        # Wir sammeln die zu behaltenden (Context) und hinzuzufügenden (Added) 
        # Zeilen
        new_file_content: list[str] = original_lines[:hunk_start_index]
        
        # Wir iterieren über die Zeilen im Hunk
        while hunk_line_index < len(hunk.lines):
            hunk_line = hunk.lines[hunk_line_index]
            prefix = hunk_line[0]
            
            if prefix == ' ': # Kontextzeile
                
                # Normalisierung der Hunk-Zeile
                norm_hunk_line = self._normalize_line(hunk_line, 
                                                      strip_prefix=True)
                
                # --- Blank Line Tolerance (Skip-Ahead) Logik ---
                # Wenn wir BLANK LINES ignorieren sollen und die Hunk-Zeile 
                # eine INHALTSzeile erwartet (norm_hunk_line != '').
                if self.ignore_blank_lines and norm_hunk_line != '':
                    
                    # Solange die aktuelle Zeile in der Zieldatei nur Leerzeile 
                    # ist, überspringen wir sie, da der Hunk eine Inhaltszeile 
                    # erwartet.
                    while file_current_index < len(original_lines):
                        original_line_for_check = original_lines[file_current_index]
                        norm_original_for_check = self._normalize_line(
                            original_line_for_check, strip_prefix=False
                        )
                        
                        if norm_original_for_check == '':
                            # Eine unerwartete Leerzeile im Original gefunden 
                            # (merging/collapsing). Überspringen.
                            file_current_index += 1
                            
                            # Wir müssen hier sicherstellen, dass wir 
                            # nicht über das Ende des Hunk-Bereichs hinausgehen
                            if file_current_index >= hunk_start_index + hunk.original_length:
                                # Wir haben eine Leerzeile übersprungen, die 
                                # außerhalb des ursprünglichen Hunk-Bereichs liegt.
                                # Dies deutet auf einen Fehler oder einen 
                                # zu aggressiven Skip hin. Wir brechen ab.
                                raise FtwPatchError(
                                    f"Skipped blank line in file '{file_path}' at "
                                    f"line {file_current_index}, exceeding hunk bounds."
                                )
                                
                        else:
                            # Die nächste Inhaltszeile im Original gefunden. 
                            break
                # --- Ende Blank Line Tolerance Logik ---
                
                
                # Überprüfe, ob wir noch Zeilen in der Originaldatei haben
                if file_current_index >= len(original_lines):
                    raise FtwPatchError(
                        f"End of file reached unexpectedly in file '{file_path}' "
                        f"at expected line {file_current_index + 1} while matching hunk."
                    )
                
                # Jetzt die Zeile holen, die entweder matchen soll oder zu 
                # Mismatch führt
                original_line = original_lines[file_current_index]
                norm_original_line = self._normalize_line(original_line, 
                                                          strip_prefix=False)
                
                if norm_hunk_line != norm_original_line:
                    # Mismatch! Der Patch kann nicht angewendet werden.
                    raise FtwPatchError(
                        f"Context mismatch in file '{file_path}' at expected "
                        f"line {file_current_index + 1}: Expected "
                        f"'{norm_hunk_line!r}', found '{norm_original_line!r}'."
                    )
                
                # Kontextzeile ist korrekt, füge sie dem neuen Inhalt hinzu 
                # (mit der Originalzeile).
                new_file_content.append(original_line)
                file_current_index += 1
                
            elif prefix == '-': # Zu löschende Zeile
                # Hunk-Zeile für den Vergleich vorbereiten
                norm_hunk_line = self._normalize_line(hunk_line, 
                                                      strip_prefix=True)
                
                # --- Blank Line Tolerance (Skip-Ahead) Logik ---
                # Wie oben, aber gilt hier für eine zu LÖSCHENDE Zeile.
                if self.ignore_blank_lines and norm_hunk_line != '':
                    while file_current_index < len(original_lines):
                        original_line_for_check = original_lines[file_current_index]
                        norm_original_for_check = self._normalize_line(
                            original_line_for_check, strip_prefix=False
                        )
                        
                        if norm_original_for_check == '':
                            # Eine unerwartete Leerzeile im Original gefunden. 
                            # Überspringen (wird nicht in den neuen Inhalt 
                            # aufgenommen).
                            file_current_index += 1
                            if file_current_index >= hunk_start_index + hunk.original_length:
                                raise FtwPatchError(
                                    f"Skipped blank line in file '{file_path}' at "
                                    f"line {file_current_index}, exceeding hunk bounds."
                                )
                        else:
                            break
                # --- Ende Blank Line Tolerance Logik ---
                
                
                # Standard-Matching (mit dem möglicherweise übersprungenen Index)
                if file_current_index >= len(original_lines):
                    raise FtwPatchError(
                        f"End of file reached unexpectedly in file '{file_path}' "
                        f"at expected line {file_current_index + 1} while matching hunk."
                    )
                    
                    
                original_line = original_lines[file_current_index]
                norm_original_line = self._normalize_line(original_line, 
                                                          strip_prefix=False)

                if norm_hunk_line != norm_original_line:
                    # Mismatch! Der Patch kann nicht angewendet werden.
                    raise FtwPatchError(
                        f"Deletion mismatch in file '{file_path}' at line "
                        f"{file_current_index + 1}: Expected to delete "
                        f"'{norm_hunk_line!r}', but found "
                        f"'{norm_original_line!r}'."
                    )
                
                # Zeile wird gelöscht, nicht zum neuen Inhalt hinzugefügt.
                file_current_index += 1
                
            elif prefix == '+': # Hinzuzufügende Zeile
                # 2. Füge die neue Zeile zum Inhalt hinzu.
                new_line_content = hunk_line[1:]
                
                # Stelle sicher, dass die Zeile ein Newline-Zeichen enthält, 
                # falls es fehlt (dies gilt nur für hinzugefügte Zeilen)
                if not new_line_content.endswith(('\n', '\r')):
                    new_line_content += '\n'
                    
                new_file_content.append(new_line_content)
                
            else:
                # Sollte durch PatchParser.iter_files abgefangen werden.
                 raise PatchParseError(
                     f"Unexpected line prefix in hunk line: {hunk_line!r}"
                 )

            hunk_line_index += 1
            
        # 3. Füge den Rest der Originaldatei hinzu
        new_file_content.extend(original_lines[file_current_index:])
        
        # 4. Newline-Status der neuen Datei korrigieren
        if new_file_content and not hunk.new_has_newline:
            # rstrip entfernt '\n' oder '\r\n'
            last_line = new_file_content[-1]
            new_file_content[-1] = last_line.rstrip('\n\r')
        
        return new_file_content

    def apply_patch(self, dry_run: bool = False) -> int:
        """
        Applies the loaded patch to the target files.

        :param dry_run: If :py:obj:`True`, only simulate the patching process.
        :raises builtins.IOError: If an I/O error occurs during patch file 
                                  reading or writing.
        :raises PatchParseError: If the patch file content is malformed.
        :raises FtwPatchError: If an error occurs during the application of 
                               the patch or path stripping.
        :returns: The exit code, typically 0 for success.
        """
        parser = PatchParser(self.patch_file_path) 

        print(
            f"Applying patch from {self.patch_file_path!r} in directory "
            f"{self.target_directory!r} (strip={self.strip_count}, ws_norm="
            f"{self.normalize_whitespace}, bl_ignore={self.ignore_blank_lines}, "
            f"ws_all_ignore={self.ignore_all_whitespace}, dry_run: {dry_run})"
        )
        
        # Struktur zum Speichern der erfolgreich gepatchten Inhalte im Speicher 
        # (All-or-Nothing)
        # Key: Path (full_new_path), Value: list[str] (der neue Inhalt)
        patched_file_storage: dict[Path, list[str]] = {}
        files_to_delete: list[Path] = [] 
        applied_file_count = 0
        
        try:
            for original_patch_path, new_patch_path, hunks in \
                parser.iter_files():
                
                # Pfadberechnung
                target_original_path = self._clean_patch_path(
                    original_patch_path
                )
                target_new_path = self._clean_patch_path(new_patch_path)
                
                full_original_path = self.target_directory / target_original_path
                full_new_path = self.target_directory / target_new_path

                print(f"\nProcessing file: {target_original_path} -> "
                      f"{target_new_path} ({len(hunks)} hunks)")
                
                
                # 1. Dateierstellung (--- /dev/null)
                if target_original_path == DEV_NULL_PATH:
                    if not target_new_path == DEV_NULL_PATH:
                        print("  -> File creation detected.")
                    original_lines = []
                    
                # 2. Dateilöschung (+++ /dev/null)
                elif target_new_path == DEV_NULL_PATH:
                    print("  -> File deletion detected.")
                    
                    if not full_original_path.is_file():
                        # Bei einer Löschung muss die Originaldatei existieren
                        raise FileNotFoundError(
                            "Cannot delete file that does not exist: "
                            f"{full_original_path!r}"
                        )
                        
                    # Markiere die Datei zum Löschen und überspringe die 
                    # Hunk-Anwendung
                    files_to_delete.append(full_original_path)
                    applied_file_count += 1
                    print(
                        "  -> Successfully verified for deletion: "
                        f"{full_original_path!r}."
                    )
                    continue # Springe zur nächsten Datei/nächsten Iteration
                    
                # 3. Datei-Änderung (Standardfall)
                else: 
                    # Prüfe, ob die Zieldatei zum Patchen existiert
                    if not full_original_path.is_file():
                        raise FileNotFoundError(
                            "Target file not found for patching: "
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
                        f"  - Applying Hunk {i+1}/{len(hunks)} "
                        f"(@ Line {hunk.original_start}: "
                        f"{hunk.original_length} -> {hunk.new_length})"
                    )
                    
                    current_lines = self._apply_hunk_to_file(
                        file_path=full_original_path, 
                        hunk=hunk, 
                        original_lines=current_lines
                    )

                # 5. Ergebnis im Speicher zwischenspeichern (nur wenn keine 
                # Löschung)
                if target_new_path != DEV_NULL_PATH:
                    patched_file_storage[full_new_path] = current_lines
                    applied_file_count += 1
                    print(
                        "  -> Patch successfully verified and stored in "
                        f"memory ({len(current_lines)} lines)."
                    )


            # ENDE DER ITERATION: Wenn wir hier ankommen, war der gesamte 
            # Patch-Vorgang fehlerfrei.
            
            # 6. Dateien schreiben und löschen (All-or-Nothing-Schreibphase)
            if not dry_run:
                print("\nStarting write/delete phase: Applying changes to "
                      "file system...")
                
                # Zuerst Löschungen durchführen
                for file_path in files_to_delete:
                    file_path.unlink()
                    print(f"  -> Successfully deleted {file_path!r}.")

                # Dann Änderungen schreiben
                for full_new_path, final_content in patched_file_storage.items():
                    # Sicherstellen, dass das Zielverzeichnis existiert
                    full_new_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Inhalt in die Zieldatei schreiben
                    # Da die letzte Zeile ggf. kein Newline enthält, 
                    # verwenden wir writelines() oder schreiben den Inhalt 
                    # direkt als String
                    with full_new_path.open(
                        mode="w", encoding="utf-8", errors="replace"
                    ) as f:
                        f.writelines(final_content)
                        
                    print(f"  -> Successfully wrote {full_new_path!r}.")
            else:
                 print("\nPatch run finished successfully in dry-run mode.")
            
            print(f"\nSuccessfully processed {applied_file_count} changes.")
            return 0 # Success exit code

        # Fehlerbehandlung: bricht vor dem Schreiben ab
        except FileNotFoundError as e:
            print(f"\nError: {e}")
            return 1
        except IOError as e:
            print(f"\nFatal I/O Error: {e}")
            return 1
        except PatchParseError as e:
            print(f"\nPatch Parsing Error: {e}")
            return 1
        except FtwPatchError as e:
            print(f"\nPatch Application Error: {e}")
            return 1
            
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            return 1


def cli_parse_ftw_patch() -> ArgumentParser:
    """
    Creates the parser for the ``ftwpatch`` command-line interface.

    :returns: Command-line interface parser with all options ready to
              parse ``sys.args``.
    """
    parser = ArgumentParser(
        prog="ftwpatch",
        description="Ein Unicode resistenter Ersatz für patch."
    )
    
    parser.add_argument(
        "patch_file",
        type=Path,
        help="Path to the patch or diff file to be applied. If '-' is given, "
             "patch is read from stdin.",
    )
    
    # Standard patch options
    parser.add_argument(
        "-p", "--strip",
        type=int,
        default=0,
        dest="strip_count",
        help=(
            "Set the number of leading path components to strip from file names "
            "before trying to find the file. Default is 0."
        ),
    )
    
    parser.add_argument(
        "-d", "--directory",
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
            "This implements a skip-ahead logic to tolerate differences in the "
            "count of consecutive blank lines."
        ),
    )

    parser.add_argument(
        "--ignore-all-ws",
        action="store_true",
        dest="ignore_all_whitespace",
        help=(
            "Completely ignore all whitespace characters when comparing lines. "
            "This is a last resort for non-whitespace-sensitive languages "
            "(e.g., C, Java) to ignore formatting differences. This option is "
            "dominant."
        ),
    )
    
    return parser


def prog_ftw_patch(): # pyright: ignore[reportUndefinedVariable]
    """
    Function that represents the program defined
    in pyproject.toml under [project.scripts].

    It handles parsing command-line arguments and executing the
    main program logic.
    """
    parser = cli_parse_ftw_patch()
    
    # Placeholder for argparse.Namespace since we don't execute sys.args here
    class MockNamespace(object):
        """Placeholder for argparse.Namespace"""
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
        def __repr__(self):
            return f"MockNamespace(" \
                   f"{', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())}" \
                   f")"


    # Placeholder for demonstrating FtwPatch usage with full options
    mock_args = MockNamespace(
        patch_file=Path("testdata/my_feature.diff"), # Dummy path for demo
        strip_count=1, 
        target_directory=Path("src"),
        normalize_whitespace=False,
        ignore_blank_lines=False,
        ignore_all_whitespace=True,
    )
    
    try:
        # Übergabe des gesamten Namespace-Objekts (PIMPLE-Idiom)
        patcher = FtwPatch(args=mock_args)
        
        # apply_patch wird aufgerufen, FileNotFoundError wird bereits im __init__ 
        # abgefangen.
        exit_code = patcher.apply_patch(dry_run=True) 
        print(f"Program finished with exit code: {exit_code}")
    except FileNotFoundError as e:
        print(f"File System Error: {e}")
        exit(1)
    except FtwPatchError as e:
        print(f"An ftw_patch error occurred: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)


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
        str(testfilesbasedir / "get_started_ftw_patch.rst"),
        verbose=be_verbose,
        optionflags=option_flags,
    )
    test_sum += doctestresult.attempted
    if doctestresult.failed:
        print(f"Total tests run: {test_sum}" )
        exit(1)