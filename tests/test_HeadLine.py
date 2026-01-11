from pathlib import Path

import pytest

from fitzzftw.patch.ftw_patch import HeadLine


class TestHeadLine:
    """
    Unit tests for the HeadLine class.
    Focus: Edge cases, path extraction, and property logic.
    """
    @pytest.mark.parametrize("path, expected", [
        ("/dev/null", True),
        ("/Dev/null", False),
        ("/dev/Null", False),
        ("dev/null", False),   # Relativer Pfad-Check
        ("a/normal/path", False),
        ("nul", True),
        ("Nul", True),
        ("nUl", True),
        ("", False),          # Edge-Case: leerer String
        (None, False),        # Edge-Case: None-Type Handling
    ])
    def test_is_null_path_logic(self, path, expected):
        """Tests the logic for identifying null paths (Unix & Windows)."""
        assert HeadLine.check_is_null_path(path) == expected

    @pytest.mark.parametrize("input_str, expected", [
        ("--- a/file.py\n", "a/file.py"),
        ("+++ b/file.py", "b/file.py"),
        ("--- /dev/null\n", "/dev/null"),
        ("+++   b/spaced_path.py   \n", "  b/spaced_path.py   "),
    ])
    def test_initialization_valid_header(self, input_str, expected):
        """Tests if the class correctly strips prefixes and newlines."""
        fhl = HeadLine(input_str)
        assert fhl.content == expected
        

    @pytest.mark.parametrize("bad_input", [
        ("nur text ohne präfix"),
        (""),              # Empty String
        ("@@ -1,1 +1,1 @@"), # Hunk-Header insteat File-Header
        ("-- falsches_präfix"),
    ])
    def test_initialization_raises_error(self, bad_input):
        """Ensures ValueError is raised for invalid header formats."""
        with pytest.raises(ValueError): 
            HeadLine(bad_input)

    def test_initialization_wrong_type(self):
        """Checks the reaction to None or numeric values."""
        with pytest.raises(TypeError):
            HeadLine(None)
        with pytest.raises(TypeError):
            HeadLine(123)

    def test_property_prefix(self):
        """Checks if the prefix (--- or +++) is correctly identified."""
        assert HeadLine("--- a/old.py").prefix == "--- "
        assert HeadLine("+++ b/new.py").prefix == "+++ "

    def test_property_is_orig(self):
        """Checks if the line is identified as the original source file (---)."""
        assert HeadLine("--- a/old.py").is_orig is True
        assert HeadLine("+++ b/new.py").is_orig is False

    def test_property_is_new(self):
        """Checks if the line is identified as the new target file (+++)."""
        assert HeadLine("+++ b/new.py").is_new is True
        assert HeadLine("--- a/old.py").is_new is False

    def test_property_is_null_path(self):
        """Checks if the object correctly identifies itself as a null path."""
        assert HeadLine("--- /dev/null").is_null_path is True
        assert HeadLine("+++ b/file.py").is_null_path is False

    def test_property_info(self):
        """Tests the extraction of metadata after a tab separator."""
        # If no tab separator is present, info should be None
        assert HeadLine("--- a/file.py").info is None
        # If a tab is present but the field is empty, info should be an empty string
        assert HeadLine("--- a/file.py\t").info == ""

        # If metadata exists after the tab (e.g., a timestamp), it should be extracted
        line_with_info = "--- a/file.py\t2023-10-27 10:00:00"
        assert HeadLine(line_with_info).info == "2023-10-27 10:00:00"

    def test_get_path_raises_value_error_on_negative_strip(self):
        """Ensures ValueError is raised when strip_count is negative."""
        hl = HeadLine("--- a/src/main.py")
        
        # Negative values are not valid for stripping path segments from the start
        with pytest.raises(ValueError):
            hl.get_path(-1)

    def test_get_path_too_high_strip_raises_error(self):
        """Covers the second error branch (Line 255-258)."""
        hl = HeadLine("--- a/b/c")
        # Path has 3 segments, trying to strip 3 or more should fail
        with pytest.raises(ValueError, match="too high for path"):
            hl.get_path(3)
        with pytest.raises(ValueError, match="too high for path"):
            hl.get_path(10)

    def test_get_path_valid_stripping(self):
        """Standard case: stripping 1 or more segments."""
        hl = HeadLine("+++ a/b/c/file.txt")
        # -p1 -> b/c/file.txt
        assert hl.get_path(1) == Path("b/c/file.txt")
        # -p0 -> a/b/c/file.txt
        assert hl.get_path(0) == Path("a/b/c/file.txt")

    def test_check_is_null_path_with_path_object(self):
        """
        Ensure the static method handles pathlib.Path objects correctly.
        This covers Line 278.
        """
        # Testing with a Path object
        path_obj = Path("/dev/null")
        assert HeadLine.check_is_null_path(path_obj) is True
        
        # Testing with a normal Path object
        assert HeadLine.check_is_null_path(Path("README.md")) is False


    def test_headline_repr(self):
        """
        Verifies the string representation of a HeadLine object.
        This covers Line 298.
        """
        raw_input = "--- a/file.txt"
        hl = HeadLine(raw_input)
        
        representation = repr(hl)
        
        # Check for class name
        assert "HeadLine" in representation
        # Check for the actual content (stripped of prefix)
        assert "Content: 'a/file.txt'" in representation
        # Check for the prefix
        assert "Prefix: '--- '" in representation
