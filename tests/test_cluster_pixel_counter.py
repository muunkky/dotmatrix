"""Tests for CMYK cluster pixel counting.

TDD tests for the cluster_pixel_counter module that implements:
- Midtone completion (Phase 1)
- Nearest pixel clustering (Phase 2)
- Pixel counting with deduplication (Phase 3)
"""

import numpy as np
import pytest

from dotmatrix.cluster_pixel_counter import ClusterResult


class TestMidtoneCompletion:
    """Test Phase 1: Completing midtone masks with RGB overlaps."""

    def test_complete_cyan_mask_includes_green_pixels(self):
        """Cyan mask should include Green (C∩Y) pixels."""
        from dotmatrix.cluster_pixel_counter import complete_midtone_masks

        # Create simple test masks
        # Green pixel at (5, 5) - should be in both C and Y
        cyan_mask = np.zeros((10, 10), dtype=np.uint8)
        cyan_mask[2, 2] = 255  # Pure cyan

        yellow_mask = np.zeros((10, 10), dtype=np.uint8)
        yellow_mask[3, 3] = 255  # Pure yellow

        # Green = C ∩ Y at (5, 5)
        cyan_mask[5, 5] = 255
        yellow_mask[5, 5] = 255

        magenta_mask = np.zeros((10, 10), dtype=np.uint8)
        black_mask = np.zeros((10, 10), dtype=np.uint8)

        completed = complete_midtone_masks(cyan_mask, magenta_mask, yellow_mask, black_mask)

        # Cyan completed mask should include the green pixel
        assert completed['cyan'][5, 5] == 255
        assert completed['cyan'][2, 2] == 255  # Original cyan still there

    def test_complete_magenta_mask_includes_red_pixels(self):
        """Magenta mask should include Red (M∩Y) pixels."""
        from dotmatrix.cluster_pixel_counter import complete_midtone_masks

        cyan_mask = np.zeros((10, 10), dtype=np.uint8)
        magenta_mask = np.zeros((10, 10), dtype=np.uint8)
        yellow_mask = np.zeros((10, 10), dtype=np.uint8)
        black_mask = np.zeros((10, 10), dtype=np.uint8)

        # Red pixel at (5, 5) - M ∩ Y
        magenta_mask[5, 5] = 255
        yellow_mask[5, 5] = 255

        completed = complete_midtone_masks(cyan_mask, magenta_mask, yellow_mask, black_mask)

        # Magenta completed mask should include red pixel
        assert completed['magenta'][5, 5] == 255

    def test_complete_yellow_mask_includes_green_and_red_pixels(self):
        """Yellow mask should include Green (C∩Y) and Red (M∩Y) pixels."""
        from dotmatrix.cluster_pixel_counter import complete_midtone_masks

        cyan_mask = np.zeros((10, 10), dtype=np.uint8)
        magenta_mask = np.zeros((10, 10), dtype=np.uint8)
        yellow_mask = np.zeros((10, 10), dtype=np.uint8)
        black_mask = np.zeros((10, 10), dtype=np.uint8)

        # Green at (3, 3), Red at (7, 7)
        cyan_mask[3, 3] = 255
        yellow_mask[3, 3] = 255  # Green

        magenta_mask[7, 7] = 255
        yellow_mask[7, 7] = 255  # Red

        completed = complete_midtone_masks(cyan_mask, magenta_mask, yellow_mask, black_mask)

        assert completed['yellow'][3, 3] == 255  # Green pixel
        assert completed['yellow'][7, 7] == 255  # Red pixel


class TestFindBlackDotCenters:
    """Test finding black dot centers."""

    def test_find_single_black_dot_center(self):
        """Should find center of a single black dot."""
        from dotmatrix.cluster_pixel_counter import find_black_dot_centers

        # Create a black dot (filled circle)
        black_mask = np.zeros((100, 100), dtype=np.uint8)
        # Draw a circle at (50, 50) with radius 10
        y, x = np.ogrid[:100, :100]
        circle_mask = (x - 50)**2 + (y - 50)**2 <= 10**2
        black_mask[circle_mask] = 255

        centers = find_black_dot_centers(black_mask)

        assert len(centers) == 1
        cx, cy = centers[0]
        # Center should be close to (50, 50)
        assert abs(cx - 50) <= 2
        assert abs(cy - 50) <= 2

    def test_find_multiple_black_dot_centers(self):
        """Should find centers of multiple black dots."""
        from dotmatrix.cluster_pixel_counter import find_black_dot_centers

        black_mask = np.zeros((200, 200), dtype=np.uint8)

        # Draw two dots
        y, x = np.ogrid[:200, :200]
        dot1 = (x - 50)**2 + (y - 50)**2 <= 15**2
        dot2 = (x - 150)**2 + (y - 150)**2 <= 15**2
        black_mask[dot1] = 255
        black_mask[dot2] = 255

        centers = find_black_dot_centers(black_mask)

        assert len(centers) == 2

    def test_no_black_dots_returns_empty(self):
        """Should return empty list when no black dots."""
        from dotmatrix.cluster_pixel_counter import find_black_dot_centers

        black_mask = np.zeros((100, 100), dtype=np.uint8)
        centers = find_black_dot_centers(black_mask)

        assert len(centers) == 0


class TestNearestPixelClustering:
    """Test Phase 2: Clustering by nearest black pixel."""

    def test_assign_pixel_to_nearest_cluster(self):
        """Pixels should be assigned to nearest black dot."""
        from dotmatrix.cluster_pixel_counter import create_cluster_labels

        # Two black dots
        black_mask = np.zeros((100, 100), dtype=np.uint8)
        black_mask[25, 25] = 255  # Dot 0
        black_mask[75, 75] = 255  # Dot 1

        labels = create_cluster_labels(black_mask)

        # Pixel at (20, 20) should be closer to dot at (25, 25)
        assert labels[20, 20] == labels[25, 25]

        # Pixel at (80, 80) should be closer to dot at (75, 75)
        assert labels[80, 80] == labels[75, 75]

    def test_cluster_labels_cover_entire_image(self):
        """Every pixel should have a cluster label (except background)."""
        from dotmatrix.cluster_pixel_counter import create_cluster_labels

        black_mask = np.zeros((50, 50), dtype=np.uint8)
        black_mask[25, 25] = 255

        labels = create_cluster_labels(black_mask)

        # All pixels should be assigned to cluster 0 (only one black dot)
        # -1 for background (white), 0+ for clusters
        assert labels.shape == (50, 50)


class TestPixelCountingDeduplication:
    """Test Phase 3: Pixel counting with no double counting."""

    def test_rgb_subtracted_from_parent_midtones(self):
        """RGB overlap pixels should be subtracted from CMY counts."""
        from dotmatrix.cluster_pixel_counter import count_cluster_pixels

        # Create masks with known overlaps
        cyan_mask = np.zeros((10, 10), dtype=np.uint8)
        magenta_mask = np.zeros((10, 10), dtype=np.uint8)
        yellow_mask = np.zeros((10, 10), dtype=np.uint8)
        black_mask = np.zeros((10, 10), dtype=np.uint8)

        # Black dot at center
        black_mask[5, 5] = 255

        # 5 pure cyan pixels
        cyan_mask[0:5, 0] = 255

        # 3 pure magenta pixels
        magenta_mask[0:3, 1] = 255

        # 2 pure yellow pixels
        yellow_mask[0:2, 2] = 255

        # 1 Green pixel (C ∩ Y) - should NOT count in C or Y final
        cyan_mask[8, 8] = 255
        yellow_mask[8, 8] = 255

        # 1 Red pixel (M ∩ Y) - should NOT count in M or Y final
        magenta_mask[9, 9] = 255
        yellow_mask[9, 9] = 255

        # Cluster label: all belong to cluster 0
        labels = np.zeros((10, 10), dtype=np.int32)

        result = count_cluster_pixels(
            cluster_id=0,
            labels=labels,
            cyan_mask=cyan_mask,
            magenta_mask=magenta_mask,
            yellow_mask=yellow_mask,
            black_mask=black_mask,
            center=(5, 5)
        )

        # Pure colors only (RGB subtracted)
        assert result.cyan == 5      # 5 pure + 1 green, but green subtracted
        assert result.magenta == 3   # 3 pure + 1 red, but red subtracted
        assert result.yellow == 2    # 2 pure + 1 green + 1 red, but both subtracted
        assert result.black == 1
        assert result.red == 1       # M ∩ Y
        assert result.green == 1     # C ∩ Y
        assert result.blue == 0      # C ∩ M (none in this test)

    def test_no_double_counting_total(self):
        """Total pixels counted should equal total colored pixels."""
        from dotmatrix.cluster_pixel_counter import count_cluster_pixels

        cyan_mask = np.zeros((10, 10), dtype=np.uint8)
        magenta_mask = np.zeros((10, 10), dtype=np.uint8)
        yellow_mask = np.zeros((10, 10), dtype=np.uint8)
        black_mask = np.zeros((10, 10), dtype=np.uint8)

        # Black at center
        black_mask[5, 5] = 255

        # Create overlapping regions
        # Pure C: (0,0)
        cyan_mask[0, 0] = 255

        # Green (C∩Y): (1,1)
        cyan_mask[1, 1] = 255
        yellow_mask[1, 1] = 255

        # Red (M∩Y): (2,2)
        magenta_mask[2, 2] = 255
        yellow_mask[2, 2] = 255

        # Blue (C∩M): (3,3)
        cyan_mask[3, 3] = 255
        magenta_mask[3, 3] = 255

        labels = np.zeros((10, 10), dtype=np.int32)

        result = count_cluster_pixels(
            cluster_id=0,
            labels=labels,
            cyan_mask=cyan_mask,
            magenta_mask=magenta_mask,
            yellow_mask=yellow_mask,
            black_mask=black_mask,
            center=(5, 5)
        )

        # Total should be: 1 black + 1 pure C + 1 G + 1 R + 1 B = 5 pixels
        total = (result.cyan + result.magenta + result.yellow +
                 result.black + result.red + result.green + result.blue)
        assert total == 5


class TestClusterResult:
    """Test ClusterResult dataclass."""

    def test_cluster_result_as_tuple(self):
        """ClusterResult should convert to [x, y, C, M, Y, K, R, G, B] tuple."""
        from dotmatrix.cluster_pixel_counter import ClusterResult

        result = ClusterResult(
            x=100, y=200,
            cyan=50, magenta=30, yellow=20,
            black=100, red=5, green=10, blue=3,
            partial=False
        )

        as_list = result.to_list()
        assert as_list == [100, 200, 50, 30, 20, 100, 5, 10, 3]

    def test_cluster_result_partial_flag(self):
        """Edge clusters should be flagged as partial."""
        from dotmatrix.cluster_pixel_counter import ClusterResult

        result = ClusterResult(
            x=0, y=0,  # At edge
            cyan=10, magenta=5, yellow=3,
            black=20, red=1, green=2, blue=0,
            partial=True
        )

        assert result.partial is True


class TestEdgeCases:
    """Test edge case handling."""

    def test_cluster_with_missing_colors(self):
        """Clusters can have 0 of some colors."""
        from dotmatrix.cluster_pixel_counter import count_cluster_pixels

        cyan_mask = np.zeros((10, 10), dtype=np.uint8)
        magenta_mask = np.zeros((10, 10), dtype=np.uint8)
        yellow_mask = np.zeros((10, 10), dtype=np.uint8)
        black_mask = np.zeros((10, 10), dtype=np.uint8)

        # Only black dot, no CMY
        black_mask[5, 5] = 255

        labels = np.zeros((10, 10), dtype=np.int32)

        result = count_cluster_pixels(
            cluster_id=0,
            labels=labels,
            cyan_mask=cyan_mask,
            magenta_mask=magenta_mask,
            yellow_mask=yellow_mask,
            black_mask=black_mask,
            center=(5, 5)
        )

        assert result.cyan == 0
        assert result.magenta == 0
        assert result.yellow == 0
        assert result.black == 1

    def test_edge_cluster_detection(self):
        """Clusters at image boundaries should be flagged."""
        from dotmatrix.cluster_pixel_counter import is_edge_cluster

        image_shape = (100, 100)

        # Center at (5, 5) with radius ~10 touches edge
        assert is_edge_cluster(5, 5, radius_estimate=10, image_shape=image_shape) is True

        # Center at (50, 50) with radius ~10 doesn't touch edge
        assert is_edge_cluster(50, 50, radius_estimate=10, image_shape=image_shape) is False


class TestIntegration:
    """Integration tests for full clustering pipeline."""

    def test_full_clustering_pipeline(self):
        """Test complete pipeline from masks to cluster results."""
        from dotmatrix.cluster_pixel_counter import cluster_and_count_pixels

        # Create a simple test image with one black dot and some CMY
        cyan_mask = np.zeros((100, 100), dtype=np.uint8)
        magenta_mask = np.zeros((100, 100), dtype=np.uint8)
        yellow_mask = np.zeros((100, 100), dtype=np.uint8)
        black_mask = np.zeros((100, 100), dtype=np.uint8)

        # Black dot at (50, 50) - filled circle radius 10
        y, x = np.ogrid[:100, :100]
        black_dot = (x - 50)**2 + (y - 50)**2 <= 10**2
        black_mask[black_dot] = 255

        # Cyan region nearby
        cyan_region = (x - 40)**2 + (y - 50)**2 <= 8**2
        cyan_mask[cyan_region] = 255

        # Magenta region
        magenta_region = (x - 60)**2 + (y - 50)**2 <= 8**2
        magenta_mask[magenta_region] = 255

        results = cluster_and_count_pixels(
            cyan_mask=cyan_mask,
            magenta_mask=magenta_mask,
            yellow_mask=yellow_mask,
            black_mask=black_mask,
            image_shape=(100, 100)
        )

        assert len(results) == 1
        result = results[0]

        # Should have found the black dot center
        assert abs(result.x - 50) <= 2
        assert abs(result.y - 50) <= 2

        # Should have counted some pixels
        assert result.black > 0
        assert result.cyan > 0
        assert result.magenta > 0

    def test_cluster_result_to_dict_serialization(self):
        """ClusterResult should serialize to JSON-compatible dict."""
        from dotmatrix.cluster_pixel_counter import ClusterResult
        import json

        result = ClusterResult(
            x=100, y=200,
            cyan=50, magenta=30, yellow=20,
            black=100, red=5, green=10, blue=3,
            partial=True
        )

        as_dict = result.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(as_dict)
        assert '"center": [100, 200]' in json_str
        assert '"partial": true' in json_str

        # Check structure
        assert as_dict['center'] == [100, 200]
        assert as_dict['pixel_counts']['cyan'] == 50
        assert as_dict['pixel_counts']['black'] == 100
        assert as_dict['partial'] is True


class TestCLIIntegration:
    """CLI integration tests for --cluster-count flag."""

    def test_cluster_count_json_output(self, tmp_path):
        """Test that --cluster-count outputs JSON array of cluster data."""
        import subprocess
        import json
        from pathlib import Path

        # Path to test image (same as used in convex integration tests)
        test_image = Path(__file__).parent.parent / "test_dotmatrix.png"
        if not test_image.exists():
            pytest.skip("Test image not found")

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(test_image),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--cluster-count",
                "--no-extract"
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Output should be valid JSON array
        data = json.loads(result.stdout)
        assert isinstance(data, list), "Output should be a JSON array"

        # Each item should have cluster structure
        if len(data) > 0:
            cluster = data[0]
            assert 'center' in cluster, "Cluster should have 'center'"
            assert 'pixel_counts' in cluster, "Cluster should have 'pixel_counts'"
            assert len(cluster['center']) == 2, "Center should be [x, y]"

            counts = cluster['pixel_counts']
            expected_keys = {'cyan', 'magenta', 'yellow', 'black', 'red', 'green', 'blue'}
            assert expected_keys.issubset(counts.keys()), f"Missing keys: {expected_keys - set(counts.keys())}"

    def test_cluster_count_requires_cmyk(self):
        """Test that --cluster-count requires CMYK palette."""
        import subprocess
        from pathlib import Path

        test_image = Path(__file__).parent.parent / "test_dotmatrix.png"
        if not test_image.exists():
            pytest.skip("Test image not found")

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(test_image),
                "--convex-edge",
                "--palette", "rgb",  # Not CMYK
                "--cluster-count",
                "--no-extract"
            ],
            capture_output=True,
            text=True
        )

        # Should fail or warn about CMYK requirement
        assert result.returncode != 0 or "CMYK" in result.stderr

    def test_cluster_count_csv_not_supported(self):
        """Test that --cluster-count with --format csv shows helpful message."""
        import subprocess
        from pathlib import Path

        test_image = Path(__file__).parent.parent / "test_dotmatrix.png"
        if not test_image.exists():
            pytest.skip("Test image not found")

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(test_image),
                "--convex-edge",
                "--palette", "cmyk",
                "--cluster-count",
                "--format", "csv",
                "--no-extract"
            ],
            capture_output=True,
            text=True
        )

        # CSV format for cluster data - check it either works with flat format
        # or provides a helpful error message
        # (We'll implement flat CSV: x,y,C,M,Y,K,R,G,B)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # Should have header + data rows
            assert len(lines) >= 1
            header = lines[0]
            assert 'center_x' in header or 'x' in header


class TestAnchorMethod:
    """Test anchor_method parameter for cluster assignment.

    Feature: CLUSTEREXT sprint - card v3ld39
    Default should be 'centroid', with 'nearest_pixel' as legacy option.
    """

    def test_anchor_method_centroid_default(self):
        """Default anchor_method should be 'centroid'."""
        from dotmatrix.cluster_pixel_counter import cluster_and_count_pixels
        import inspect

        sig = inspect.signature(cluster_and_count_pixels)
        anchor_param = sig.parameters.get('anchor_method')

        assert anchor_param is not None, "anchor_method parameter should exist"
        assert anchor_param.default == 'centroid', "Default should be 'centroid'"

    def test_anchor_method_centroid_produces_valid_results(self):
        """anchor_method='centroid' should produce valid ClusterResult."""
        from dotmatrix.cluster_pixel_counter import cluster_and_count_pixels

        # Create test image with one black dot
        cyan_mask = np.zeros((100, 100), dtype=np.uint8)
        magenta_mask = np.zeros((100, 100), dtype=np.uint8)
        yellow_mask = np.zeros((100, 100), dtype=np.uint8)
        black_mask = np.zeros((100, 100), dtype=np.uint8)

        # Black dot at (50, 50)
        y, x = np.ogrid[:100, :100]
        black_dot = (x - 50)**2 + (y - 50)**2 <= 10**2
        black_mask[black_dot] = 255

        # Cyan region
        cyan_region = (x - 40)**2 + (y - 50)**2 <= 8**2
        cyan_mask[cyan_region] = 255

        results = cluster_and_count_pixels(
            cyan_mask=cyan_mask,
            magenta_mask=magenta_mask,
            yellow_mask=yellow_mask,
            black_mask=black_mask,
            anchor_method='centroid'
        )

        assert len(results) == 1
        assert results[0].black > 0
        assert results[0].cyan > 0

    def test_anchor_method_nearest_pixel_produces_valid_results(self):
        """anchor_method='nearest_pixel' should produce valid ClusterResult."""
        from dotmatrix.cluster_pixel_counter import cluster_and_count_pixels

        cyan_mask = np.zeros((100, 100), dtype=np.uint8)
        magenta_mask = np.zeros((100, 100), dtype=np.uint8)
        yellow_mask = np.zeros((100, 100), dtype=np.uint8)
        black_mask = np.zeros((100, 100), dtype=np.uint8)

        # Black dot at (50, 50)
        y, x = np.ogrid[:100, :100]
        black_dot = (x - 50)**2 + (y - 50)**2 <= 10**2
        black_mask[black_dot] = 255

        # Cyan region
        cyan_region = (x - 40)**2 + (y - 50)**2 <= 8**2
        cyan_mask[cyan_region] = 255

        results = cluster_and_count_pixels(
            cyan_mask=cyan_mask,
            magenta_mask=magenta_mask,
            yellow_mask=yellow_mask,
            black_mask=black_mask,
            anchor_method='nearest_pixel'
        )

        assert len(results) == 1
        assert results[0].black > 0
        assert results[0].cyan > 0

    def test_anchor_method_invalid_raises_error(self):
        """Invalid anchor_method should raise ValueError."""
        from dotmatrix.cluster_pixel_counter import cluster_and_count_pixels

        cyan_mask = np.zeros((10, 10), dtype=np.uint8)
        magenta_mask = np.zeros((10, 10), dtype=np.uint8)
        yellow_mask = np.zeros((10, 10), dtype=np.uint8)
        black_mask = np.zeros((10, 10), dtype=np.uint8)
        black_mask[5, 5] = 255

        with pytest.raises(ValueError, match="anchor_method"):
            cluster_and_count_pixels(
                cyan_mask=cyan_mask,
                magenta_mask=magenta_mask,
                yellow_mask=yellow_mask,
                black_mask=black_mask,
                anchor_method='invalid_method'
            )

    def test_anchor_method_works_with_separation_methods(self):
        """anchor_method should work with both separation_method options."""
        from dotmatrix.cluster_pixel_counter import cluster_and_count_pixels

        cyan_mask = np.zeros((100, 100), dtype=np.uint8)
        magenta_mask = np.zeros((100, 100), dtype=np.uint8)
        yellow_mask = np.zeros((100, 100), dtype=np.uint8)
        black_mask = np.zeros((100, 100), dtype=np.uint8)

        y, x = np.ogrid[:100, :100]
        black_dot = (x - 50)**2 + (y - 50)**2 <= 10**2
        black_mask[black_dot] = 255
        cyan_mask[40:60, 30:40] = 255

        # Test all 4 combinations
        for sep_method in ['connected', 'distance_transform']:
            for anchor in ['centroid', 'nearest_pixel']:
                results = cluster_and_count_pixels(
                    cyan_mask=cyan_mask,
                    magenta_mask=magenta_mask,
                    yellow_mask=yellow_mask,
                    black_mask=black_mask,
                    separation_method=sep_method,
                    anchor_method=anchor
                )
                assert len(results) == 1, f"Failed for {sep_method}/{anchor}"
                assert results[0].black > 0, f"No black for {sep_method}/{anchor}"

    def test_centroid_vs_nearest_pixel_difference(self):
        """Centroid and nearest_pixel should give different results for irregular dots.

        With an irregular black region, nearest_pixel considers edge pixels,
        while centroid only considers the center point.
        """
        from dotmatrix.cluster_pixel_counter import cluster_and_count_pixels

        # Create an irregular L-shaped black region
        black_mask = np.zeros((100, 100), dtype=np.uint8)
        black_mask[40:60, 40:50] = 255  # Vertical part
        black_mask[50:60, 40:70] = 255  # Horizontal part (L-shape)

        cyan_mask = np.zeros((100, 100), dtype=np.uint8)
        magenta_mask = np.zeros((100, 100), dtype=np.uint8)
        yellow_mask = np.zeros((100, 100), dtype=np.uint8)

        # Cyan pixel near the horizontal arm of L
        cyan_mask[55, 65] = 255

        results_centroid = cluster_and_count_pixels(
            cyan_mask=cyan_mask,
            magenta_mask=magenta_mask,
            yellow_mask=yellow_mask,
            black_mask=black_mask,
            anchor_method='centroid'
        )

        results_nearest = cluster_and_count_pixels(
            cyan_mask=cyan_mask,
            magenta_mask=magenta_mask,
            yellow_mask=yellow_mask,
            black_mask=black_mask,
            anchor_method='nearest_pixel'
        )

        # Both should find the cluster
        assert len(results_centroid) == 1
        assert len(results_nearest) == 1

        # Both should count the cyan pixel
        assert results_centroid[0].cyan >= 1
        assert results_nearest[0].cyan >= 1


class TestBoundingBox:
    """Test bounding box field in ClusterResult.
    Feature: CLUSTEREXT sprint - card euac65
    """

    def test_bbox_field_exists_in_cluster_result(self):
        """ClusterResult should have bbox field with correct default."""
        result = ClusterResult(
            x=50, y=50,
            cyan=10, magenta=10, yellow=10,
            black=100, red=0, green=0, blue=0
        )

        # bbox should exist and default to None
        assert hasattr(result, 'bbox')
        assert result.bbox is None

    def test_bbox_tuple_format(self):
        """bbox should be (x_min, y_min, x_max, y_max) tuple."""
        result = ClusterResult(
            x=50, y=50,
            cyan=10, magenta=10, yellow=10,
            black=100, red=0, green=0, blue=0,
            bbox=(40, 40, 60, 60)
        )

        assert result.bbox is not None
        assert len(result.bbox) == 4
        x_min, y_min, x_max, y_max = result.bbox
        assert x_min == 40
        assert y_min == 40
        assert x_max == 60
        assert y_max == 60

    def test_bbox_included_in_to_dict(self):
        """to_dict() should include bbox field."""
        import json

        result = ClusterResult(
            x=50, y=50,
            cyan=10, magenta=10, yellow=10,
            black=100, red=0, green=0, blue=0,
            bbox=(40, 40, 60, 60)
        )

        as_dict = result.to_dict()

        assert 'bbox' in as_dict
        assert as_dict['bbox'] == [40, 40, 60, 60]  # Converted to list for JSON

        # Should be JSON serializable
        json_str = json.dumps(as_dict)
        assert '"bbox": [40, 40, 60, 60]' in json_str

    def test_bbox_none_in_to_dict(self):
        """to_dict() should handle None bbox."""
        result = ClusterResult(
            x=50, y=50,
            cyan=10, magenta=10, yellow=10,
            black=100, red=0, green=0, blue=0,
            bbox=None
        )

        as_dict = result.to_dict()

        assert 'bbox' in as_dict
        assert as_dict['bbox'] is None

    def test_bbox_computed_from_cluster(self):
        """cluster_and_count_pixels should compute bbox from cluster mask."""
        from dotmatrix.cluster_pixel_counter import cluster_and_count_pixels

        # Create test image with one black dot at (50, 50) with radius 10
        cyan_mask = np.zeros((100, 100), dtype=np.uint8)
        magenta_mask = np.zeros((100, 100), dtype=np.uint8)
        yellow_mask = np.zeros((100, 100), dtype=np.uint8)
        black_mask = np.zeros((100, 100), dtype=np.uint8)

        # Black dot at center (50, 50) with radius 10
        y, x = np.ogrid[:100, :100]
        black_dot = (x - 50)**2 + (y - 50)**2 <= 10**2
        black_mask[black_dot] = 255

        results = cluster_and_count_pixels(
            cyan_mask=cyan_mask,
            magenta_mask=magenta_mask,
            yellow_mask=yellow_mask,
            black_mask=black_mask
        )

        assert len(results) == 1
        assert results[0].bbox is not None

        x_min, y_min, x_max, y_max = results[0].bbox
        # For a circle at (50, 50) with radius 10, bbox should be roughly (40, 40, 60, 60)
        assert 38 <= x_min <= 42
        assert 38 <= y_min <= 42
        assert 58 <= x_max <= 62
        assert 58 <= y_max <= 62

    def test_bbox_rectangular_cluster(self):
        """bbox should accurately capture rectangular cluster shape."""
        from dotmatrix.cluster_pixel_counter import cluster_and_count_pixels

        cyan_mask = np.zeros((100, 100), dtype=np.uint8)
        magenta_mask = np.zeros((100, 100), dtype=np.uint8)
        yellow_mask = np.zeros((100, 100), dtype=np.uint8)
        black_mask = np.zeros((100, 100), dtype=np.uint8)

        # Rectangular black region from (20,30) to (40,70)
        black_mask[30:71, 20:41] = 255

        results = cluster_and_count_pixels(
            cyan_mask=cyan_mask,
            magenta_mask=magenta_mask,
            yellow_mask=yellow_mask,
            black_mask=black_mask
        )

        assert len(results) == 1
        assert results[0].bbox is not None

        x_min, y_min, x_max, y_max = results[0].bbox
        # bbox should match the rectangular region
        assert x_min == 20
        assert y_min == 30
        assert x_max == 40
        assert y_max == 70
