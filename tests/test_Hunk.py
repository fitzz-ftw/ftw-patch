from types import SimpleNamespace

import pytest

from fitzzftw.patch.ftw_patch import (
    FileLine,
    FtwPatchError,
    Hunk,
    HunkHeadLine,
    HunkLine,
)


class TestHunk:
    """Tests for the Hunk container class with direct internal state verification."""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Prepares the test bench with reusable objects."""
        # HeadLines
        self.header_std = HunkHeadLine("@@ -1,5 +1,6 @@")
        self.header_off = HunkHeadLine("@@ -10,2 +20,2 @@")
        
        # Reusable HunkLines
        self.line_ctx = HunkLine(" context")
        self.line_add = HunkLine("+added")
        self.line_del = HunkLine("-removed")

        # Option Namespaces (Centralized as you suggested)
        self.opts_default = SimpleNamespace(
            ignore_blank_lines=False,
            ignore_all_space=False,
            ignore_space_change=False
        )
        self.opts_ignore_all_ws = SimpleNamespace(
            ignore_blank_lines=False,
            ignore_all_space=True,
            ignore_space_change=False
        )
        self.opts_ignore_change_ws = SimpleNamespace(
            ignore_blank_lines=False,
            ignore_all_space=False,
            ignore_space_change=True
        )
        self.opts_ignore_blanks = SimpleNamespace(
            ignore_blank_lines=True,
            ignore_all_space=False,
            ignore_space_change=False
        )

    def test_init_sets_internal_header(self):
        """Verify that the HunkHeadLine is correctly stored internally."""
        hunk = Hunk(self.header_std)
        # Direktzugriff auf das interne Attribut ist hier absolut gewollt
        assert hunk._header == self.header_std

    def test_init_raises_on_invalid_types(self):
        """Ensure the guard prevents non-HunkHeadLine objects."""
        with pytest.raises(TypeError, match="header must be HunkHeadLine"):
            Hunk("Just a string")
        with pytest.raises(TypeError, match="header must be HunkHeadLine"):
            Hunk(None)

    def test_delegation_to_header(self):
        """Check if start properties correctly delegate to the header object."""
        hunk = Hunk(self.header_off)
        assert hunk.old_start == 10
        assert hunk.new_start == 20

    def test_line_collection_management(self):
        """Test the list management and line access."""
        hunk = Hunk(self.header_std)
        hunk.add_line(self.line_ctx)
        hunk.add_line(self.line_del)
        
        assert len(hunk) == 2
        assert hunk[0] == self.line_ctx
        assert hunk.lines[1] == self.line_del
        
        # Test the iterator protocol
        lines = [l for l in hunk]  # noqa: E741
        assert lines == [self.line_ctx, self.line_del]

    def test_repr_output(self):
        """Verify the string representation for debugging."""
        hunk = Hunk(self.header_std)
        hunk.add_line(self.line_add)
        
        r = repr(hunk)
        assert "Hunk" in r
        # We verify against the tuple representation provided by the HunkHeadLine object
        assert "header=(1, 5, 1, 6)" in r
        assert "lines=1" in r

    def test_compare_context_exact_match(self):
        """Verify context matching with default options."""
        hunk = Hunk(self.header_std)
        expected = [self.line_ctx]
        actual = [FileLine("context")]
        assert hunk._compare_context(expected, actual, self.opts_default) is True

    def test_compare_context_whitespace_variants(self):
        """Verify the different whitespace comparison strategies."""
        hunk = Hunk(self.header_std)
        # " context    with   spaces"
        complex_line = [HunkLine(" context    with   spaces")]
        
        # Test ignore_space_change
        actual_norm = [FileLine("context with spaces")]
        assert hunk._compare_context(complex_line, actual_norm, self.opts_ignore_change_ws) is True
        
        # Test ignore_all_space
        actual_none = [FileLine("contextwithspaces")]
        assert hunk._compare_context(complex_line, actual_none, self.opts_ignore_all_ws) is True

    def test_compare_context_blank_lines(self):
        """Verify handling of blank lines."""
        hunk = Hunk(self.header_std)
        expected = [HunkLine(" ")] # Represents an empty context line
        actual = [FileLine("")]     # Truly empty line
        
        assert hunk._compare_context(expected, actual, self.opts_ignore_blanks) is True

    def test_compare_context_early_exit(self):
        """Ensure it returns False if line counts differ."""
        hunk = Hunk(self.header_std)
        assert hunk._compare_context([self.line_ctx], [], self.opts_default) is False

    def test_compare_context_mismatch_all_ws(self):
        """Trigger 'return False' for ignore_all_space (Line 760)."""
        hunk = Hunk(self.header_std)
        # Difference in non-whitespace characters
        exp = [HunkLine(" context")] # content: 'context'
        act = [FileLine("different")] # content: 'different'
        assert hunk._compare_context(exp, act, self.opts_ignore_all_ws) is False

    def test_compare_context_mismatch_normalized(self):
        """Trigger 'return False' for ignore_space_change (Line 764)."""
        hunk = Hunk(self.header_std)
        exp = [HunkLine(" line A")]
        act = [FileLine("line B")]
        assert hunk._compare_context(exp, act, self.opts_ignore_change_ws) is False

    def test_compare_context_mismatch_exact(self):
        """Trigger 'return False' for the final 'else' match (Line 768)."""
        hunk = Hunk(self.header_std)
        exp = [self.line_ctx] # " context"
        act = [FileLine("context ")] # trailing space mismatch
        assert hunk._compare_context([exp[0]], act, self.opts_default) is False

    def test_compare_context_ignore_blank_lines_trigger(self):
        """Trigger the 'continue' in ignore_blank_lines (Line 754)."""
        hunk = Hunk(self.header_std)
        # Both must be empty to trigger the 'continue'
        exp = [HunkLine(" ")] # Empty context line
        act = [FileLine("")]   # Truly empty file line
        
        # This will now enter the 'if exp.is_empty and act.is_empty' block
        assert hunk._compare_context(exp, act, self.opts_ignore_blanks) is True

    def test_compare_context_ignore_blank_lines_with_text(self):
        """
        Close the BrPart hole at 754.
        Option is ON, but lines contain text, so it should NOT continue 
        but proceed to normal matching.
        """
        hunk = Hunk(self.header_std)
        exp = [HunkLine(" some text")]
        act = [FileLine("some text")]
        
        # Option is active, but condition 'is_empty' is false
        assert hunk._compare_context(exp, act, self.opts_ignore_blanks) is True

    def test_apply_success(self):
        """Test successful application of a hunk to a file."""
        # Header starts at line 1 (original file)
        hunk = Hunk(self.header_std) 
        hunk.add_line(HunkLine(" context"))
        hunk.add_line(HunkLine("-removed"))
        hunk.add_line(HunkLine("+added"))
        
        file_content = [
            FileLine("context"),
            FileLine("removed"),
            FileLine("keep this")
        ]
        
        result = hunk.apply(file_content, self.opts_default)
        
        assert len(result) == 3
        assert result[0].content == "context"
        assert result[1].content == "added"
        assert result[2].content == "keep this"
        # Verify result contains FileLine objects, not HunkLines
        assert isinstance(result[1], FileLine)

    def test_apply_out_of_bounds(self):
        """Verify error when hunk exceeds file line count."""
        # Header starts at line 10, but file only has 2 lines
        hunk = Hunk(self.header_off) # old_start is 10
        hunk.add_line(self.line_ctx)
        
        file_content = [FileLine("line1"), FileLine("line2")]
        
        with pytest.raises(FtwPatchError, match="exceeds file bounds"):
            hunk.apply(file_content, self.opts_default)

    def test_apply_context_mismatch(self):
        """Verify error when file content doesn't match hunk context."""
        hunk = Hunk(self.header_std) # starts at 1
        hunk.add_line(HunkLine(" expected context"))
        
        file_content = [FileLine("WRONG CONTENT")]
        
        with pytest.raises(FtwPatchError, match="actual file content does not match"):
            hunk.apply(file_content, self.opts_default)
