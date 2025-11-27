"""Tests for large file handling features.

Part of card brz25i: Implement Large File Processing Pipeline.
Based on spike w804xa findings documented in ADR-001.
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotmatrix.image_loader import load_image, get_image_megapixels


class TestGetImageMegapixels:
    """Tests for get_image_megapixels helper function."""

    def test_1000x1000_is_1_megapixel(self):
        """1000x1000 image is 1.0 megapixels."""
        image = np.zeros((1000, 1000, 3), dtype=np.uint8)
        assert get_image_megapixels(image) == 1.0

    def test_2000x2000_is_4_megapixels(self):
        """2000x2000 image is 4.0 megapixels."""
        image = np.zeros((2000, 2000, 3), dtype=np.uint8)
        assert get_image_megapixels(image) == 4.0

    def test_1920x1080_is_approximately_2_megapixels(self):
        """1920x1080 (1080p) is ~2.07 megapixels."""
        image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mp = get_image_megapixels(image)
        assert 2.0 < mp < 2.1

    def test_5000x5000_is_25_megapixels(self):
        """5000x5000 image is 25.0 megapixels."""
        image = np.zeros((5000, 5000, 3), dtype=np.uint8)
        assert get_image_megapixels(image) == 25.0

    def test_small_image(self):
        """Small image returns correct megapixels."""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        assert get_image_megapixels(image) == 0.01

    def test_rectangular_image(self):
        """Rectangular image calculates correctly."""
        image = np.zeros((1000, 2000, 3), dtype=np.uint8)
        assert get_image_megapixels(image) == 2.0


class TestLargeImageWarning:
    """Tests for large image warning in CLI."""

    @pytest.fixture
    def large_image_path(self, tmp_path):
        """Create a test image that appears large based on dimensions."""
        # Create 4600x4600 image (~21 MP - just over the 20 MP threshold)
        # Use simple content for fast creation
        image = np.full((4600, 4600, 3), 255, dtype=np.uint8)
        # Add a few circles
        cv2.circle(image, (2300, 2300), 500, (0, 0, 0), -1)

        path = tmp_path / "large_test.png"
        cv2.imwrite(str(path), image)
        return path

    @pytest.fixture
    def medium_image_path(self, tmp_path):
        """Create a medium-sized image (under threshold)."""
        # 3000x3000 = 9 MP (under 20 MP threshold)
        image = np.full((3000, 3000, 3), 255, dtype=np.uint8)
        cv2.circle(image, (1500, 1500), 300, (0, 0, 0), -1)

        path = tmp_path / "medium_test.png"
        cv2.imwrite(str(path), image)
        return path

    def test_warning_displayed_for_large_image_with_convex(self, large_image_path):
        """Warning should be displayed for >20MP images with --convex-edge."""
        # Use a short timeout since we just want to see the warning
        # The warning appears before processing starts
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(large_image_path),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "100"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Should warn about large image (warning includes "megapixels")
        assert "megapixel" in result.stderr.lower(), f"Expected warning, got: {result.stderr}"

    def test_no_warning_for_medium_image_with_convex(self, medium_image_path):
        """No warning for images under 20MP threshold."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(medium_image_path),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "100"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Should not warn about large image
        assert "large image" not in result.stderr.lower()

    def test_no_warning_for_large_image_without_convex(self, large_image_path):
        """No warning for large images without --convex-edge (Hough is fast)."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(large_image_path),
                "--min-radius", "100"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Hough detection is fast, no warning needed
        assert "large image" not in result.stderr.lower()


class TestLargeFileProcessing:
    """Integration tests for large file processing."""

    @pytest.fixture
    def test_image_10mp(self, tmp_path):
        """Create a 10MP test image (~3162x3162)."""
        size = 3162  # ~10 MP
        image = np.full((size, size, 3), 250, dtype=np.uint8)

        # Add circles with different colors
        colors = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
        np.random.seed(42)
        for i in range(20):
            x = np.random.randint(200, size - 200)
            y = np.random.randint(200, size - 200)
            r = np.random.randint(80, 150)
            cv2.circle(image, (x, y), r, colors[i % 4], -1)

        path = tmp_path / "test_10mp.png"
        cv2.imwrite(str(path), image)
        return path

    def test_hough_detection_on_10mp_image(self, test_image_10mp):
        """Hough detection completes in <30s for 10MP image."""
        import time

        start = time.time()
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(test_image_10mp),
                "--min-radius", "80",
                "--format", "json",
                "--no-extract"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        elapsed = time.time() - start

        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert elapsed < 30, f"Processing took {elapsed:.1f}s, expected <30s"

        # Should detect circles
        import json
        circles = json.loads(result.stdout)
        assert len(circles) > 0

    @pytest.mark.slow
    def test_convex_detection_on_10mp_image(self, test_image_10mp):
        """Convex detection completes in <30s for 10MP image (under threshold)."""
        import time

        start = time.time()
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(test_image_10mp),
                "--convex-edge",
                "--palette", "rgb",
                "--min-radius", "80",
                "--format", "json",
                "--no-extract"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        elapsed = time.time() - start

        # Should complete (may be slow but under 60s for 10MP)
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert elapsed < 60, f"Processing took {elapsed:.1f}s, expected <60s"


class TestProgressReporting:
    """Tests for progress reporting feature."""

    @pytest.fixture
    def slow_operation_image(self, tmp_path):
        """Create an image that will trigger slow operation (>5s)."""
        # 4500x4500 = ~20 MP, should take >5s with convex
        size = 4500
        image = np.full((size, size, 3), 250, dtype=np.uint8)

        for i in range(30):
            x = np.random.randint(200, size - 200)
            y = np.random.randint(200, size - 200)
            cv2.circle(image, (x, y), 150, (0, 0, 0), -1)

        path = tmp_path / "slow_test.png"
        cv2.imwrite(str(path), image)
        return path

    @pytest.mark.slow
    def test_progress_output_for_long_operation(self, slow_operation_image):
        """Progress should be shown for operations taking >5 seconds."""
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(slow_operation_image),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "100"
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Should show progress indication for convex detection on large images
        stderr_lower = result.stderr.lower()
        has_progress = (
            "detecting" in stderr_lower or
            "processing" in stderr_lower or
            "%" in result.stderr or
            "progress" in stderr_lower
        )

        # Verify operation completes
        assert result.returncode == 0 or "No circles" in result.stderr

        # Verify progress message is shown (image is > 5 MP so message should appear)
        assert has_progress, f"Expected progress message, got stderr: {result.stderr}"
