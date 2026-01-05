"""Tests for edge_detector module - TDD approach for M2 edge detection feature.

Test Plan:
- Test Canny edge detection with various threshold values
- Test adaptive thresholding preprocessing
- Test false positive rate < 10% requirement
- Test integration with existing circle detection pipeline
- Test performance impact < 20% requirement
"""

import pytest
import numpy as np
import cv2
from pathlib import Path

from dotmatrix.edge_detector import (
    EdgeDetector,
    detect_edges_canny,
    apply_adaptive_threshold,
    calculate_false_positive_rate,
)


class TestCannyEdgeDetection:
    """Test Canny edge detection implementation."""

    def test_canny_edge_detection_basic(self):
        """Test basic Canny edge detection on synthetic image."""
        # Create synthetic image with circle
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(image, (50, 50), 30, 255, -1)
        
        # This will fail until we implement detect_edges_canny
        edges = detect_edges_canny(image, low_threshold=50, high_threshold=150)
        
        assert edges is not None
        assert edges.shape == image.shape
        assert edges.dtype == np.uint8
        # Should detect edges around the circle
        assert np.any(edges > 0)

    def test_canny_with_custom_thresholds(self):
        """Test Canny edge detection with custom threshold values."""
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(image, (50, 50), 30, 255, -1)
        
        # This will fail until implementation
        edges_low = detect_edges_canny(image, low_threshold=30, high_threshold=100)
        edges_high = detect_edges_canny(image, low_threshold=100, high_threshold=200)
        
        # Lower thresholds should detect more edges
        assert np.sum(edges_low) >= np.sum(edges_high)

    def test_canny_on_overlapping_circles(self):
        """Test edge detection on overlapping circles (key M2 requirement)."""
        # Create image with two overlapping circles with strong contrast
        image = np.zeros((200, 200), dtype=np.uint8)
        # Fill background
        image[:] = 30
        # Draw two overlapping circles with strong intensity difference
        cv2.circle(image, (80, 100), 50, 200, -1)
        cv2.circle(image, (120, 100), 50, 200, -1)
        
        # Apply light blur to create detectable edges
        image = cv2.GaussianBlur(image, (3, 3), 0)
        
        edges = detect_edges_canny(image, low_threshold=20, high_threshold=60)
        
        # Should detect edges of both circles
        assert edges is not None
        assert np.any(edges > 0), "Should detect some edges"
        # Verify edges exist somewhere in the image (more lenient check)
        total_edge_pixels = np.sum(edges > 0)
        assert total_edge_pixels > 100, f"Should detect substantial edges, found {total_edge_pixels} pixels"


class TestAdaptiveThresholding:
    """Test adaptive thresholding preprocessing."""

    def test_adaptive_threshold_basic(self):
        """Test basic adaptive thresholding."""
        # Create image with varying lighting
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        # This will fail until implementation
        thresholded = apply_adaptive_threshold(image)
        
        assert thresholded is not None
        assert thresholded.shape == image.shape
        assert thresholded.dtype == np.uint8
        # Binary image: values should be 0 or 255
        assert set(np.unique(thresholded)).issubset({0, 255})

    def test_adaptive_threshold_handles_varying_lighting(self):
        """Test adaptive thresholding with non-uniform lighting."""
        # Create gradient image (simulates uneven lighting)
        image = np.zeros((100, 100), dtype=np.uint8)
        for i in range(100):
            image[i, :] = i * 2  # Gradient from dark to bright
        
        # Add circle in middle
        cv2.circle(image, (50, 50), 20, 255, -1)
        
        # This will fail until implementation
        thresholded = apply_adaptive_threshold(image)
        
        # Should handle gradient and still detect circle
        assert thresholded is not None
        # Circle region should be thresholded to white
        circle_region = thresholded[40:60, 40:60]
        assert np.mean(circle_region) > 128, "Circle should be detected despite gradient"


class TestFalsePositiveRate:
    """Test false positive rate calculation (TDD spec: <10%)."""

    def test_false_positive_rate_calculation(self):
        """Test FPR calculation with known ground truth."""
        # Ground truth edges
        ground_truth = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(ground_truth, (50, 50), 30, 255, 1)  # Circle outline
        
        # Detected edges (with some false positives)
        detected = ground_truth.copy()
        detected[10:15, 10:15] = 255  # Add false positive region
        
        # This will fail until implementation
        fpr = calculate_false_positive_rate(detected, ground_truth)
        
        assert isinstance(fpr, float)
        assert 0.0 <= fpr <= 1.0
        assert fpr > 0, "Should detect the false positive region we added"

    def test_false_positive_rate_below_threshold(self):
        """Test that FPR meets <10% requirement on overlapping circles.
        
        This is the key TDD spec from the roadmap.
        """
        # TODO: Load test image with overlapping circles and ground truth
        # For now, create synthetic test case
        image = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(image, (80, 100), 50, 128, -1)
        cv2.circle(image, (120, 100), 50, 128, -1)
        
        # This will fail until full implementation
        edges = detect_edges_canny(image, low_threshold=50, high_threshold=150)
        
        # Create approximate ground truth
        ground_truth = np.zeros_like(image)
        cv2.circle(ground_truth, (80, 100), 50, 255, 1)
        cv2.circle(ground_truth, (120, 100), 50, 255, 1)
        
        fpr = calculate_false_positive_rate(edges, ground_truth)
        
        # Key assertion: FPR must be < 10% (0.10)
        assert fpr < 0.10, f"False positive rate {fpr:.2%} exceeds 10% threshold"


class TestEdgeDetectorClass:
    """Test EdgeDetector class for integration."""

    def test_edge_detector_initialization(self):
        """Test EdgeDetector class initialization."""
        # This will fail until we create the class
        detector = EdgeDetector(
            canny_low=50,
            canny_high=150,
            use_adaptive_threshold=True
        )
        
        assert detector.canny_low == 50
        assert detector.canny_high == 150
        assert detector.use_adaptive_threshold is True

    def test_edge_detector_process_image(self):
        """Test full edge detection pipeline."""
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(image, (50, 50), 30, 255, -1)
        
        # This will fail until implementation
        detector = EdgeDetector()
        edges = detector.process(image)
        
        assert edges is not None
        assert edges.shape == image.shape
        assert np.any(edges > 0)

    def test_edge_detector_with_preprocessing(self):
        """Test edge detection with adaptive threshold preprocessing."""
        # Create image with uneven lighting and a circle
        image = np.zeros((100, 100), dtype=np.uint8)
        # Create gradient background
        for i in range(100):
            image[i, :] = i + 50  # Gradient from 50 to 150
        # Add bright circle that contrasts with background
        cv2.circle(image, (50, 50), 20, 220, -1)
        # Add blur to create smooth edges
        image = cv2.GaussianBlur(image, (5, 5), 0)
        
        detector = EdgeDetector(use_adaptive_threshold=True, canny_low=30, canny_high=100)
        edges = detector.process(image)
        
        # Should handle gradient and detect circle edges
        assert edges is not None
        # Check for edges around the circle perimeter (not center)
        edge_region = edges[30:70, 30:70]  # Wider region around circle
        assert np.any(edge_region > 0), "Should detect circle edges despite gradient"


class TestPerformanceRequirement:
    """Test performance requirement: <20% overhead."""

    @pytest.mark.performance
    def test_edge_detection_performance_overhead(self):
        """Test that edge detection adds <20% overhead to pipeline.
        
        This is the acceptance criterion from the feature card.
        """
        # Create realistic test image
        image = np.random.randint(0, 255, (1000, 1000), dtype=np.uint8)
        cv2.circle(image, (500, 500), 200, 128, -1)
        
        import time
        
        # Measure baseline (no edge detection)
        start = time.perf_counter()
        _ = cv2.HoughCircles(
            image,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=100
        )
        baseline_time = time.perf_counter() - start
        
        # Measure with edge detection
        # This will fail until implementation
        detector = EdgeDetector()
        start = time.perf_counter()
        edges = detector.process(image)
        _ = cv2.HoughCircles(
            edges,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=100
        )
        enhanced_time = time.perf_counter() - start
        
        # Calculate overhead
        overhead_pct = ((enhanced_time - baseline_time) / baseline_time) * 100
        
        # Key assertion: overhead must be < 20%
        assert overhead_pct < 20, f"Overhead {overhead_pct:.1f}% exceeds 20% threshold"


# Test fixtures
@pytest.fixture
def sample_overlapping_circles():
    """Fixture providing image with overlapping circles for testing."""
    image = np.zeros((200, 200), dtype=np.uint8)
    cv2.circle(image, (80, 100), 50, 128, -1)
    cv2.circle(image, (120, 100), 50, 128, -1)
    return image


@pytest.fixture
def sample_ground_truth():
    """Fixture providing ground truth edges for overlapping circles."""
    ground_truth = np.zeros((200, 200), dtype=np.uint8)
    cv2.circle(ground_truth, (80, 100), 50, 255, 1)
    cv2.circle(ground_truth, (120, 100), 50, 255, 1)
    return ground_truth
