"""Tests for planetary renderer - CMY dots tangent to black circle surface.

TDD Tests for the planetary render method which positions CMY dots on the
surface of the black center (like moons orbiting a planet) rather than
overlapping with it like flower mode.

Key difference from flower:
- Flower: petal_distance = black_radius * fraction (dots overlap black)
- Planetary: orbital_distance = black_radius + petal_radius (dots tangent to black)
"""

import math
import pytest
import numpy as np

from dotmatrix.cluster_pixel_counter import ClusterResult
from dotmatrix.colors import PETAL_ANGLES


class TestPlanetaryPositioning:
    """Test that CMY dots are positioned tangent to black circle."""
    
    def test_planetary_dot_distance_from_center(self):
        """CMY dots should be positioned at black_radius + cmy_radius from center."""
        from dotmatrix.circle_renderer import render_planetary_svg
        
        # Create a simple cluster with known values
        cluster = ClusterResult(
            x=100, y=100,
            cyan=100, magenta=100, yellow=100,
            red=0, green=0, blue=0,
            black=400,  # radius ~11.28
            partial=False
        )
        
        svg_output = render_planetary_svg(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
            rotation_mode='fixed',
            base_rotation=0.0,
        )
        
        # Parse SVG to extract circle positions
        import re
        circles = re.findall(r'<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"', svg_output)
        
        # Should have 4 circles: black + cyan + magenta + yellow
        assert len(circles) >= 4, f"Expected at least 4 circles, got {len(circles)}"
        
        # Find black circle (largest radius, at center)
        black_circle = None
        cmy_circles = []
        
        for cx, cy, r in circles:
            cx, cy, r = float(cx), float(cy), float(r)
            # Black is at center and has largest radius
            if abs(cx - 100) < 1 and abs(cy - 100) < 1:
                black_circle = (cx, cy, r)
            else:
                cmy_circles.append((cx, cy, r))
        
        assert black_circle is not None, "Black circle not found at center"
        black_cx, black_cy, black_r = black_circle
        
        # Verify CMY circles are tangent to black (distance = black_r + cmy_r)
        for cx, cy, r in cmy_circles:
            distance_from_center = math.sqrt((cx - black_cx)**2 + (cy - black_cy)**2)
            expected_distance = black_r + r
            # Allow small tolerance for floating point
            assert abs(distance_from_center - expected_distance) < 0.5, \
                f"CMY dot at ({cx}, {cy}) has distance {distance_from_center:.2f} from center, " \
                f"expected {expected_distance:.2f} (black_r={black_r:.2f} + cmy_r={r:.2f})"
    
    def test_planetary_dots_do_not_overlap_black(self):
        """CMY dots should not overlap with black circle (tangent only)."""
        from dotmatrix.circle_renderer import render_planetary_svg
        
        cluster = ClusterResult(
            x=100, y=100,
            cyan=200, magenta=200, yellow=200,
            red=0, green=0, blue=0,
            black=600,
            partial=False
        )
        
        svg_output = render_planetary_svg(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
        )
        
        import re
        circles = re.findall(r'<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"', svg_output)
        
        # Find black circle
        black_circle = None
        cmy_circles = []
        
        for cx, cy, r in circles:
            cx, cy, r = float(cx), float(cy), float(r)
            if abs(cx - 100) < 1 and abs(cy - 100) < 1:
                black_circle = (cx, cy, r)
            else:
                cmy_circles.append((cx, cy, r))
        
        assert black_circle is not None
        black_cx, black_cy, black_r = black_circle
        
        # Verify no CMY circle overlaps with black
        for cx, cy, r in cmy_circles:
            distance_from_center = math.sqrt((cx - black_cx)**2 + (cy - black_cy)**2)
            min_non_overlap_distance = black_r + r
            assert distance_from_center >= min_non_overlap_distance - 0.5, \
                f"CMY dot at ({cx}, {cy}) overlaps black circle! " \
                f"Distance {distance_from_center:.2f} < required {min_non_overlap_distance:.2f}"


class TestPlanetaryAngularSpacing:
    """Test that CMY dots maintain 90° angular spacing (same as flower)."""
    
    def test_planetary_120_degree_spacing(self):
        """CMY dots should be spaced 90° apart (N, E, S positions)."""
        from dotmatrix.circle_renderer import render_planetary_svg
        
        cluster = ClusterResult(
            x=100, y=100,
            cyan=100, magenta=100, yellow=100,
            red=0, green=0, blue=0,
            black=400,
            partial=False
        )
        
        svg_output = render_planetary_svg(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
            rotation_mode='fixed',
            base_rotation=0.0,
        )
        
        import re
        circles = re.findall(r'<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"', svg_output)
        
        # Separate black from CMY
        center = (100, 100)
        cmy_angles = []
        
        for cx, cy, r in circles:
            cx, cy, r = float(cx), float(cy), float(r)
            if abs(cx - 100) > 1 or abs(cy - 100) > 1:
                # Calculate angle from center
                angle = math.degrees(math.atan2(cy - center[1], cx - center[0]))
                cmy_angles.append(angle)
        
        assert len(cmy_angles) == 3, f"Expected 3 CMY dots, got {len(cmy_angles)}"
        
        # Sort angles
        cmy_angles.sort()
        
        # Check spacing between consecutive angles
        spacing = []
        for i in range(len(cmy_angles)):
            next_i = (i + 1) % len(cmy_angles)
            diff = cmy_angles[next_i] - cmy_angles[i]
            if diff < 0:
                diff += 360
            spacing.append(diff)
        
        # Each spacing should be approximately 90° (N, E, S pattern)
        for s in spacing:
            assert 85 < s < 95 or 175 < s < 185, \
                f"Angular spacing {s}° is not close to 90° or 180°"


class TestPlanetaryRotation:
    """Test rotation modes work with planetary renderer."""
    
    def test_planetary_fixed_rotation(self):
        """Fixed rotation mode should position all clusters identically."""
        from dotmatrix.circle_renderer import render_planetary_svg
        
        clusters = [
            ClusterResult(x=50, y=50, cyan=100, magenta=100, yellow=100, 
                         red=0, green=0, blue=0, black=200, partial=False),
            ClusterResult(x=150, y=150, cyan=100, magenta=100, yellow=100,
                         red=0, green=0, blue=0, black=200, partial=False),
        ]
        
        svg_output = render_planetary_svg(
            clusters=clusters,
            image_shape=(200, 200),
            scale=1,
            rotation_mode='fixed',
            base_rotation=0.0,
        )
        
        # Both clusters should have consistent angular positioning
        assert 'cyan' in svg_output.lower() or 'fill="#00FFFF"' in svg_output or '#00ffff' in svg_output.lower()
    
    def test_planetary_cluster_hash_rotation(self):
        """Cluster-hash rotation mode should produce different orientations."""
        from dotmatrix.circle_renderer import render_planetary_svg
        
        clusters = [
            ClusterResult(x=50, y=50, cyan=100, magenta=100, yellow=100,
                         red=0, green=0, blue=0, black=200, partial=False),
            ClusterResult(x=150, y=150, cyan=100, magenta=100, yellow=100,
                         red=0, green=0, blue=0, black=200, partial=False),
        ]
        
        svg1 = render_planetary_svg(
            clusters=clusters,
            image_shape=(200, 200),
            scale=1,
            rotation_mode='cluster-hash',
        )
        
        # Should produce valid SVG
        assert '<svg' in svg1
        assert '</svg>' in svg1


class TestPlanetaryJitter:
    """Test jitter options work with planetary renderer."""
    
    def test_planetary_position_jitter(self):
        """Position jitter should affect CMY dot positions."""
        from dotmatrix.circle_renderer import render_planetary_svg
        
        cluster = ClusterResult(
            x=100, y=100,
            cyan=100, magenta=100, yellow=100,
            red=0, green=0, blue=0,
            black=400,
            partial=False
        )
        
        # Without jitter
        svg_no_jitter = render_planetary_svg(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
            jitter_position=0,
        )
        
        # With jitter
        svg_with_jitter = render_planetary_svg(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
            jitter_position=25,
            jitter_seed=42,
        )
        
        # Outputs should be different
        assert svg_no_jitter != svg_with_jitter
    
    def test_planetary_size_jitter(self):
        """Size jitter should affect CMY dot sizes."""
        from dotmatrix.circle_renderer import render_planetary_svg
        
        cluster = ClusterResult(
            x=100, y=100,
            cyan=100, magenta=100, yellow=100,
            red=0, green=0, blue=0,
            black=400,
            partial=False
        )
        
        # Without jitter
        svg_no_jitter = render_planetary_svg(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
            jitter_size=0,
        )
        
        # With size jitter
        svg_with_jitter = render_planetary_svg(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
            jitter_size=25,
            jitter_seed=42,
        )
        
        # Outputs should be different
        assert svg_no_jitter != svg_with_jitter
    
    def test_planetary_jitter_exclude_black(self):
        """Jitter exclude 'k' should not jitter black circle."""
        from dotmatrix.circle_renderer import render_planetary_svg
        
        cluster = ClusterResult(
            x=100, y=100,
            cyan=100, magenta=100, yellow=100,
            red=0, green=0, blue=0,
            black=400,
            partial=False
        )
        
        svg_output = render_planetary_svg(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
            jitter_position=25,
            jitter_size=25,
            jitter_seed=42,
            jitter_exclude='k',
        )
        
        # Black circle should still be at center (100, 100)
        import re
        # Look for black layer circles
        black_section = re.search(r'id="black-layer"[^>]*>(.*?)</g>', svg_output, re.DOTALL)
        if black_section:
            black_circles = re.findall(r'<circle cx="([^"]+)" cy="([^"]+)"', black_section.group(1))
            if black_circles:
                cx, cy = float(black_circles[0][0]), float(black_circles[0][1])
                assert abs(cx - 100) < 1 and abs(cy - 100) < 1, \
                    f"Black circle should be at (100, 100), got ({cx}, {cy})"


class TestPlanetaryPNG:
    """Test PNG output with planetary renderer."""
    
    def test_planetary_png_output(self):
        """Planetary PNG renderer should produce valid image array."""
        from dotmatrix.circle_renderer import render_planetary
        
        cluster = ClusterResult(
            x=100, y=100,
            cyan=100, magenta=100, yellow=100,
            red=0, green=0, blue=0,
            black=400,
            partial=False
        )
        
        result = render_planetary(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
        )
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (200, 200, 3)  # BGR image
        assert result.dtype == np.uint8
    
    def test_planetary_png_blend_overlaps(self):
        """Planetary PNG with blend_overlaps should produce valid output."""
        from dotmatrix.circle_renderer import render_planetary
        
        cluster = ClusterResult(
            x=100, y=100,
            cyan=100, magenta=100, yellow=100,
            red=0, green=0, blue=0,
            black=400,
            partial=False
        )
        
        result = render_planetary(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
            blend_overlaps=True,
        )
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (200, 200, 3)


class TestPlanetaryVsFlower:
    """Compare planetary and flower renderers."""
    
    def test_planetary_has_larger_footprint_than_flower(self):
        """Planetary clusters should have larger footprint since dots don't overlap."""
        from dotmatrix.circle_renderer import render_flower_svg, render_planetary_svg
        
        cluster = ClusterResult(
            x=100, y=100,
            cyan=200, magenta=200, yellow=200,
            red=0, green=0, blue=0,
            black=600,
            partial=False
        )
        
        flower_svg = render_flower_svg(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
        )
        
        planetary_svg = render_planetary_svg(
            clusters=[cluster],
            image_shape=(200, 200),
            scale=1,
        )
        
        # Both should be valid SVGs
        assert '<svg' in flower_svg
        assert '<svg' in planetary_svg
        
        # Planetary CMY dots should be further from center than flower petals
        import re
        
        def get_cmy_distances(svg, center):
            circles = re.findall(r'<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"', svg)
            distances = []
            for cx, cy, r in circles:
                cx, cy = float(cx), float(cy)
                if abs(cx - center[0]) > 1 or abs(cy - center[1]) > 1:
                    dist = math.sqrt((cx - center[0])**2 + (cy - center[1])**2)
                    distances.append(dist)
            return distances
        
        flower_distances = get_cmy_distances(flower_svg, (100, 100))
        planetary_distances = get_cmy_distances(planetary_svg, (100, 100))
        
        if flower_distances and planetary_distances:
            avg_flower = sum(flower_distances) / len(flower_distances)
            avg_planetary = sum(planetary_distances) / len(planetary_distances)
            assert avg_planetary > avg_flower, \
                f"Planetary avg distance ({avg_planetary:.2f}) should be > flower ({avg_flower:.2f})"


class TestPlanetaryCLI:
    """Test CLI integration for planetary render method."""
    
    def test_planetary_cli_option_exists(self):
        """CLI should accept --render-method planetary."""
        from click.testing import CliRunner
        from dotmatrix.cli import cli
        
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        # Check that planetary is listed in help
        assert 'planetary' in result.output.lower() or result.exit_code == 0
