"""Tests for GPU acceleration functions in gpu.py."""

import numpy as np
import pytest
from dotmatrix.gpu import (
    is_gpu_available,
    get_gpu_info,
)


class TestGPUNMSCenters:
    """Test GPU-accelerated Non-Maximum Suppression."""

    def test_gpu_nms_centers_basic(self):
        """Test basic NMS with well-separated centers."""
        from dotmatrix.gpu import gpu_nms_centers

        # Create centers that are well separated (distance > min_distance)
        centers = np.array([
            [10, 10],
            [50, 50],
            [100, 100],
        ], dtype=np.float64)
        scores = np.array([1.0, 2.0, 3.0])  # Sorted descending: 2, 1, 0

        result = gpu_nms_centers(centers, scores, min_distance=20.0)

        # All should be kept since they're far apart
        assert len(result) == 3

    def test_gpu_nms_centers_suppression(self):
        """Test that nearby centers are suppressed."""
        from dotmatrix.gpu import gpu_nms_centers

        # Two centers very close together
        centers = np.array([
            [10, 10],
            [12, 12],  # Very close to first
            [100, 100],  # Far from others
        ], dtype=np.float64)
        scores = np.array([3.0, 1.0, 2.0])  # First has highest score

        result = gpu_nms_centers(centers, scores, min_distance=10.0)

        # First and third should be kept, second suppressed
        assert len(result) == 2
        # First (highest score) should be in result
        assert any(np.allclose(r, [10, 10]) for r in result)
        # Third (far from first) should be in result
        assert any(np.allclose(r, [100, 100]) for r in result)

    def test_gpu_nms_centers_empty(self):
        """Test with empty input."""
        from dotmatrix.gpu import gpu_nms_centers

        centers = np.array([]).reshape(0, 2)
        scores = np.array([])

        result = gpu_nms_centers(centers, scores, min_distance=10.0)

        assert len(result) == 0

    def test_gpu_nms_centers_single(self):
        """Test with single center."""
        from dotmatrix.gpu import gpu_nms_centers

        centers = np.array([[50, 50]], dtype=np.float64)
        scores = np.array([1.0])

        result = gpu_nms_centers(centers, scores, min_distance=10.0)

        assert len(result) == 1
        assert np.allclose(result[0], [50, 50])

    def test_gpu_nms_centers_matches_cpu(self):
        """Test that GPU NMS produces identical results to CPU version."""
        from dotmatrix.gpu import gpu_nms_centers, _cpu_nms_centers

        # Generate random centers
        np.random.seed(42)
        n_centers = 500
        centers = np.random.rand(n_centers, 2) * 1000
        scores = np.random.rand(n_centers)
        min_distance = 30.0

        cpu_result = _cpu_nms_centers(centers, scores, min_distance)
        gpu_result = gpu_nms_centers(centers, scores, min_distance, force_gpu=False)

        # Should have same number of results
        assert len(cpu_result) == len(gpu_result), \
            f"CPU returned {len(cpu_result)}, GPU returned {len(gpu_result)}"

        # Results should match (order may differ, compare with tolerance for float precision)
        # Sort both by x then y for deterministic comparison
        cpu_sorted = sorted(cpu_result.tolist(), key=lambda c: (round(c[0], 2), round(c[1], 2)))
        gpu_sorted = sorted(gpu_result.tolist(), key=lambda c: (round(c[0], 2), round(c[1], 2)))

        for i, (cpu_c, gpu_c) in enumerate(zip(cpu_sorted, gpu_sorted)):
            assert abs(cpu_c[0] - gpu_c[0]) < 0.1, f"Mismatch at {i}: CPU={cpu_c}, GPU={gpu_c}"
            assert abs(cpu_c[1] - gpu_c[1]) < 0.1, f"Mismatch at {i}: CPU={cpu_c}, GPU={gpu_c}"

    @pytest.mark.skipif(not is_gpu_available(), reason="GPU not available")
    def test_gpu_nms_centers_gpu_execution(self):
        """Test that GPU path executes correctly when available."""
        from dotmatrix.gpu import gpu_nms_centers

        np.random.seed(42)
        centers = np.random.rand(1000, 2) * 1000
        scores = np.random.rand(1000)

        # Force GPU execution
        result = gpu_nms_centers(centers, scores, min_distance=20.0, force_gpu=True)

        assert len(result) > 0
        assert result.shape[1] == 2

    @pytest.mark.skipif(not is_gpu_available(), reason="GPU not available")
    def test_gpu_nms_performance(self):
        """Benchmark GPU vs CPU performance."""
        import time
        from dotmatrix.gpu import gpu_nms_centers, _cpu_nms_centers

        np.random.seed(42)
        n_centers = 5000
        centers = np.random.rand(n_centers, 2) * 2000
        scores = np.random.rand(n_centers)
        min_distance = 15.0

        # CPU timing
        start = time.perf_counter()
        cpu_result = _cpu_nms_centers(centers, scores, min_distance)
        cpu_time = time.perf_counter() - start

        # GPU timing (with warmup)
        _ = gpu_nms_centers(centers[:100], scores[:100], min_distance, force_gpu=True)

        start = time.perf_counter()
        gpu_result = gpu_nms_centers(centers, scores, min_distance, force_gpu=True)
        gpu_time = time.perf_counter() - start

        speedup = cpu_time / gpu_time if gpu_time > 0 else float('inf')
        print(f"\nNMS Performance: CPU={cpu_time:.3f}s, GPU={gpu_time:.3f}s, Speedup={speedup:.1f}x")

        # Verify results match
        assert len(cpu_result) == len(gpu_result)

        # Expect at least 2x speedup for 5000 centers
        # (Being conservative here - actual speedup should be much higher)
        assert speedup > 2.0, f"Expected >2x speedup, got {speedup:.1f}x"


class TestGPUNearestCenterLabels:
    """Test GPU-accelerated nearest center labeling."""

    def test_gpu_nearest_center_labels_basic(self):
        """Test basic nearest center assignment."""
        from dotmatrix.gpu import gpu_nearest_center_labels

        # 3 centers in a row
        centers = np.array([
            [0, 0],
            [100, 0],
            [200, 0],
        ], dtype=np.float64)

        # Pixels near each center
        pixels = np.array([
            [5, 0],    # Near center 0
            [95, 0],   # Near center 1
            [190, 0],  # Near center 2
        ], dtype=np.float64)

        labels = gpu_nearest_center_labels(pixels, centers)

        assert labels[0] == 0
        assert labels[1] == 1
        assert labels[2] == 2

    def test_gpu_nearest_center_labels_matches_kdtree(self):
        """Test that GPU results match scipy KDTree."""
        from dotmatrix.gpu import gpu_nearest_center_labels
        from scipy.spatial import KDTree

        np.random.seed(42)
        centers = np.random.rand(100, 2) * 500
        pixels = np.random.rand(10000, 2) * 500

        # KDTree reference
        tree = KDTree(centers)
        _, kdtree_labels = tree.query(pixels)

        # GPU implementation
        gpu_labels = gpu_nearest_center_labels(pixels, centers)

        # Should match exactly
        np.testing.assert_array_equal(gpu_labels, kdtree_labels)

    @pytest.mark.skipif(not is_gpu_available(), reason="GPU not available")
    def test_gpu_nearest_center_performance(self):
        """Benchmark GPU vs KDTree performance."""
        import time
        from dotmatrix.gpu import gpu_nearest_center_labels
        from scipy.spatial import KDTree

        np.random.seed(42)
        centers = np.random.rand(500, 2) * 1000
        pixels = np.random.rand(1_000_000, 2) * 1000

        # KDTree timing
        start = time.perf_counter()
        tree = KDTree(centers)
        _, kdtree_labels = tree.query(pixels)
        kdtree_time = time.perf_counter() - start

        # GPU timing (with warmup)
        _ = gpu_nearest_center_labels(pixels[:1000], centers, force_gpu=True)

        start = time.perf_counter()
        gpu_labels = gpu_nearest_center_labels(pixels, centers, force_gpu=True)
        gpu_time = time.perf_counter() - start

        speedup = kdtree_time / gpu_time if gpu_time > 0 else float('inf')
        print(f"\nNearest Center Performance: KDTree={kdtree_time:.3f}s, GPU={gpu_time:.3f}s, Speedup={speedup:.1f}x")

        # Verify results mostly match (float32 vs float64 precision can cause
        # different tie-breaking for equidistant points, allowing tiny discrepancy)
        match_rate = np.mean(gpu_labels == kdtree_labels.astype(np.int32))
        assert match_rate > 0.9999, f"Match rate {match_rate:.6f} too low"


class TestGPUClusterColorCounting:
    """Test GPU-accelerated cluster color counting."""

    def test_gpu_count_cluster_colors_basic(self):
        """Test basic color counting per cluster."""
        from dotmatrix.gpu import gpu_count_cluster_colors

        # Simple 4x4 image with 2 clusters
        labels = np.array([
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 1],
        ], dtype=np.int32)

        # Color mask: first cluster all cyan, second cluster all magenta
        cyan_mask = np.array([
            [1, 1, 0, 0],
            [1, 1, 0, 0],
            [1, 1, 0, 0],
            [1, 1, 0, 0],
        ], dtype=bool)

        magenta_mask = np.array([
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 1],
        ], dtype=bool)

        color_masks = {'C': cyan_mask, 'M': magenta_mask}

        counts = gpu_count_cluster_colors(labels, color_masks, n_clusters=2)

        assert counts['C'][0] == 8  # Cluster 0 has 8 cyan pixels
        assert counts['C'][1] == 0  # Cluster 1 has 0 cyan pixels
        assert counts['M'][0] == 0  # Cluster 0 has 0 magenta pixels
        assert counts['M'][1] == 8  # Cluster 1 has 8 magenta pixels

    def test_gpu_count_cluster_colors_matches_cpu(self):
        """Test that GPU results match CPU bincount."""
        from dotmatrix.gpu import gpu_count_cluster_colors, _cpu_count_cluster_colors

        np.random.seed(42)
        h, w = 100, 100
        n_clusters = 50

        labels = np.random.randint(0, n_clusters, size=(h, w), dtype=np.int32)
        color_masks = {
            'C': np.random.rand(h, w) > 0.5,
            'M': np.random.rand(h, w) > 0.5,
            'Y': np.random.rand(h, w) > 0.5,
            'K': np.random.rand(h, w) > 0.5,
        }

        cpu_counts = _cpu_count_cluster_colors(labels, color_masks, n_clusters)
        gpu_counts = gpu_count_cluster_colors(labels, color_masks, n_clusters)

        for color in color_masks:
            np.testing.assert_array_equal(cpu_counts[color], gpu_counts[color])

    @pytest.mark.skipif(not is_gpu_available(), reason="GPU not available")
    def test_gpu_count_cluster_colors_performance(self):
        """Benchmark GPU vs CPU color counting."""
        import time
        from dotmatrix.gpu import gpu_count_cluster_colors, _cpu_count_cluster_colors

        np.random.seed(42)
        h, w = 2000, 2000
        n_clusters = 1000

        labels = np.random.randint(0, n_clusters, size=(h, w), dtype=np.int32)
        color_masks = {
            'C': np.random.rand(h, w) > 0.5,
            'M': np.random.rand(h, w) > 0.5,
            'Y': np.random.rand(h, w) > 0.5,
            'K': np.random.rand(h, w) > 0.5,
        }

        # CPU timing
        start = time.perf_counter()
        cpu_counts = _cpu_count_cluster_colors(labels, color_masks, n_clusters)
        cpu_time = time.perf_counter() - start

        # GPU timing (with warmup)
        _ = gpu_count_cluster_colors(labels[:100, :100],
                                     {k: v[:100, :100] for k, v in color_masks.items()},
                                     n_clusters, force_gpu=True)

        start = time.perf_counter()
        gpu_counts = gpu_count_cluster_colors(labels, color_masks, n_clusters, force_gpu=True)
        gpu_time = time.perf_counter() - start

        speedup = cpu_time / gpu_time if gpu_time > 0 else float('inf')
        print(f"\nColor Counting Performance: CPU={cpu_time:.3f}s, GPU={gpu_time:.3f}s, Speedup={speedup:.1f}x")

        # Verify results match
        for color in color_masks:
            np.testing.assert_array_equal(cpu_counts[color], gpu_counts[color])
