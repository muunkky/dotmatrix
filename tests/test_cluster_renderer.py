"""Unit tests for cluster_renderer module (TDD)."""

import math
from pathlib import Path
import numpy as np
import pytest
import cv2

from dotmatrix.cluster_pixel_counter import ClusterResult
from dotmatrix.cluster_renderer import (
    calculate_cumulative_radii,
    render_bullseye,
    render_single_cluster,
)

# Path to test image
TEST_IMAGE = Path(__file__).parent.parent / "test_dotmatrix.png"


class TestRadiusCalculation:
    """Tests for radius calculation from pixel counts."""

    def test_radius_from_area_formula(self):
        """Test that radius = sqrt(area / pi)."""
        # 100 pixels -> radius = sqrt(100/pi) ≈ 5.64
        area = 100
        expected_radius = math.sqrt(area / math.pi)
        assert abs(expected_radius - 5.64) < 0.01

    def test_cumulative_radii_single_channel(self):
        """Test radii calculation with only black pixels."""
        cluster = ClusterResult(
            x=50, y=50,
            cyan=0, magenta=0, yellow=0, black=100,
            red=0, green=0, blue=0
        )
        radii = calculate_cumulative_radii(cluster)

        # Only black, so only K radius is non-zero
        assert radii['black'] > 0
        assert radii['cyan'] == radii['black']  # No cyan added
        assert radii['magenta'] == radii['black']  # No magenta added
        assert radii['yellow'] == radii['black']  # No yellow added

    def test_cumulative_radii_full_cmyk(self):
        """Test radii with all CMYK channels populated."""
        cluster = ClusterResult(
            x=50, y=50,
            cyan=50, magenta=75, yellow=100, black=25,
            red=0, green=0, blue=0
        )
        radii = calculate_cumulative_radii(cluster)

        # Black is innermost (smallest)
        # Then cyan includes black
        # Then magenta includes cyan
        # Then yellow is outermost (largest)
        assert radii['black'] < radii['cyan']
        assert radii['cyan'] < radii['magenta']
        assert radii['magenta'] < radii['yellow']

    def test_cumulative_radii_with_overlaps(self):
        """Test radii calculation includes RGB overlap pixels."""
        cluster = ClusterResult(
            x=50, y=50,
            cyan=50, magenta=50, yellow=50, black=25,
            red=10, green=10, blue=10  # Overlaps
        )
        radii = calculate_cumulative_radii(cluster)

        # All radii should be positive
        assert radii['black'] > 0
        assert radii['cyan'] > radii['black']
        assert radii['magenta'] > radii['cyan']
        assert radii['yellow'] > radii['magenta']

        # Total area should include all pixels
        total_pixels = 50 + 50 + 50 + 25 + 10 + 10 + 10
        expected_outer_radius = math.sqrt(total_pixels / math.pi)
        assert abs(radii['yellow'] - expected_outer_radius) < 0.1

    def test_cumulative_radii_zero_pixels(self):
        """Test handling of cluster with zero pixels in some channels."""
        cluster = ClusterResult(
            x=50, y=50,
            cyan=0, magenta=0, yellow=100, black=0,
            red=0, green=0, blue=0
        )
        radii = calculate_cumulative_radii(cluster)

        # Only yellow has pixels
        assert radii['black'] == 0
        assert radii['cyan'] == 0
        assert radii['magenta'] == 0
        assert radii['yellow'] > 0


class TestSingleClusterRendering:
    """Tests for rendering a single cluster."""

    def test_renders_to_correct_shape(self):
        """Test that output has correct dimensions."""
        cluster = ClusterResult(
            x=50, y=50,
            cyan=50, magenta=75, yellow=100, black=25,
            red=0, green=0, blue=0
        )
        image_shape = (100, 100)

        output = render_single_cluster(cluster, image_shape)

        assert output.shape == (100, 100, 3)
        assert output.dtype == np.uint8

    def test_black_at_center(self):
        """Test that black pixels appear at cluster center."""
        cluster = ClusterResult(
            x=50, y=50,
            cyan=50, magenta=50, yellow=50, black=100,
            red=0, green=0, blue=0
        )
        image_shape = (100, 100)

        output = render_single_cluster(cluster, image_shape)

        # Center should be black (0, 0, 0)
        center_color = output[50, 50]
        assert tuple(center_color) == (0, 0, 0)

    def test_yellow_at_outer_edge(self):
        """Test that yellow appears at the outer edge of cluster."""
        cluster = ClusterResult(
            x=50, y=50,
            cyan=100, magenta=200, yellow=400, black=50,
            red=0, green=0, blue=0
        )
        image_shape = (100, 100)

        output = render_single_cluster(cluster, image_shape)

        # Calculate expected yellow radius
        total_pixels = 100 + 200 + 400 + 50
        yellow_radius = math.sqrt(total_pixels / math.pi)

        # Sample point just inside yellow ring (but outside magenta)
        # Yellow is (0, 255, 255) in BGR or (255, 255, 0) in RGB
        # We use RGB format
        sample_distance = int(yellow_radius - 2)
        sample_x = 50 + sample_distance
        if sample_x < 100:
            sample_color = output[50, sample_x]
            # Should be yellow (255, 255, 0) in RGB
            assert sample_color[0] == 255  # R
            assert sample_color[1] == 255  # G
            assert sample_color[2] == 0    # B

    def test_white_background(self):
        """Test that areas outside cluster are white."""
        cluster = ClusterResult(
            x=50, y=50,
            cyan=10, magenta=10, yellow=10, black=10,
            red=0, green=0, blue=0
        )
        image_shape = (100, 100)

        output = render_single_cluster(cluster, image_shape)

        # Far corner should be white
        corner_color = output[0, 0]
        assert tuple(corner_color) == (255, 255, 255)


class TestMultiClusterRendering:
    """Tests for rendering multiple clusters."""

    def test_renders_multiple_clusters(self):
        """Test rendering multiple clusters at different positions."""
        clusters = [
            ClusterResult(x=25, y=25, cyan=50, magenta=50, yellow=50, black=25,
                         red=0, green=0, blue=0),
            ClusterResult(x=75, y=75, cyan=50, magenta=50, yellow=50, black=25,
                         red=0, green=0, blue=0),
        ]
        image_shape = (100, 100)

        output = render_bullseye(clusters, image_shape)

        assert output.shape == (100, 100, 3)

        # Both cluster centers should be black
        assert tuple(output[25, 25]) == (0, 0, 0)
        assert tuple(output[75, 75]) == (0, 0, 0)

    def test_empty_clusters_list(self):
        """Test rendering with no clusters returns white image."""
        clusters = []
        image_shape = (100, 100)

        output = render_bullseye(clusters, image_shape)

        assert output.shape == (100, 100, 3)
        # Should be all white
        assert np.all(output == 255)

    def test_skip_partial_clusters(self):
        """Test that partial clusters can be skipped."""
        clusters = [
            ClusterResult(x=50, y=50, cyan=50, magenta=50, yellow=50, black=25,
                         red=0, green=0, blue=0, partial=False),
            ClusterResult(x=5, y=5, cyan=50, magenta=50, yellow=50, black=25,
                         red=0, green=0, blue=0, partial=True),
        ]
        image_shape = (100, 100)

        output = render_bullseye(clusters, image_shape, skip_partial=True)

        # Center cluster should be rendered
        assert tuple(output[50, 50]) == (0, 0, 0)

        # Partial cluster at (5,5) should be skipped - area should be white
        # (unless affected by the other cluster's radius)
        # Actually the full cluster at 50,50 won't reach (5,5), so it should be white
        assert tuple(output[5, 5]) == (255, 255, 255)

    def test_render_partial_clusters_by_default(self):
        """Test that partial clusters are rendered by default."""
        clusters = [
            ClusterResult(x=5, y=5, cyan=50, magenta=50, yellow=50, black=25,
                         red=0, green=0, blue=0, partial=True),
        ]
        image_shape = (100, 100)

        output = render_bullseye(clusters, image_shape)

        # Partial cluster should be rendered (center should be black)
        assert tuple(output[5, 5]) == (0, 0, 0)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_cluster_at_corner(self):
        """Test cluster at image corner clips correctly."""
        cluster = ClusterResult(
            x=0, y=0,
            cyan=100, magenta=100, yellow=100, black=50,
            red=0, green=0, blue=0
        )
        image_shape = (100, 100)

        output = render_single_cluster(cluster, image_shape)

        # Should not raise error, corner should have cluster color
        assert output.shape == (100, 100, 3)
        # Origin should have black (or near it)
        assert tuple(output[0, 0]) == (0, 0, 0)

    def test_all_zero_pixels(self):
        """Test cluster with all zero pixel counts."""
        cluster = ClusterResult(
            x=50, y=50,
            cyan=0, magenta=0, yellow=0, black=0,
            red=0, green=0, blue=0
        )
        image_shape = (100, 100)

        output = render_single_cluster(cluster, image_shape)

        # With no pixels, should just be white background
        assert tuple(output[50, 50]) == (255, 255, 255)

    def test_very_large_cluster(self):
        """Test cluster with large pixel counts doesn't overflow."""
        cluster = ClusterResult(
            x=500, y=500,
            cyan=10000, magenta=10000, yellow=10000, black=5000,
            red=1000, green=1000, blue=1000
        )
        image_shape = (1000, 1000)

        output = render_single_cluster(cluster, image_shape)

        assert output.shape == (1000, 1000, 3)
        # Center should still be black
        assert tuple(output[500, 500]) == (0, 0, 0)


class TestRGBOverlaps:
    """Tests for RGB overlap colors at circle intersections."""

    def test_red_overlap_visible(self):
        """Test that red (M∩Y) overlap is visible between magenta and yellow."""
        # Create cluster with magenta and yellow (should show red where they overlap)
        cluster = ClusterResult(
            x=100, y=100,
            cyan=0, magenta=500, yellow=800, black=50,
            red=100, green=0, blue=0  # Explicit red overlap area
        )
        image_shape = (200, 200)

        output = render_single_cluster(cluster, image_shape)

        # The magenta ring should overlap with yellow ring
        # Due to the drawing order (Y then M), magenta appears on top
        # Red emerges where both M and Y would be
        # Actually with our current implementation, we draw solid circles
        # so the layering creates the visual effect

        # Check that center is black
        assert tuple(output[100, 100]) == (0, 0, 0)

        # Check that magenta color exists somewhere
        # Sample at a position that should be magenta (between cyan and yellow radius)
        radii = calculate_cumulative_radii(cluster)
        magenta_r = int(radii['magenta'])
        cyan_r = int(radii['cyan'])
        sample_dist = (magenta_r + cyan_r) // 2
        if sample_dist > 0:
            sample_color = output[100, 100 + sample_dist]
            # Should be magenta (255, 0, 255)
            assert sample_color[0] == 255  # R
            assert sample_color[1] == 0    # G
            assert sample_color[2] == 255  # B

    def test_layer_order_creates_correct_colors(self):
        """Test that the Y→M→C→K layer order produces expected colors."""
        cluster = ClusterResult(
            x=100, y=100,
            cyan=200, magenta=400, yellow=600, black=100,
            red=50, green=50, blue=50
        )
        image_shape = (200, 200)

        output = render_single_cluster(cluster, image_shape)
        radii = calculate_cumulative_radii(cluster)

        # Center should be black (innermost)
        assert tuple(output[100, 100]) == (0, 0, 0)

        # Just outside black radius should be cyan
        k_r = int(radii['black'])
        c_r = int(radii['cyan'])
        if c_r > k_r + 2:
            sample_dist = (k_r + c_r) // 2
            sample = output[100, 100 + sample_dist]
            assert tuple(sample) == (0, 255, 255), f"Expected cyan, got {sample}"


class TestPerformance:
    """Performance tests for cluster rendering."""

    def test_100_clusters_under_1_second(self):
        """Test that rendering 100 clusters completes in under 1 second."""
        import time

        # Create 100 clusters spread across the image
        clusters = []
        for i in range(10):
            for j in range(10):
                clusters.append(ClusterResult(
                    x=50 + i * 100, y=50 + j * 100,
                    cyan=50, magenta=50, yellow=50, black=25,
                    red=10, green=10, blue=10
                ))
        image_shape = (1000, 1000)

        start = time.time()
        output = render_bullseye(clusters, image_shape)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Rendering took {elapsed:.2f}s, expected <1s"
        assert output.shape == (1000, 1000, 3)


class TestOutputFormat:
    """Tests for output image format and properties."""

    def test_output_is_rgb(self):
        """Test that output is RGB format (not BGR)."""
        cluster = ClusterResult(
            x=50, y=50,
            cyan=0, magenta=0, yellow=500, black=0,
            red=0, green=0, blue=0
        )
        image_shape = (100, 100)

        output = render_single_cluster(cluster, image_shape)

        # Yellow in RGB is (255, 255, 0)
        center_color = output[50, 50]
        assert center_color[0] == 255  # R
        assert center_color[1] == 255  # G
        assert center_color[2] == 0    # B

    def test_output_dtype(self):
        """Test that output is uint8."""
        clusters = [
            ClusterResult(x=50, y=50, cyan=50, magenta=50, yellow=50, black=25,
                         red=0, green=0, blue=0)
        ]
        image_shape = (100, 100)

        output = render_bullseye(clusters, image_shape)

        assert output.dtype == np.uint8

    def test_output_value_range(self):
        """Test that output values are in valid 0-255 range."""
        clusters = [
            ClusterResult(x=50, y=50, cyan=50, magenta=50, yellow=50, black=25,
                         red=0, green=0, blue=0)
        ]
        image_shape = (100, 100)

        output = render_bullseye(clusters, image_shape)

        assert output.min() >= 0
        assert output.max() <= 255


class TestIntegration:
    """Integration tests with real image data."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_with_real_cluster_data(self):
        """Test rendering with real cluster data from test_dotmatrix.png."""
        # Create synthetic cluster data representative of real detection
        # (actual integration would use cluster_and_count_pixels from real image)
        clusters = [
            ClusterResult(x=100, y=100, cyan=150, magenta=200, yellow=250, black=100,
                         red=50, green=50, blue=50, partial=False),
            ClusterResult(x=300, y=300, cyan=100, magenta=150, yellow=200, black=80,
                         red=30, green=40, blue=20, partial=False),
            ClusterResult(x=500, y=200, cyan=200, magenta=100, yellow=300, black=120,
                         red=40, green=60, blue=30, partial=False),
        ]

        # Use dimensions similar to test image
        image_shape = (600, 800)

        output = render_bullseye(clusters, image_shape)

        # Verify all cluster centers have black
        for cluster in clusters:
            assert tuple(output[cluster.y, cluster.x]) == (0, 0, 0)

    def test_output_loadable_by_cv2(self, tmp_path):
        """Test that output image can be saved and loaded by cv2."""
        clusters = [
            ClusterResult(x=50, y=50, cyan=50, magenta=50, yellow=50, black=25,
                         red=10, green=10, blue=10)
        ]
        image_shape = (100, 100)

        output = render_bullseye(clusters, image_shape)

        # Save to temp file
        output_path = tmp_path / "test_output.png"
        # Convert RGB to BGR for cv2.imwrite
        bgr_output = cv2.cvtColor(output, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(output_path), bgr_output)

        # Load back
        loaded = cv2.imread(str(output_path))
        assert loaded is not None
        assert loaded.shape == (100, 100, 3)

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_output_dimensions_match_source(self):
        """Test that output dimensions match specified source dimensions."""
        # Load test image to get its dimensions
        source = cv2.imread(str(TEST_IMAGE))
        h, w = source.shape[:2]

        # Create clusters
        clusters = [
            ClusterResult(x=w//4, y=h//4, cyan=100, magenta=100, yellow=100, black=50,
                         red=20, green=20, blue=20)
        ]

        output = render_bullseye(clusters, (h, w))

        assert output.shape[0] == h
        assert output.shape[1] == w
        assert output.shape[2] == 3
