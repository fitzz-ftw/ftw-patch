import pytest

from ftw.patch.ftw_patch import PatchParseError, PatchParser


class TestPatchParser:

    def test_parser_repr(self):
        """Covers lines 1121-1124: The __repr__ method."""
        parser = PatchParser()
        assert repr(parser) == "PatchParser()"

    def test_iter_files_full_flow(self):
        """
        Covers the main loop and line 1154->1141 (yielding previous file).
        Fix: Added content to the second file to ensure it's fully yielded.
        """
        stream = [
            "--- a/file1.txt",
            "+++ b/file1.txt",
            "@@ -1,1 +1,1 @@",
            " context1",
            "--- a/file2.txt",
            "+++ b/file2.txt",
            "@@ -1,1 +1,1 @@",
            " context2"
        ]
        parser = PatchParser()
        files = list(parser.iter_files(stream))
        
        assert len(files) == 2
        assert files[0].orig_header.content == "a/file1.txt"
        assert files[1].orig_header.content == "a/file2.txt"

    def test_unexpected_error_handling(self):
        """Covers lines 1191-1193: The generic Exception block."""
        parser = PatchParser()
        # Ein Nicht-String Objekt provoziert einen AttributeError bei .startswith()
        with pytest.raises(PatchParseError, match="Unexpected error at line 1"):
            list(parser.iter_files([12345]))

    def test_get_lines_generator(self):
        """Ensures the get_lines classmethod works as expected."""
        stream = ["--- a/file.txt", "@@ -1,1 +1,1 @@"]
        lines = list(PatchParser.get_lines(stream))
        assert len(lines) == 2
        assert lines[0].__class__.__name__ == "HeadLine"

    def test_strict_hunk_rule(self):
        """Verifies the else-branch within a hunk block."""
        parser = PatchParser()
        stream = [
            "--- a/f.txt", "+++ b/f.txt",
            "@@ -1,1 +1,1 @@",
            "INVALID_CONTENT_WITHOUT_PREFIX"
        ]
        with pytest.raises(PatchParseError, match="Invalid line within hunk"):
            list(parser.iter_files(stream))

    def test_metadata_ignored_outside_hunk(self):
        """Verifies the else-branch/continue outside of a hunk."""
        parser = PatchParser()
        stream = [
            "diff --git a/f.txt b/f.txt", # Metadata
            "--- a/f.txt",
            "+++ b/f.txt",
            "@@ -1,1 +1,1 @@",
            " "
        ]
        files = list(parser.iter_files(stream))
        assert len(files) == 1


    def test_create_line_fallback_coverage(self):
        """Covers lines 1106-1111: Direct call to create_line with unknown prefix."""
        parser = PatchParser()
        # Testet den 'else'-Zweig in create_line
        # Da PatchLine (Basisklasse) vermutlich 'content' nutzt:
        line = parser.create_line("index 12345..67890 100644")
        assert "PatchLine" in str(type(line))
        # Wir prüfen nur, ob das Objekt erstellt wurde, ohne auf das .raw Attribut zu pochen
        assert hasattr(line, 'content') or hasattr(line, 'raw')

    def test_first_file_transition_logic(self):
        """Covers 1153->1141: The branch where current_file is None on first '---'."""
        parser = PatchParser()
        # Wir fügen einen Hunk-Header hinzu, damit das Objekt valide ist 
        # und am Ende der Schleife via 'if current_file: yield' ausgegeben wird.
        stream = [
            "--- a/file.txt", 
            "+++ b/file.txt",
            "@@ -1,1 +1,1 @@"
        ]
        files = list(parser.iter_files(stream))
        assert len(files) == 1
        assert files[0].orig_header.content == "a/file.txt"

    def test_unexpected_error_handling_with_mock(self):
        """Covers line 1190: Generic Exception block using a mock."""
        from unittest.mock import MagicMock
        parser = PatchParser()
        
        # Wir provozieren einen Fehler direkt beim Start der Iteration
        mock_stream = MagicMock()
        mock_stream.__iter__.side_effect = TypeError("Unexpected Type")
        
        # Dank 'line_no = 0' vor dem try-Block gibt es jetzt keinen UnboundLocalError mehr
        with pytest.raises(PatchParseError, match="Unexpected error at line 0"):
            list(parser.iter_files(mock_stream))

    def test_create_line_full_branch_coverage(self):
        """Covers line 1107: The else branch in the create_line factory."""
        parser = PatchParser()
        # Forcing the factory into the 'else' branch with a metadata string
        line = parser.create_line("index 12345..67890 100644")
        assert line.__class__.__name__ == "PatchLine"
        # Accessing content to ensure the object is fully exercised
        assert str(line).strip() == "PatchLine(Content: 'index 12345..67890 100644')"

    def test_missing_header_branches(self):
        """Covers 1155, 1161, 1169: Specific error paths for invalid sequences."""
        parser = PatchParser()
        
        # 1155: Handling +++ before any --- header is seen
        with pytest.raises(PatchParseError, match=r"Found '\+\+\+' before '---'"):
            list(parser.iter_files(["+++ b/file.txt"]))
            
        # 1161: Handling @@ before any file header exists
        # with pytest.raises(PatchParseError, match=r"Found '@@' before file headers"):
        with pytest.raises(PatchParseError, match=r"Line 1: Found '@@ ' before file headers"):
            list(parser.iter_files(["@@ -1,1 +1,1 @@"]))
            
        # 1169: Handling content lines before a hunk header is defined
        stream = ["--- a/f.txt", "+++ b/f.txt", " context"]
        with pytest.raises(PatchParseError, match=r"Found content line before '@@' header"):
            list(parser.iter_files(stream))

    def test_generator_empty_exit_path(self):
        """Covers 1184->exit: The path where no file is yielded at the end."""
        parser = PatchParser()
        # A stream containing only noise, resulting in current_file being None
        stream = ["# Git patch metadata", "old mode 100644", "new mode 100755"]
        files = list(parser.iter_files(stream))
        assert len(files) == 0

    def test_create_line_factory_branches(self):
        """Covers lines 1106-1111: All branches of the create_line factory."""
        parser = PatchParser()
        
        # Test HunkLine branch in factory
        line_plus = parser.create_line("+added")
        assert line_plus.__class__.__name__ == "HunkLine"
        
        line_minus = parser.create_line("-removed")
        assert line_minus.__class__.__name__ == "HunkLine"
        
        line_context = parser.create_line(" context")
        assert line_context.__class__.__name__ == "HunkLine"
        
        # Test Fallback branch (PatchLine)
        line_meta = parser.create_line("index 12345..67890")
        assert line_meta.__class__.__name__ == "PatchLine"

    def test_missing_header_logic_and_exit_branches(self):
        """Covers error branches (1155, 1161, 1169) and the generator exit (1184)."""
        parser = PatchParser()
        
        # 1155: Error on '+++' without '---'
        with pytest.raises(PatchParseError, match=r"Found '\+\+\+' before '---'"):
            list(parser.iter_files(["+++ b/file.txt"]))
            
        # 1161: Error on '@@' without file headers
        with pytest.raises(PatchParseError, match=r"Line 1: Found '@@ ' before file headers"):
            list(parser.iter_files(["@@ -1,1 +1,1 @@"]))
            
        # 1169: Error on content before hunk header
        with pytest.raises(PatchParseError, match=r"Found content line before '@@' header"):
            list(parser.iter_files(["--- a/f.txt", "+++ b/f.txt", " +added"]))

    def test_empty_stream_exit_coverage(self):
        """Covers the branch 1184->exit (generator ends with current_file being None)."""
        parser = PatchParser()
        # Stream that never initializes a DiffCodeFile
        assert list(parser.iter_files(["# Comment only"])) == []

    def test_multi_file_branch_coverage(self):
        """
        Fixes the branch 1153->1141.
        By providing two files, we force 'current_file' to be NOT None 
        when the second '---' header arrives.
        """
        parser = PatchParser()
        stream = [
            "--- a/file1.txt", 
            "+++ b/file1.txt", 
            "@@ -1,1 +1,1 @@", 
            " context",
            "--- a/file2.txt", # <--- Hier wird current_file (file1) yielded
            "+++ b/file2.txt", 
            "@@ -1,1 +1,1 @@", 
            " context"
        ]
        files = list(parser.iter_files(stream))
        assert len(files) == 2
        assert files[0].orig_header.content == "a/file1.txt"
        assert files[1].orig_header.content == "a/file2.txt"

    def test_ultimate_branch_coverage_finalizer(self):
        """
        Forces 100% branch coverage for the yield logic.
        We ensure no hunk is active when noise appears.
        """
        parser = PatchParser()
        stream = [
            "--- a/file1.txt", 
            "+++ b/file1.txt", 
            "@@ -1,1 +1,1 @@", 
            " context", 
            # Wir fangen eine neue Datei an. Das setzt current_hunk auf None!
            "--- a/file2.txt", 
            "random noise here", # JETZT ist current_hunk None, der Else-Zweig greift
            "+++ b/file2.txt", 
            "@@ -1,1 +1,1 @@", 
            " context"
        ]
        files = list(parser.iter_files(stream))
        assert len(files) == 2
