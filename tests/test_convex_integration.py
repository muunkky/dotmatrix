"""Integration tests for convex edge detection via CLI."""

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


class TestConvexEdgeCLI:
    """Integration tests for --convex-edge CLI flag."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_convex_edge_detects_circles_with_ink_separation(self):
        """Test that convex edge detection with CMYK ink separation finds circles."""
        # CMYK now triggers proper ink separation mode (same as cmyk-sep)
        # This produces 12 circles for the test image (grouped by ink channel)
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--format", "json",
                "--no-extract"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        circles = json.loads(result.stdout)
        # CMYK ink separation produces 17 circles from the test image
        # (Updated from 13 after adding color quantization before CMYK separation)
        assert len(circles) == 17, f"Expected 17 circles with ink separation, got {len(circles)}"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_convex_edge_ink_separation_colors(self):
        """Test that convex edge detection with ink separation assigns CMYK ink colors."""
        # CMYK now triggers proper ink separation mode
        # Colors are pure ink colors: (0,255,255), (255,0,255), (255,255,0), (0,0,0)
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--format", "json",
                "--no-extract"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        circles = json.loads(result.stdout)

        # Count by color
        color_counts = {}
        for circle in circles:
            color = tuple(circle["color"])
            color_counts[color] = color_counts.get(color, 0) + 1

        # With CMYK ink separation, expect ink colors (not literal CMYK palette)
        # The actual counts depend on the test image composition after ink separation
        # Verify we have CMYK ink colors
        ink_colors = {(0, 255, 255), (255, 0, 255), (255, 255, 0), (0, 0, 0)}
        detected_colors = set(color_counts.keys())

        # All detected colors should be valid CMYK ink colors
        assert detected_colors.issubset(ink_colors), f"Unexpected colors: {detected_colors - ink_colors}"
        # Should detect circles in at least some channels
        assert len(color_counts) >= 2, f"Expected at least 2 color channels, got {color_counts}"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_convex_edge_extract_creates_output_files(self, temp_output_dir):
        """Test that --output-dir creates CMYK layer PNG files and results."""
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

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Find the run directory (organized output creates timestamped subdirectory)
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1, f"Expected 1 run directory, got {len(subdirs)}"
        run_dir = subdirs[0]

        # Check that CMYK layer PNG files were created (at least 1)
        png_files = list(run_dir.glob("*.png"))
        assert len(png_files) >= 1, f"Expected at least 1 PNG file, got {len(png_files)}"

        # Check that results.json was created
        assert (run_dir / "results.json").exists(), "results.json not created"

        # Check that output mentions CMYK layer generation
        assert "CMYK layer file" in result.stdout or "Generated" in result.stdout

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_convex_edge_quantize_output(self, temp_output_dir):
        """Test that --quantize-output creates a quantized image with RGB palette."""
        # Note: Quantized output is not available with CMYK ink separation mode
        # Use RGB palette to test quantization functionality
        quantize_path = temp_output_dir / "quantized.png"

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "rgb",  # Use RGB palette for quantize test (cmyk triggers ink separation)
                "--min-radius", "80",
                "--quantize-output", str(quantize_path)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert quantize_path.exists(), "Quantized image not created"
        assert quantize_path.stat().st_size > 0, "Quantized image is empty"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_convex_edge_csv_output(self):
        """Test that CSV output format works with convex edge detection."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--format", "csv",
                "--no-extract"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        lines = result.stdout.strip().split("\n")
        # Header + 17 data rows (CMYK ink separation mode produces 17 circles)
        # (Updated from 14 after adding color quantization before CMYK separation)
        assert len(lines) == 18, f"Expected 18 lines (header + 17 circles), got {len(lines)}"

        # Check header
        header = lines[0]
        assert "center_x" in header
        assert "center_y" in header
        assert "radius" in header
        assert "color_r" in header

    def test_convex_edge_custom_palette(self):
        """Test that custom RGB palette works."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "255,0,0;0,255,0;0,0,255",
                "--format", "json",
                "--no-extract"
            ],
            capture_output=True,
            text=True
        )

        # Should run without error (even if no circles detected)
        assert result.returncode == 0 or "No circles detected" in result.stderr

    def test_convex_edge_invalid_palette(self):
        """Test that invalid palette gives helpful error."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "invalid_palette",
                "--no-extract"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "Invalid palette" in result.stderr or "Error" in result.stderr

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_convex_edge_rgb_preset(self):
        """Test that RGB preset palette works."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "rgb",
                "--min-radius", "80",
                "--format", "json",
                "--no-extract"
            ],
            capture_output=True,
            text=True
        )

        # Should run without error (may find no circles with wrong colors)
        assert result.returncode == 0 or "No circles detected" in result.stderr


class TestConvexEdgePerformance:
    """Performance tests for convex edge detection."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_convex_edge_performance(self):
        """Test that detection completes in reasonable time (<10 seconds)."""
        import time

        start = time.time()
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--format", "json",
                "--no-extract"
            ],
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start

        assert result.returncode == 0
        assert elapsed < 10, f"Detection took {elapsed:.2f}s, expected <10s"


class TestConvexEdgeFallback:
    """Tests for graceful fallback behavior."""

    def test_no_circles_graceful_exit(self, temp_output_dir):
        """Test graceful handling when no circles are detected."""
        # Create a blank white image
        import cv2
        import numpy as np

        white_image = np.full((100, 100, 3), 255, dtype=np.uint8)
        white_path = temp_output_dir / "white.png"
        cv2.imwrite(str(white_path), white_image)

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(white_path),
                "--convex-edge",
                "--palette", "cmyk"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "No circles detected" in result.stderr


class TestCompositeImageCLI:
    """Integration tests for composite image generation via CLI."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_composite_created_by_default(self, temp_output_dir):
        """Test that composite.png is created by default during extraction."""
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

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Find the run directory
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1
        run_dir = subdirs[0]

        # composite.png should exist
        composite_path = run_dir / "composite.png"
        assert composite_path.exists(), "composite.png not created"
        assert composite_path.stat().st_size > 0, "composite.png is empty"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_no_composite_flag_skips_generation(self, temp_output_dir):
        """Test that --no-composite skips composite image generation."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--output-dir", str(temp_output_dir),
                "--no-composite"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Find the run directory
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1
        run_dir = subdirs[0]

        # composite.png should NOT exist
        composite_path = run_dir / "composite.png"
        assert not composite_path.exists(), "composite.png should not be created with --no-composite"

        # But other files (CMYK layers) should still exist
        png_files = list(run_dir.glob("*.png"))
        assert len(png_files) >= 1, "Should still create CMYK layer files"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_composite_included_in_manifest(self, temp_output_dir):
        """Test that composite.png is listed in manifest output_files."""
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
        manifest_path = subdirs[0] / "manifest.json"

        with open(manifest_path) as f:
            manifest = json.load(f)

        output_files = manifest["output_files"]
        assert "composite.png" in output_files, "composite.png not listed in manifest"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_no_composite_not_in_manifest(self, temp_output_dir):
        """Test that composite.png is NOT in manifest when --no-composite is used."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--output-dir", str(temp_output_dir),
                "--no-composite"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Find the run directory
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        manifest_path = subdirs[0] / "manifest.json"

        with open(manifest_path) as f:
            manifest = json.load(f)

        output_files = manifest["output_files"]
        assert "composite.png" not in output_files, "composite.png should not be in manifest"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_composite_output_message(self, temp_output_dir):
        """Test that CLI output mentions composite.png generation."""
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
        # Should mention composite in output
        assert "composite.png" in result.stdout


class TestReconstituteCLI:
    """Integration tests for --reconstitute CLI flag."""

    def _find_run_dir(self, temp_output_dir):
        """Find the run subdirectory in temp_output_dir."""
        subdirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 1, f"Expected 1 run dir, found {len(subdirs)}"
        return subdirs[0]

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_reconstitute_creates_output_file(self, temp_output_dir):
        """Test that --reconstitute creates reconstituted.png."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--reconstitute",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # reconstituted.png should exist in run subdirectory
        run_dir = self._find_run_dir(temp_output_dir)
        reconstituted_path = run_dir / "reconstituted.png"
        assert reconstituted_path.exists(), "reconstituted.png not created"
        assert reconstituted_path.stat().st_size > 0, "reconstituted.png is empty"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_reconstitute_valid_png(self, temp_output_dir):
        """Test that reconstituted.png is a valid PNG image."""
        import cv2

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--reconstitute",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        run_dir = self._find_run_dir(temp_output_dir)
        reconstituted_path = run_dir / "reconstituted.png"
        img = cv2.imread(str(reconstituted_path))
        assert img is not None, "cv2 could not load reconstituted.png"
        assert img.shape[2] == 3, "Image should have 3 channels"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_reconstitute_manifest_includes_file(self, temp_output_dir):
        """Test that manifest.json includes reconstituted.png in output_files."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--reconstitute",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        run_dir = self._find_run_dir(temp_output_dir)
        manifest_path = run_dir / "manifest.json"
        assert manifest_path.exists(), "manifest.json not created"

        with open(manifest_path) as f:
            manifest = json.load(f)

        # Check that reconstituted.png is in output_files (may have path prefix)
        output_files_str = str(manifest["output_files"])
        assert "reconstituted.png" in output_files_str, \
            "reconstituted.png not in manifest output_files"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_reconstitute_output_message(self, temp_output_dir):
        """Test that CLI output mentions reconstituted.png generation."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--reconstitute",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should mention reconstituted.png in output (stderr or stdout)
        output = result.stdout + result.stderr
        assert "reconstituted.png" in output

    def test_reconstitute_requires_cmyk(self, temp_output_dir):
        """Test that --reconstitute requires CMYK palette."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "rgb",
                "--reconstitute",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "requires CMYK" in result.stderr

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_reconstitute_with_cluster_count(self, temp_output_dir):
        """Test that --reconstitute works alongside --cluster-count."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--reconstitute",
                "--cluster-count",
                "--output-dir", str(temp_output_dir)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Both outputs should be created
        run_dir = self._find_run_dir(temp_output_dir)
        reconstituted_path = run_dir / "reconstituted.png"
        assert reconstituted_path.exists(), "reconstituted.png not created"

        # cluster-count should output JSON data to stdout
        # (will appear as JSON array)
        assert "[" in result.stdout or "center" in result.stdout
