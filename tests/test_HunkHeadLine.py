import pytest

from ftw.patch.ftw_patch import HunkHeadLine, PatchParseError


class TestHunkHeadLine:
    """
    Test suite for the HunkHeadLine class.
    Aims to reach 100% coverage by testing valid formats, 
    edge cases, and error handling.
    """

    def test_standard_header_parsing(self):
        """
        Tests parsing of a standard hunk header with start and length.
        Example: @@ -1,4 +1,4 @@
        """
        raw = "@@ -10,5 +16,7 @@"
        hh = HunkHeadLine(raw)
        
        assert hh.old_start == 10
        assert hh.old_len == 5
        assert hh.new_start == 16
        assert hh.new_len == 7
        assert hh.prefix == "@@ "

    def test_single_line_header_parsing(self):
        """
        Tests headers where the length is omitted (defaults to 1).
        Example: @@ -1 +1 @@
        """
        raw = "@@ -1 +5 @@"
        hh = HunkHeadLine(raw)
        
        assert hh.old_start == 1
        assert hh.old_len == 1  # Should default to 1
        assert hh.new_start == 5
        assert hh.new_len == 1  # Should default to 1

    def test_header_with_trailing_text(self):
        """
        Unified diff headers often contain the function name after the @@.
        Example: @@ -1,1 +1,1 @@ def my_func():
        """
        raw = "@@ -1,1 +1,1 @@ class MyClass:"
        hh = HunkHeadLine(raw)
        assert hh.old_start == 1
        # Checks if the parsing stops correctly at the @@

    def test_invalid_header_format_raises_error(self):
        """
        Verify that malformed headers trigger a ValueError.
        """
        # Test Case 1: Letters instead of numbers (Triggers Regex failure)
        with pytest.raises(ValueError) as excinfo:
            HunkHeadLine("@@ -a,1 +b,1 @@")
        assert "Invalid Hunk coordinates" in str(excinfo.value)

        # Test Case 2: Missing leading @@ (Triggers startswith check)
        with pytest.raises(ValueError) as excinfo:
            HunkHeadLine(" -1,1 +1,1 @@")
        assert "Expected '@@ '" in str(excinfo.value)

        # Test Case 3: Empty string
        with pytest.raises(ValueError):
            HunkHeadLine("")

    def test_hunk_header_repr(self):
        """
        Covers the __repr__ method for HunkHeadLine.
        """
        hh = HunkHeadLine("@@ -1,4 +1,4 @@")
        rep = repr(hh)
        assert "HunkHeadLine" in rep
        assert "-1,4 +1,4" in rep

    def test_hunk_headline_no_suffix_and_repr(self):
        """
        Covers the 'else' branch (343-345) and the representation (391).
        Tests a header that ends exactly with ' @@'.
        """
        # Dieser String triggert den else-Zweig, da kein Text nach dem @@ folgt
        raw = "@@ -1,1 +1,1 @@"
        hh = HunkHeadLine(raw)
        
        # Verifizierung der internen Zustände für diesen Zweig
        assert hh.info is None
        assert hh._suffix_marker == " @@"
        
        # Wenn wir schon dabei sind: Trigger __repr__ (vermutlich Zeile 391)
        # und die Getter (vermutlich Zeile 366)
        assert "HunkHeadLine" in repr(hh)
        assert hh.old_start == 1
        assert hh.old_len == 1

    def test_hunk_headline_properties(self):
        """Test if properties return the correct extracted values."""
        raw = "@@ -1,5 +1,6 @@ some context"
        hh = HunkHeadLine(raw)
        
        # This covers the property getter line in your coverage report
        assert hh.coords == (1, 5, 1, 6)
        assert hh.info == " some context"

    def test_hunk_headline_init_validation(self):
        """Test the input guards for type and prefix format."""
        # Guard 1: Type check
        with pytest.raises(PatchParseError, match="expected a string"):
            HunkHeadLine(None)
        
        # Guard 2: Prefix check
        with pytest.raises(ValueError, match="Expected '@@ '"):
            HunkHeadLine("InvalidPrefix -1,1 +1,1 @@")

        """Test for missing closing ' @@' delimiter."""
        # This will trigger the ValueError in line 338
        with pytest.raises(ValueError, match="Missing closing ' @@'"):
            HunkHeadLine("@@ -1,1 +1,1")
