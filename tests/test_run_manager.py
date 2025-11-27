"""Tests for run_manager module."""

import re
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from dotmatrix.run_manager import (
    sanitize_filename,
    generate_timestamp,
    create_run_directory,
    get_run_info,
    copy_input_file,
    get_default_output_dir,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_basic_string(self):
        """Test that a basic string passes through."""
        assert sanitize_filename("my_run") == "my_run"

    def test_spaces_to_underscores(self):
        """Test that spaces are converted to underscores."""
        assert sanitize_filename("my run name") == "my_run_name"

    def test_special_characters_removed(self):
        """Test that special characters are removed."""
        assert sanitize_filename("test@#$%^&*()!") == "test"

    def test_consecutive_separators_collapsed(self):
        """Test that consecutive underscores/hyphens are collapsed."""
        assert sanitize_filename("test___name") == "test_name"
        assert sanitize_filename("test---name") == "test_name"
        assert sanitize_filename("test-_-name") == "test_name"

    def test_leading_trailing_separators_removed(self):
        """Test that leading/trailing separators are removed."""
        assert sanitize_filename("_test_") == "test"
        assert sanitize_filename("-test-") == "test"
        assert sanitize_filename("...test...") == "test"

    def test_max_length_truncation(self):
        """Test that long names are truncated."""
        long_name = "a" * 100
        result = sanitize_filename(long_name, max_length=50)
        assert len(result) <= 50

    def test_empty_string_returns_unnamed(self):
        """Test that empty/invalid strings return 'unnamed'."""
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("@#$%") == "unnamed"

    def test_preserves_dots_in_middle(self):
        """Test that dots are preserved in the middle of names."""
        assert sanitize_filename("test.v1") == "test.v1"

    def test_unicode_handling(self):
        """Test that unicode is handled gracefully."""
        result = sanitize_filename("test_émoji_🎉")
        assert "test" in result
        # Non-ASCII should be removed by the regex


class TestGenerateTimestamp:
    """Tests for generate_timestamp function."""

    def test_format(self):
        """Test that timestamp has correct format."""
        timestamp = generate_timestamp()
        # Format: YYYYMMDD_HHMMSS
        assert re.match(r'^\d{8}_\d{6}$', timestamp)

    def test_is_current(self):
        """Test that timestamp is approximately current time."""
        before = datetime.now().strftime('%Y%m%d')
        timestamp = generate_timestamp()
        after = datetime.now().strftime('%Y%m%d')

        # Date portion should match
        date_portion = timestamp[:8]
        assert date_portion in [before, after]


class TestCreateRunDirectory:
    """Tests for create_run_directory function."""

    def test_creates_timestamped_dir_by_default(self):
        """Test that default creates timestamped subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            run_dir = create_run_directory(base)

            # Should be a subdirectory
            assert run_dir.parent == base
            # Should exist
            assert run_dir.exists()
            # Name should start with "run_"
            assert run_dir.name.startswith("run_")
            # Should have timestamp format
            assert re.match(r'^run_\d{8}_\d{6}$', run_dir.name)

    def test_custom_run_name(self):
        """Test that custom name is used with timestamp suffix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            run_dir = create_run_directory(base, run_name="myexperiment")

            assert run_dir.exists()
            # Should start with sanitized name
            assert run_dir.name.startswith("myexperiment_")
            # Should have timestamp suffix
            assert re.match(r'^myexperiment_\d{8}_\d{6}$', run_dir.name)

    def test_no_organize_uses_base_dir(self):
        """Test that organize=False uses base directory directly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            run_dir = create_run_directory(base, organize=False)

            # Should be the same as base
            assert run_dir == base
            assert run_dir.exists()

    def test_creates_nested_directories(self):
        """Test that parent directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "deep" / "nested" / "path"
            run_dir = create_run_directory(base)

            assert run_dir.exists()
            assert base.exists()

    def test_custom_name_sanitized(self):
        """Test that custom names are sanitized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            run_dir = create_run_directory(base, run_name="My Test Run!")

            assert run_dir.exists()
            # Should be sanitized
            assert "My_Test_Run" in run_dir.name

    def test_multiple_runs_unique(self):
        """Test that multiple runs get unique directories."""
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            run1 = create_run_directory(base)
            time.sleep(1)  # Ensure different timestamp
            run2 = create_run_directory(base)

            assert run1 != run2
            assert run1.exists()
            assert run2.exists()


class TestGetRunInfo:
    """Tests for get_run_info function."""

    def test_returns_basic_info(self):
        """Test that basic run info is returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            info = get_run_info(run_dir)

            assert 'path' in info
            assert 'name' in info
            assert 'created' in info
            assert info['path'] == tmpdir
            assert info['name'] == Path(tmpdir).name

    def test_created_is_iso_format(self):
        """Test that created timestamp is ISO format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            info = get_run_info(run_dir)

            # Should be parseable as ISO datetime
            datetime.fromisoformat(info['created'])


class TestCopyInputFile:
    """Tests for copy_input_file function."""

    def test_copies_file_to_run_dir(self):
        """Test that input file is copied to run directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a source file
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            source_file = source_dir / "test_image.png"
            source_file.write_text("test content")

            # Create run directory
            run_dir = Path(tmpdir) / "run"
            run_dir.mkdir()

            # Copy input file
            copied_path = copy_input_file(source_file, run_dir)

            # Verify
            assert copied_path.exists()
            assert copied_path.name == "input_test_image.png"
            assert copied_path.read_text() == "test content"

    def test_preserves_original(self):
        """Test that original file is not modified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "original.png"
            source_file.write_text("original content")

            run_dir = Path(tmpdir) / "run"
            run_dir.mkdir()

            copy_input_file(source_file, run_dir)

            # Original should still exist and be unchanged
            assert source_file.exists()
            assert source_file.read_text() == "original content"

    def test_input_prefix_added(self):
        """Test that 'input_' prefix is added to copied file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "my_file.png"
            source_file.write_text("test")

            run_dir = Path(tmpdir) / "run"
            run_dir.mkdir()

            copied_path = copy_input_file(source_file, run_dir)

            assert copied_path.name.startswith("input_")


class TestGetDefaultOutputDir:
    """Tests for get_default_output_dir function."""

    def test_returns_output_path(self):
        """Test that default output directory is 'output'."""
        default_dir = get_default_output_dir()
        assert default_dir == Path('output')
