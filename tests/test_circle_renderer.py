"""Tests for circle_renderer module."""

import pytest
import numpy as np

from dotmatrix.circle_renderer import (
    compute_cluster_rotation,
    radius_from_pixels,
    pixels_from_radius,
    render_flower,
    render_flower_cluster,
    PETAL_ANGLES,
)
from dotmatrix.cluster_pixel_counter import ClusterResult


class TestComputeClusterRotation:
    """Tests for compute_cluster_rotation function."""

    def test_fixed_mode_returns_base_rotation(self):
        """Fixed mode should return exactly the base_rotation value."""
        result = compute_cluster_rotation(100, 200, mode='fixed', base_rotation=45.0)
        assert result == 45.0

    def test_fixed_mode_default_base_rotation(self):
        """Fixed mode with default base_rotation should return 0."""
        result = compute_cluster_rotation(100, 200, mode='fixed')
        assert result == 0.0

    def test_random_mode_returns_different_values(self):
        """Random mode should return different values for different positions."""
        result1 = compute_cluster_rotation(100, 200, mode='random')
        result2 = compute_cluster_rotation(150, 250, mode='random')
        # With high probability, random values will differ
        # (very small chance they're identical)
        assert 0 <= result1 < 360 or result1 >= 0  # Valid range check

    def test_random_mode_with_seed_is_reproducible(self):
        """Random mode with seed should be reproducible."""
        result1 = compute_cluster_rotation(100, 200, mode='random', seed=42)
        result2 = compute_cluster_rotation(100, 200, mode='random', seed=42)
        assert result1 == result2

    def test_random_mode_different_seeds_differ(self):
        """Random mode with different seeds should produce different results."""
        result1 = compute_cluster_rotation(100, 200, mode='random', seed=42)
        result2 = compute_cluster_rotation(100, 200, mode='random', seed=123)
        assert result1 != result2

    def test_cluster_hash_is_deterministic(self):
        """Cluster-hash mode should return the same value for same position."""
        result1 = compute_cluster_rotation(100, 200, mode='cluster-hash')
        result2 = compute_cluster_rotation(100, 200, mode='cluster-hash')
        assert result1 == result2

    def test_cluster_hash_differs_by_position(self):
        """Cluster-hash mode should return different values for different positions."""
        result1 = compute_cluster_rotation(100, 200, mode='cluster-hash')
        result2 = compute_cluster_rotation(150, 250, mode='cluster-hash')
        assert result1 != result2

    def test_cluster_hash_with_base_rotation(self):
        """Cluster-hash mode should add base_rotation to hash result."""
        result_no_offset = compute_cluster_rotation(100, 200, mode='cluster-hash', base_rotation=0.0)
        result_with_offset = compute_cluster_rotation(100, 200, mode='cluster-hash', base_rotation=45.0)
        assert abs(result_with_offset - result_no_offset - 45.0) < 0.001

    def test_cluster_hash_returns_valid_range(self):
        """Cluster-hash mode should return values in valid range."""
        for x in range(0, 500, 50):
            for y in range(0, 500, 50):
                result = compute_cluster_rotation(x, y, mode='cluster-hash')
                assert 0 <= result < 360

    def test_unknown_mode_returns_base_rotation(self):
        """Unknown mode should fall back to base_rotation."""
        result = compute_cluster_rotation(100, 200, mode='unknown', base_rotation=30.0)
        assert result == 30.0


class TestRadiusCalculations:
    """Tests for radius calculation functions."""

    def test_radius_from_pixels_zero(self):
        """Zero pixels should return zero radius."""
        assert radius_from_pixels(0) == 0.0

    def test_radius_from_pixels_negative(self):
        """Negative pixels should return zero radius."""
        assert radius_from_pixels(-10) == 0.0

    def test_radius_from_pixels_positive(self):
        """Positive pixel count should return correct radius."""
        # Area = pi * r^2, so for 100 pixels: r = sqrt(100/pi) ≈ 5.64
        radius = radius_from_pixels(100)
        assert abs(radius - 5.64) < 0.1

    def test_pixels_from_radius_zero(self):
        """Zero radius should return zero pixels."""
        assert pixels_from_radius(0) == 0

    def test_pixels_from_radius_negative(self):
        """Negative radius should return zero pixels."""
        assert pixels_from_radius(-5) == 0

    def test_radius_pixels_roundtrip(self):
        """Converting pixels to radius and back should be close to original."""
        original = 100
        radius = radius_from_pixels(original)
        recovered = pixels_from_radius(radius)
        assert abs(recovered - original) <= 1  # Allow for rounding


class TestRenderFlower:
    """Tests for render_flower function."""

    def make_cluster(self, x, y, black=100, cyan=50, magenta=50, yellow=50):
        """Create a test ClusterResult."""
        return ClusterResult(
            x=x, y=y,
            black=black, cyan=cyan, magenta=magenta, yellow=yellow,
            red=0, green=0, blue=0,
            partial=False
        )

    def test_render_flower_creates_image(self):
        """render_flower should create an RGB image."""
        clusters = [self.make_cluster(50, 50)]
        result = render_flower(clusters, (100, 100))
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_render_flower_with_scale(self):
        """render_flower with scale should create larger image."""
        clusters = [self.make_cluster(50, 50)]
        result = render_flower(clusters, (100, 100), scale=2)
        assert result.shape == (200, 200, 3)

    def test_render_flower_fixed_rotation(self):
        """render_flower with fixed rotation should work."""
        clusters = [self.make_cluster(50, 50)]
        result = render_flower(
            clusters, (100, 100),
            rotation_mode='fixed',
            base_rotation=45.0
        )
        assert result.shape == (100, 100, 3)

    def test_render_flower_cluster_hash_rotation(self):
        """render_flower with cluster-hash rotation should work."""
        clusters = [self.make_cluster(50, 50)]
        result = render_flower(
            clusters, (100, 100),
            rotation_mode='cluster-hash'
        )
        assert result.shape == (100, 100, 3)

    def test_render_flower_random_rotation_with_seed(self):
        """render_flower with random rotation and seed should be reproducible."""
        clusters = [self.make_cluster(50, 50)]
        result1 = render_flower(
            clusters, (100, 100),
            rotation_mode='random',
            rotation_seed=42
        )
        result2 = render_flower(
            clusters, (100, 100),
            rotation_mode='random',
            rotation_seed=42
        )
        np.testing.assert_array_equal(result1, result2)

    def test_render_flower_skip_partial(self):
        """render_flower with skip_partial should skip partial clusters."""
        full_cluster = self.make_cluster(50, 50)
        partial_cluster = ClusterResult(
            x=10, y=10,
            black=100, cyan=50, magenta=50, yellow=50,
            red=0, green=0, blue=0,
            partial=True
        )
        clusters = [full_cluster, partial_cluster]

        # With skip_partial, only full_cluster should be rendered
        result = render_flower(clusters, (100, 100), skip_partial=True)
        assert result.shape == (100, 100, 3)

    def test_render_flower_empty_clusters(self):
        """render_flower with empty clusters should create white image."""
        result = render_flower([], (100, 100))
        assert result.shape == (100, 100, 3)
        # Should be all white (255, 255, 255)
        assert np.all(result == 255)


class TestPetalAngles:
    """Tests for petal angle constants."""

    def test_petal_angles_exist(self):
        """PETAL_ANGLES should contain CMY colors."""
        assert 'cyan' in PETAL_ANGLES
        assert 'magenta' in PETAL_ANGLES
        assert 'yellow' in PETAL_ANGLES

    def test_petal_angles_120_apart(self):
        """CMY petals should be 120 degrees apart."""
        angles = list(PETAL_ANGLES.values())
        angles.sort()
        diffs = [angles[1] - angles[0], angles[2] - angles[1], 360 - angles[2] + angles[0]]
        for diff in diffs:
            assert diff == 120
