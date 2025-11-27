"""End-to-end workflow tests for WORKFLOW sprint features.

Tests the complete workflow: create runs, save/load config, list, show, replay.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml


# Path to test image
TEST_IMAGE = Path(__file__).parent.parent / "test_dotmatrix.png"


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
class TestE2EWorkflow:
    """End-to-end workflow tests."""

    def test_complete_workflow(self, temp_workspace):
        """Test full workflow: config -> extract -> manifest -> list -> show -> replay."""
        config_path = temp_workspace / "my_config.yaml"
        output_dir = temp_workspace / "output"

        # Step 1: Run detection with config save
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--output-dir", str(output_dir),
                "--save-config", str(config_path)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Detection failed: {result.stderr}"
        assert "Generated" in result.stdout or "CMYK" in result.stdout

        # Step 2: Verify config was saved
        assert config_path.exists(), "Config file not created"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config is not None

        # Step 3: Verify run directory with manifest
        subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1
        run_dir = subdirs[0]
        run_name = run_dir.name

        manifest_path = run_dir / "manifest.json"
        assert manifest_path.exists(), "Manifest not created"

        with open(manifest_path) as f:
            manifest = json.load(f)
        assert manifest["results"]["total_circles"] == 16

        # Step 4: List runs
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "list",
                "--dir", str(output_dir)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert run_name in result.stdout
        assert "test_dotmatrix.png" in result.stdout

        # Step 5: Show run details
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "show", run_name,
                "--dir", str(output_dir)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Total circles: 16" in result.stdout
        assert "convex_edge" in result.stdout

        # Step 6: Replay with dry-run
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "replay", run_name,
                "--dir", str(output_dir),
                "--dry-run"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--convex-edge" in result.stdout
        assert "--min-radius 80" in result.stdout

        # Step 7: Create new run using saved config
        output_dir2 = temp_workspace / "output2"
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--config", str(config_path),
                "--output-dir", str(output_dir2)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Generated" in result.stdout or "CMYK" in result.stdout

        # Verify same results
        subdirs2 = [d for d in output_dir2.iterdir() if d.is_dir()]
        manifest_path2 = subdirs2[0] / "manifest.json"
        with open(manifest_path2) as f:
            manifest2 = json.load(f)
        assert manifest2["results"]["total_circles"] == 16

    def test_filter_runs_by_source(self, temp_workspace):
        """Test filtering runs by source file."""
        output_dir = temp_workspace / "output"

        # Create a run
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--min-radius", "80",
                "--output-dir", str(output_dir)
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Filter by source - should find it
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "list",
                "--dir", str(output_dir),
                "--source", "test_dotmatrix"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "test_dotmatrix.png" in result.stdout

        # Filter by different source - should not find it
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "runs", "list",
                "--dir", str(output_dir),
                "--source", "nonexistent"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "No runs found" in result.stdout

    def test_no_organize_mode(self, temp_workspace):
        """Test flat output without organized directories."""
        output_dir = temp_workspace / "output"

        # Create run with --no-organize
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--min-radius", "80",
                "--output-dir", str(output_dir),
                "--no-organize"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Files should be directly in output_dir
        png_files = list(output_dir.glob("*.png"))
        assert len(png_files) >= 1

        # Manifest should be directly in output_dir
        manifest_path = output_dir / "manifest.json"
        assert manifest_path.exists()

    def test_no_manifest_mode(self, temp_workspace):
        """Test disabling manifest generation."""
        output_dir = temp_workspace / "output"

        # Create run with --no-manifest
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--min-radius", "80",
                "--output-dir", str(output_dir),
                "--no-manifest"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Find run directory
        subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        run_dir = subdirs[0]

        # PNG files should exist
        png_files = list(run_dir.glob("*.png"))
        assert len(png_files) >= 1

        # Manifest should NOT exist
        manifest_path = run_dir / "manifest.json"
        assert not manifest_path.exists()

    def test_custom_run_name(self, temp_workspace):
        """Test custom run naming."""
        output_dir = temp_workspace / "output"

        # Create run with custom name
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--min-radius", "80",
                "--output-dir", str(output_dir),
                "--run-name", "my_experiment"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Find run directory - name should start with custom name
        subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1
        run_dir = subdirs[0]
        assert run_dir.name.startswith("my_experiment_")
