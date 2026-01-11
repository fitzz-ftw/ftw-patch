import pytest

from fitzzftw.patch.ftw_patch import PatchLine, PatchParseError


class TestPatchLine:
    """Unit tests for the PatchLine base class and fallback instances."""

    def test_initialization_strips_newline(self):
        """Checks if trailing newlines are removed during initialization."""
        line = PatchLine("Some random patch text\n")
        assert line.content == "Some random patch text"

    def test_initialization_with_empty_string(self):
        """Ensures the class handles empty strings correctly."""
        line = PatchLine("")
        assert line.content == ""

    def test_initialization_raises_parser_error_on_none(self):
        """Ensures FTWParserError is raised when raw_line is None."""
        with pytest.raises(PatchParseError) as excinfo:
            PatchLine(None)
        
        # Optional: Prüfen, ob die Fehlermeldung den richtigen Hinweis enthält
        assert "received None" in str(excinfo.value)
        
    @pytest.mark.parametrize("invalid_input", [
        None, 
        123, 
        45.6, 
        True, 
        ["list"], 
        {"dict": "val"}
    ])

    def test_initialization_raises_error_on_invalid_types(self, invalid_input):
        """
        Ensures FTWParserError is raised for any non-string input.
        This enforces strict type safety for patch processing.
        """
        with pytest.raises(PatchParseError) as excinfo:
            PatchLine(invalid_input)
        
        # Verify that the error message contains the type name for better debugging
        assert "expected a string" in str(excinfo.value)

    def test_property_content_is_read_only(self):
        """Ensures the content property cannot be modified directly."""
        line = PatchLine("Immutable text")
        with pytest.raises(AttributeError):
            line.content = "New text"

    def test_string_representation(self):
        """Checks if the string conversion returns the stored content."""
        content = "Standard line"
        line = PatchLine(content)
        # assert str(line) == content
        assert str(line) == "PatchLine(Content: 'Standard line')"


    def test_trailing_whitespace_getter(self):
        """Covers Line 140 (the property getter in PatchLine)."""
        # Case: True
        assert PatchLine("code  ").has_trailing_whitespace is True
        # Case: False
        assert PatchLine("code").has_trailing_whitespace is False
