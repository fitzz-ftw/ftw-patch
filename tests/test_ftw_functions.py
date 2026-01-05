import sys
from argparse import ArgumentError
from pathlib import Path

import pytest

from ftw.patch.ftw_patch import FtwPatchError, _get_argparser, prog_ftw_patch


class TestCLI:
    def test_parser_defaults(self):
        """Tests if the parser sets correct defaults with only required arguments."""
        parser = _get_argparser()
        args = parser.parse_args(["my.patch"])
        
        assert args.patch_file == Path("my.patch")
        assert args.strip_count == 0
        assert args.target_directory == Path(".")
        assert args.normalize_whitespace is False
        assert args.ignore_blank_lines is False
        assert args.ignore_all_whitespace is False
        assert args.dry_run is False
        assert args.verbose == 0

    def test_parser_full_options(self):
        """Tests if all CLI flags are correctly mapped to their destinations."""
        parser = _get_argparser()
        cmd = [
            "fixed.patch",
            "--strip", "2",
            "--directory", "/tmp/target",
            "--normalize-ws",
            "--ignore-bl",
            "--ignore-all-ws",
            "--dry-run",
            "-vvv"
        ]
        args = parser.parse_args(cmd)
        
        assert args.patch_file == Path("fixed.patch")
        assert args.strip_count == 2
        assert args.target_directory == Path("/tmp/target")
        assert args.normalize_whitespace is True
        assert args.ignore_blank_lines is True
        assert args.ignore_all_whitespace is True
        assert args.dry_run is True
        assert args.verbose == 3

    def test_parser_invalid_strip_count(self):
        """Tests if the parser rejects non-integer values for strip count."""
        parser = _get_argparser()
        # argparse raises SystemExit on error and prints to stderr
        # with pytest.raises(SystemExit):
        with pytest.raises(ArgumentError):
            parser.parse_args(["my.patch", "--strip", "not-an-int"])

class TestMainEntry:
    def test_prog_ftw_patch_success(self, mocker):
        """Tests the successful execution path (Returns 0)."""
        # Mock Parser
        mock_args = mocker.Mock(dry_run=False)
        mocker.patch("ftw.patch.ftw_patch._get_argparser").return_value.parse_args.return_value = mock_args  # noqa: E501
        
        # Mock FtwPatch logic
        mock_patcher = mocker.patch("ftw.patch.ftw_patch.FtwPatch")
        mock_patcher.return_value.apply_patch.return_value = 0
        
        exit_code = prog_ftw_patch()
        assert exit_code == 0
        mock_patcher.return_value.apply_patch.assert_called_once_with(dry_run=False)

    def test_prog_ftw_patch_ftw_error(self, mocker, capsys):
        """Tests the handling of a known FtwPatchError (Returns 1)."""
        mocker.patch("ftw.patch.ftw_patch._get_argparser").return_value.parse_args.return_value = mocker.Mock()  # noqa: E501
        
        # Force a FtwPatchError during initialization
        mocker.patch("ftw.patch.ftw_patch.FtwPatch", side_effect=FtwPatchError("Parser fail"))
        
        exit_code = prog_ftw_patch()
        
        assert exit_code == 1
        stderr = capsys.readouterr().err
        assert "An ftw_patch error occurred: Parser fail" in stderr

    def test_prog_ftw_patch_unexpected_error(self, mocker, capsys):
        """Tests the handling of an unexpected generic Exception (Returns 1)."""
        mocker.patch("ftw.patch.ftw_patch._get_argparser", side_effect=RuntimeError("System crash"))
        
        exit_code = prog_ftw_patch()
        
        assert exit_code == 1
        stderr = capsys.readouterr().err
        assert "An unexpected error occurred: System crash" in stderr

    def test_prog_ftw_patch_filenotfound_error(self, mocker, capsys):
        """
        Tests the handling of FileNotFoundError within the main entry point.
        Covers lines 1635-1636.
        """
        # 1. Mock parser to return a valid namespace
        mock_args = mocker.Mock(dry_run=False)
        mocker.patch("ftw.patch.ftw_patch._get_argparser").return_value.parse_args.return_value = mock_args  # noqa: E501
        
        # 2. Mock FtwPatch to raise the specific FileNotFoundError
        mocker.patch("ftw.patch.ftw_patch.FtwPatch", side_effect=FileNotFoundError("Target file missing"))  # noqa: E501
        
        # 3. Execute
        exit_code = prog_ftw_patch()
        
        # 4. Verify
        assert exit_code == 1
        stderr = capsys.readouterr().err
        assert "File System Error: Target file missing" in stderr
