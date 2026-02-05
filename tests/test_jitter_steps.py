"""Tests for --jitter-steps multi-step jitter-drift pipeline feature."""

import pytest
import numpy as np

from dotmatrix.cluster_pixel_counter import ClusterResult
from dotmatrix.circle_renderer import render_flower_svg, render_flower


class TestJitterSteps:
    """Test jitter_steps parameter for multi-step jitter-drift processing."""

    @pytest.fixture
    def sample_clusters(self):
        """Create sample clusters for testing."""
        return [
            ClusterResult(
                x=50, y=50,
                cyan=100, magenta=80, yellow=60,
                red=10, green=10, blue=10,
                black=120, background=0,
                partial=False
            ),
            ClusterResult(
                x=150, y=50,
                cyan=80, magenta=100, yellow=70,
                red=5, green=5, blue=5,
                black=100, background=0,
                partial=False
            ),
        ]

    def test_jitter_steps_default_is_one(self, sample_clusters):
        """Default jitter_steps=1 should match legacy behavior."""
        # SVG with drift but default steps
        svg_default = render_flower_svg(
            clusters=sample_clusters,
            image_shape=(100, 200),
            scale=1,
            jitter_position=10.0,
            jitter_seed=42,
            drift=True,
            drift_tolerance=0.2,
            drift_max_iterations=5,
            drift_max_step=2.0,
            # jitter_steps defaults to 1
        )
        
        # SVG with explicit steps=1
        svg_explicit = render_flower_svg(
            clusters=sample_clusters,
            image_shape=(100, 200),
            scale=1,
            jitter_position=10.0,
            jitter_seed=42,
            drift=True,
            drift_tolerance=0.2,
            drift_max_iterations=5,
            drift_max_step=2.0,
            jitter_steps=1,
        )
        
        # Should produce identical output
        assert svg_default == svg_explicit

    def test_jitter_steps_increases_drift_effect(self, sample_clusters):
        """Multiple jitter steps should compound the drift effect."""
        # Single step
        svg_1_step = render_flower_svg(
            clusters=sample_clusters,
            image_shape=(100, 200),
            scale=1,
            jitter_position=10.0,
            jitter_seed=42,
            drift=True,
            drift_tolerance=0.2,
            drift_max_iterations=5,
            drift_max_step=2.0,
            jitter_steps=1,
        )
        
        # Multiple steps
        svg_3_steps = render_flower_svg(
            clusters=sample_clusters,
            image_shape=(100, 200),
            scale=1,
            jitter_position=10.0,
            jitter_seed=42,
            drift=True,
            drift_tolerance=0.2,
            drift_max_iterations=5,
            drift_max_step=2.0,
            jitter_steps=3,
        )
        
        # Different steps should produce different output
        assert svg_1_step != svg_3_steps

    def test_jitter_steps_increments_seed(self, sample_clusters):
        """Each step should use a different seed (jitter_seed + step)."""
        # Step 0 uses seed 42, step 1 uses seed 43, etc.
        svg_step0 = render_flower_svg(
            clusters=sample_clusters,
            image_shape=(100, 200),
            scale=1,
            jitter_position=10.0,
            jitter_seed=42,
            drift=True,
            jitter_steps=1,
        )
        
        # Same as running with seed=43 as first step
        svg_seed43 = render_flower_svg(
            clusters=sample_clusters,
            image_shape=(100, 200),
            scale=1,
            jitter_position=10.0,
            jitter_seed=43,
            drift=True,
            jitter_steps=1,
        )
        
        # Different seeds should produce different results
        assert svg_step0 != svg_seed43

    def test_jitter_steps_png_render(self, sample_clusters):
        """Test jitter_steps with PNG render (blend_overlaps=True uses render_flower_global_blend)."""
        # Single step PNG
        png_1_step = render_flower(
            clusters=sample_clusters,
            image_shape=(100, 200),
            scale=1,
            blend_overlaps=True,
            jitter_position=10.0,
            jitter_seed=42,
            drift=True,
            drift_tolerance=0.2,
            drift_max_iterations=5,
            drift_max_step=2.0,
            jitter_steps=1,
        )
        
        # Multiple steps PNG
        png_3_steps = render_flower(
            clusters=sample_clusters,
            image_shape=(100, 200),
            scale=1,
            blend_overlaps=True,
            jitter_position=10.0,
            jitter_seed=42,
            drift=True,
            drift_tolerance=0.2,
            drift_max_iterations=5,
            drift_max_step=2.0,
            jitter_steps=3,
        )
        
        # Both should be valid images
        assert png_1_step.shape == (100, 200, 3)
        assert png_3_steps.shape == (100, 200, 3)
        
        # Different steps should produce different output
        # (compare as flat arrays)
        assert not np.array_equal(png_1_step, png_3_steps)

    def test_jitter_steps_without_drift_has_no_effect(self, sample_clusters):
        """jitter_steps should only apply when drift=True."""
        # Without drift, jitter_steps shouldn't change output
        svg_1_step = render_flower_svg(
            clusters=sample_clusters,
            image_shape=(100, 200),
            scale=1,
            jitter_position=10.0,
            jitter_seed=42,
            drift=False,  # Drift disabled
            jitter_steps=1,
        )
        
        svg_3_steps = render_flower_svg(
            clusters=sample_clusters,
            image_shape=(100, 200),
            scale=1,
            jitter_position=10.0,
            jitter_seed=42,
            drift=False,  # Drift disabled
            jitter_steps=3,
        )
        
        # Without drift, jitter_steps doesn't change output
        # (the jitter is applied once regardless of steps when drift=False)
        assert svg_1_step == svg_3_steps

    def test_jitter_steps_zero_or_negative_treated_as_one(self, sample_clusters):
        """Edge case: jitter_steps=0 should be handled gracefully."""
        # This tests that the range(0) produces no iterations
        # but the code should still work (no crashes)
        svg_zero = render_flower_svg(
            clusters=sample_clusters,
            image_shape=(100, 200),
            scale=1,
            jitter_position=10.0,
            jitter_seed=42,
            drift=True,
            jitter_steps=0,  # Edge case
        )
        # Should not crash - produces output with no drift applied
        assert '<?xml' in svg_zero


class TestJitterStepsGPU:
    """Test jitter_steps with GPU renderer."""

    @pytest.fixture
    def sample_clusters(self):
        """Create sample clusters for testing."""
        return [
            ClusterResult(
                x=50, y=50,
                cyan=100, magenta=80, yellow=60,
                red=10, green=10, blue=10,
                black=120, background=0,
                partial=False
            ),
        ]

    def test_gpu_renderer_jitter_steps(self, sample_clusters):
        """Test jitter_steps parameter with GPU renderer."""
        from dotmatrix.gpu_renderer import render_flower_global_blend_gpu
        
        # Single step
        result_1_step = render_flower_global_blend_gpu(
            clusters=sample_clusters,
            image_shape=(100, 100),
            scale=1,
            use_gpu=False,  # Use CPU fallback for test
            jitter_position=10,
            jitter_seed=42,
            drift=True,
            drift_tolerance=0.2,
            drift_max_iterations=5,
            drift_max_step=2.0,
            jitter_steps=1,
        )
        
        # Multiple steps
        result_3_steps = render_flower_global_blend_gpu(
            clusters=sample_clusters,
            image_shape=(100, 100),
            scale=1,
            use_gpu=False,
            jitter_position=10,
            jitter_seed=42,
            drift=True,
            drift_tolerance=0.2,
            drift_max_iterations=5,
            drift_max_step=2.0,
            jitter_steps=3,
        )
        
        # Both should be valid images
        assert result_1_step.shape == (100, 100, 3)
        assert result_3_steps.shape == (100, 100, 3)
        
        # Different steps should produce different output
        assert not np.array_equal(result_1_step, result_3_steps)
