"""Tests for CMYK cluster pixel counting.

TDD tests for the cluster_pixel_counter module that implements:
- Midtone completion (Phase 1)
- Nearest pixel clustering (Phase 2)
- Pixel counting with deduplication (Phase 3)
"""

import numpy as np
import pytest


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
