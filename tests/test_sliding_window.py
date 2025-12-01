"""Tests for sliding window processing."""

import numpy as np
import pytest

from dotmatrix.sliding_window import process_sliding_window
from dotmatrix.cluster_pixel_counter import ClusterResult


class TestSlidingWindowSeams:
    """Tests for tile boundary handling in sliding window processing."""

    def test_overlap_cluster_petals_visible_in_core(self):
        """Verify that clusters in overlap contribute petals to adjacent core.

        The key bug: if a cluster's CENTER is in the overlap region (not core),
        it won't be rendered at all (before fix), even though its PETALS should
        extend into the core region and be visible.

        Test setup:
        - 300x100 image, window_size=150, overlap=50
        - Tile 1: 0-150, core: 0-125 (edge tile, core_x2 = 150 - 50//2 = 125)
        - Tile 2: 100-250, core: 125-200 (middle tile behavior)
        - Tile 3: 200-300, core: 200-300 (edge tile)

        Circle at x=135 (in Tile 1's overlap region 125-150)
        Its petals with radius 25 extend from x=110 to x=160
        The left petals (x=110-125) should be in Tile 1's core

        Before fix: Tile 1 won't render this (center at local 135 > core_x2=125)
                    Tile 2 will see it (local x=35, core 25-100), and will render
                    But Tile 2's core starts at global x=125

        Actually, with this setup Tile 2 WILL render it because local 35 is in core.
        The bug manifests when a cluster falls in the "gap" between tiles' cores.

        Let me use: Circle at x=130, y=50
        - In Tile 1 (0-150): local x=130, core 0-125. NOT in core.
        - In Tile 2 (100-250): local x=30, core 25-200. IS in core!

        So Tile 2 renders it and petals extending left into Tile 1's region
        are visible because we copy Tile 2's core starting at global 125.

        The ACTUAL bug is about the COPY region clipping flowers, not rendering.
        A flower in Tile 1's core at x=120 extends to x=145, but we only
        copy up to x=125. Pixels 125-145 from this flower are cut.

        Tile 2's core starts at 125, but the flower's center (120) is NOT in
        Tile 2's core (it's at local x=20, core starts at 25). So Tile 2
        won't render it either.

        Result: Flower at x=120 is rendered by Tile 1, but petals at x>125 cut.
        """
        import cv2

        # 300x100 image, larger to avoid auto-adjustment of parameters
        image = np.ones((100, 300, 3), dtype=np.uint8) * 255

        # Circle at (120, 50) with radius 25
        # Tile 1 core: 0-125, so center IS in core
        # Flower extends to x=145, but copy only goes to 125
        # Petals at 125-145 are cut
        cv2.circle(image, (120, 50), 25, (0, 0, 0), -1)

        # Use smaller max_radius to prevent overlap adjustment
        output, clusters, stats = process_sliding_window(
            image,
            window_size=150,
            overlap=50,
            min_radius=5,
            max_radius=25,  # overlap=50 >= 2*25, so no adjustment
            petal_distance=0.35,
            render_scale=1,
            color_mode='absolute',
            debug=False
        )

        # Check that flower petals exist beyond x=125
        # Before fix: This region is all white (cut off)
        # After fix: Petals from overlap clusters contribute here
        test_region = output[40:60, 130:145]
        non_white_pixels = np.sum(np.any(test_region < 255, axis=2))

        # After the fix, we should see some pixels here
        # This tests that overlap clusters are rendered, not just core clusters
        assert non_white_pixels > 0, (
            f"Expected rendered pixels at x=130-145 (flower petals beyond core), "
            f"but found {non_white_pixels} non-white pixels. "
            "Clusters in overlap are not being rendered."
        )

    def test_no_duplicate_circles_at_boundaries(self):
        """Verify that circles are rendered exactly once, not duplicated.

        A circle whose center is in Tile A's core should be rendered by
        Tile A only, not also by Tile B (even if it's in Tile B's overlap).
        """
        # Create image with circle at (125, 100) - in Tile 2's core
        image = np.ones((200, 200, 3), dtype=np.uint8) * 255

        import cv2
        cv2.circle(image, (125, 100), 20, (0, 0, 0), -1)

        output, clusters, stats = process_sliding_window(
            image,
            window_size=100,
            overlap=50,
            min_radius=10,
            max_radius=30,
            petal_distance=0.35,
            render_scale=1,
            color_mode='absolute',
            debug=False
        )

        # The stats should show this cluster was rendered exactly once
        total_rendered = stats['total_rendered']

        # With one circle, we should have exactly 1 cluster rendered
        # (not duplicated across tiles)
        assert total_rendered == 1, (
            f"Expected exactly 1 cluster rendered, but got {total_rendered}. "
            "Clusters may be duplicated at tile boundaries."
        )

    def test_overlap_region_clusters_contribute_petals(self):
        """Test that clusters in overlap region contribute petals to core.

        A cluster whose center is in the overlap region (not core) should
        still be rendered so its petals that extend into core are visible.
        """
        # Create image with circle at (90, 100) - in Tile 1's overlap region
        # but its petals extend into Tile 2's core
        # Tile 1: 0-100, core: 0-75
        # Circle at x=90 with radius 20 extends from x=70 to x=110
        # The part from x=75 to x=100 would be in Tile 1's overlap

        image = np.ones((200, 200, 3), dtype=np.uint8) * 255

        import cv2
        cv2.circle(image, (90, 100), 20, (0, 0, 0), -1)

        output, clusters, stats = process_sliding_window(
            image,
            window_size=100,
            overlap=50,
            min_radius=10,
            max_radius=30,
            petal_distance=0.35,
            render_scale=1,
            color_mode='absolute',
            debug=False
        )

        # Check that there's rendering in the core region around x=90
        # This circle's center is in overlap, but after fix it should render
        center_region = output[90:110, 85:95]
        non_white = np.sum(np.any(center_region < 255, axis=2))

        assert non_white > 0, (
            "Cluster in overlap region was not rendered. "
            "The fix should render all tile_clusters, not just core_clusters."
        )


class TestSlidingWindowStats:
    """Tests for sliding window statistics."""

    def test_stats_track_clusters_correctly(self):
        """Verify stats accurately track detected and rendered clusters."""
        # Create image with 4 black circles in different positions
        image = np.ones((200, 200, 3), dtype=np.uint8) * 255

        import cv2
        # Spread circles across image
        cv2.circle(image, (50, 50), 15, (0, 0, 0), -1)
        cv2.circle(image, (150, 50), 15, (0, 0, 0), -1)
        cv2.circle(image, (50, 150), 15, (0, 0, 0), -1)
        cv2.circle(image, (150, 150), 15, (0, 0, 0), -1)

        output, clusters, stats = process_sliding_window(
            image,
            window_size=100,
            overlap=50,
            min_radius=10,
            max_radius=30,
            petal_distance=0.35,
            render_scale=1,
            color_mode='absolute',
            debug=False
        )

        # Should have reasonable number of tiles
        assert stats['total_tiles'] >= 4, "Expected at least 4 tiles for 200x200 image"

        # Total clusters should match what we put in
        # (may detect more due to overlap, but should be deduplicated)
        assert stats['total_clusters'] >= 4, "Expected at least 4 clusters detected"

        # Rendered count should be >= detected unique circles
        assert stats['total_rendered'] >= 4, "Expected at least 4 clusters rendered"
