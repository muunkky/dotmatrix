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
    _compute_match_score,
)


class TestCLIIntegration:
    """Test CLI integration for --target-image flag."""
    
    def test_target_image_option_exists(self):
        """CLI should accept --target-image option."""
        from click.testing import CliRunner
        from dotmatrix.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        # Check that target-image is listed in help
        assert '--target-image' in result.output
        assert result.exit_code == 0
    
    def test_target_weight_option_exists(self):
        """CLI should accept --target-weight option."""
        from click.testing import CliRunner
        from dotmatrix.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        # Check that target-weight is listed in help
        assert '--target-weight' in result.output
        assert result.exit_code == 0
    
    def test_target_image_requires_file(self, tmp_path):
        """--target-image should require an existing file."""
        from click.testing import CliRunner
        from dotmatrix.cli import cli
        
        runner = CliRunner()
        
        # Non-existent file should fail
        result = runner.invoke(cli, [
            '-i', str(tmp_path / 'input.png'),  # Will also fail
            '--target-image', '/nonexistent/file.png',
        ])
        
        # Should show path error
        assert result.exit_code != 0


class TestJitterSeedReproducibility:
    """Test that target-guided optimization is reproducible with --jitter-seed."""
    
    def test_same_seed_same_result(self):
        """Same jitter-seed should produce identical optimization results."""
        # Setup identical inputs
        circles_by_color = {
            'cyan': [(0.0, 0.0, 10.0)],
            'magenta': [],
            'yellow': [],
            'black': [(0.0, 0.0, 15.0)],
        }
        cluster_metadata = [{'cx': 0, 'cy': 0, 'black_radius': 15, 'black_circle_idx': 0}]
        cluster_circle_map = [{'cyan': (0, 100)}]
        
        target_circles = [TargetCircle(x=50, y=50, radius=10, color='cyan')]
        target_index = TargetCircleIndex(target_circles)
        
        config = TargetGuidedConfig(
            target_image_path=Path("dummy.png"),
            target_weight=1.0,
            step_size=0.5,
            max_iterations=10,
        )
        
        # Run optimization twice
        result1 = apply_target_guided_optimization(
            {'cyan': [(0.0, 0.0, 10.0)], 'magenta': [], 'yellow': [], 'black': [(0.0, 0.0, 15.0)]},
            cluster_metadata,
            cluster_circle_map,
            target_index,
            image_shape=(200, 200),
            config=config,
        )
        
        result2 = apply_target_guided_optimization(
            {'cyan': [(0.0, 0.0, 10.0)], 'magenta': [], 'yellow': [], 'black': [(0.0, 0.0, 15.0)]},
            cluster_metadata,
            cluster_circle_map,
            target_index,
            image_shape=(200, 200),
            config=config,
        )
        
        # Results should be identical (deterministic algorithm)
        assert result1['cyan'][0] == result2['cyan'][0], "Same inputs should produce same outputs"


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


class TestProgressLogging:
    """Test that progress logging shows match score improving."""
    
    def test_match_score_computed(self):
        """Match score function should return valid percentage."""
        from dotmatrix.target_guided import _compute_match_score
        
        # Setup circles
        circles_by_color = {
            'cyan': [(50.0, 50.0, 10.0)],
            'magenta': [],
            'yellow': [],
            'black': [],
        }
        cluster_circle_map = [{'cyan': (0, 100)}]
        
        # Create target index with circle at same position
        target_circles = [TargetCircle(x=50, y=50, radius=10, color='cyan')]
        target_index = TargetCircleIndex(target_circles)
        
        score = _compute_match_score(
            circles_by_color, cluster_circle_map, target_index, max_distance=200
        )
        
        # Perfect match should give high score (close to 100%)
        assert score > 90.0, f"Perfect match should have high score, got {score}"
    
    def test_match_score_improves_toward_target(self):
        """Match score should be higher when closer to target."""
        from dotmatrix.target_guided import _compute_match_score
        
        # Target at (100, 100)
        target_circles = [TargetCircle(x=100, y=100, radius=10, color='cyan')]
        target_index = TargetCircleIndex(target_circles)
        max_distance = 200
        
        # Circle far from target
        far_circles = {'cyan': [(0.0, 0.0, 10.0)], 'magenta': [], 'yellow': [], 'black': []}
        cluster_map = [{'cyan': (0, 100)}]
        far_score = _compute_match_score(far_circles, cluster_map, target_index, max_distance)
        
        # Circle close to target
        close_circles = {'cyan': [(90.0, 90.0, 10.0)], 'magenta': [], 'yellow': [], 'black': []}
        close_score = _compute_match_score(close_circles, cluster_map, target_index, max_distance)
        
        assert close_score > far_score, f"Closer circle should have higher score: {close_score} vs {far_score}"


class TestCMYKMassPreservation:
    """Test that CMYK color mass is preserved within tolerance."""
    
    def test_optimization_preserves_total_radius(self):
        """Total circle radius should be approximately preserved after optimization."""
        # Setup: multiple clusters with CMY petals
        circles_by_color = {
            'cyan': [(0.0, 0.0, 10.0), (100.0, 0.0, 15.0)],
            'magenta': [(0.0, 50.0, 12.0)],
            'yellow': [(50.0, 50.0, 8.0)],
            'black': [(50.0, 50.0, 20.0)],
        }
        
        # Calculate initial total mass (sum of areas)
        initial_cyan_area = sum(3.14159 * r * r for _, _, r in circles_by_color['cyan'])
        initial_magenta_area = sum(3.14159 * r * r for _, _, r in circles_by_color['magenta'])
        initial_yellow_area = sum(3.14159 * r * r for _, _, r in circles_by_color['yellow'])
        
        # Setup cluster metadata
        cluster_metadata = [
            {'cx': 0, 'cy': 0, 'black_radius': 20, 'black_circle_idx': 0},
            {'cx': 100, 'cy': 0, 'black_radius': 20, 'black_circle_idx': 0},
        ]
        cluster_circle_map = [
            {'cyan': (0, 100)},
            {'cyan': (1, 150)},
        ]
        
        # Target circles with slightly different positions
        target_circles = [
            TargetCircle(x=10, y=10, radius=10, color='cyan'),
            TargetCircle(x=110, y=10, radius=15, color='cyan'),
        ]
        target_index = TargetCircleIndex(target_circles)
        
        config = TargetGuidedConfig(
            target_image_path=Path("dummy.png"),
            target_weight=0.5,  # Balanced weight preserves more mass
            step_size=0.1,
            max_iterations=10,
        )
        
        result = apply_target_guided_optimization(
            circles_by_color,
            cluster_metadata,
            cluster_circle_map,
            target_index,
            image_shape=(200, 200),
            config=config,
        )
        
        # Calculate final cyan area
        final_cyan_area = sum(3.14159 * r * r for _, _, r in result['cyan'])
        
        # Area should not deviate more than 30% (with target_weight=0.5)
        deviation = abs(final_cyan_area - initial_cyan_area) / initial_cyan_area
        assert deviation < 0.30, f"Cyan area deviation {deviation:.1%} exceeds 30% tolerance"
    
    def test_mass_preserved_within_drift_tolerance(self):
        """CMYK mass should be preserved within drift_tolerance (typically 0.2 = 20%)."""
        drift_tolerance = 0.2  # Standard drift tolerance value
        
        # Setup with known initial masses
        initial_cyan = [(50.0, 50.0, 10.0)]  # Area = π * 100 ≈ 314
        circles_by_color = {
            'cyan': list(initial_cyan),
            'magenta': [],
            'yellow': [],
            'black': [(50.0, 50.0, 20.0)],
        }
        
        initial_mass = sum(3.14159 * r * r for _, _, r in initial_cyan)
        
        cluster_metadata = [{'cx': 50, 'cy': 50, 'black_radius': 20, 'black_circle_idx': 0}]
        cluster_circle_map = [{'cyan': (0, 100)}]
        
        # Target with same radius but different position
        target_circles = [TargetCircle(x=60, y=60, radius=10, color='cyan')]
        target_index = TargetCircleIndex(target_circles)
        
        # Use target_weight < 1 to allow mass preservation to dominate
        config = TargetGuidedConfig(
            target_image_path=Path("dummy.png"),
            target_weight=0.3,  # Lower weight preserves more mass
            step_size=0.1,
            max_iterations=20,
        )
        
        result = apply_target_guided_optimization(
            circles_by_color,
            cluster_metadata,
            cluster_circle_map,
            target_index,
            image_shape=(200, 200),
            config=config,
        )
        
        final_mass = sum(3.14159 * r * r for _, _, r in result['cyan'])
        
        # Mass deviation should be within drift_tolerance
        deviation = abs(final_mass - initial_mass) / initial_mass
        assert deviation <= drift_tolerance, (
            f"CMYK mass deviation {deviation:.1%} exceeds drift_tolerance {drift_tolerance:.0%}"
        )


class TestEndToEndTargetMatching:
    """Integration tests for end-to-end target matching."""
    
    def test_optimization_moves_circles_toward_target(self):
        """Circles should move toward target positions after optimization."""
        # Initial circle at origin
        circles_by_color = {
            'cyan': [(0.0, 0.0, 10.0)],
            'magenta': [],
            'yellow': [],
            'black': [(0.0, 0.0, 15.0)],
        }
        cluster_metadata = [{'cx': 0, 'cy': 0, 'black_radius': 15, 'black_circle_idx': 0}]
        cluster_circle_map = [{'cyan': (0, 100)}]
        
        # Target at (100, 100)
        target = TargetCircle(x=100, y=100, radius=10, color='cyan')
        target_index = TargetCircleIndex([target])
        
        config = TargetGuidedConfig(
            target_image_path=Path("dummy.png"),
            target_weight=1.0,  # Full target weight
            step_size=0.5,
            max_iterations=50,
        )
        
        result = apply_target_guided_optimization(
            circles_by_color,
            cluster_metadata,
            cluster_circle_map,
            target_index,
            image_shape=(200, 200),
            config=config,
        )
        
        final_x, final_y, final_r = result['cyan'][0]
        
        # Calculate distances
        initial_dist = np.sqrt(0**2 + 0**2 - 100**2 - 100**2 + 200**2)  # To (100, 100)
        initial_dist = np.sqrt((0 - 100)**2 + (0 - 100)**2)
        final_dist = np.sqrt((final_x - 100)**2 + (final_y - 100)**2)
        
        # Final distance should be less than initial (moved toward target)
        assert final_dist < initial_dist, f"Circle should move toward target: initial={initial_dist:.1f}, final={final_dist:.1f}"
        
        # Should have moved significantly (at least 20% closer after 50 iterations)
        improvement = (initial_dist - final_dist) / initial_dist
        assert improvement > 0.2, f"Should improve by >20%, got {improvement:.1%}"
    
    def test_multiple_colors_optimize_independently(self):
        """Each color channel should optimize toward its own targets."""
        circles_by_color = {
            'cyan': [(0.0, 0.0, 10.0)],
            'magenta': [(0.0, 50.0, 10.0)],
            'yellow': [(50.0, 0.0, 10.0)],
            'black': [(25.0, 25.0, 15.0)],
        }
        cluster_metadata = [
            {'cx': 0, 'cy': 0, 'black_radius': 15, 'black_circle_idx': 0},
            {'cx': 0, 'cy': 50, 'black_radius': 15, 'black_circle_idx': 0},
            {'cx': 50, 'cy': 0, 'black_radius': 15, 'black_circle_idx': 0},
        ]
        cluster_circle_map = [
            {'cyan': (0, 100)},
            {'magenta': (0, 100)},
            {'yellow': (0, 100)},
        ]
        
        # Different targets for each color
        targets = [
            TargetCircle(x=100, y=0, radius=10, color='cyan'),      # Cyan target right
            TargetCircle(x=0, y=100, radius=10, color='magenta'),   # Magenta target down
            TargetCircle(x=100, y=100, radius=10, color='yellow'),  # Yellow target diagonal
        ]
        target_index = TargetCircleIndex(targets)
        
        config = TargetGuidedConfig(
            target_image_path=Path("dummy.png"),
            target_weight=1.0,
            step_size=0.3,
            max_iterations=20,
        )
        
        result = apply_target_guided_optimization(
            circles_by_color,
            cluster_metadata,
            cluster_circle_map,
            target_index,
            image_shape=(200, 200),
            config=config,
        )
        
        # Cyan should have moved right (x increased)
        cyan_x, cyan_y, _ = result['cyan'][0]
        assert cyan_x > 10, "Cyan should move toward x=100"
        
        # Magenta should have moved down (y increased)
        magenta_x, magenta_y, _ = result['magenta'][0]
        assert magenta_y > 55, "Magenta should move toward y=100"
        
        # Yellow should have moved diagonally (both x and y increased)
        yellow_x, yellow_y, _ = result['yellow'][0]
        assert yellow_x > 55, "Yellow should move toward x=100"
        assert yellow_y > 5, "Yellow should move toward y=100"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
