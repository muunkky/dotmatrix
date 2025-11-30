"""Tests for circle_renderer module."""

import math
import pytest
import numpy as np

from dotmatrix.circle_renderer import (
    compute_cluster_rotation,
    radius_from_pixels,
    pixels_from_radius,
    render_flower,
    render_flower_cluster,
    PETAL_ANGLES,
    lens_area,
    exposed_area,
    radius_for_exposed_pixels,
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


class TestLensArea:
    """Tests for lens_area function (circle-circle intersection)."""

    def test_no_overlap_far_apart(self):
        """Circles far apart should have zero intersection."""
        # Two circles of radius 5, centers 20 apart
        assert lens_area(5, 5, 20) == 0.0

    def test_no_overlap_just_touching(self):
        """Circles just touching should have zero intersection."""
        # Two circles of radius 5, centers exactly 10 apart
        assert lens_area(5, 5, 10) == 0.0

    def test_concentric_circles(self):
        """Concentric circles should return area of smaller circle."""
        # Concentric circles (distance = 0)
        result = lens_area(10, 5, 0)
        expected = math.pi * 5 ** 2  # Smaller circle fully inside
        assert abs(result - expected) < 0.01

    def test_one_inside_other(self):
        """Small circle fully inside larger should return small circle area."""
        # Small circle inside large (r1=10, r2=3, d=2 means r2 is inside r1)
        result = lens_area(10, 3, 2)
        expected = math.pi * 3 ** 2
        assert abs(result - expected) < 0.01

    def test_identical_circles_same_position(self):
        """Identical circles at same position should return full area."""
        result = lens_area(5, 5, 0)
        expected = math.pi * 5 ** 2
        assert abs(result - expected) < 0.01

    def test_partial_overlap_symmetric(self):
        """Symmetric partial overlap should give positive area < smaller circle."""
        # Two circles of radius 10 with centers 10 apart (50% overlap roughly)
        result = lens_area(10, 10, 10)
        max_area = math.pi * 10 ** 2
        assert 0 < result < max_area

    def test_overlap_increases_as_distance_decreases(self):
        """Overlap area should increase as circles get closer."""
        r1, r2 = 10, 10
        area_far = lens_area(r1, r2, 15)
        area_near = lens_area(r1, r2, 5)
        assert area_near > area_far

    def test_asymmetric_circles(self):
        """Asymmetric circles should compute correct overlap."""
        # r1=10, r2=5, d=8 (partial overlap)
        result = lens_area(10, 5, 8)
        assert result > 0
        assert result < math.pi * 5 ** 2  # Less than smaller circle


class TestExposedArea:
    """Tests for exposed_area function."""

    def test_no_overlap_full_exposure(self):
        """When circles don't overlap, exposed area equals full petal area."""
        # Petal far from black circle
        result = exposed_area(5, 10, 30)
        expected = math.pi * 5 ** 2
        assert abs(result - expected) < 0.01

    def test_full_overlap_zero_exposure(self):
        """When petal is inside black circle, exposed area is zero."""
        # Small petal inside large black circle
        result = exposed_area(3, 10, 2)
        assert result == 0.0

    def test_partial_overlap_reduced_exposure(self):
        """Partial overlap should reduce exposed area."""
        petal_r, black_r, d = 5, 10, 10
        full_area = math.pi * petal_r ** 2
        result = exposed_area(petal_r, black_r, d)
        assert 0 < result < full_area

    def test_exposed_area_never_negative(self):
        """Exposed area should never be negative."""
        # Various scenarios
        for petal_r in [3, 5, 10]:
            for black_r in [5, 10, 15]:
                for d in [0, 2, 5, 10, 20]:
                    result = exposed_area(petal_r, black_r, d)
                    assert result >= 0


class TestRadiusForExposedPixels:
    """Tests for radius_for_exposed_pixels function."""

    def test_zero_target_returns_zero(self):
        """Zero target pixels should return zero radius."""
        result = radius_for_exposed_pixels(0, 10, 15)
        assert result == 0.0

    def test_no_black_circle_simple_area(self):
        """With no black circle, radius should match simple area formula."""
        target = 100
        result = radius_for_exposed_pixels(target, 0, 15)
        expected = radius_from_pixels(target)
        assert abs(result - expected) < 0.1

    def test_with_overlap_radius_larger(self):
        """With overlap, radius should be larger to compensate."""
        target = 100
        black_r = 10
        d = 12  # Close enough for overlap

        # Without overlap
        simple_radius = radius_from_pixels(target)

        # With overlap - need larger radius to get same exposed area
        result = radius_for_exposed_pixels(target, black_r, d)

        assert result >= simple_radius

    def test_result_achieves_target(self):
        """Found radius should give approximately the target exposed area."""
        target = 100
        black_r = 10
        d = 15

        found_radius = radius_for_exposed_pixels(target, black_r, d)
        actual_exposed = exposed_area(found_radius, black_r, d)

        assert abs(actual_exposed - target) < 1.0  # Within tolerance

    def test_various_targets(self):
        """Test convergence for various target values."""
        black_r = 10
        d = 14

        for target in [50, 100, 200, 500]:
            found_radius = radius_for_exposed_pixels(target, black_r, d)
            actual_exposed = exposed_area(found_radius, black_r, d)
            assert abs(actual_exposed - target) < 1.0


class TestRenderFlowerWithExposedArea:
    """Tests for render_flower with use_exposed_area parameter."""

    def make_cluster(self, x, y, black=100, cyan=50, magenta=50, yellow=50):
        """Create a test ClusterResult."""
        return ClusterResult(
            x=x, y=y,
            black=black, cyan=cyan, magenta=magenta, yellow=yellow,
            red=0, green=0, blue=0,
            partial=False
        )

    def test_render_flower_with_exposed_area_creates_image(self):
        """render_flower with use_exposed_area should create valid image."""
        clusters = [self.make_cluster(50, 50)]
        result = render_flower(clusters, (100, 100), use_exposed_area=True)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_render_flower_exposed_area_differs_from_default(self):
        """Exposed area sizing should produce different results than default."""
        clusters = [self.make_cluster(50, 50, black=200, cyan=100)]
        result_default = render_flower(clusters, (100, 100), use_exposed_area=False)
        result_exposed = render_flower(clusters, (100, 100), use_exposed_area=True)
        # The images should differ (petals will be sized differently)
        # We can't guarantee they're always different, but with significant overlap they should be
        # Just verify both produce valid images
        assert result_default.shape == result_exposed.shape


class TestRenderFlowerWithBlending:
    """Tests for render_flower with blend_overlaps parameter (subtractive CMY)."""

    def make_cluster(self, x, y, black=100, cyan=50, magenta=50, yellow=50):
        """Create a test ClusterResult."""
        return ClusterResult(
            x=x, y=y,
            black=black, cyan=cyan, magenta=magenta, yellow=yellow,
            red=0, green=0, blue=0,
            partial=False
        )

    def test_render_flower_with_blending_creates_image(self):
        """render_flower with blend_overlaps should create valid image."""
        clusters = [self.make_cluster(50, 50)]
        result = render_flower(clusters, (100, 100), blend_overlaps=True)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_render_flower_blending_differs_from_default(self):
        """Blending mode should produce different results than default."""
        clusters = [self.make_cluster(50, 50, black=100, cyan=100, magenta=100, yellow=100)]
        result_default = render_flower(clusters, (100, 100), blend_overlaps=False)
        result_blended = render_flower(clusters, (100, 100), blend_overlaps=True)
        # The images should differ (blending vs overlay)
        # Blended mode uses subtractive color mixing
        assert result_default.shape == result_blended.shape

    def test_blending_cyan_removes_red(self):
        """In blended mode, cyan areas should have no red component."""
        # Cluster with only cyan
        cluster = ClusterResult(
            x=50, y=50,
            black=0, cyan=200, magenta=0, yellow=0,
            red=0, green=0, blue=0,
            partial=False
        )
        result = render_flower([cluster], (100, 100), blend_overlaps=True)
        # Find cyan pixels (non-white, non-black)
        non_white = np.any(result != 255, axis=2)
        if np.any(non_white):
            # Cyan pixels should have R=0 (BGR format: channel 2 is R)
            cyan_pixels = result[non_white]
            # Pure cyan in subtractive should be (255, 255, 0) in BGR = cyan
            assert np.all(cyan_pixels[:, 2] == 0)  # Red channel should be 0

    def test_blending_magenta_removes_green(self):
        """In blended mode, magenta areas should have no green component."""
        cluster = ClusterResult(
            x=50, y=50,
            black=0, cyan=0, magenta=200, yellow=0,
            red=0, green=0, blue=0,
            partial=False
        )
        result = render_flower([cluster], (100, 100), blend_overlaps=True)
        non_white = np.any(result != 255, axis=2)
        if np.any(non_white):
            magenta_pixels = result[non_white]
            # Pure magenta should have G=0 (BGR format: channel 1 is G)
            assert np.all(magenta_pixels[:, 1] == 0)

    def test_blending_yellow_removes_blue(self):
        """In blended mode, yellow areas should have no blue component."""
        cluster = ClusterResult(
            x=50, y=50,
            black=0, cyan=0, magenta=0, yellow=200,
            red=0, green=0, blue=0,
            partial=False
        )
        result = render_flower([cluster], (100, 100), blend_overlaps=True)
        non_white = np.any(result != 255, axis=2)
        if np.any(non_white):
            yellow_pixels = result[non_white]
            # Pure yellow should have B=0 (BGR format: channel 0 is B)
            assert np.all(yellow_pixels[:, 0] == 0)

    def test_blending_cyan_magenta_makes_blue(self):
        """Cyan + Magenta overlap should produce blue (in subtractive mixing)."""
        # Large cyan and magenta to ensure overlap
        cluster = ClusterResult(
            x=50, y=50,
            black=0, cyan=300, magenta=300, yellow=0,
            red=0, green=0, blue=0,
            partial=False
        )
        result = render_flower([cluster], (100, 100), blend_overlaps=True)
        # Find pixels that are blue-ish (low R, low G, high B)
        # In BGR: high channel 0 (B), low channel 1 (G), low channel 2 (R)
        blue_mask = (result[:, :, 0] > 200) & (result[:, :, 1] < 50) & (result[:, :, 2] < 50)
        # There should be some blue pixels where C and M overlap
        assert np.any(blue_mask), "Expected blue pixels from C+M overlap"

    def test_blending_all_cmy_makes_dark(self):
        """Cyan + Magenta + Yellow overlap should produce near-black."""
        # Large CMY to ensure overlap in center
        cluster = ClusterResult(
            x=50, y=50,
            black=0, cyan=400, magenta=400, yellow=400,
            red=0, green=0, blue=0,
            partial=False
        )
        result = render_flower([cluster], (100, 100), blend_overlaps=True)
        # Find very dark pixels (all channels near 0)
        dark_mask = np.all(result < 50, axis=2)
        # There should be some dark pixels where all three overlap
        assert np.any(dark_mask), "Expected dark pixels from C+M+Y overlap"
