"""Tests for drift-balanced jitter functionality.

Tests the drift compensation algorithm that maintains cluster color balance
while applying jitter randomization.
"""

import math
import pytest
import numpy as np
from unittest.mock import Mock, patch

from dotmatrix.circle_renderer import (
    _apply_drift_to_svg_circles,
    _measure_svg_circle_mass,
)


class TestDriftScalingBounds:
    """Test that scale_factor is properly bounded to prevent runaway growth."""
    
    def test_scale_factor_clamped_to_max_2x(self):
        """When actual_pixels is very small, scale_factor should be clamped to 2.0."""
        # Setup: petal with target=100 pixels, but actual=1 pixel (mostly occluded)
        # Without clamping: scale_factor = sqrt(100/1) = 10.0 → runaway growth
        # With clamping: scale_factor = 2.0 → controlled growth
        
        circles_by_color = {
            'cyan': [(100.0, 100.0, 10.0)],
            'magenta': [],
            'yellow': [],
            'black': []
        }
        
        cluster_metadata = [{
            'cx': 100.0,
            'cy': 100.0,
            'black_radius': 15.0,
            'decomposed_counts': {'cyan': 100, 'magenta': 0, 'yellow': 0}
        }]
        
        cluster_circle_map = [
            {'cyan': (0, 100)}  # index 0, target 100 pixels
        ]
        
        # Mock the measurement to return very small value (above threshold but would cause huge scale)
        with patch('dotmatrix.circle_renderer._measure_svg_circle_mass', return_value=20):
            result = _apply_drift_to_svg_circles(
                circles_by_color=circles_by_color,
                cluster_metadata=cluster_metadata,
                cluster_circle_map=cluster_circle_map,
                image_shape=(200, 200),
                drift_tolerance=0.2,
                max_iterations=1,
            )
        
        # Should grow but be clamped to 2x max
        original_r = 10.0
        new_r = result['cyan'][0][2]
        scale = new_r / original_r
        
        assert scale <= 2.0, f"Scale factor {scale} exceeds max 2.0"
        assert scale > 1.0, f"Should still grow when actual < target, got scale={scale}"
    
    def test_scale_factor_clamped_to_min_0_5x(self):
        """When actual_pixels is very large, scale_factor should be clamped to 0.5."""
        circles_by_color = {
            'cyan': [(100.0, 100.0, 10.0)],
            'magenta': [],
            'yellow': [],
            'black': []
        }
        
        cluster_metadata = [{
            'cx': 100.0,
            'cy': 100.0,
            'black_radius': 5.0,
            'decomposed_counts': {'cyan': 100, 'magenta': 0, 'yellow': 0}
        }]
        
        cluster_circle_map = [
            {'cyan': (0, 100)}
        ]
        
        # Mock measurement to return way too much (circle grew too big)
        with patch('dotmatrix.circle_renderer._measure_svg_circle_mass', return_value=1000):
            result = _apply_drift_to_svg_circles(
                circles_by_color=circles_by_color,
                cluster_metadata=cluster_metadata,
                cluster_circle_map=cluster_circle_map,
                image_shape=(200, 200),
                drift_tolerance=0.2,
                max_iterations=1,
            )
        
        original_r = 10.0
        new_r = result['cyan'][0][2]
        scale = new_r / original_r
        
        assert scale >= 0.5, f"Scale factor {scale} below min 0.5"
        assert scale < 1.0, "Should shrink when actual > target"
    
    def test_skips_measurements_below_5_pixels(self):
        """Should skip adjustments when actual_pixels < 5 (unreliable)."""
        circles_by_color = {
            'cyan': [(100.0, 100.0, 10.0)],
            'magenta': [],
            'yellow': [],
            'black': []
        }
        
        cluster_metadata = [{
            'cx': 100.0,
            'cy': 100.0,
            'black_radius': 15.0,
            'decomposed_counts': {'cyan': 100, 'magenta': 0, 'yellow': 0}
        }]
        
        cluster_circle_map = [
            {'cyan': (0, 100)}
        ]
        
        # Mock measurement returns 2 pixels (below threshold)
        with patch('dotmatrix.circle_renderer._measure_svg_circle_mass', return_value=2):
            result = _apply_drift_to_svg_circles(
                circles_by_color=circles_by_color,
                cluster_metadata=cluster_metadata,
                cluster_circle_map=cluster_circle_map,
                image_shape=(200, 200),
                drift_tolerance=0.2,
                max_iterations=1,
            )
        
        # Circle should remain unchanged
        original_r = circles_by_color['cyan'][0][2]
        new_r = result['cyan'][0][2]
        assert new_r == original_r, "Should skip adjustment for measurements < 5 pixels"


class TestDriftConvergence:
    """Test drift algorithm convergence behavior."""
    
    def test_converges_when_within_tolerance(self):
        """Should stop iterating when all clusters balanced within tolerance."""
        circles_by_color = {
            'cyan': [(100.0, 100.0, 10.0)],
            'magenta': [],
            'yellow': [],
            'black': []
        }
        
        cluster_metadata = [{
            'cx': 100.0,
            'cy': 100.0,
            'black_radius': 5.0,
            'decomposed_counts': {'cyan': 100, 'magenta': 0, 'yellow': 0}
        }]
        
        cluster_circle_map = [
            {'cyan': (0, 100)}
        ]
        
        # Mock measurement returns value within tolerance (100 ± 20% = 80-120)
        with patch('dotmatrix.circle_renderer._measure_svg_circle_mass', return_value=110):
            result = _apply_drift_to_svg_circles(
                circles_by_color=circles_by_color,
                cluster_metadata=cluster_metadata,
                cluster_circle_map=cluster_circle_map,
                image_shape=(200, 200),
                drift_tolerance=0.2,
                max_iterations=10,
            )
        
        # Should remain unchanged (within tolerance)
        assert result['cyan'][0][2] == 10.0
    
    def test_respects_max_iterations(self):
        """Should not exceed max_iterations even if not converged."""
        circles_by_color = {
            'cyan': [(100.0, 100.0, 10.0)],
            'magenta': [],
            'yellow': [],
            'black': []
        }
        
        cluster_metadata = [{
            'cx': 100.0,
            'cy': 100.0,
            'black_radius': 5.0,
            'decomposed_counts': {'cyan': 100, 'magenta': 0, 'yellow': 0}
        }]
        
        cluster_circle_map = [
            {'cyan': (0, 100)}
        ]
        
        call_count = 0
        def mock_measure(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return 50  # Always out of tolerance, never converges
        
        with patch('dotmatrix.circle_renderer._measure_svg_circle_mass', side_effect=mock_measure):
            result = _apply_drift_to_svg_circles(
                circles_by_color=circles_by_color,
                cluster_metadata=cluster_metadata,
                cluster_circle_map=cluster_circle_map,
                image_shape=(200, 200),
                drift_tolerance=0.2,
                max_iterations=3,
            )
        
        # Should be called max 3 times (max_iterations)
        assert call_count <= 3, f"Called {call_count} times, should be <= 3"


class TestDriftWithMultiplePetals:
    """Test drift with multiple petals per cluster."""
    
    def test_balances_all_three_petals(self):
        """Should adjust all three petals (C/M/Y) independently."""
        circles_by_color = {
            'cyan': [(100.0, 110.0, 8.0)],
            'magenta': [(100.0, 90.0, 8.0)],
            'yellow': [(90.0, 100.0, 8.0)],
            'black': []
        }
        
        cluster_metadata = [{
            'cx': 100.0,
            'cy': 100.0,
            'black_radius': 5.0,
            'decomposed_counts': {'cyan': 200, 'magenta': 200, 'yellow': 200}
        }]
        
        cluster_circle_map = [
            {
                'cyan': (0, 200),
                'magenta': (0, 200),
                'yellow': (0, 200)
            }
        ]
        
        # Mock: cyan too small, magenta correct, yellow too large
        def mock_measure(px, py, pr, *args):
            if py > 105:  # cyan (y=110)
                return 100  # Too small
            elif py < 95:  # magenta (y=90)
                return 200  # Perfect
            else:  # yellow (x=90)
                return 400  # Too large
        
        with patch('dotmatrix.circle_renderer._measure_svg_circle_mass', side_effect=mock_measure):
            result = _apply_drift_to_svg_circles(
                circles_by_color=circles_by_color,
                cluster_metadata=cluster_metadata,
                cluster_circle_map=cluster_circle_map,
                image_shape=(200, 200),
                drift_tolerance=0.2,
                max_iterations=1,
            )
        
        cyan_r = result['cyan'][0][2]
        magenta_r = result['magenta'][0][2]
        yellow_r = result['yellow'][0][2]
        
        assert cyan_r > 8.0, "Cyan should grow (actual < target)"
        assert magenta_r == 8.0, "Magenta should stay same (balanced)"
        assert yellow_r < 8.0, "Yellow should shrink (actual > target)"


class TestMeasureSVGCircleMass:
    """Test the cluster-local mass measurement function."""
    
    def test_measures_circle_without_occlusion(self):
        """Should measure full circle area when no black occlusion."""
        # Circle with r=10 should have area ≈ 314 pixels
        pixels = _measure_svg_circle_mass(
            petal_x=100.0,
            petal_y=100.0,
            petal_r=10.0,
            black_r=0.0,  # No black
            black_x=100.0,
            black_y=100.0,
            h=200,
            w=200
        )
        
        expected = math.pi * 10**2
        # cv2.LINE_AA antialiasing counts partial pixels, causing ~30% increase
        assert abs(pixels - expected) < 100, f"Expected ~{expected}, got {pixels}"
    
    def test_measures_exposed_area_with_occlusion(self):
        """Should measure exposed area (petal - black overlap)."""
        # Petal with r=15 overlapped by black with r=10 at same center
        # Should measure much less than full petal area
        full_pixels = _measure_svg_circle_mass(
            petal_x=100.0, petal_y=100.0, petal_r=15.0,
            black_r=0.0, black_x=100.0, black_y=100.0,
            h=200, w=200
        )
        
        exposed_pixels = _measure_svg_circle_mass(
            petal_x=100.0, petal_y=100.0, petal_r=15.0,
            black_r=10.0, black_x=100.0, black_y=100.0,
            h=200, w=200
        )
        
        assert exposed_pixels < full_pixels, "Exposed should be less than full"
        assert exposed_pixels > 0, "Should still have some exposed area"
    
    def test_returns_zero_when_fully_occluded(self):
        """Should return 0 or near-0 when petal fully covered by black."""
        # Small petal completely covered by large black
        pixels = _measure_svg_circle_mass(
            petal_x=100.0, petal_y=100.0, petal_r=5.0,
            black_r=20.0, black_x=100.0, black_y=100.0,
            h=200, w=200
        )
        
        assert pixels < 5, f"Fully occluded should be < 5 pixels, got {pixels}"


class TestDriftEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_handles_empty_circles_gracefully(self):
        """Should handle empty circle lists without errors."""
        circles_by_color = {
            'cyan': [],
            'magenta': [],
            'yellow': [],
            'black': []
        }
        
        result = _apply_drift_to_svg_circles(
            circles_by_color=circles_by_color,
            cluster_metadata=[],
            cluster_circle_map=[],
            image_shape=(200, 200),
            drift_tolerance=0.2,
            max_iterations=10,
        )
        
        assert result == circles_by_color
    
    def test_handles_cluster_without_petals(self):
        """Should skip clusters with no petal circles."""
        circles_by_color = {
            'cyan': [],
            'magenta': [],
            'yellow': [],
            'black': [(100.0, 100.0, 10.0)]
        }
        
        cluster_metadata = [{
            'cx': 100.0,
            'cy': 100.0,
            'black_radius': 10.0,
            'decomposed_counts': {'cyan': 0, 'magenta': 0, 'yellow': 0}
        }]
        
        cluster_circle_map = [{}]  # No petals
        
        result = _apply_drift_to_svg_circles(
            circles_by_color=circles_by_color,
            cluster_metadata=cluster_metadata,
            cluster_circle_map=cluster_circle_map,
            image_shape=(200, 200),
            drift_tolerance=0.2,
            max_iterations=10,
        )
        
        # Should complete without error
        assert result == circles_by_color
    
    def test_tolerates_target_pixels_zero(self):
        """Should handle target_pixels=0 edge case."""
        circles_by_color = {
            'cyan': [(100.0, 100.0, 10.0)],
            'magenta': [],
            'yellow': [],
            'black': []
        }
        
        cluster_metadata = [{
            'cx': 100.0,
            'cy': 100.0,
            'black_radius': 5.0,
            'decomposed_counts': {'cyan': 0, 'magenta': 0, 'yellow': 0}
        }]
        
        cluster_circle_map = [
            {'cyan': (0, 0)}  # target=0
        ]
        
        with patch('dotmatrix.circle_renderer._measure_svg_circle_mass', return_value=10):
            result = _apply_drift_to_svg_circles(
                circles_by_color=circles_by_color,
                cluster_metadata=cluster_metadata,
                cluster_circle_map=cluster_circle_map,
                image_shape=(200, 200),
                drift_tolerance=0.2,
                max_iterations=1,
            )
        
        # Should not crash, may shrink or skip
        assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
