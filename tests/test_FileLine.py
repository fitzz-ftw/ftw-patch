import pytest

from fitzzftw.patch.ftw_patch import FileLine, PatchParseError


class TestFileLine:
    """Unit tests for FileLine, focusing on whitespace and indentation handling."""

    def test_preserves_leading_spaces(self):
        """Ensures that leading spaces (indentation) are strictly preserved."""
        indented_line = "    return True"
        fl = FileLine(indented_line)
        assert fl.content == indented_line

    def test_whitespace_only_line(self):
        """Ensures that lines containing only whitespace are handled correctly."""
        ws_line = "    "
        fl = FileLine(ws_line)
        assert fl.content == "    "

    def test_invalid_input_raises_patch_parse_error(self):
        """Checks if the correct PatchParseError is raised for non-string input."""
        with pytest.raises(PatchParseError) as excinfo:
            FileLine(None)
        assert "expected a string" in str(excinfo.value)

    def test_strips_only_trailing_newline(self):
        """Verifies that only the newline is removed, keeping trailing spaces."""
        line = "content   \n"
        fl = FileLine(line)
        assert fl.content == "content   "

    def test_whitespace_properties(self):
        """Tests that leading whitespace is preserved in normalized_ws."""
        raw = " \tdata  value \t"
        fl = FileLine(raw)
        
        # Normalized: Keeps leading WS, reduces internal WS, strips trailing
        assert fl.normalized_ws_content == " \tdata value"
        
        # Ignore All: Radical removal of everything
        assert fl.ignore_all_ws_content == "datavalue"
        
        assert fl.has_trailing_whitespace is True

    def test_has_newline_rw_behavior(self):
        """Tests that has_newline is truly read-write."""
        fl = FileLine("no newline")
        assert fl.has_newline is False
        
        fl.has_newline = True
        assert fl.has_newline is True
        
        fl.has_newline = False
        assert fl.has_newline is False

    @pytest.mark.parametrize("prop_name", [
        "prefix", "normalized_ws_content", "ignore_all_ws_content", 
        "has_trailing_whitespace", "is_empty", "line_string"
    ])
    def test_properties_are_read_only(self, prop_name):
        """Verifies that RO properties raise AttributeError on write."""
        fl = FileLine("test")
        with pytest.raises(AttributeError):
            setattr(fl, prop_name, "attempt to write")

    def test_empty_line_behavior(self):
        """Checks properties when the line is completely empty."""
        fl = FileLine("")
        assert fl.is_empty is True
        assert fl.has_trailing_whitespace is False
        assert fl.normalized_ws_content == ""

    def test_file_line_repr(self):
        """
        Verify the string representation of a FileLine object.
        This covers the __repr__ method (currently around line 436).
        """
        content = "    some python code"
        fl = FileLine(content)
        
        representation = repr(fl)
        
        # Check for class name
        assert "FileLine" in representation
        # FileLine stores content exactly as given
        assert f"Content: {content!r}" in representation
        # Prefix for FileLine is always empty
        assert "Prefix: ''" in representation

    def test_file_line_is_empty_variants(self):
        """
        Covers the branches of the is_empty property.
        Checks both a line with content and a truly empty line.
        """
        # Case 1: Line with content
        fl_content = FileLine("some code")
        assert fl_content.is_empty is False
        
        # Case 2: Truly empty line (Covers the missing branch)
        fl_empty = FileLine("")
        assert fl_empty.is_empty is True

    def test_line_string_reconstruction(self):
        """
        Verifies that line_string correctly appends a newline only if needed.
        This covers both branches of the inline if-statement.
        """
        # Case 1: Line with newline
        fl_nl = FileLine("data")
        fl_nl.has_newline = True
        assert fl_nl.line_string == "data\n"
        
        # Case 2: Line without newline (the missing branch)
        fl_no_nl = FileLine("data")
        fl_no_nl.has_newline = False
        assert fl_no_nl.line_string == "data"
