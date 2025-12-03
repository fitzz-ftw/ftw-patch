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
    :returns: None
    """
    original_start: int
    original_length: int
    new_start: int
    new_length: int
    lines: list[str]


# --- Exceptions ---

class FtwPatchError(Exception):
    """
    Base exception for all errors raised by the :py:mod:`ftw_patch` module.

    **Inheritance Hierarchy**
        * :py:class:`FtwPatchError`
        * :py:class:`builtins.Exception`
    """
    def __repr__(self) -> str:
        """
        Returns a string representation of the object.
        """
        return f"{self.__class__.__name__}()"


class PatchParseError(FtwPatchError):
    """
    Exception raised when an error occurs during the parsing of the patch file content.

    **Inheritance Hierarchy**
        * :py:class:`PatchParseError`
        * :py:class:`FtwPatchError`
        * :py:class:`builtins.Exception`
    """
    def __init__(self, message: str) -> None:
        """
        Initializes the PatchParseError.

        :param message: The error message.
        :returns: None
        """
        super().__init__(message)
    
    def __repr__(self) -> str:
        """
        Returns a string representation of the object.
        """
        return f"{self.__class__.__name__}(message={self.args[0]!r})"


# --- Parser ---

class PatchParser:
    """
    Handles the parsing of the diff or patch file content.

    This class is responsible for reading the file, handling potential encoding issues,
    and iterating over the hunks and files defined in the patch.
    """
    
    # Regex to capture the standard unified hunk header: @@ -<start>,<len> +<start>,<len> @@ (optional text)
    _HUNK_HEADER_RE = re.compile(
        r"^@@\s*-(\d+)(?:,(\d+))?\s*\+(\d+)(?:,(\d+))?\s*@@.*$"
    )
    
    def __init__(self, patch_file_path: Path) -> None:
        """
        Initializes the PatchParser instance.

        :param patch_file_path: Path to the .diff or .patch file.
        :raises builtins.FileNotFoundError: If the patch file does not exist.
        :returns: None
        """
        if not patch_file_path.is_file():
            raise FileNotFoundError(f"Patch file not found: {patch_file_path}")
        
        self._patch_file_path = patch_file_path

    def __repr__(self) -> str:
        """
        Returns a string representation of the object.
        """
        return f"{self.__class__.__name__}(patch_file_path={self._patch_file_path!r})"
    
    def iter_files(self) -> Iterator[tuple[Path, Path, list[Hunk]]]:
        """
        Iterates over the files defined in the patch.

        This method reads the patch file, identifies the file boundaries, 
        collects all hunks for one file change, and yields the result.

        :returns: An iterator yielding tuples of (original_path, new_path, list_of_hunks).
        :raises PatchParseError: If the patch file format is invalid.
        :raises builtins.IOError: If an I/O error occurs during file reading.
        """
        original_file_path: Path = Path()
        new_file_path: Path = Path()
        hunks: list[Hunk] = []
        
        try:
            file_handle: TextIO
            # Use manual readline for stateful parsing of file/hunk blocks
            with self._patch_file_path.open(mode="r", encoding="utf-8", errors="replace") as file_handle:
                
                # Variable to store a line that was read but belongs to the next block
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
                            raise PatchParseError("Found '+++' line without preceding '---' line.")
                            
                        # Reset hunks list for the new file
                        hunks = [] 
                        continue
                    
                    # 3. Identify Hunk Header '@@ ... @@'
                    elif line.startswith('@@ '):
                        if not new_file_path:
                            raise PatchParseError("Found hunk header '@@' before '+++' file definition.")
                            
                        match = self._HUNK_HEADER_RE.match(line)
                        if not match:
                            raise PatchParseError(f"Malformed hunk header found: {line.strip()}")
                            
                        # Extract start/length values. Default length to 1 if missing
                        o_start, o_len_str, n_start, n_len_str = match.groups()
                        o_len = int(o_len_str or 1)
                        n_len = int(n_len_str or 1)
                        
                        current_hunk_lines: list[str] = []
                        
                        # --- START HUNK LINE CONSUMPTION ---
                        while True:
                            hunk_line = file_handle.readline()
                            if not hunk_line: # EOF while reading hunk content
                                break
                            
                            # Hunk content lines: context (' '), added ('+'), or removed ('-')
                            if hunk_line.startswith((' ', '+', '-')):
                                current_hunk_lines.append(hunk_line)
                            
                            # Check for the start of the next block: new hunk, new file, or end of diff
                            elif hunk_line.startswith(('@@ ', '--- ', 'diff ')):
                                # This line belongs to the next block. Put it back for the main loop.
                                next_line = hunk_line
                                break
                            
                            else:
                                # Ignore other metadata lines inside the diff block, like '\ No newline at end of file'
                                continue 
                        # --- END HUNK LINE CONSUMPTION ---

                        # Create and append Hunk
                        hunk = Hunk(
                            original_start=int(o_start),
                            original_length=o_len,
                            new_start=int(n_start),
                            new_length=n_len,
                            lines=current_hunk_lines 
                        )
                        hunks.append(hunk)
                        
                        continue # Start the main loop iteration again (either with next_line or a fresh read)


                    # 4. Handle end of a file block (e.g., empty lines or other headers before next '---')
                    elif line.startswith('diff ') and new_file_path:
                        # Found the start of the next diff, yield the current file's hunks
                        yield original_file_path, new_file_path, hunks
                        # Reset state for the new file block
                        original_file_path = Path()
                        new_file_path = Path()
                        hunks = []
                        
                # 5. Handle EOF: Yield the last collected file patch if any hunks were found
                if new_file_path and hunks:
                    yield original_file_path, new_file_path, hunks

        except IOError as e:
            # Catch I/O errors (e.g., encoding problems, read errors)
            raise IOError(f"Error reading patch file '{self._patch_file_path.name}': {e}")
        except Exception as e:
            # Catch other unexpected parsing issues and wrap them
            if not isinstance(e, PatchParseError):
                 raise PatchParseError(f"Unexpected error during patch parsing: {e}")
            raise # Re-raise if it was already a PatchParseError


# --- FtwPatch (Main Application) ---

class FtwPatch:
    """
    Main class for the ``ftwpatch`` program.

    Es implementiert das PIMPLE-Idiom, indem es das Namespace-Objekt
    speichert und die Argumente über Getter bereitstellt.
    """
    def __init__(self, args: Namespace) -> None:
        """
        Initializes the FtwPatch instance by storing the parsed command-line arguments.

        :param args: The Namespace object returned by :py:func:`argparse.ArgumentParser.parse_args()`.
                     Must contain attributes: patch_file (Path), strip_count (int), target_directory (Path), 
                     normalize_whitespace (bool), ignore_blank_lines (bool), ignore_all_whitespace (bool).
        :raises builtins.FileNotFoundError: If the patch file does not exist (checked proaktiv).
        :raises FtwPatchError: If any internal error occurs during setup.
        :returns: None
        """
        self._args = args

        # Proaktive Prüfung der Existenz der Patch-Datei
        if not self._args.patch_file.is_file():
             raise FileNotFoundError(f"Patch file not found at {self._args.patch_file!r}")

    def __repr__(self) -> str:
        """
        Returns a string representation of the object.
        """
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
        Indicates if all whitespace differences should be completely ignored (**ro**).

        :returns: The ignore status.
        """
        return self._args.ignore_all_whitespace

    def _normalize_line(self, line: str, strip_prefix: bool = False) -> str:
        """
        Applies whitespace normalization rules based on CLI arguments.
        
        :param line: The line content from the file or the patch.
        :param strip_prefix: If True, strips the diff prefix (' ', '+', '-') from the patch line.
                             Default is False, da dies die Normalisierung von Zieldateizeilen erleichtert.
        :returns: The normalized line.
        """
        # Strip the diff prefix if present and requested
        if strip_prefix and line.startswith((' ', '+', '-')):
            line = line[1:]
        
        # Dominante Option: --ignore-all-ws
        if self.ignore_all_whitespace:
            # Entferne alle Whitespace-Zeichen (einschließlich Newlines, Tabs und Leerzeichen)
            return "".join(line.split())
        
        # Sekundäre Optionen: --normalize-ws und --ignore-bl
        
        # Newline und Carriage Return am Ende entfernen
        line = line.strip('\n\r') 

        # Whitespace Normalization (außer führender Whitespace)
        if self.normalize_whitespace:
            # Wir verwenden re.split für Whitespace am Anfang und verarbeiten dann den Rest.
            match = re.match(r'^\s*', line)
            leading_ws = match.group(0) if match else ''
            rest = line[len(leading_ws):]
            
            # Normalisiere den Rest: Ersetze alle inneren Whitespace-Sequenzen durch ein einzelnes Leerzeichen.
            rest_normalized = re.sub(r'[ \t\f\v]+', ' ', rest)
            line = leading_ws + rest_normalized
        
        # Ignore Blank Lines
        if self.ignore_blank_lines and not line.strip():
            # Eine leere Zeile wird zu einem leeren String normalisiert.
            return ''
             
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

        :param file_path: The full path to the file being patched (for error messages).
        :param hunk: The Hunk object containing the change details.
        :param original_lines: The list of lines (content) of the original file.
        :raises FtwPatchError: If the hunk cannot be applied (e.g., context mismatch or line number out of bounds).
        :returns: The modified list of lines after applying the hunk.
        """
        
        # Hunk-Zeilennummern sind 1-basiert, Listenindizes sind 0-basiert.
        # Wir müssen also von der 1-basierten 'original_start' zur 0-basierten 'index' wechseln.
        hunk_start_index = hunk.original_start - 1
        
        if hunk_start_index < 0 or hunk_start_index + hunk.original_length > len(original_lines):
            raise FtwPatchError(
                f"Hunk (starts at line {hunk.original_start}, length {hunk.original_length}) "
                f"is out of bounds for file '{file_path}' (length {len(original_lines)})."
            )

        # 1. Kontext- und Deletions-Prüfung (Matching)
        hunk_line_index = 0
        file_current_index = hunk_start_index
        
        # Wir sammeln die zu behaltenden (Context) und hinzuzufügenden (Added) Zeilen
        new_file_content: list[str] = original_lines[:hunk_start_index]
        
        # Wir iterieren über die Zeilen im Hunk
        while hunk_line_index < len(hunk.lines):
            hunk_line = hunk.lines[hunk_line_index]
            prefix = hunk_line[0]
            
            if prefix == ' ': # Kontextzeile
                # 1.1 Prüfe, ob die Kontextzeile in der Originaldatei übereinstimmt.
                # Wir benötigen die 0-basierte Zeile aus der Originaldatei
                original_line = original_lines[file_current_index]
                
                # Normalisierung beider Zeilen
                norm_hunk_line = self._normalize_line(hunk_line, strip_prefix=True)
                norm_original_line = self._normalize_line(original_line, strip_prefix=False)
                
                if norm_hunk_line != norm_original_line:
                    # Mismatch! Der Patch kann nicht angewendet werden.
                    raise FtwPatchError(
                        f"Context mismatch in file '{file_path}' at expected line {file_current_index + 1}: "
                        f"Expected '{norm_hunk_line!r}', found '{norm_original_line!r}'."
                    )
                
                # Kontextzeile ist korrekt, füge sie dem neuen Inhalt hinzu (mit der Originalzeile).
                new_file_content.append(original_line)
                file_current_index += 1
                
            elif prefix == '-': # Zu löschende Zeile
                # 1.2 Prüfe, ob die zu löschende Zeile in der Originaldatei übereinstimmt.
                original_line = original_lines[file_current_index]

                norm_hunk_line = self._normalize_line(hunk_line, strip_prefix=True)
                norm_original_line = self._normalize_line(original_line, strip_prefix=False)

                if norm_hunk_line != norm_original_line:
                    # Mismatch! Der Patch kann nicht angewendet werden.
                    raise FtwPatchError(
                        f"Deletion mismatch in file '{file_path}' at line {file_current_index + 1}: "
                        f"Expected to delete '{norm_hunk_line!r}', but found '{norm_original_line!r}'."
                    )
                
                # Zeile wird gelöscht, nicht zum neuen Inhalt hinzugefügt.
                file_current_index += 1
                
            elif prefix == '+': # Hinzuzufügende Zeile
                # 2. Füge die neue Zeile zum Inhalt hinzu.
                new_line_content = hunk_line[1:]
                
                # Stelle sicher, dass die Zeile ein Newline-Zeichen enthält, falls es fehlt 
                if not new_line_content.endswith(('\n', '\r')):
                    new_line_content += '\n'
                    
                new_file_content.append(new_line_content)
                
            else:
                # Sollte durch PatchParser.iter_files abgefangen werden.
                 raise PatchParseError(f"Unexpected line prefix in hunk line: {hunk_line!r}")

            hunk_line_index += 1
            
        # 3. Füge den Rest der Originaldatei hinzu
        new_file_content.extend(original_lines[file_current_index:])
        
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
            f"Applying patch from {self.patch_file_path!r} in directory {self.target_directory!r} "
            f"(strip={self.strip_count}, ws_norm={self.normalize_whitespace}, bl_ignore={self.ignore_blank_lines}, "
            f"ws_all_ignore={self.ignore_all_whitespace}, dry_run: {dry_run})"
        )
        
        # Struktur zum Speichern der erfolgreich gepatchten Inhalte im Speicher (All-or-Nothing)
        # Key: Path (full_new_path), Value: list[str] (der neue Inhalt)
        patched_file_storage: dict[Path, list[str]] = {}
        applied_file_count = 0
        
        try:
            for original_patch_path, new_patch_path, hunks in parser.iter_files():
                
                # Pfadberechnung
                target_original_path = self._clean_patch_path(original_patch_path)
                target_new_path = self._clean_patch_path(new_patch_path)
                
                full_original_path = self.target_directory / target_original_path
                full_new_path = self.target_directory / target_new_path

                print(f"\nProcessing file: {target_original_path} -> {target_new_path} ({len(hunks)} hunks)")
                
                if not full_original_path.is_file():
                    # Wir müssen dies später für /dev/null anpassen
                    raise FileNotFoundError(f"Target file not found for patching: {full_original_path!r}")

                # 1. Datei-Inhalt lesen
                try:
                    with full_original_path.open(mode="r", encoding="utf-8", errors="replace") as f:
                        original_lines = f.readlines()
                except IOError as e:
                    raise IOError(f"Error reading target file {full_original_path}: {e}")
                
                # 2. Hunks sequenziell im Speicher anwenden
                current_lines = original_lines
                
                for i, hunk in enumerate(hunks):
                    print(
                        f"  - Applying Hunk {i+1}/{len(hunks)} "
                        f"(@ Line {hunk.original_start}: {hunk.original_length} -> {hunk.new_length})"
                    )
                    
                    current_lines = self._apply_hunk_to_file(
                        file_path=full_original_path, 
                        hunk=hunk, 
                        original_lines=current_lines
                    )

                # 3. Ergebnis im Speicher zwischenspeichern (für All-or-Nothing-Ansatz)
                patched_file_storage[full_new_path] = current_lines
                applied_file_count += 1
                print(f"  -> Patch successfully verified and stored in memory ({len(current_lines)} lines).")

            # ENDE DER ITERATION: Wenn wir hier ankommen, war der gesamte Patch-Vorgang fehlerfrei.
            
            # 4. Dateien schreiben (All-or-Nothing-Schreibphase)
            if not dry_run:
                print("\nStarting write phase: Applying changes to file system...")
                for full_new_path, final_content in patched_file_storage.items():
                    # Sicherstellen, dass das Zielverzeichnis existiert
                    full_new_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Inhalt in die Zieldatei schreiben
                    with full_new_path.open(mode="w", encoding="utf-8", errors="replace") as f:
                        f.writelines(final_content)
                        
                    print(f"  -> Successfully wrote {full_new_path!r}.")
            else:
                 print("\nPatch run finished successfully in dry-run mode.")
            
            print(f"\nSuccessfully processed {applied_file_count} files.")
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
        help="Path to the patch or diff file to be applied. If '-' is given, patch is read from stdin.",
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
            "This makes matching less sensitive to minor changes in blank line count."
        ),
    )

    parser.add_argument(
        "--ignore-all-ws",
        action="store_true",
        dest="ignore_all_whitespace",
        help=(
            "Completely ignore all whitespace characters when comparing lines. "
            "This is a last resort for non-whitespace-sensitive languages (e.g., C, Java) "
            "to ignore formatting differences. This option is dominant."
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
            return f"MockNamespace({', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())})"


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
        
        # apply_patch wird aufgerufen, FileNotFoundError wird bereits im __init__ abgefangen.
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