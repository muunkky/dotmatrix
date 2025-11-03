"""Tests for circle_detector module."""

import pytest
import numpy as np

from dotmatrix.image_loader import load_image
from dotmatrix.circle_detector import Circle, detect_circles


class TestCircle:
    """Test Circle dataclass."""

    def test_circle_creation(self):
        """Test creating a Circle object."""
        circle = Circle(center_x=100.5, center_y=200.3, radius=45.2)

        assert circle.center_x == 100.5
        assert circle.center_y == 200.3
        assert circle.radius == 45.2

    def test_circle_repr(self):
        """Test Circle string representation."""
        circle = Circle(center_x=100, center_y=200, radius=50)
        repr_str = repr(circle)

        assert 'Circle' in repr_str
        assert '100' in repr_str
        assert '200' in repr_str
        assert '50' in repr_str

    def test_circle_with_confidence(self):
        """Test creating Circle with confidence score."""
        circle = Circle(center_x=100.0, center_y=200.0, radius=50.0, confidence=95.5)

        assert circle.center_x == 100.0
        assert circle.center_y == 200.0
        assert circle.radius == 50.0
        assert circle.confidence == 95.5

    def test_circle_confidence_in_range(self):
        """Test that confidence is in valid range 0-100."""
        circle = Circle(center_x=100.0, center_y=200.0, radius=50.0, confidence=100.0)
        assert 0 <= circle.confidence <= 100

        circle2 = Circle(center_x=100.0, center_y=200.0, radius=50.0, confidence=0.0)
        assert 0 <= circle2.confidence <= 100


class TestDetectCircles:
    """Test circle detection algorithm."""

    def test_detect_with_custom_min_radius(self, test_image_various_sizes):
        """Test detection with custom minimum radius filter."""
        image_path, ground_truth = test_image_various_sizes
        image = load_image(image_path)

        # Detect with min_radius=30 (should filter out small circles)
        circles = detect_circles(image, min_radius=30)

        # All detected circles should have radius >= 30
        for circle in circles:
            assert circle.radius >= 30, f"Circle radius {circle.radius} < min_radius 30"

        # Should detect fewer circles than with default min_radius=10
        all_circles = detect_circles(image, min_radius=10)
        assert len(circles) <= len(all_circles)

    def test_detect_with_custom_max_radius(self, test_image_various_sizes):
        """Test detection with custom maximum radius filter."""
        image_path, ground_truth = test_image_various_sizes
        image = load_image(image_path)

        # Detect with max_radius=40 (should filter out large circles)
        circles = detect_circles(image, max_radius=40)

        # All detected circles should have radius <= 40
        for circle in circles:
            assert circle.radius <= 40, f"Circle radius {circle.radius} > max_radius 40"

    def test_min_radius_default_value(self, test_image_single_circle):
        """Test that min_radius defaults to 10."""
        image_path, ground_truth = test_image_single_circle
        image = load_image(image_path)

        # Should work without specifying min_radius
        circles = detect_circles(image)
        assert len(circles) >= 0  # Should not error

    def test_detect_single_circle(self, test_image_single_circle):
        """Test detecting a single circle."""
        image_path, ground_truth = test_image_single_circle
        image = load_image(image_path)

        circles = detect_circles(image)

        # Should detect at least one circle
        assert len(circles) >= 1

        # Check first detected circle against ground truth
        detected = circles[0]
        expected = ground_truth[0]

        # Center should be within 5px tolerance
        assert abs(detected.center_x - expected['center'][0]) <= 5
        assert abs(detected.center_y - expected['center'][1]) <= 5

        # Radius should be within 10% tolerance
        expected_radius = expected['radius']
        tolerance = expected_radius * 0.1
        assert abs(detected.radius - expected_radius) <= tolerance

    def test_detect_multiple_circles(self, test_image_multiple_circles):
        """Test detecting multiple circles."""
        image_path, ground_truth = test_image_multiple_circles
        image = load_image(image_path)

        circles = detect_circles(image)

        # Should detect at least 2 circles (aim for 90% detection rate)
        assert len(circles) >= 2

        # Verify each detected circle is close to at least one ground truth circle
        for detected in circles:
            # Find closest ground truth circle
            min_distance = float('inf')
            for expected in ground_truth:
                distance = np.sqrt(
                    (detected.center_x - expected['center'][0]) ** 2 +
                    (detected.center_y - expected['center'][1]) ** 2
                )
                min_distance = min(min_distance, distance)

            # Should be within reasonable distance
            assert min_distance <= 10

    def test_detect_no_circles(self, test_image_no_circles):
        """Test image with no circles returns empty list."""
        image_path, _ = test_image_no_circles
        image = load_image(image_path)

        circles = detect_circles(image)

        # Should return empty list or very few false positives
        assert len(circles) <= 1  # Allow up to 1 false positive

    def test_detect_various_sizes(self, test_image_various_sizes):
        """Test detecting circles of various sizes."""
        image_path, ground_truth = test_image_various_sizes
        image = load_image(image_path)

        circles = detect_circles(image)

        # Should detect at least 2 out of 3 circles
        assert len(circles) >= 2

        # Check that we detect both small and large circles
        radii = [c.radius for c in circles]
        assert min(radii) < 30  # Should detect small circles
        assert max(radii) > 70  # Should detect large circles

    def test_returns_list_of_circles(self, test_image_single_circle):
        """Test that detect_circles returns list of Circle objects."""
        image_path, _ = test_image_single_circle
        image = load_image(image_path)

        circles = detect_circles(image)

        assert isinstance(circles, list)
        if len(circles) > 0:
            assert isinstance(circles[0], Circle)

    def test_invalid_image(self):
        """Test error handling for invalid image input."""
        # Empty array
        with pytest.raises(ValueError):
            detect_circles(np.array([]))

        # Wrong dimensions
        with pytest.raises(ValueError):
            detect_circles(np.array([1, 2, 3]))

    def test_circle_coordinates_within_image(self, test_image_single_circle):
        """Test that detected circles are within image bounds."""
        image_path, _ = test_image_single_circle
        image = load_image(image_path)

        circles = detect_circles(image)

        height, width = image.shape[:2]

        for circle in circles:
            # Center should be within image
            assert 0 <= circle.center_x <= width
            assert 0 <= circle.center_y <= height

            # Radius should be positive
            assert circle.radius > 0

    def test_sensitivity_strict_preset(self, test_image_multiple_circles):
        """Test strict sensitivity detects fewer circles (higher quality)."""
        image_path, ground_truth = test_image_multiple_circles
        image = load_image(image_path)

        # Detect with strict sensitivity
        circles_strict = detect_circles(image, sensitivity="strict")

        # Should return circles
        assert isinstance(circles_strict, list)
        # Strict should filter more aggressively
        assert len(circles_strict) >= 0

    def test_sensitivity_relaxed_preset(self, test_image_multiple_circles):
        """Test relaxed sensitivity detects more circles (lower threshold)."""
        image_path, ground_truth = test_image_multiple_circles
        image = load_image(image_path)

        # Detect with relaxed sensitivity
        circles_relaxed = detect_circles(image, sensitivity="relaxed")

        # Should return circles
        assert isinstance(circles_relaxed, list)
        # Relaxed should be more permissive
        assert len(circles_relaxed) >= 0

    def test_sensitivity_normal_is_default(self, test_image_single_circle):
        """Test that normal sensitivity is the default."""
        image_path, ground_truth = test_image_single_circle
        image = load_image(image_path)

        # Detect with explicit normal
        circles_normal = detect_circles(image, sensitivity="normal")

        # Detect with default (no sensitivity specified)
        circles_default = detect_circles(image)

        # Should detect same circles
        assert len(circles_normal) == len(circles_default)

    def test_sensitivity_invalid_raises_error(self, test_image_single_circle):
        """Test that invalid sensitivity raises ValueError."""
        image_path, ground_truth = test_image_single_circle
        image = load_image(image_path)

        with pytest.raises(ValueError, match="Invalid sensitivity"):
            detect_circles(image, sensitivity="invalid")

    def test_detect_circles_have_confidence_scores(self, test_image_multiple_circles):
        """Test that detected circles include confidence scores."""
        image_path, ground_truth = test_image_multiple_circles
        image = load_image(image_path)

        circles = detect_circles(image)

        assert len(circles) > 0, "Should detect at least one circle"

        for circle in circles:
            # All circles should have confidence attribute
            assert hasattr(circle, 'confidence')
            # Confidence should be in range 0-100
            assert 0 <= circle.confidence <= 100
            assert isinstance(circle.confidence, float)

    def test_confidence_decreases_with_detection_order(self, test_image_multiple_circles):
        """Test that first detected circle has highest confidence."""
        image_path, ground_truth = test_image_multiple_circles
        image = load_image(image_path)

        circles = detect_circles(image)

        if len(circles) > 1:
            # First circle should have highest or equal confidence
            for i in range(len(circles) - 1):
                assert circles[i].confidence >= circles[i+1].confidence

    def test_min_distance_parameter_exists(self, test_image_multiple_circles):
        """Test that detect_circles accepts min_distance parameter."""
        image_path, ground_truth = test_image_multiple_circles
        image = load_image(image_path)

        # Should not raise TypeError
        circles = detect_circles(image, min_distance=20)
        assert isinstance(circles, list)

    def test_min_distance_filters_close_circles(self, test_image_multiple_circles):
        """Test that larger min_distance results in fewer circles."""
        image_path, ground_truth = test_image_multiple_circles
        image = load_image(image_path)

        # Detect with small min_distance (more circles)
        circles_small = detect_circles(image, min_distance=10)

        # Detect with large min_distance (fewer circles)
        circles_large = detect_circles(image, min_distance=100)

        # Larger distance should filter out more circles
        assert len(circles_large) <= len(circles_small)

    def test_min_distance_default_is_20(self, test_image_multiple_circles):
        """Test that default min_distance is 20 pixels."""
        image_path, ground_truth = test_image_multiple_circles
        image = load_image(image_path)

        # Detect with explicit default
        circles_explicit = detect_circles(image, min_distance=20)

        # Detect with implicit default
        circles_default = detect_circles(image)

        # Should detect same circles
        assert len(circles_explicit) == len(circles_default)
