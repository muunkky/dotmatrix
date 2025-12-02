"""Tests for orphan pixel diagnostic tool.

TDD tests for the orphan_diagnostic module that identifies pixels
not covered by any detected cluster.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from dotmatrix.orphan_diagnostic import (
    OrphanDiagnostic,
    OrphanStats,
    find_orphan_pixels,
    compute_distance_map,
    generate_overlay_image,
    generate_heatmap,
)


class TestOrphanStats:
    """Test the OrphanStats dataclass."""

    def test_orphan_stats_creation(self):
        """OrphanStats should hold orphan pixel statistics."""
        stats = OrphanStats(
            total_orphans=1000,
            total_nonwhite=10000,
            orphan_percentage=10.0,
            region_bounds=(100, 200, 300, 400),  # x_min, y_min, x_max, y_max
            max_distance=75.5,
            mean_distance=45.2,
        )
        assert stats.total_orphans == 1000
        assert stats.orphan_percentage == 10.0
        assert stats.region_bounds == (100, 200, 300, 400)


class TestDistanceMap:
    """Test distance map computation from cluster centers."""

    def test_compute_distance_map_single_cluster(self):
        """Distance map should show distance to single cluster center."""
        # 10x10 image, cluster at (5, 5)
        image_shape = (10, 10, 3)
        cluster_centers = [(5, 5)]
        
        distance_map = compute_distance_map(image_shape[:2], cluster_centers)
        
        # Distance at cluster center should be 0
        assert distance_map[5, 5] == 0.0
        # Distance at (0, 0) should be sqrt(50) ≈ 7.07
        assert abs(distance_map[0, 0] - np.sqrt(50)) < 0.01
        # Distance at (5, 0) should be 5
        assert abs(distance_map[0, 5] - 5.0) < 0.01

    def test_compute_distance_map_multiple_clusters(self):
        """Distance map should show minimum distance to any cluster."""
        # 10x10 image, clusters at (2, 2) and (8, 8)
        image_shape = (10, 10)
        cluster_centers = [(2, 2), (8, 8)]
        
        distance_map = compute_distance_map(image_shape, cluster_centers)
        
        # Distance at (2, 2) should be 0 (nearest cluster)
        assert distance_map[2, 2] == 0.0
        # Distance at (8, 8) should be 0 (nearest cluster)
        assert distance_map[8, 8] == 0.0
        # Distance at (5, 5) should be equidistant ≈ 4.24
        expected = np.sqrt((5-2)**2 + (5-2)**2)
        assert abs(distance_map[5, 5] - expected) < 0.01

    def test_compute_distance_map_no_clusters(self):
        """Distance map with no clusters should be all infinity."""
        image_shape = (10, 10)
        cluster_centers = []
        
        distance_map = compute_distance_map(image_shape, cluster_centers)
        
        assert np.all(np.isinf(distance_map))


class TestFindOrphanPixels:
    """Test finding orphan pixels based on distance threshold."""

    def test_find_orphans_simple_case(self):
        """Orphans should be non-white pixels far from clusters."""
        # Create a simple image: white background, black dots
        image = np.ones((20, 20, 3), dtype=np.uint8) * 255
        # Black dot at (5, 5) - near cluster
        image[4:7, 4:7] = [0, 0, 0]
        # Black dot at (15, 15) - far from cluster
        image[14:17, 14:17] = [0, 0, 0]
        
        # Cluster only at (5, 5)
        cluster_centers = [(5, 5)]
        threshold = 5.0
        
        orphan_coords, stats = find_orphan_pixels(
            image, cluster_centers, threshold
        )
        
        # Orphans should be around (15, 15)
        assert stats.total_orphans > 0
        # All orphans should be far from (5, 5)
        for y, x in orphan_coords:
            dist = np.sqrt((x - 5)**2 + (y - 5)**2)
            assert dist > threshold

    def test_find_orphans_white_pixels_excluded(self):
        """White pixels should never be orphans."""
        # All white image
        image = np.ones((10, 10, 3), dtype=np.uint8) * 255
        cluster_centers = [(5, 5)]
        
        orphan_coords, stats = find_orphan_pixels(image, cluster_centers, threshold=1.0)
        
        assert stats.total_orphans == 0
        assert stats.total_nonwhite == 0

    def test_find_orphans_stats_percentage(self):
        """Orphan percentage should be calculated correctly."""
        # Image with known non-white pixels
        image = np.ones((10, 10, 3), dtype=np.uint8) * 255
        # 10 black pixels
        image[0, 0:10] = [0, 0, 0]
        
        # No clusters - all should be orphans
        cluster_centers = []
        
        _, stats = find_orphan_pixels(image, cluster_centers, threshold=1.0)
        
        assert stats.total_nonwhite == 10
        assert stats.total_orphans == 10
        assert stats.orphan_percentage == 100.0


class TestGenerateOverlayImage:
    """Test overlay image generation highlighting orphans."""

    def test_overlay_highlights_orphans(self):
        """Overlay should mark orphan pixels in red."""
        # Create test image
        original = np.ones((20, 20, 3), dtype=np.uint8) * 128  # Gray
        orphan_coords = [(5, 5), (10, 10), (15, 15)]
        
        overlay = generate_overlay_image(original, orphan_coords)
        
        # Orphan pixels should be red (255, 0, 0)
        for y, x in orphan_coords:
            assert tuple(overlay[y, x]) == (255, 0, 0), f"Pixel at ({y}, {x}) should be red"

    def test_overlay_preserves_non_orphan_pixels(self):
        """Non-orphan pixels should keep original color."""
        original = np.ones((10, 10, 3), dtype=np.uint8) * 128
        orphan_coords = [(5, 5)]
        
        overlay = generate_overlay_image(original, orphan_coords)
        
        # Non-orphan pixels should be unchanged
        assert tuple(overlay[0, 0]) == (128, 128, 128)


class TestGenerateHeatmap:
    """Test heatmap generation showing distance from clusters."""

    def test_heatmap_colormap(self):
        """Heatmap should use color gradient for distances."""
        distance_map = np.array([
            [0.0, 10.0, 20.0],
            [10.0, 15.0, 25.0],
            [20.0, 25.0, 50.0],
        ])
        
        heatmap = generate_heatmap(distance_map, max_distance=50.0)
        
        # Should be 3-channel color image
        assert heatmap.shape == (3, 3, 3)
        # Center (0, 0) should be different color than corner (2, 2)
        assert not np.array_equal(heatmap[0, 0], heatmap[2, 2])


class TestOrphanDiagnostic:
    """Integration tests for the OrphanDiagnostic class."""

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create a sample image for testing."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255
        # Add some black dots
        image[20:25, 20:25] = [0, 0, 0]  # Near cluster
        image[80:85, 80:85] = [0, 0, 0]  # Far from cluster (orphan)
        
        image_path = tmp_path / "test_image.png"
        Image.fromarray(image).save(image_path)
        return image_path

    @pytest.fixture
    def sample_clusters(self, tmp_path):
        """Create sample cluster JSON for testing."""
        clusters = {
            "circles": [
                {"x": 22, "y": 22, "radius": 3.0},
            ]
        }
        json_path = tmp_path / "clusters.json"
        json_path.write_text(json.dumps(clusters))
        return json_path

    def test_diagnostic_end_to_end(self, sample_image, sample_clusters, tmp_path):
        """Full diagnostic workflow should produce output files."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        diagnostic = OrphanDiagnostic(
            image_path=sample_image,
            cluster_json_path=sample_clusters,
            threshold=50.0,
        )
        
        result = diagnostic.run(output_dir)
        
        # Should find orphans near (80, 80)
        assert result.stats.total_orphans > 0
        # Should generate output files
        assert (output_dir / "orphan_overlay.png").exists()
        assert (output_dir / "distance_heatmap.png").exists()
        assert (output_dir / "orphan_stats.json").exists()

    def test_diagnostic_stats_json(self, sample_image, sample_clusters, tmp_path):
        """Stats JSON should contain expected fields."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        diagnostic = OrphanDiagnostic(
            image_path=sample_image,
            cluster_json_path=sample_clusters,
            threshold=50.0,
        )
        
        diagnostic.run(output_dir)
        
        stats_json = json.loads((output_dir / "orphan_stats.json").read_text())
        assert "total_orphans" in stats_json
        assert "orphan_percentage" in stats_json
        assert "region_bounds" in stats_json
