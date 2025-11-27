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
    def test_convex_edge_detects_16_circles(self):
        """Test that convex edge detection finds all 16 circles in test image."""
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
        assert len(circles) == 16, f"Expected 16 circles, got {len(circles)}"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_convex_edge_correct_color_counts(self):
        """Test that convex edge detection assigns correct colors."""
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

        # Expect 4 of each: black, cyan, magenta, yellow
        expected_colors = {
            (0, 0, 0): 4,        # Black
            (118, 193, 241): 4,  # Cyan
            (217, 93, 155): 4,   # Magenta
            (238, 206, 94): 4,   # Yellow
        }

        assert color_counts == expected_colors, f"Color counts mismatch: {color_counts}"

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
        """Test that --quantize-output creates a quantized image."""
        quantize_path = temp_output_dir / "quantized.png"

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
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
        # Header + 16 data rows
        assert len(lines) == 17, f"Expected 17 lines (header + 16 circles), got {len(lines)}"

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
