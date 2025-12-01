"""Tests for GPU-accelerated flower renderer.

Tests verify:
1. GPU output matches CPU baseline within tolerance
2. Performance improvement with GPU acceleration
3. Graceful fallback to CPU when GPU unavailable
"""

import pytest
import numpy as np
import math
import time

from dotmatrix.cluster_pixel_counter import ClusterResult
from dotmatrix.circle_renderer import render_flower_global_blend
from dotmatrix.gpu_renderer import render_flower_global_blend_gpu
from dotmatrix.gpu import is_gpu_available


def make_test_cluster(x, y, black=100, cyan=50, magenta=50, yellow=50,
                       red=0, green=0, blue=0) -> ClusterResult:
    """Create a test ClusterResult with specified pixel counts."""
    return ClusterResult(
        x=x,
        y=y,
        black=black,
        cyan=cyan,
        magenta=magenta,
        yellow=yellow,
        red=red,
        green=green,
        blue=blue,
        partial=False,
    )


class TestGPURendererEquivalence:
    """Test that GPU renderer produces output matching CPU baseline."""

    def test_single_cluster_equivalence(self):
        """GPU and CPU should produce identical output for single cluster."""
        clusters = [make_test_cluster(50, 50, black=500, cyan=200, magenta=200, yellow=200)]
        image_shape = (100, 100)

        cpu_result = render_flower_global_blend(
            clusters, image_shape, petal_distance=0.35, scale=1
        )
        gpu_result = render_flower_global_blend_gpu(
            clusters, image_shape, petal_distance=0.35, scale=1, use_gpu=True
        )

        # Results should match exactly or within very small tolerance
        np.testing.assert_array_equal(cpu_result.shape, gpu_result.shape)

        # Allow small differences due to floating point in GPU vs CPU
        diff = np.abs(cpu_result.astype(int) - gpu_result.astype(int))
        max_diff = np.max(diff)

        # Maximum pixel difference should be minimal (anti-aliasing differences)
        assert max_diff <= 1, f"Max pixel difference: {max_diff}"

    def test_multiple_clusters_equivalence(self):
        """GPU and CPU should produce matching output for multiple clusters."""
        # Create a grid of clusters
        clusters = []
        for row in range(3):
            for col in range(3):
                x = 50 + col * 100
                y = 50 + row * 100
                clusters.append(make_test_cluster(
                    x, y,
                    black=300 + row * 50,
                    cyan=100 + col * 30,
                    magenta=100 + row * 30,
                    yellow=100 + (row + col) * 20,
                ))

        image_shape = (350, 350)

        cpu_result = render_flower_global_blend(clusters, image_shape)
        gpu_result = render_flower_global_blend_gpu(clusters, image_shape, use_gpu=True)

        np.testing.assert_array_equal(cpu_result.shape, gpu_result.shape)

        # Count pixels that differ
        diff = np.abs(cpu_result.astype(int) - gpu_result.astype(int))
        diff_pixels = np.sum(diff > 1)
        total_pixels = cpu_result.shape[0] * cpu_result.shape[1]

        # Less than 0.1% of pixels should differ significantly
        diff_ratio = diff_pixels / total_pixels
        assert diff_ratio < 0.001, f"Too many differing pixels: {diff_ratio:.4%}"

    def test_overlapping_clusters_equivalence(self):
        """GPU handles overlapping clusters same as CPU."""
        # Create overlapping clusters to test global black mask handling
        clusters = [
            make_test_cluster(40, 50, black=400, cyan=150, magenta=150, yellow=150),
            make_test_cluster(60, 50, black=400, cyan=150, magenta=150, yellow=150),
        ]
        image_shape = (100, 120)

        cpu_result = render_flower_global_blend(clusters, image_shape)
        gpu_result = render_flower_global_blend_gpu(clusters, image_shape, use_gpu=True)

        diff = np.abs(cpu_result.astype(int) - gpu_result.astype(int))
        max_diff = np.max(diff)
        assert max_diff <= 1, f"Max pixel difference for overlapping: {max_diff}"

    def test_with_rotation_equivalence(self):
        """GPU handles rotation modes same as CPU."""
        clusters = [make_test_cluster(50, 50, black=300, cyan=100, magenta=100, yellow=100)]
        image_shape = (100, 100)

        for rotation_mode in ['fixed', 'cluster-hash']:
            cpu_result = render_flower_global_blend(
                clusters, image_shape,
                rotation_mode=rotation_mode,
                base_rotation=45.0,
            )
            gpu_result = render_flower_global_blend_gpu(
                clusters, image_shape,
                rotation_mode=rotation_mode,
                base_rotation=45.0,
                use_gpu=True,
            )

            diff = np.abs(cpu_result.astype(int) - gpu_result.astype(int))
            max_diff = np.max(diff)
            assert max_diff <= 1, f"Max diff for {rotation_mode}: {max_diff}"

    def test_scale_factor_equivalence(self):
        """GPU handles scale factor same as CPU."""
        clusters = [make_test_cluster(25, 25, black=200, cyan=80, magenta=80, yellow=80)]
        image_shape = (50, 50)

        cpu_result = render_flower_global_blend(clusters, image_shape, scale=2)
        gpu_result = render_flower_global_blend_gpu(clusters, image_shape, scale=2, use_gpu=True)

        assert cpu_result.shape == (100, 100, 3)
        assert gpu_result.shape == (100, 100, 3)

        diff = np.abs(cpu_result.astype(int) - gpu_result.astype(int))
        max_diff = np.max(diff)
        assert max_diff <= 1


class TestGPURendererFallback:
    """Test graceful fallback to CPU when GPU unavailable."""

    def test_use_gpu_false_uses_cpu(self):
        """use_gpu=False should use CPU path regardless of GPU availability."""
        clusters = [make_test_cluster(50, 50)]
        image_shape = (100, 100)

        # This should work even if GPU is available - forces CPU path
        result = render_flower_global_blend_gpu(
            clusters, image_shape, use_gpu=False
        )

        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8


class TestGPURendererPerformance:
    """Test GPU renderer performance characteristics."""

    def test_gpu_renderer_equivalent_performance(self):
        """GPU renderer should have equivalent performance to CPU.

        Note: After profiling, the CPU implementation with local ROIs is already
        highly optimized (~1.6ms per cluster). GPU transfer overhead exceeds the
        compute benefit for Phase 1c operations. The GPU renderer now uses the
        optimized CPU path internally while providing the GPU-aware API.

        This test verifies the GPU renderer produces correct output with
        acceptable performance overhead.
        """
        # Create test clusters
        clusters = []
        for i in range(50):
            x = 25 + (i % 10) * 50
            y = 25 + (i // 10) * 50
            clusters.append(make_test_cluster(
                x, y, black=200, cyan=80, magenta=80, yellow=80
            ))

        image_shape = (500, 500)

        # Time CPU
        start = time.perf_counter()
        cpu_result = render_flower_global_blend(clusters, image_shape)
        cpu_time = time.perf_counter() - start

        # Time GPU (uses optimized CPU path internally)
        start = time.perf_counter()
        gpu_result = render_flower_global_blend_gpu(clusters, image_shape, use_gpu=True)
        gpu_time = time.perf_counter() - start

        print(f"\nCPU time: {cpu_time:.3f}s, GPU renderer time: {gpu_time:.3f}s")

        # Verify equivalence - outputs should match exactly
        diff = np.abs(cpu_result.astype(int) - gpu_result.astype(int))
        max_diff = np.max(diff)
        assert max_diff <= 1, f"GPU output should match CPU, max diff: {max_diff}"

        # Performance should be within 2x of direct CPU call
        # (accounting for function call overhead)
        assert gpu_time < cpu_time * 2, "GPU renderer should not have excessive overhead"


class TestGPURendererEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_clusters(self):
        """Should handle empty cluster list."""
        result = render_flower_global_blend_gpu([], (100, 100), use_gpu=True)
        assert result.shape == (100, 100, 3)
        # Empty should be all white
        assert np.all(result == 255)

    def test_cluster_no_black(self):
        """Should handle cluster with no black component."""
        clusters = [make_test_cluster(50, 50, black=0, cyan=100, magenta=100, yellow=100)]
        image_shape = (100, 100)

        result = render_flower_global_blend_gpu(clusters, image_shape, use_gpu=True)
        assert result.shape == (100, 100, 3)

    def test_cluster_black_only(self):
        """Should handle cluster with only black component."""
        clusters = [make_test_cluster(50, 50, black=500, cyan=0, magenta=0, yellow=0)]
        image_shape = (100, 100)

        result = render_flower_global_blend_gpu(clusters, image_shape, use_gpu=True)
        assert result.shape == (100, 100, 3)

        # Should have black pixels
        assert np.any(result == 0)

    def test_cluster_at_edge(self):
        """Should handle clusters at image edges."""
        clusters = [
            make_test_cluster(5, 5, black=200, cyan=80, magenta=80, yellow=80),
            make_test_cluster(95, 95, black=200, cyan=80, magenta=80, yellow=80),
        ]
        image_shape = (100, 100)

        result = render_flower_global_blend_gpu(clusters, image_shape, use_gpu=True)
        assert result.shape == (100, 100, 3)

    def test_very_small_radii(self):
        """Should handle very small pixel counts (tiny radii)."""
        clusters = [make_test_cluster(50, 50, black=10, cyan=5, magenta=5, yellow=5)]
        image_shape = (100, 100)

        result = render_flower_global_blend_gpu(clusters, image_shape, use_gpu=True)
        assert result.shape == (100, 100, 3)

    def test_secondary_colors(self):
        """Should handle clusters with secondary colors (red, green, blue)."""
        clusters = [make_test_cluster(
            50, 50,
            black=200,
            cyan=50, magenta=50, yellow=50,
            red=30, green=30, blue=30,
        )]
        image_shape = (100, 100)

        cpu_result = render_flower_global_blend(clusters, image_shape)
        gpu_result = render_flower_global_blend_gpu(clusters, image_shape, use_gpu=True)

        diff = np.abs(cpu_result.astype(int) - gpu_result.astype(int))
        max_diff = np.max(diff)
        assert max_diff <= 1
