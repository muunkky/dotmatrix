"""
Test CLI warning messages for large images with convex-edge detection.

Tests the size warning feature that alerts users when using --convex-edge
on images exceeding 20MP, which can have significant performance impact.
"""

import pytest
import numpy as np
from click.testing import CliRunner
from pathlib import Path
import tempfile
import cv2

from dotmatrix.cli import cli


class TestLargeImageConvexWarning:
    """Test warning behavior for large images with convex-edge detection."""

    @pytest.fixture
    def runner(self):
        """Provide a Click test runner."""
        return CliRunner()

    @pytest.fixture
    def small_test_image(self, tmp_path):
        """Create a small test image (< 20MP) for testing."""
        # 3000x3000 = 9MP (below threshold)
        image = np.random.randint(0, 255, (3000, 3000, 3), dtype=np.uint8)
        image_path = tmp_path / "small_test.png"
        cv2.imwrite(str(image_path), image)
        return image_path

    @pytest.fixture
    def large_test_image(self, tmp_path):
        """Create a large test image (> 20MP) for testing."""
        # 5000x5000 = 25MP (above threshold)
        image = np.random.randint(0, 255, (5000, 5000, 3), dtype=np.uint8)
        image_path = tmp_path / "large_test.png"
        cv2.imwrite(str(image_path), image)
        return image_path

    def test_warning_appears_for_large_image_with_convex_edge(self, runner, large_test_image, tmp_path):
        """
        Test that warning is displayed when using --convex-edge on large images.
        
        Given: A large image (>20MP)
        When: Running detection with --convex-edge flag
        Then: Warning message should appear on stderr
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = runner.invoke(cli, [
            'detect',
            str(large_test_image),
            '--convex-edge',
            '--palette', 'cmyk',
            '--output-dir', str(output_dir),
            '--no-extract'  # Skip output generation for speed
        ])

        # Check that warning appears in stderr
        assert "Warning" in result.stderr or "Warning" in result.output
        assert "convex-edge" in result.stderr.lower() or "convex-edge" in result.output.lower()
        assert "MP" in result.stderr or "MP" in result.output
        assert "large image" in result.stderr.lower() or "large image" in result.output.lower()

    def test_no_warning_for_small_image_with_convex_edge(self, runner, small_test_image, tmp_path):
        """
        Test that no warning is displayed for small images with --convex-edge.
        
        Given: A small image (≤20MP)
        When: Running detection with --convex-edge flag
        Then: Warning message should NOT appear
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = runner.invoke(cli, [
            'detect',
            str(small_test_image),
            '--convex-edge',
            '--palette', 'cmyk',
            '--output-dir', str(output_dir),
            '--no-extract'
        ])

        # Check that convex-edge warning does NOT appear
        # (Other warnings may appear, so check specifically for convex-edge warning)
        stderr_lower = result.stderr.lower()
        
        # If there's a warning, it should NOT be about convex-edge and large images
        if "warning" in stderr_lower:
            assert not ("convex-edge" in stderr_lower and "large" in stderr_lower)

    def test_no_warning_for_large_image_without_convex_edge(self, runner, large_test_image, tmp_path):
        """
        Test that no warning is displayed for large images without --convex-edge.
        
        Given: A large image (>20MP)
        When: Running detection WITHOUT --convex-edge flag
        Then: Convex-edge warning should NOT appear
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = runner.invoke(cli, [
            'detect',
            str(large_test_image),
            '--output-dir', str(output_dir),
            '--no-extract'
        ])

        # Check that convex-edge warning does NOT appear
        stderr_lower = result.stderr.lower()
        
        # May have other warnings (sliding window auto-enable, etc), 
        # but should NOT warn about convex-edge
        if "warning" in stderr_lower:
            assert not ("convex-edge" in stderr_lower)

    def test_warning_message_content(self, runner, large_test_image, tmp_path):
        """
        Test that warning message contains helpful information.
        
        Given: A large image with convex-edge enabled
        When: Warning is displayed
        Then: Message should include image size, performance note, and suggestions
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = runner.invoke(cli, [
            'detect',
            str(large_test_image),
            '--convex-edge',
            '--palette', 'cmyk',
            '--output-dir', str(output_dir),
            '--no-extract'
        ])

        combined_output = result.stderr + result.output

        # Check for key components of warning message
        assert "MP" in combined_output  # Image size in megapixels
        assert "slow" in combined_output.lower() or "performance" in combined_output.lower()
        
        # Check for suggestions (at least one should be present)
        has_suggestion = (
            "sliding-window" in combined_output.lower() or
            "sliding window" in combined_output.lower() or
            "preprocessing" in combined_output.lower() or
            "reduce resolution" in combined_output.lower()
        )
        assert has_suggestion, "Warning should suggest alternatives"

    def test_warning_does_not_block_execution(self, runner, large_test_image, tmp_path):
        """
        Test that warning does not prevent detection from running.
        
        Given: A large image with convex-edge enabled
        When: Warning is displayed
        Then: Detection should still proceed normally
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = runner.invoke(cli, [
            'detect',
            str(large_test_image),
            '--convex-edge',
            '--palette', 'cmyk',
            '--output-dir', str(output_dir),
            '--no-extract',
            '--no-verify-black'  # Skip verification for speed
        ])

        # Command should succeed (exit code 0)
        assert result.exit_code == 0, f"Command failed: {result.output}\n{result.stderr}"

    def test_warning_appears_before_detection(self, runner, large_test_image, tmp_path):
        """
        Test that warning appears early in the output, before detection starts.
        
        Given: A large image with convex-edge enabled
        When: Detection runs
        Then: Warning should appear before "Detecting circles" or similar messages
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = runner.invoke(cli, [
            'detect',
            str(large_test_image),
            '--convex-edge',
            '--palette', 'cmyk',
            '--output-dir', str(output_dir),
            '--no-extract'
        ])

        combined_output = result.stderr + result.output
        
        # Find positions of warning and detection start
        warning_pos = combined_output.lower().find("warning")
        detection_pos = max(
            combined_output.lower().find("detecting"),
            combined_output.lower().find("using cmyk")
        )

        # Warning should appear before detection messages (if both present)
        if warning_pos >= 0 and detection_pos >= 0:
            assert warning_pos < detection_pos, "Warning should appear before detection starts"


class TestThresholdBoundary:
    """Test behavior at the 20MP threshold boundary."""

    @pytest.fixture
    def runner(self):
        """Provide a Click test runner."""
        return CliRunner()

    def test_exactly_20mp_no_warning(self, runner, tmp_path):
        """
        Test that exactly 20MP does not trigger warning (threshold is > not ≥).
        
        Given: An image with exactly 20MP
        When: Running detection with --convex-edge
        Then: Warning should NOT appear (threshold is >20, not ≥20)
        """
        # 4472x4472 ≈ 20.0MP (exactly at threshold)
        image = np.random.randint(0, 255, (4472, 4472, 3), dtype=np.uint8)
        image_path = tmp_path / "exactly_20mp.png"
        cv2.imwrite(str(image_path), image)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = runner.invoke(cli, [
            'detect',
            str(image_path),
            '--convex-edge',
            '--palette', 'cmyk',
            '--output-dir', str(output_dir),
            '--no-extract'
        ])

        # Should NOT warn at exactly 20MP
        stderr_lower = result.stderr.lower()
        if "warning" in stderr_lower:
            assert not ("convex-edge" in stderr_lower and "large" in stderr_lower)

    def test_just_over_20mp_shows_warning(self, runner, tmp_path):
        """
        Test that just over 20MP triggers warning.
        
        Given: An image with 20.1MP
        When: Running detection with --convex-edge
        Then: Warning should appear
        """
        # 4490x4490 ≈ 20.16MP (just over threshold)
        image = np.random.randint(0, 255, (4490, 4490, 3), dtype=np.uint8)
        image_path = tmp_path / "just_over_20mp.png"
        cv2.imwrite(str(image_path), image)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = runner.invoke(cli, [
            'detect',
            str(image_path),
            '--convex-edge',
            '--palette', 'cmyk',
            '--output-dir', str(output_dir),
            '--no-extract'
        ])

        # Should warn just over 20MP
        combined_output = result.stderr + result.output
        assert "warning" in combined_output.lower()
        assert "convex-edge" in combined_output.lower() or "large" in combined_output.lower()
