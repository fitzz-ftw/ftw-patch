from pathlib import Path
from types import SimpleNamespace

import pytest

from ftw.patch.ftw_patch import (
    DiffCodeFile,
    FileLine,
    FtwPatchError,
    HeadLine,
    Hunk,
    HunkHeadLine,
    PatchParseError,
)


class TestDiffCodeFile:
    """Tests for the DiffCodeFile container class."""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Prepare common test data for DiffCodeFile."""
        self.header_orig = HeadLine("--- a/test.txt")
        self.header_new = HeadLine("+++ b/test.txt")
        # A minimal valid hunk for testing management
        h_head = HunkHeadLine("@@ -1,1 +1,1 @@")
        self.sample_hunk = Hunk(h_head)

    def test_init_validation(self):
        """Verify that orig_header must be a HeadLine instance."""
        dcf = DiffCodeFile(self.header_orig)
        assert dcf.orig_header == self.header_orig
        assert dcf.new_header is None
        assert len(dcf) == 0
        
        with pytest.raises(TypeError, match="orig_header must be HeadLine"):
            DiffCodeFile("--- a/test.txt") # String instead of HeadLine

    def test_new_header_setter(self):
        """Test the setter for the '+++' header with validation."""
        dcf = DiffCodeFile(self.header_orig)
        dcf.new_header = self.header_new
        assert dcf.new_header == self.header_new
        
        with pytest.raises(TypeError, match="new_header must be HeadLine"):
            dcf.new_header = "+++ b/test.txt"

    def test_hunk_management(self):
        """Test adding and accessing hunks (iter, len, getitem)."""
        dcf = DiffCodeFile(self.header_orig)
        dcf.add_hunk(self.sample_hunk)
        
        assert len(dcf) == 1
        assert dcf[0] == self.sample_hunk
        assert list(dcf) == [self.sample_hunk]
        # Check read-only property 'hunks'
        assert dcf.hunks == [self.sample_hunk]

    def test_representation(self):
        """Verify the __repr__ output."""
        dcf = DiffCodeFile(self.header_orig)
        res = repr(dcf)
        assert "DiffCodeFile" in res
        assert "orig=a/test.txt" in res # Assuming .content returns the path part
        assert "hunks=0" in res

    def test_temp_path_generation(self):
        """Verify _temp_path is in temp directory and unique per instance."""
        import tempfile
        dcf1 = DiffCodeFile(self.header_orig)
        dcf2 = DiffCodeFile(self.header_orig)
        
        path1 = dcf1._temp_path
        path2 = dcf2._temp_path
        
        # Check location
        assert str(tempfile.gettempdir()) in str(path1)
        # Check naming convention
        assert "ftw_patch_" in path1.name
        # Check uniqueness (via object ID)
        assert path1 != path2

    def test_source_path_derivation(self):
        """Verify source_path is correctly derived from the orig_header."""
        # Wir nutzen die Instanz aus setup_data, die bereits ein echtes HeadLine-Objekt ist
        dcf = DiffCodeFile(self.header_orig)
        
        # Annahme: self.header_orig wurde mit "--- a/test.txt" initialisiert
        # Wir prüfen, ob das Property den Pfad korrekt als Path-Objekt liefert
        assert dcf.get_source_path() == Path("a/test.txt")
        assert isinstance(dcf.get_source_path(), Path)


    def test_read_file_exception(self, mocker):
        """
        Simulate an OSError to verify FtwPatchError conversion (Lines 967-977).
        """
        dcf = DiffCodeFile(self.header_orig)
        
        # 1. Wir erstellen ein Mock-Objekt, das vorgibt ein Path zu sein
        mock_path = mocker.MagicMock(spec=Path)
        
        # 2. WICHTIG: Wir sagen diesem spezifischen Objekt, dass sein .open() 
        # eine Exception werfen soll. Das ist viel sicherer als globale Patches.
        mock_path.open.side_effect = OSError("Disk failure")
        
        # 3. Wir rufen die Methode mit unserem "kaputten" Pfad auf
        with pytest.raises(FtwPatchError, match="Could not read file"):
            dcf._read_file(mock_path)


    def test_write_to_staging_success(self, mocker):
        """
        Verify staging logic by mocking the _temp_path property.
        """
        dcf = DiffCodeFile(self.header_orig)
        
        # Mock the path object
        mock_path = mocker.MagicMock(spec=Path)
        # Mock the property on the CLASS
        mocker.patch.object(DiffCodeFile, '_temp_path', new_callable=mocker.PropertyMock, return_value=mock_path)
        
        # Mock the file stream (Context Manager)
        m_open = mocker.mock_open()
        mocker.patch.object(mock_path, 'open', m_open)
        
        lines = [FileLine("line1\n")]
        result = dcf._write_to_staging(lines)
        
        assert result == mock_path
        # Verify the line string was written to the stream
        m_open().write.assert_called_once_with("line1\n")

    def test_write_to_staging_error(self, mocker):
        """
        Verify FtwPatchError is raised when writing to staging fails (Lines 1030-1038).
        """
        dcf = DiffCodeFile(self.header_orig)
        
        mock_path = mocker.MagicMock(spec=Path)
        # Simulate disk error on open
        mock_path.open.side_effect = OSError("No space left on device")
        mocker.patch.object(DiffCodeFile, '_temp_path', new_callable=mocker.PropertyMock, return_value=mock_path)
        
        with pytest.raises(FtwPatchError, match="Could not write to staging file"):
            dcf._write_to_staging([FileLine("data")])



    def test_apply_orchestration(self, mocker):
        """
        Check if apply sorts hunks in reverse and pipelines the content correctly.
        """
        dcf = DiffCodeFile(self.header_orig)
        
        # 1. Create mock hunks with different start lines
        # Reverse sorting is crucial so changes at the bottom don't break top offsets
        h1 = mocker.MagicMock(spec=Hunk)
        h1.old_start = 10
        h2 = mocker.MagicMock(spec=Hunk)
        h2.old_start = 50
        
        dcf.add_hunk(h1)
        dcf.add_hunk(h2)
        
        # 2. Mock internal methods to isolate the orchestration logic
        # We mock get_source_path because source_path attribute no longer exists
        mocker.patch.object(dcf, 'get_source_path', return_value=Path("src.txt"))
        
        initial_lines = [FileLine("old\n")]
        mocker.patch.object(dcf, '_read_file', return_value=initial_lines)
        
        # 3. Define the return values for the application chain
        # h2 (start 50) must be called BEFORE h1 (start 10) due to reverse sorting
        h2.apply.return_value = [FileLine("after h2\n")]
        h1.apply.return_value = [FileLine("final\n")]
        
        # 4. Execute with mock options
        opts = SimpleNamespace(strip_count=0)
        result = dcf.apply(opts)
        
        # 5. Verifications
        assert result[0].content == "final"
        
        # Verify reverse order execution
        # h2.apply should have been called first
        h2.apply.assert_called_once()
        h1.apply.assert_called_once()
        
        # Check if the result of h2 was passed as input to h1
        # The first argument of h1.apply should be the output of h2.apply
        args, _ = h1.apply.call_args
        assert args[0][0].content == "after h2"

    def test_apply_execution_path(self, mocker):
        """
        Verify full execution path of apply and close the coverage gap.
        """
        dcf = DiffCodeFile(self.header_orig)
        
        # 1. Setup a mock hunk that actually returns something
        mock_hunk = mocker.MagicMock(spec=Hunk)
        mock_hunk.old_start = 1
        # Hunk.apply must return a list of FileLines
        mock_hunk.apply.return_value = [FileLine("patched content")]
        dcf.add_hunk(mock_hunk)
        
        # 2. Setup path and file mocks
        mock_path = mocker.MagicMock(spec=Path)
        mocker.patch.object(dcf, 'get_source_path', return_value=mock_path)
        
        # Mock open with content (no newlines in content as per your rule)
        m_open = mocker.mock_open(read_data="original line")
        mocker.patch.object(mock_path, 'open', m_open)
        
        # 3. Execute with correct strip_count
        opts = SimpleNamespace(strip_count=0)
        result = dcf.apply(opts)
        
        # 4. Verify results
        assert len(result) == 1
        assert result[0].content == "patched content"
        mock_path.open.assert_called_once()
        mock_hunk.apply.assert_called_once()

    def test_diff_code_file_init_with_wrong_header_type(self):
        """
        Ensure DiffCodeFile rejects initialization with a 'new' header (+++).
        It must always start with an 'original' header (---).
        """
        # Create a 'new' header line
        wrong_header = self.header_new
        
        # Verification: Must raise FtwPatchError
        with pytest.raises(PatchParseError, match="must start with an original header"):
            DiffCodeFile(wrong_header)
