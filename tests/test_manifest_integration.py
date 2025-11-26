"""Integration tests for manifest generation via CLI."""

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


class TestManifestCLI:
    """Integration tests for manifest generation."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_extract_creates_manifest(self, temp_output_dir):
        """Test that --extract creates manifest.json by default."""
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

        # Find the run directory
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1
        run_dir = subdirs[0]

        # Check manifest exists
        manifest_path = run_dir / "manifest.json"
        assert manifest_path.exists(), "manifest.json not created"

        # Verify it's valid JSON
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest is not None

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_manifest_has_required_fields(self, temp_output_dir):
        """Test that manifest contains all required fields."""
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

        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        manifest_path = subdirs[0] / "manifest.json"

        with open(manifest_path) as f:
            manifest = json.load(f)

        # Check required fields
        assert "dotmatrix_version" in manifest
        assert "timestamp" in manifest
        assert "source_file" in manifest
        assert "settings" in manifest
        assert "results" in manifest
        assert "output_files" in manifest

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_manifest_source_file_hash(self, temp_output_dir):
        """Test that manifest includes source file hash."""
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

        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        manifest_path = subdirs[0] / "manifest.json"

        with open(manifest_path) as f:
            manifest = json.load(f)

        source_file = manifest["source_file"]
        assert "hash" in source_file
        assert source_file["hash"].startswith("sha256:")

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_manifest_results_summary(self, temp_output_dir):
        """Test that manifest includes accurate results summary."""
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

        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        manifest_path = subdirs[0] / "manifest.json"

        with open(manifest_path) as f:
            manifest = json.load(f)

        results = manifest["results"]
        assert results["total_circles"] == 16

        # Should have 4 colors (CMYK minus white)
        by_color = results["circles_by_color"]
        assert len(by_color) == 4  # black, cyan, magenta, yellow

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_manifest_output_files_list(self, temp_output_dir):
        """Test that manifest lists output files."""
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

        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        run_dir = subdirs[0]
        manifest_path = run_dir / "manifest.json"

        with open(manifest_path) as f:
            manifest = json.load(f)

        output_files = manifest["output_files"]
        assert len(output_files) == 4  # 4 color groups

        # Verify listed files exist
        for filename in output_files:
            assert (run_dir / filename).exists(), f"Listed file {filename} not found"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_no_manifest_flag(self, temp_output_dir):
        """Test that --no-manifest skips manifest generation."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--extract", str(temp_output_dir),
                "--no-manifest"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        run_dir = subdirs[0]

        # manifest.json should NOT exist
        manifest_path = run_dir / "manifest.json"
        assert not manifest_path.exists(), "manifest.json should not be created with --no-manifest"

        # But PNG files should still exist
        png_files = list(run_dir.glob("*.png"))
        assert len(png_files) == 4

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_manifest_includes_settings(self, temp_output_dir):
        """Test that manifest includes detection settings."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--max-radius", "350",
                "--sensitivity", "relaxed",
                "--extract", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        manifest_path = subdirs[0] / "manifest.json"

        with open(manifest_path) as f:
            manifest = json.load(f)

        settings = manifest["settings"]
        assert settings["min_radius"] == 80
        assert settings["max_radius"] == 350
        assert settings["sensitivity"] == "relaxed"
        assert settings["convex_edge"] is True
        assert settings["palette"] == "cmyk"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_manifest_includes_version(self, temp_output_dir):
        """Test that manifest includes dotmatrix version."""
        from dotmatrix import __version__

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

        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        manifest_path = subdirs[0] / "manifest.json"

        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest["dotmatrix_version"] == __version__
