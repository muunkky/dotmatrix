"""Tests for spatial indexing deduplication in convex_detector.py"""

import pytest
import numpy as np
import time
from dotmatrix.convex_detector import (
    DetectedCircle,
    deduplicate_circles_kdtree,
)


class TestDeduplicateCirclesKDTree:
    """Tests for KD-tree based deduplication."""

    def test_empty_input(self):
        """Empty list should return empty list."""
        result = deduplicate_circles_kdtree([], (255, 0, 0))
        assert result == []

    def test_single_circle(self):
        """Single circle should be returned as-is."""
        circles = [(100, 100, 50)]
        result = deduplicate_circles_kdtree(circles, (255, 0, 0))
        assert len(result) == 1
        assert result[0].x == 100
        assert result[0].y == 100
        assert result[0].radius == 50

    def test_no_duplicates(self):
        """Circles far apart should all be kept."""
        circles = [
            (100, 100, 50),
            (500, 100, 50),
            (100, 500, 50),
            (500, 500, 50),
        ]
        result = deduplicate_circles_kdtree(circles, (255, 0, 0), dedup_distance=20)
        assert len(result) == 4

    def test_all_duplicates(self):
        """Circles very close together should be deduplicated to one."""
        circles = [
            (100, 100, 50),
            (101, 101, 51),
            (102, 102, 52),
            (103, 103, 53),
        ]
        result = deduplicate_circles_kdtree(circles, (255, 0, 0), dedup_distance=20)
        # All are within 20px of each other, should keep only first
        assert len(result) == 1
        assert result[0].x == 100
        assert result[0].y == 100

    def test_partial_duplicates(self):
        """Mix of duplicates and unique circles."""
        circles = [
            (100, 100, 50),   # Keep
            (105, 105, 51),   # Duplicate of first (within 20px)
            (500, 500, 50),   # Keep (far away)
            (505, 505, 51),   # Duplicate of third
        ]
        result = deduplicate_circles_kdtree(circles, (255, 0, 0), dedup_distance=20)
        assert len(result) == 2

    def test_chain_of_duplicates(self):
        """Chain of circles where each is close to next but not all to first."""
        # 0 is close to 10, 10 is close to 20, but 0 is not close to 20 (distance 20 > 15)
        circles = [
            (100, 100, 50),   # Keep
            (110, 100, 50),   # Close to first (dist=10), marked as dup
            (120, 100, 50),   # Close to second (dist=10) but already marked, still checked vs first
            (200, 100, 50),   # Far from all (dist=80 from first), keep
        ]
        result = deduplicate_circles_kdtree(circles, (255, 0, 0), dedup_distance=15)
        # First marks second as dup (dist=10 < 15)
        # Third: dist from first = 20 > 15, not marked by first
        # Third becomes a keeper
        # Fourth is far, becomes a keeper
        assert len(result) == 3

    def test_returns_detected_circle_objects(self):
        """Result should be DetectedCircle objects with correct color."""
        circles = [(100, 100, 50)]
        color = (255, 128, 0)
        result = deduplicate_circles_kdtree(circles, color)

        assert len(result) == 1
        assert isinstance(result[0], DetectedCircle)
        assert result[0].color == color

    def test_custom_dedup_distance(self):
        """Dedup distance should be configurable."""
        circles = [
            (100, 100, 50),
            (130, 100, 50),  # 30px away
        ]
        # With distance=20, both should be kept
        result1 = deduplicate_circles_kdtree(circles, (255, 0, 0), dedup_distance=20)
        assert len(result1) == 2

        # With distance=40, second should be deduplicated
        result2 = deduplicate_circles_kdtree(circles, (255, 0, 0), dedup_distance=40)
        assert len(result2) == 1


class TestDeduplicationPerformance:
    """Performance benchmarks for deduplication."""

    def test_10k_circles_under_1_second(self):
        """10,000 circles should deduplicate in under 1 second."""
        np.random.seed(42)
        circles = [
            (np.random.randint(0, 5000), np.random.randint(0, 5000), np.random.randint(10, 50))
            for _ in range(10000)
        ]

        start = time.perf_counter()
        result = deduplicate_circles_kdtree(circles, (255, 0, 0))
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"10k circles took {elapsed:.2f}s (should be <1s)"
        assert len(result) > 0

    @pytest.mark.slow
    def test_50k_circles_under_10_seconds(self):
        """50,000 circles should deduplicate in under 10 seconds."""
        np.random.seed(42)
        circles = [
            (np.random.randint(0, 5000), np.random.randint(0, 5000), np.random.randint(10, 50))
            for _ in range(50000)
        ]

        start = time.perf_counter()
        result = deduplicate_circles_kdtree(circles, (255, 0, 0))
        elapsed = time.perf_counter() - start

        assert elapsed < 10.0, f"50k circles took {elapsed:.2f}s (should be <10s)"
        assert len(result) > 0
