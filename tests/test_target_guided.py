"""Tests for target-guided dot optimization.

Spike: feshwj - Research Target-Guided Dot Optimization Algorithm
Feature: io1h5h - Target-Guided Dot Optimization (--target-image flag)

TDD approach: These tests define the expected behavior for the feature.
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import MagicMock

from dotmatrix.target_guided import (
    TargetCircle,
    TargetGuidedConfig,
    TargetCircleIndex,
    parse_target_image,
    compute_target_gradient,
    apply_target_guided_optimization,
)


class TestTargetCircleIndex:
    """Test spatial index for target circles."""
    
    def test_empty_index(self):
        """Empty index returns None for queries."""
        index = TargetCircleIndex([])
        result = index.find_nearest(100, 100, 'cyan')
        assert result is None
    
    def test_single_circle(self):
        """Single circle is always nearest."""
        circles = [TargetCircle(x=50, y=50, radius=10, color='cyan')]
        index = TargetCircleIndex(circles)
        
        result = index.find_nearest(100, 100, 'cyan')
        assert result is not None
        circle, distance = result
        assert circle.x == 50
        assert circle.y == 50
        # Distance should be sqrt((100-50)^2 + (100-50)^2) ≈ 70.7
        assert abs(distance - 70.71) < 1.0
    
    def test_multiple_circles_nearest(self):
        """Finds correct nearest among multiple circles."""
        circles = [
            TargetCircle(x=0, y=0, radius=10, color='cyan'),
            TargetCircle(x=100, y=0, radius=10, color='cyan'),
            TargetCircle(x=50, y=50, radius=10, color='cyan'),  # Nearest to (60, 60)
        ]
        index = TargetCircleIndex(circles)
        
        result = index.find_nearest(60, 60, 'cyan')
        assert result is not None
        circle, distance = result
        assert circle.x == 50
        assert circle.y == 50
    
    def test_color_filtering(self):
        """Only searches within requested color."""
        circles = [
            TargetCircle(x=10, y=10, radius=10, color='cyan'),
            TargetCircle(x=100, y=100, radius=10, color='magenta'),  # Closer but wrong color
        ]
        index = TargetCircleIndex(circles)
        
        result = index.find_nearest(90, 90, 'cyan')  # Query near magenta
        assert result is not None
        circle, _ = result
        assert circle.color == 'cyan'
        assert circle.x == 10  # Gets cyan even though magenta is closer


class TestTargetGradient:
    """Test gradient computation for target-guided optimization."""
    
    def test_gradient_direction(self):
        """Gradient points toward target."""
        config = TargetGuidedConfig(
            target_image_path=Path("dummy.png"),
            target_weight=1.0,
            step_size=0.5,
        )
        target = TargetCircle(x=100, y=0, radius=10, color='cyan')
        
        # Source at origin, target at (100, 0)
        dx, dy, dr = compute_target_gradient(
            source_x=0, source_y=0, source_r=10,
            target_circle=target,
            max_distance=200,
            config=config,
        )
        
        # dx should be positive (moving right toward target)
        assert dx > 0
        # dy should be ~0 (no vertical movement needed)
        assert abs(dy) < 0.01
    
    def test_radius_gradient(self):
        """Radius gradient adjusts toward target size."""
        config = TargetGuidedConfig(
            target_image_path=Path("dummy.png"),
            target_weight=1.0,
            step_size=1.0,
        )
        
        # Target is larger
        target = TargetCircle(x=0, y=0, radius=20, color='cyan')
        _, _, dr = compute_target_gradient(
            source_x=0, source_y=0, source_r=10,
            target_circle=target,
            max_distance=200,
            config=config,
        )
        assert dr > 0  # Should grow
        
        # Target is smaller
        target = TargetCircle(x=0, y=0, radius=5, color='cyan')
        _, _, dr = compute_target_gradient(
            source_x=0, source_y=0, source_r=10,
            target_circle=target,
            max_distance=200,
            config=config,
        )
        assert dr < 0  # Should shrink


class TestApplyOptimization:
    """Test the main optimization loop."""
    
    def test_converges_to_target(self):
        """Circles move toward target positions."""
        # Setup: single cluster with cyan circle
        circles_by_color = {
            'cyan': [(0.0, 0.0, 10.0)],
            'magenta': [],
            'yellow': [],
            'black': [(0.0, 0.0, 15.0)],
        }
        cluster_metadata = [{'cx': 0, 'cy': 0, 'black_radius': 15, 'black_circle_idx': 0}]
        cluster_circle_map = [{'cyan': (0, 100)}]  # Circle index 0, target 100 pixels
        
        # Target at (50, 50)
        target_circles = [TargetCircle(x=50, y=50, radius=10, color='cyan')]
        target_index = TargetCircleIndex(target_circles)
        
        config = TargetGuidedConfig(
            target_image_path=Path("dummy.png"),
            target_weight=1.0,
            step_size=0.5,
            max_iterations=100,
        )
        
        result = apply_target_guided_optimization(
            circles_by_color,
            cluster_metadata,
            cluster_circle_map,
            target_index,
            image_shape=(200, 200),
            config=config,
        )
        
        # Check cyan circle moved toward target
        final_x, final_y, _ = result['cyan'][0]
        # Should be closer to (50, 50) than original (0, 0)
        assert final_x > 10  # Moved right
        assert final_y > 10  # Moved down


class TestParseTargetImage:
    """Test target image parsing (requires actual image file)."""
    
    def test_parse_synthetic_halftone(self, tmp_path):
        """Parse a synthetically generated halftone image."""
        # Create synthetic halftone with known circles
        img = np.ones((200, 200, 3), dtype=np.uint8) * 255  # White background
        
        # Draw cyan circle (appears as red absence = high in 255-R channel)
        cv2.circle(img, (50, 50), 15, (255, 255, 0), -1)  # Yellow = no blue = cyan-ish
        
        # Draw magenta circle (appears as green absence)
        cv2.circle(img, (100, 50), 15, (255, 0, 255), -1)  # Purple-ish
        
        # Draw yellow circle (appears as blue absence)
        cv2.circle(img, (150, 50), 15, (0, 255, 255), -1)  # Yellow
        
        # Draw black circle
        cv2.circle(img, (100, 100), 20, (0, 0, 0), -1)  # Black
        
        # Save to temp file
        test_img_path = tmp_path / "test_halftone.png"
        cv2.imwrite(str(test_img_path), img)
        
        # Parse
        index = parse_target_image(
            test_img_path,
            sensitivity="relaxed",
            min_radius=10,
            max_radius=30,
        )
        
        # Should detect the black circle at minimum
        black_circles = index._by_color['black']
        assert len(black_circles) >= 1
        
        # Verify black circle detected near (100, 100)
        black_found = any(
            abs(c.x - 100) < 10 and abs(c.y - 100) < 10
            for c in black_circles
        )
        assert black_found, "Black circle at (100, 100) not detected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
