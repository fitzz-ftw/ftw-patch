import pytest

from fitzzftw.patch.ftw_patch import HunkLine, PatchParseError


class TestHunkLine:
    """Tests for the HunkLine class logic."""

    def test_addition_line(self):
        """Verify handling of an added line (+)."""
        hl = HunkLine("+print('hello')")
        assert hl.is_addition is True
        assert hl.prefix == "+"
        assert hl.content == "print('hello')"

    def test_deletion_line(self):
        """Verify handling of a removed line (-)."""
        hl = HunkLine("-old code")
        assert hl.is_deletion is True
        assert hl.prefix == "-"
        assert hl.content == "old code"

    def test_context_line(self):
        """Verify handling of a context line (space)."""
        hl = HunkLine(" unchanged line")
        assert hl.is_context is True
        assert hl.prefix == " "
        assert hl.content == "unchanged line"

    def test_hunk_line_repr(self):
        """
        Verifies the string representation of a HunkLine.
        This covers Line 586.
        """
        # Test with an addition
        hl = HunkLine("+print('test')")
        representation = repr(hl)
        
        assert "HunkLine" in representation
        assert ("Content: \"print('test')\"" in representation 
            or "Content: 'print(\\'test\\')'" in representation)
        assert "Prefix: '+'" in representation

    def test_hunk_line_invalid_prefix_raises_error(self):
        """
        Verify that HunkLine raises PatchParseError for invalid prefixes.
        This covers Line 586 and its internal branches.
        """
        # Case 1: Invalid prefix (e.g., a letter 'a' instead of ' ', '+', '-')
        with pytest.raises(PatchParseError) as excinfo:
            HunkLine("a invalid line")
        assert "missing valid prefix" in str(excinfo.value)

        # Case 2: Empty string (The 'not raw_line' part of the check)
        with pytest.raises(PatchParseError):
            HunkLine("")

    def test_hunk_line_inherited_properties(self):
        """
        Ensure HunkLine correctly uses inherited logic for whitespace and newlines.
        Even though these are in the parent class, we verify they work here.
        """
        # Test 1: Trailing whitespace
        hl_space = HunkLine("+content with space   ")
        assert hl_space.has_trailing_whitespace is True
        
        # Test 2: Normal content
        hl_normal = HunkLine("-normal")
        assert hl_normal.has_trailing_whitespace is False

        # Test 3: Newline handling (Getter/Setter)
        hl_nl = HunkLine(" context line")
        hl_nl.has_newline = True
        assert hl_nl.has_newline is True
        # Ensure the line_string (if you have it) would include the newline
        # assert hl_nl.line_string().endswith('\n')
