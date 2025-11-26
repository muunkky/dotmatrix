"""Tests for chunked/tiled processing in convex_detector.py"""

import pytest
import numpy as np
from dotmatrix.convex_detector import (
    DetectedCircle,
    generate_tiles,
    calculate_chunk_size,
    process_chunked,
)


class TestGenerateTiles:
    """Tests for tile generation."""

    def test_single_tile_small_image(self):
        """Small image should produce single tile."""
        tiles = generate_tiles((100, 100), chunk_size=200, overlap=20)
        assert len(tiles) == 1
        assert tiles[0] == (0, 0, 100, 100)

    def test_multiple_tiles_large_image(self):
        """Large image should produce multiple tiles."""
        tiles = generate_tiles((1000, 1000), chunk_size=500, overlap=50)
        # With 500px chunks and 50px overlap, step is 450px
        # 1000 / 450 = ~2.2, so 2x2 grid = 4 tiles minimum, but edge cases
        assert len(tiles) >= 4

    def test_tiles_cover_entire_image(self):
        """All pixels should be covered by at least one tile."""
        h, w = 1000, 800
        tiles = generate_tiles((h, w), chunk_size=400, overlap=50)

        # Create coverage mask
        coverage = np.zeros((h, w), dtype=int)
        for x1, y1, x2, y2 in tiles:
            coverage[y1:y2, x1:x2] += 1

        # Every pixel should be covered at least once
        assert coverage.min() >= 1

    def test_tiles_have_overlap(self):
        """Adjacent tiles should overlap."""
        tiles = generate_tiles((1000, 1000), chunk_size=500, overlap=50)

        # Check that some pixels are in multiple tiles
        coverage = np.zeros((1000, 1000), dtype=int)
        for x1, y1, x2, y2 in tiles:
            coverage[y1:y2, x1:x2] += 1

        # Some pixels should be in 2+ tiles (the overlap regions)
        assert coverage.max() >= 2

    def test_edge_tiles_bounded_by_image(self):
        """Tile coordinates should not exceed image dimensions."""
        h, w = 750, 500
        tiles = generate_tiles((h, w), chunk_size=400, overlap=50)

        for x1, y1, x2, y2 in tiles:
            assert x1 >= 0
            assert y1 >= 0
            assert x2 <= w
            assert y2 <= h


class TestCalculateChunkSize:
    """Tests for automatic chunk size calculation."""

    def test_uses_max_radius_multiplier(self):
        """Chunk size should be proportional to max_radius."""
        # For small max_radius with large image, should use minimum size
        size1 = calculate_chunk_size((5000, 5000), max_radius=20)
        assert size1 >= 2000  # Minimum chunk size

        # For large max_radius, should scale up
        size2 = calculate_chunk_size((5000, 5000), max_radius=100)
        assert size2 >= size1

    def test_capped_by_image_dimensions(self):
        """Chunk size should not exceed image dimensions."""
        size = calculate_chunk_size((500, 600), max_radius=100)
        assert size <= 500  # Should be capped by smaller dimension

    def test_returns_integer(self):
        """Chunk size should be an integer."""
        size = calculate_chunk_size((1000, 1000), max_radius=50)
        assert isinstance(size, int)


class TestProcessChunked:
    """Tests for chunked processing pipeline."""

    def test_small_image_single_chunk(self):
        """Small image should work with single chunk."""
        # Create test image with a circle
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        img[:] = (255, 255, 255)  # White background

        # Draw a simple black circle
        import cv2
        cv2.circle(img, (100, 100), 30, (0, 0, 0), -1)

        from dotmatrix.convex_detector import PALETTES

        circles = process_chunked(
            img,
            palette=PALETTES['cmyk'],
            chunk_size=500,  # Larger than image
            max_radius=50,
            min_radius=20
        )

        # Should find the circle
        assert len(circles) >= 1

    def test_coordinates_offset_to_global(self):
        """Circle coordinates should be in global image space."""
        # Create image with circles in different quadrants
        img = np.zeros((1000, 1000, 3), dtype=np.uint8)
        img[:] = (255, 255, 255)

        import cv2
        # Circle in top-left
        cv2.circle(img, (100, 100), 30, (0, 0, 0), -1)
        # Circle in bottom-right
        cv2.circle(img, (900, 900), 30, (0, 0, 0), -1)

        from dotmatrix.convex_detector import PALETTES

        circles = process_chunked(
            img,
            palette=PALETTES['cmyk'],
            chunk_size=500,
            max_radius=50,
            min_radius=20
        )

        # Should find circles in both locations
        centers = [(c.x, c.y) for c in circles]

        # Check we have circles near both expected positions
        has_top_left = any(
            abs(x - 100) < 50 and abs(y - 100) < 50
            for x, y in centers
        )
        has_bottom_right = any(
            abs(x - 900) < 50 and abs(y - 900) < 50
            for x, y in centers
        )

        assert has_top_left, f"Missing top-left circle, found: {centers}"
        assert has_bottom_right, f"Missing bottom-right circle, found: {centers}"

    def test_boundary_circles_deduplicated(self):
        """Circles on tile boundaries should not be duplicated."""
        # Create image with circle right at tile boundary
        img = np.zeros((1000, 1000, 3), dtype=np.uint8)
        img[:] = (255, 255, 255)

        import cv2
        # Circle at center (will be on boundary with 500px chunks)
        cv2.circle(img, (500, 500), 30, (0, 0, 0), -1)

        from dotmatrix.convex_detector import PALETTES

        circles = process_chunked(
            img,
            palette=PALETTES['cmyk'],
            chunk_size=500,
            max_radius=50,
            min_radius=20
        )

        # Should find exactly 1 circle (not duplicated)
        center_circles = [
            c for c in circles
            if abs(c.x - 500) < 50 and abs(c.y - 500) < 50
        ]
        assert len(center_circles) == 1, f"Found {len(center_circles)} circles at center"


class TestChunkedPerformance:
    """Performance tests for chunked processing."""

    @pytest.mark.slow
    def test_large_synthetic_image(self):
        """Large synthetic image should process without timeout."""
        # Create 4000x4000 image (16 MP)
        img = np.zeros((4000, 4000, 3), dtype=np.uint8)
        img[:] = (255, 255, 255)

        import cv2
        # Add some circles
        for i in range(10):
            for j in range(10):
                x, y = 200 + i * 400, 200 + j * 400
                cv2.circle(img, (x, y), 30, (0, 0, 0), -1)

        from dotmatrix.convex_detector import PALETTES
        import time

        start = time.perf_counter()
        circles = process_chunked(
            img,
            palette=PALETTES['cmyk'],
            chunk_size=1000,
            max_radius=50,
            min_radius=20
        )
        elapsed = time.perf_counter() - start

        # Should complete in reasonable time
        assert elapsed < 60, f"16 MP image took {elapsed:.1f}s (should be <60s)"
        # Should find most circles
        assert len(circles) >= 50, f"Only found {len(circles)} circles"
