"""Tests for fit_metric module - diff-based radius accuracy measurement."""

import numpy as np
import pytest

from dotmatrix.fit_metric import calculate_fit_accuracy, FitMetrics


class TestCalculateFitAccuracy:
    """Tests for calculate_fit_accuracy function."""

    def test_perfect_fit_returns_score_of_one(self):
        """A perfect fit (no overfit or underfit) should return fit_score of 1.0."""
        # Create a diff image that's entirely background (perfect match)
        diff_image = np.full((100, 100, 3), 255, dtype=np.uint8)  # All white background

        metrics = calculate_fit_accuracy(diff_image, background_color=(255, 255, 255))

        assert metrics.fit_score == 1.0
        assert metrics.overfit_ratio == 0.0
        assert metrics.underfit_ratio == 0.0

    def test_complete_overfit_detected(self):
        """An image with only overfit (black pixels) should be detected."""
        # Create image with black pixels indicating overfit
        diff_image = np.full((100, 100, 3), 0, dtype=np.uint8)  # All black (overfit)

        metrics = calculate_fit_accuracy(diff_image, background_color=(255, 255, 255))

        assert metrics.overfit_ratio == 1.0
        assert metrics.underfit_ratio == 0.0
        assert metrics.fit_score == 0.0

    def test_complete_underfit_detected(self):
        """An image with colored pixels (not black, not white) indicates underfit."""
        # Create image with magenta pixels (original color showing through)
        diff_image = np.full((100, 100, 3), [255, 0, 255], dtype=np.uint8)  # Magenta

        metrics = calculate_fit_accuracy(diff_image, background_color=(255, 255, 255))

        assert metrics.overfit_ratio == 0.0
        assert metrics.underfit_ratio == 1.0
        assert metrics.fit_score == 0.0

    def test_mixed_fit_calculates_correct_ratios(self):
        """A mix of perfect, overfit, and underfit should calculate correct ratios."""
        # Create 10x10 image: 25% perfect (white), 25% overfit (black), 50% underfit (cyan)
        diff_image = np.zeros((10, 10, 3), dtype=np.uint8)

        # Top-left quadrant: white (background/perfect)
        diff_image[0:5, 0:5] = [255, 255, 255]  # 25 pixels

        # Top-right quadrant: black (overfit)
        diff_image[0:5, 5:10] = [0, 0, 0]  # 25 pixels

        # Bottom half: cyan (underfit - original color visible)
        diff_image[5:10, :] = [0, 255, 255]  # 50 pixels

        metrics = calculate_fit_accuracy(diff_image, background_color=(255, 255, 255))

        assert metrics.overfit_ratio == pytest.approx(0.25, abs=0.01)
        assert metrics.underfit_ratio == pytest.approx(0.50, abs=0.01)
        assert metrics.fit_score == pytest.approx(0.25, abs=0.01)  # Only 25% is perfect

    def test_custom_background_color(self):
        """Should handle non-white background colors."""
        # Gray background
        diff_image = np.full((100, 100, 3), 128, dtype=np.uint8)

        metrics = calculate_fit_accuracy(diff_image, background_color=(128, 128, 128))

        assert metrics.fit_score == 1.0  # All gray = all background = perfect
        assert metrics.overfit_ratio == 0.0
        assert metrics.underfit_ratio == 0.0

    def test_returns_fit_metrics_dataclass(self):
        """Should return a FitMetrics dataclass with all required fields."""
        diff_image = np.full((10, 10, 3), 255, dtype=np.uint8)

        metrics = calculate_fit_accuracy(diff_image, background_color=(255, 255, 255))

        assert isinstance(metrics, FitMetrics)
        assert hasattr(metrics, 'fit_score')
        assert hasattr(metrics, 'overfit_ratio')
        assert hasattr(metrics, 'underfit_ratio')
        assert hasattr(metrics, 'overfit_pixels')
        assert hasattr(metrics, 'underfit_pixels')
        assert hasattr(metrics, 'total_pixels')

    def test_pixel_counts_are_accurate(self):
        """Should correctly count the number of overfit and underfit pixels."""
        # 10x10 image = 100 pixels total
        diff_image = np.zeros((10, 10, 3), dtype=np.uint8)

        # 30 pixels white (background)
        diff_image[0:3, :] = [255, 255, 255]

        # 40 pixels black (overfit)
        diff_image[3:7, :] = [0, 0, 0]

        # 30 pixels colored (underfit)
        diff_image[7:10, :] = [255, 0, 0]

        metrics = calculate_fit_accuracy(diff_image, background_color=(255, 255, 255))

        assert metrics.total_pixels == 100
        assert metrics.overfit_pixels == 40
        assert metrics.underfit_pixels == 30

    def test_empty_image_returns_zero_score(self):
        """An empty (all black) image should return 0 fit score."""
        diff_image = np.zeros((50, 50, 3), dtype=np.uint8)

        metrics = calculate_fit_accuracy(diff_image, background_color=(255, 255, 255))

        assert metrics.fit_score == 0.0
        assert metrics.overfit_pixels == 50 * 50

    def test_handles_grayscale_overfit_near_black(self):
        """Dark grays near black should be counted as overfit."""
        # Very dark gray (almost black) - should be overfit
        diff_image = np.full((100, 100, 3), 10, dtype=np.uint8)

        metrics = calculate_fit_accuracy(diff_image, background_color=(255, 255, 255))

        # Dark pixels are overfit (drawn circles going beyond original)
        assert metrics.overfit_ratio > 0.9


class TestFitMetricsDataclass:
    """Tests for FitMetrics dataclass."""

    def test_to_dict_returns_dictionary(self):
        """FitMetrics.to_dict() should return all values as a dictionary."""
        metrics = FitMetrics(
            fit_score=0.75,
            overfit_ratio=0.15,
            underfit_ratio=0.10,
            overfit_pixels=1500,
            underfit_pixels=1000,
            total_pixels=10000
        )

        result = metrics.to_dict()

        assert isinstance(result, dict)
        assert result['fit_score'] == 0.75
        assert result['overfit_ratio'] == 0.15
        assert result['underfit_ratio'] == 0.10
        assert result['overfit_pixels'] == 1500
        assert result['underfit_pixels'] == 1000
        assert result['total_pixels'] == 10000

    def test_fit_bias_property_positive_when_overfit(self):
        """fit_bias should be positive when overfit > underfit."""
        metrics = FitMetrics(
            fit_score=0.5,
            overfit_ratio=0.30,
            underfit_ratio=0.20,
            overfit_pixels=3000,
            underfit_pixels=2000,
            total_pixels=10000
        )

        assert metrics.fit_bias > 0  # Positive = overfit bias

    def test_fit_bias_property_negative_when_underfit(self):
        """fit_bias should be negative when underfit > overfit."""
        metrics = FitMetrics(
            fit_score=0.5,
            overfit_ratio=0.10,
            underfit_ratio=0.40,
            overfit_pixels=1000,
            underfit_pixels=4000,
            total_pixels=10000
        )

        assert metrics.fit_bias < 0  # Negative = underfit bias

    def test_fit_bias_zero_when_balanced(self):
        """fit_bias should be zero when overfit equals underfit."""
        metrics = FitMetrics(
            fit_score=0.6,
            overfit_ratio=0.20,
            underfit_ratio=0.20,
            overfit_pixels=2000,
            underfit_pixels=2000,
            total_pixels=10000
        )

        assert metrics.fit_bias == 0.0


class TestRealWorldScenarios:
    """Integration-style tests with realistic diff images."""

    def test_white_halo_pattern_detected_as_overfit(self):
        """White ring halos around circles indicate radius overestimation."""
        # Simulate a diff where circles are too big (white halos)
        diff_image = np.full((100, 100, 3), 255, dtype=np.uint8)  # Background

        # Add white halo ring pattern (simulating overfit)
        # Draw ring of black pixels where circle was drawn beyond original
        for y in range(30, 70):
            for x in range(30, 70):
                dist = np.sqrt((x - 50)**2 + (y - 50)**2)
                if 15 < dist < 20:  # Ring between radius 15 and 20
                    diff_image[y, x] = [0, 0, 0]  # Overfit

        metrics = calculate_fit_accuracy(diff_image, background_color=(255, 255, 255))

        assert metrics.overfit_ratio > 0
        assert metrics.fit_bias > 0  # Indicates overfit
        assert metrics.fit_score < 1.0

    def test_colored_residue_detected_as_underfit(self):
        """Colored pixels showing through indicate radius underestimation."""
        # Simulate a diff where circles are too small (original color visible)
        diff_image = np.full((100, 100, 3), 255, dtype=np.uint8)  # Background

        # Add colored residue (original dot color showing through)
        for y in range(40, 60):
            for x in range(40, 60):
                diff_image[y, x] = [0, 255, 255]  # Cyan residue

        metrics = calculate_fit_accuracy(diff_image, background_color=(255, 255, 255))

        assert metrics.underfit_ratio > 0
        assert metrics.fit_bias < 0  # Indicates underfit
        assert metrics.fit_score < 1.0
