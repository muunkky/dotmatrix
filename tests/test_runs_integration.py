"""Integration tests for runs CLI commands."""

import json
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


class TestRunsListCommand:
    """Integration tests for 'dotmatrix runs list' command."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_list_shows_created_runs(self, temp_output_dir):
        """Test that list command shows created runs."""
        # Create a run
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # List runs
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "list",
                "--dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "test_dotmatrix.png" in result.stdout
        # CMYK ink separation produces 12 circles
        assert "12" in result.stdout  # Circle count

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_list_filter_by_source(self, temp_output_dir):
        """Test that list command filters by source."""
        # Create a run
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--min-radius", "80",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Filter by existing source
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "list",
                "--dir", str(temp_output_dir),
                "--source", "test_dotmatrix"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "test_dotmatrix.png" in result.stdout

        # Filter by non-existing source
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "list",
                "--dir", str(temp_output_dir),
                "--source", "nonexistent"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "No runs found" in result.stdout


class TestRunsShowCommand:
    """Integration tests for 'dotmatrix runs show' command."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_show_displays_manifest(self, temp_output_dir):
        """Test that show command displays manifest details."""
        # Create a run
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Find the run directory
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1
        run_name = subdirs[0].name

        # Show the run
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "show", run_name,
                "--dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Run:" in result.stdout
        assert "Settings:" in result.stdout
        assert "Results:" in result.stdout
        # CMYK ink separation produces 12 circles
        assert "Total circles: 12" in result.stdout
        assert "Output files:" in result.stdout

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_show_nonexistent_run(self, temp_output_dir):
        """Test show command with nonexistent run."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "show", "nonexistent_run",
                "--dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "not found" in result.stderr


class TestRunsReplayCommand:
    """Integration tests for 'dotmatrix runs replay' command."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_replay_dry_run(self, temp_output_dir):
        """Test that replay --dry-run shows command."""
        # Create a run
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Find the run directory
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        run_name = subdirs[0].name

        # Replay with dry-run
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "replay", run_name,
                "--dir", str(temp_output_dir),
                "--dry-run"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "python3 -m dotmatrix" in result.stdout
        assert "--convex-edge" in result.stdout
        assert "--min-radius 80" in result.stdout
        assert str(TEST_IMAGE) in result.stdout

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_replay_produces_same_results(self, temp_output_dir):
        """Test that replay produces same results."""
        # Create a run
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Find the run directory
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        run_name = subdirs[0].name

        # Get the replay command
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "replay", run_name,
                "--dir", str(temp_output_dir),
                "--dry-run"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Run the command with --no-extract to get JSON output on stdout
        cmd = result.stdout.strip() + " --no-extract"
        # Execute and check circle count
        replay_result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )

        assert replay_result.returncode == 0
        circles = json.loads(replay_result.stdout)
        # CMYK ink separation produces 12 circles
        assert len(circles) == 12


class TestBlackVerification:
    """Integration tests for black dot verification feature."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_verification_enabled_by_default(self, temp_output_dir):
        """Test that verification is enabled by default for CMYK mode."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Verification output should appear on stderr
        assert "Black Dot Verification:" in result.stderr
        assert "Circles detected:" in result.stderr

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_verification_includes_in_manifest(self, temp_output_dir):
        """Test that verification data is included in manifest."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Find manifest and check for verification
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1
        manifest_path = subdirs[0] / "manifest.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            manifest = json.load(f)

        assert "verification" in manifest
        assert "black_circles_detected" in manifest["verification"]
        assert "radius_mean" in manifest["verification"]
        assert "passed" in manifest["verification"]

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_no_verify_black_disables_verification(self, temp_output_dir):
        """Test that --no-verify-black disables verification."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--output-dir", str(temp_output_dir),
                "--no-verify-black"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Verification output should NOT appear
        assert "Black Dot Verification:" not in result.stderr

        # Check manifest doesn't have verification
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        manifest_path = subdirs[0] / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert "verification" not in manifest

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_verify_abort_exits_on_warnings(self, temp_output_dir):
        """Test that --verify-abort exits with error when verification has warnings."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",  # This will trigger warnings about low count
                "--output-dir", str(temp_output_dir),
                "--verify-abort"
            ],
            capture_output=True,
            text=True
        )

        # Should exit with error due to warnings
        assert result.returncode == 1
        assert "Aborting due to verification warnings" in result.stderr


class TestBackwardCompatibility:
    """Test backward compatibility with existing CLI usage."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_detect_without_subcommand(self, temp_output_dir):
        """Test that detect works without 'detect' subcommand."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--min-radius", "80",
                "--format", "json",
                "--no-extract"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        circles = json.loads(result.stdout)
        # Default behavior now produces 12 circles (convex-edge with default palette)
        assert len(circles) == 12
