"""Integration tests for run organization feature."""

import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest


# Path to test image
TEST_IMAGE = Path(__file__).parent.parent / "test_dotmatrix.png"


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestRunOrganizationCLI:
    """Integration tests for --run-name and --no-organize flags."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_extract_creates_timestamped_dir_by_default(self, temp_output_dir):
        """Test that --extract creates a timestamped subdirectory by default."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--extract", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Should have created a timestamped subdirectory
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1, f"Expected 1 subdirectory, got {len(subdirs)}"

        # Subdirectory should match timestamp pattern
        subdir = subdirs[0]
        assert re.match(r'^run_\d{8}_\d{6}$', subdir.name), f"Unexpected dir name: {subdir.name}"

        # Should contain PNG files
        png_files = list(subdir.glob("*.png"))
        assert len(png_files) == 4, f"Expected 4 PNG files, got {len(png_files)}"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_run_name_creates_named_dir(self, temp_output_dir):
        """Test that --run-name creates a custom-named subdirectory."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--extract", str(temp_output_dir),
                "--run-name", "my-experiment"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Should have created a named subdirectory
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1

        # Subdirectory should start with custom name (hyphens sanitized to underscores)
        subdir = subdirs[0]
        assert subdir.name.startswith("my_experiment_"), f"Unexpected dir name: {subdir.name}"

        # Should contain PNG files
        png_files = list(subdir.glob("*.png"))
        assert len(png_files) == 4

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_no_organize_uses_flat_output(self, temp_output_dir):
        """Test that --no-organize puts files directly in extract dir."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--extract", str(temp_output_dir),
                "--no-organize"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Should NOT have created a subdirectory
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 0, f"Expected no subdirectories, got {len(subdirs)}"

        # PNG files should be directly in output dir
        png_files = list(temp_output_dir.glob("*.png"))
        assert len(png_files) == 4, f"Expected 4 PNG files, got {len(png_files)}"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_multiple_runs_create_separate_dirs(self, temp_output_dir):
        """Test that multiple runs create separate directories."""
        import time

        # First run
        result1 = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--extract", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )
        assert result1.returncode == 0

        # Wait for timestamp to change
        time.sleep(1)

        # Second run
        result2 = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--extract", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )
        assert result2.returncode == 0

        # Should have two separate directories
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 2, f"Expected 2 subdirectories, got {len(subdirs)}"

        # Each should have PNG files
        for subdir in subdirs:
            png_files = list(subdir.glob("*.png"))
            assert len(png_files) == 4

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_run_name_with_spaces(self, temp_output_dir):
        """Test that --run-name with spaces is sanitized."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--extract", str(temp_output_dir),
                "--run-name", "My Test Experiment"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1

        # Name should be sanitized (spaces to underscores)
        subdir = subdirs[0]
        assert "My_Test_Experiment" in subdir.name

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_output_shows_correct_path(self, temp_output_dir):
        """Test that CLI output shows the correct output directory path."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--extract", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Output should mention the actual output directory (not just base dir)
        # The run directory should be in the output
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1
        run_dir = subdirs[0]

        assert str(run_dir) in result.stdout, f"Output dir not in stdout: {result.stdout}"
