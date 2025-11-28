"""Unit tests for black dot verification module."""

import numpy as np
import pytest

from dotmatrix.black_verification import (
    verify_black_dot_detection,
    calculate_verification_metrics,
    generate_verification_warnings,
    VerificationResult,
)


class TestVerifyBlackDotDetection:
    """Tests for verify_black_dot_detection function."""

    def test_returns_verification_result(self):
        """Test that function returns a VerificationResult."""
        # Create a simple test image with black dots
        image = np.full((200, 200, 3), 255, dtype=np.uint8)  # White background
        # Draw black circles
        import cv2
        cv2.circle(image, (50, 50), 20, (0, 0, 0), -1)
        cv2.circle(image, (100, 100), 20, (0, 0, 0), -1)
        cv2.circle(image, (150, 150), 20, (0, 0, 0), -1)

        result = verify_black_dot_detection(
            image=image,
            min_radius=10,
            max_radius=30
        )

        assert isinstance(result, VerificationResult)
        assert result.black_circles_detected >= 0
        assert result.expected_density is not None

    def test_detects_black_dots(self):
        """Test that black dots are detected."""
        # Create image with known black dots
        image = np.full((300, 300, 3), 255, dtype=np.uint8)
        import cv2
        # Draw 4 black circles
        cv2.circle(image, (75, 75), 25, (0, 0, 0), -1)
        cv2.circle(image, (225, 75), 25, (0, 0, 0), -1)
        cv2.circle(image, (75, 225), 25, (0, 0, 0), -1)
        cv2.circle(image, (225, 225), 25, (0, 0, 0), -1)

        result = verify_black_dot_detection(
            image=image,
            min_radius=15,
            max_radius=35
        )

        # Should detect all 4 black circles
        assert result.black_circles_detected == 4
        assert result.radius_mean > 0
        assert result.radius_std >= 0

    def test_no_black_dots_returns_zero(self):
        """Test handling of image with no black dots."""
        # Pure white image
        image = np.full((200, 200, 3), 255, dtype=np.uint8)

        result = verify_black_dot_detection(
            image=image,
            min_radius=10,
            max_radius=30
        )

        assert result.black_circles_detected == 0
        assert result.radius_mean == 0.0
        assert result.radius_std == 0.0

    def test_radius_bounds_respected(self):
        """Test that radius bounds filter detection."""
        # Use larger image for convex edge detection to work properly
        image = np.full((600, 600, 3), 255, dtype=np.uint8)
        import cv2
        # Draw circles of varying sizes - need larger circles for convex detection
        cv2.circle(image, (100, 100), 15, (0, 0, 0), -1)   # Too small (radius 15 < min 40)
        cv2.circle(image, (300, 300), 60, (0, 0, 0), -1)   # In range (radius 60 in [40, 80])
        cv2.circle(image, (500, 500), 120, (0, 0, 0), -1)  # Too big (radius 120 > max 80)

        result = verify_black_dot_detection(
            image=image,
            min_radius=40,
            max_radius=80
        )

        # Only the mid-sized circle should be detected
        assert result.black_circles_detected == 1


class TestCalculateVerificationMetrics:
    """Tests for calculate_verification_metrics function."""

    def test_calculates_density(self):
        """Test density calculation."""
        metrics = calculate_verification_metrics(
            black_circle_count=100,
            image_shape=(1000, 1000),
            radii=[20, 21, 22, 19, 20]
        )

        assert 'density' in metrics
        # 100 circles in 1000x1000 = 100/1000000 = 0.0001 per pixel
        # But density should be per 1000x1000 area for readability
        assert metrics['density'] > 0

    def test_calculates_radius_distribution(self):
        """Test radius statistics."""
        radii = [18, 19, 20, 21, 22]
        metrics = calculate_verification_metrics(
            black_circle_count=5,
            image_shape=(500, 500),
            radii=radii
        )

        assert metrics['radius_mean'] == pytest.approx(20.0, rel=0.01)
        assert metrics['radius_min'] == 18
        assert metrics['radius_max'] == 22
        assert metrics['radius_std'] >= 0

    def test_calculates_coverage(self):
        """Test coverage calculation."""
        # 4 circles with radius 50 each = 4 * pi * 50^2 = ~31416 pixels
        # In 400x400 = 160000 pixels = ~19.6% coverage
        metrics = calculate_verification_metrics(
            black_circle_count=4,
            image_shape=(400, 400),
            radii=[50, 50, 50, 50]
        )

        assert 'coverage_percent' in metrics
        assert metrics['coverage_percent'] > 0
        assert metrics['coverage_percent'] < 100

    def test_empty_radii_handled(self):
        """Test handling of no detected circles."""
        metrics = calculate_verification_metrics(
            black_circle_count=0,
            image_shape=(500, 500),
            radii=[]
        )

        assert metrics['radius_mean'] == 0.0
        assert metrics['radius_std'] == 0.0
        assert metrics['coverage_percent'] == 0.0


class TestGenerateVerificationWarnings:
    """Tests for generate_verification_warnings function."""

    def test_no_warnings_for_good_detection(self):
        """Test that good detection generates no warnings."""
        warnings = generate_verification_warnings(
            black_circle_count=50,
            expected_count_range=(40, 60),
            radius_mean=25.0,
            radius_std=2.0,
            min_radius=20,
            max_radius=30,
            coverage_percent=15.0
        )

        assert len(warnings) == 0

    def test_warns_on_low_count(self):
        """Test warning when count is below expected."""
        warnings = generate_verification_warnings(
            black_circle_count=10,
            expected_count_range=(40, 60),
            radius_mean=25.0,
            radius_std=2.0,
            min_radius=20,
            max_radius=30,
            coverage_percent=5.0
        )

        assert len(warnings) > 0
        assert any('low' in w.lower() or 'few' in w.lower() for w in warnings)

    def test_warns_on_radius_at_boundary(self):
        """Test warning when mean radius near min/max boundary."""
        # Mean radius too close to min_radius
        warnings = generate_verification_warnings(
            black_circle_count=50,
            expected_count_range=(40, 60),
            radius_mean=22.0,  # Close to min_radius=20
            radius_std=3.0,
            min_radius=20,
            max_radius=50,
            coverage_percent=15.0
        )

        assert any('radius' in w.lower() for w in warnings)

    def test_warns_on_high_radius_variance(self):
        """Test warning when radius variance is high."""
        warnings = generate_verification_warnings(
            black_circle_count=50,
            expected_count_range=(40, 60),
            radius_mean=25.0,
            radius_std=15.0,  # High std relative to mean
            min_radius=10,
            max_radius=50,
            coverage_percent=15.0
        )

        assert any('variance' in w.lower() or 'std' in w.lower() or 'variation' in w.lower() for w in warnings)

    def test_warns_on_very_low_coverage(self):
        """Test warning when coverage is suspiciously low."""
        warnings = generate_verification_warnings(
            black_circle_count=5,
            expected_count_range=(40, 60),
            radius_mean=25.0,
            radius_std=2.0,
            min_radius=20,
            max_radius=30,
            coverage_percent=0.5  # Very low coverage
        )

        assert len(warnings) > 0


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_result_attributes(self):
        """Test that VerificationResult has all expected attributes."""
        result = VerificationResult(
            black_circles_detected=50,
            radius_mean=25.0,
            radius_std=2.5,
            radius_min=20,
            radius_max=30,
            expected_density=0.0001,
            actual_density=0.00009,
            coverage_percent=15.0,
            warnings=[],
            passed=True
        )

        assert result.black_circles_detected == 50
        assert result.radius_mean == 25.0
        assert result.radius_std == 2.5
        assert result.radius_min == 20
        assert result.radius_max == 30
        assert result.expected_density == 0.0001
        assert result.actual_density == 0.00009
        assert result.coverage_percent == 15.0
        assert result.warnings == []
        assert result.passed is True

    def test_result_with_warnings_not_passed(self):
        """Test that warnings can indicate failed verification."""
        result = VerificationResult(
            black_circles_detected=5,
            radius_mean=25.0,
            radius_std=2.5,
            radius_min=20,
            radius_max=30,
            expected_density=0.0001,
            actual_density=0.00001,
            coverage_percent=1.0,
            warnings=["Low circle count detected"],
            passed=False
        )

        assert result.passed is False
        assert len(result.warnings) == 1

    def test_result_to_dict(self):
        """Test conversion to dictionary for JSON serialization."""
        result = VerificationResult(
            black_circles_detected=50,
            radius_mean=25.0,
            radius_std=2.5,
            radius_min=20,
            radius_max=30,
            expected_density=0.0001,
            actual_density=0.00009,
            coverage_percent=15.0,
            warnings=[],
            passed=True
        )

        d = result.to_dict()

        assert isinstance(d, dict)
        assert d['black_circles_detected'] == 50
        assert d['passed'] is True
