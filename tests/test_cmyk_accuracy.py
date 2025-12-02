"""
Tests for CMYK accuracy measurement module.

Tests cover:
- Color counting with tolerance
- CMYK decomposition from primary colors
- CMYK decomposition from secondary colors (red, green, blue)
- Comparison function and error metrics
- E2E accuracy test with real pipeline output
"""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from dotmatrix.cmyk_accuracy import (
    COLORS_BGR,
    CMYKDecomposition,
    ComparisonResult,
    compare_cmyk_vectors,
    count_color,
    decompose_to_cmyk,
    measure_accuracy,
)


class TestCountColor:
    """Tests for count_color function."""

    def test_exact_match_single_color(self):
        """Count pixels that exactly match target color."""
        # Create 10x10 image with all cyan pixels
        img = np.full((10, 10, 3), COLORS_BGR['cyan'], dtype=np.uint8)
        count = count_color(img, COLORS_BGR['cyan'], tolerance=0)
        assert count == 100

    def test_no_match(self):
        """Count returns 0 when no pixels match."""
        img = np.full((10, 10, 3), COLORS_BGR['cyan'], dtype=np.uint8)
        count = count_color(img, COLORS_BGR['magenta'], tolerance=0)
        assert count == 0

    def test_tolerance_matching(self):
        """Tolerance allows near-matches to count."""
        # Create image with color slightly off from target
        target = COLORS_BGR['cyan']  # (255, 255, 0)
        near_cyan = (250, 250, 5)    # Within tolerance=10
        img = np.full((10, 10, 3), near_cyan, dtype=np.uint8)

        # No match with tolerance=0
        assert count_color(img, target, tolerance=0) == 0

        # Should match with tolerance=10
        assert count_color(img, target, tolerance=10) == 100

    def test_mixed_colors(self):
        """Correctly count when image has multiple colors."""
        img = np.zeros((10, 10, 3), dtype=np.uint8)

        # Top half cyan, bottom half magenta
        img[:5, :] = COLORS_BGR['cyan']
        img[5:, :] = COLORS_BGR['magenta']

        assert count_color(img, COLORS_BGR['cyan'], tolerance=0) == 50
        assert count_color(img, COLORS_BGR['magenta'], tolerance=0) == 50
        assert count_color(img, COLORS_BGR['yellow'], tolerance=0) == 0


class TestDecomposeBasic:
    """Tests for decompose_to_cmyk with primary colors only."""

    def test_all_cyan(self):
        """Image with only cyan pixels."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.full((10, 10, 3), COLORS_BGR['cyan'], dtype=np.uint8)
            cv2.imwrite(f.name, img)

            result = decompose_to_cmyk(f.name, tolerance=0)

            assert result.cyan == 100
            assert result.magenta == 0
            assert result.yellow == 0
            assert result.black == 0
            assert result.primary_pixels == 100
            assert result.secondary_pixels == 0

    def test_all_black(self):
        """Image with only black pixels."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.full((10, 10, 3), COLORS_BGR['black'], dtype=np.uint8)
            cv2.imwrite(f.name, img)

            result = decompose_to_cmyk(f.name, tolerance=0)

            assert result.cyan == 0
            assert result.magenta == 0
            assert result.yellow == 0
            assert result.black == 100
            assert result.primary_pixels == 100

    def test_mixed_cmyk(self):
        """Image with mix of C, M, Y, K pixels."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.zeros((20, 20, 3), dtype=np.uint8)

            # 100 pixels each: cyan, magenta, yellow, black
            img[:10, :10] = COLORS_BGR['cyan']      # 100 pixels
            img[:10, 10:] = COLORS_BGR['magenta']   # 100 pixels
            img[10:, :10] = COLORS_BGR['yellow']    # 100 pixels
            img[10:, 10:] = COLORS_BGR['black']     # 100 pixels

            cv2.imwrite(f.name, img)

            result = decompose_to_cmyk(f.name, tolerance=0)

            assert result.cyan == 100
            assert result.magenta == 100
            assert result.yellow == 100
            assert result.black == 100
            assert result.primary_pixels == 400

    def test_white_background_ignored(self):
        """White pixels should not count toward any color."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.full((10, 10, 3), COLORS_BGR['white'], dtype=np.uint8)

            # Add a few cyan pixels
            img[0, :5] = COLORS_BGR['cyan']

            cv2.imwrite(f.name, img)

            result = decompose_to_cmyk(f.name, tolerance=0)

            assert result.cyan == 5
            assert result.white_pixels == 95
            assert result.total_pixels == 100


class TestDecomposeSecondary:
    """Tests for decompose_to_cmyk with secondary colors (RGB)."""

    def test_red_decomposes_to_magenta_and_yellow(self):
        """Red = Magenta + Yellow in subtractive model."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.full((10, 10, 3), COLORS_BGR['red'], dtype=np.uint8)
            cv2.imwrite(f.name, img)

            result = decompose_to_cmyk(f.name, tolerance=0)

            # Red contributes to both M and Y
            assert result.cyan == 0
            assert result.magenta == 100  # From red
            assert result.yellow == 100   # From red
            assert result.black == 0
            assert result.secondary_pixels == 100
            assert result.raw_counts['red'] == 100

    def test_green_decomposes_to_cyan_and_yellow(self):
        """Green = Cyan + Yellow ink in subtractive model."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.full((10, 10, 3), COLORS_BGR['green'], dtype=np.uint8)
            cv2.imwrite(f.name, img)

            result = decompose_to_cmyk(f.name, tolerance=0)

            # Green = C + Y ink, so contributes to both
            assert result.cyan == 100
            assert result.magenta == 0
            assert result.yellow == 100
            assert result.black == 0
            assert result.raw_counts['green'] == 100
            assert result.secondary_pixels == 100

    def test_blue_decomposes_to_cyan_and_magenta(self):
        """Blue = Cyan + Magenta ink in subtractive model."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.full((10, 10, 3), COLORS_BGR['blue'], dtype=np.uint8)
            cv2.imwrite(f.name, img)

            result = decompose_to_cmyk(f.name, tolerance=0)

            # Blue = C + M ink, so contributes to both
            assert result.cyan == 100
            assert result.magenta == 100
            assert result.yellow == 0
            assert result.black == 0
            assert result.raw_counts['blue'] == 100

    def test_all_secondary_colors_decomposed(self):
        """All secondary colors decompose to their component inks."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.zeros((30, 20, 3), dtype=np.uint8)

            # Primary colors: 100 pixels each
            img[:10, :10] = COLORS_BGR['cyan']      # 100 C
            img[:10, 10:] = COLORS_BGR['magenta']   # 100 M
            img[10:20, :10] = COLORS_BGR['yellow']  # 100 Y

            # Secondary colors: 100 pixels each
            img[10:20, 10:] = COLORS_BGR['red']     # 100 -> M+Y
            img[20:, :10] = COLORS_BGR['green']     # 100 -> C+Y
            img[20:, 10:] = COLORS_BGR['blue']      # 100 -> C+M

            cv2.imwrite(f.name, img)

            result = decompose_to_cmyk(f.name, tolerance=0)

            # Cyan: 100 (pure) + 100 (green) + 100 (blue) = 300
            assert result.cyan == 300

            # Magenta: 100 (pure) + 100 (red) + 100 (blue) = 300
            assert result.magenta == 300

            # Yellow: 100 (pure) + 100 (red) + 100 (green) = 300
            assert result.yellow == 300

            assert result.primary_pixels == 300
            assert result.secondary_pixels == 300


class TestCompareCMYKVectors:
    """Tests for compare_cmyk_vectors function."""

    def test_identical_vectors(self):
        """Identical decompositions should have 0 error."""
        source = CMYKDecomposition(
            cyan=100, magenta=100, yellow=100, black=100,
            primary_pixels=400, secondary_pixels=0, white_pixels=0, total_pixels=400,
            raw_counts={'cyan': 100, 'magenta': 100, 'yellow': 100, 'black': 100}
        )
        recon = CMYKDecomposition(
            cyan=100, magenta=100, yellow=100, black=100,
            primary_pixels=400, secondary_pixels=0, white_pixels=0, total_pixels=400,
            raw_counts={'cyan': 100, 'magenta': 100, 'yellow': 100, 'black': 100}
        )

        result = compare_cmyk_vectors(source, recon, threshold=0.10)

        assert result.total_error == 0.0
        assert result.passed is True
        for color in ['cyan', 'magenta', 'yellow', 'black']:
            assert result.per_channel[color]['diff'] == 0
            assert result.per_channel[color]['pct_error'] == 0.0

    def test_small_difference_passes(self):
        """Small differences under threshold should pass."""
        source = CMYKDecomposition(
            cyan=1000, magenta=1000, yellow=1000, black=1000,
            primary_pixels=4000, secondary_pixels=0, white_pixels=0, total_pixels=4000,
            raw_counts={}
        )
        # 5% increase in each channel
        recon = CMYKDecomposition(
            cyan=1050, magenta=1050, yellow=1050, black=1050,
            primary_pixels=4200, secondary_pixels=0, white_pixels=0, total_pixels=4200,
            raw_counts={}
        )

        result = compare_cmyk_vectors(source, recon, threshold=0.10)

        assert result.total_error == pytest.approx(0.05, abs=0.01)
        assert result.passed is True

    def test_large_difference_fails(self):
        """Large differences over threshold should fail."""
        source = CMYKDecomposition(
            cyan=1000, magenta=1000, yellow=1000, black=1000,
            primary_pixels=4000, secondary_pixels=0, white_pixels=0, total_pixels=4000,
            raw_counts={}
        )
        # 20% increase - over 10% threshold
        recon = CMYKDecomposition(
            cyan=1200, magenta=1200, yellow=1200, black=1200,
            primary_pixels=4800, secondary_pixels=0, white_pixels=0, total_pixels=4800,
            raw_counts={}
        )

        result = compare_cmyk_vectors(source, recon, threshold=0.10)

        assert result.total_error == pytest.approx(0.20, abs=0.01)
        assert result.passed is False

    def test_negative_difference(self):
        """Reconstituted having fewer pixels should also show error."""
        source = CMYKDecomposition(
            cyan=1000, magenta=0, yellow=0, black=0,
            primary_pixels=1000, secondary_pixels=0, white_pixels=0, total_pixels=1000,
            raw_counts={}
        )
        recon = CMYKDecomposition(
            cyan=900, magenta=0, yellow=0, black=0,
            primary_pixels=900, secondary_pixels=0, white_pixels=0, total_pixels=900,
            raw_counts={}
        )

        result = compare_cmyk_vectors(source, recon, threshold=0.10)

        assert result.per_channel['cyan']['diff'] == -100
        assert result.per_channel['cyan']['pct_error'] == pytest.approx(0.10, abs=0.01)

    def test_zero_source_handling(self):
        """Handle case where source has 0 of a color."""
        source = CMYKDecomposition(
            cyan=0, magenta=100, yellow=100, black=100,
            primary_pixels=300, secondary_pixels=0, white_pixels=0, total_pixels=300,
            raw_counts={}
        )
        recon = CMYKDecomposition(
            cyan=10, magenta=100, yellow=100, black=100,  # Has some cyan
            primary_pixels=310, secondary_pixels=0, white_pixels=0, total_pixels=310,
            raw_counts={}
        )

        result = compare_cmyk_vectors(source, recon, threshold=0.10)

        # Cyan error should be 100% since source was 0
        assert result.per_channel['cyan']['pct_error'] == 1.0


class TestFormatReport:
    """Tests for the report formatting."""

    def test_report_contains_key_info(self):
        """Report should contain all key metrics."""
        source = CMYKDecomposition(
            cyan=1000, magenta=800, yellow=1200, black=500,
            primary_pixels=3500, secondary_pixels=0, white_pixels=0, total_pixels=3500,
            raw_counts={'cyan': 1000, 'magenta': 800, 'yellow': 1200, 'black': 500,
                       'red': 0, 'green': 0, 'blue': 0}
        )
        recon = CMYKDecomposition(
            cyan=1050, magenta=820, yellow=1150, black=510,
            primary_pixels=3530, secondary_pixels=0, white_pixels=0, total_pixels=3530,
            raw_counts={'cyan': 1050, 'magenta': 820, 'yellow': 1150, 'black': 510,
                       'red': 0, 'green': 0, 'blue': 0}
        )

        result = compare_cmyk_vectors(source, recon, threshold=0.10)
        report = result.format_report()

        assert "CMYK Accuracy Report" in report
        assert "Cyan" in report
        assert "Magenta" in report
        assert "Yellow" in report
        assert "Black" in report
        assert "PASS" in report or "FAIL" in report


class TestMeasureAccuracy:
    """Tests for the measure_accuracy convenience function."""

    def test_measure_identical_images(self):
        """Identical images should have 0 error."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.zeros((20, 20, 3), dtype=np.uint8)
            img[:10, :] = COLORS_BGR['cyan']
            img[10:, :] = COLORS_BGR['magenta']
            cv2.imwrite(f.name, img)

            result = measure_accuracy(f.name, f.name, tolerance=0, threshold=0.10)

            assert result.total_error == 0.0
            assert result.passed is True

    def test_measure_different_images(self):
        """Different images should show appropriate error."""
        with tempfile.NamedTemporaryFile(suffix='_src.png', delete=False) as src_file:
            with tempfile.NamedTemporaryFile(suffix='_rec.png', delete=False) as rec_file:
                # Source: all cyan
                src_img = np.full((10, 10, 3), COLORS_BGR['cyan'], dtype=np.uint8)
                cv2.imwrite(src_file.name, src_img)

                # Reconstituted: half cyan, half magenta
                rec_img = np.zeros((10, 10, 3), dtype=np.uint8)
                rec_img[:, :5] = COLORS_BGR['cyan']
                rec_img[:, 5:] = COLORS_BGR['magenta']
                cv2.imwrite(rec_file.name, rec_img)

                result = measure_accuracy(
                    src_file.name, rec_file.name,
                    tolerance=0, threshold=0.10
                )

                # Source: C=100, M=0
                # Recon: C=50, M=50
                # Cyan error: (100-50)/100 = 50%
                assert result.per_channel['cyan']['pct_error'] == 0.5
                assert result.passed is False


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_invalid_image_path_raises(self):
        """Should raise error for non-existent file."""
        with pytest.raises(ValueError, match="Could not load image"):
            decompose_to_cmyk("/nonexistent/path/image.png")

    def test_all_white_image(self):
        """All-white image should have all zeros."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = np.full((10, 10, 3), 255, dtype=np.uint8)
            cv2.imwrite(f.name, img)

            result = decompose_to_cmyk(f.name, tolerance=0)

            assert result.cyan == 0
            assert result.magenta == 0
            assert result.yellow == 0
            assert result.black == 0
            assert result.white_pixels == 100

    def test_cmyk_vector_tuple(self):
        """cmyk_vector() should return correct tuple."""
        decomp = CMYKDecomposition(
            cyan=100, magenta=200, yellow=300, black=400,
            primary_pixels=1000, secondary_pixels=0, white_pixels=0, total_pixels=1000,
            raw_counts={}
        )
        assert decomp.cmyk_vector() == (100, 200, 300, 400)
