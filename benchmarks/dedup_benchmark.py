#!/usr/bin/env python3
"""Benchmark deduplication approaches for scalability spike.

This benchmark compares O(n²) nested loop vs O(n log n) KD-tree deduplication.
"""

import time
import random
import numpy as np


def generate_test_circles(n: int, image_size: int = 5000, min_radius: int = 10, max_radius: int = 50):
    """Generate n random circles for testing."""
    circles = []
    for _ in range(n):
        x = random.randint(0, image_size)
        y = random.randint(0, image_size)
        r = random.randint(min_radius, max_radius)
        circles.append((x, y, r))
    return circles


def dedup_nested_loop(circles: list, dedup_distance: int = 20):
    """Original O(n²) deduplication."""
    final_circles = []
    used = [False] * len(circles)

    for i in range(len(circles)):
        if used[i]:
            continue

        x1, y1, r1 = circles[i]
        final_circles.append((x1, y1, r1))
        used[i] = True

        for j in range(i + 1, len(circles)):
            if used[j]:
                continue

            x2, y2, r2 = circles[j]
            dist = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)

            if dist < dedup_distance:
                used[j] = True

    return final_circles


def dedup_kdtree(circles: list, dedup_distance: int = 20):
    """O(n log n) KD-tree deduplication."""
    from scipy.spatial import KDTree

    if len(circles) == 0:
        return []

    # Build KD-tree from circle centers
    centers = np.array([(c[0], c[1]) for c in circles])
    tree = KDTree(centers)

    # Deduplicate
    used = set()
    final_circles = []

    for i, (x, y, r) in enumerate(circles):
        if i in used:
            continue
        final_circles.append((x, y, r))
        # Mark nearby circles as used
        nearby = tree.query_ball_point([x, y], dedup_distance)
        used.update(nearby)

    return final_circles


def benchmark(n_values: list):
    """Run benchmark for various circle counts."""
    print(f"{'N':>10} {'Nested (s)':>12} {'KDTree (s)':>12} {'Speedup':>10} {'Same Result':>12}")
    print("-" * 60)

    for n in n_values:
        circles = generate_test_circles(n)

        # Time nested loop
        start = time.perf_counter()
        result_nested = dedup_nested_loop(circles)
        time_nested = time.perf_counter() - start

        # Time KD-tree
        start = time.perf_counter()
        result_kdtree = dedup_kdtree(circles)
        time_kdtree = time.perf_counter() - start

        # Calculate speedup
        speedup = time_nested / time_kdtree if time_kdtree > 0 else float('inf')

        # Check results are same length (not identical due to processing order)
        same_count = len(result_nested) == len(result_kdtree)

        print(f"{n:>10} {time_nested:>12.4f} {time_kdtree:>12.4f} {speedup:>10.1f}x {str(same_count):>12}")


if __name__ == "__main__":
    print("=== Deduplication Benchmark ===\n")

    # Test various circle counts
    n_values = [100, 500, 1000, 2000, 5000, 10000, 20000, 50000]

    print("Testing with dedup_distance=20, image_size=5000\n")
    benchmark(n_values)

    print("\n=== Individual timing for target sizes ===\n")

    # More detailed test for key sizes
    for n in [10000, 50000]:
        circles = generate_test_circles(n)

        print(f"\n{n} circles:")

        start = time.perf_counter()
        result = dedup_kdtree(circles)
        elapsed = time.perf_counter() - start
        print(f"  KD-tree: {elapsed:.3f}s -> {len(result)} unique circles")
