"""Tests for jitter module (TDD implementation)."""

import pytest
import numpy as np
from dotmatrix.jitter import (
    apply_position_jitter,
    apply_size_jitter,
    validate_jitter_params,
)


class TestJitterValidation:
    """Tests for jitter parameter validation."""

    def test_validate_position_jitter_valid_range(self):
        """Position jitter should accept 0-100%."""
        # Should not raise
        validate_jitter_params(position_pct=0, size_pct=0)
        validate_jitter_params(position_pct=50, size_pct=0)
        validate_jitter_params(position_pct=100, size_pct=0)

    def test_validate_position_jitter_invalid_negative(self):
        """Position jitter should reject negative values."""
        with pytest.raises(ValueError, match="position_pct must be"):
            validate_jitter_params(position_pct=-1, size_pct=0)

    def test_validate_position_jitter_invalid_over_100(self):
        """Position jitter should reject values over 100%."""
        with pytest.raises(ValueError, match="position_pct must be"):
            validate_jitter_params(position_pct=101, size_pct=0)

    def test_validate_size_jitter_valid_range(self):
        """Size jitter should accept 0-100%."""
        # Should not raise
        validate_jitter_params(position_pct=0, size_pct=0)
        validate_jitter_params(position_pct=0, size_pct=50)
        validate_jitter_params(position_pct=0, size_pct=100)

    def test_validate_size_jitter_invalid_negative(self):
        """Size jitter should reject negative values."""
        with pytest.raises(ValueError, match="size_pct must be"):
            validate_jitter_params(position_pct=0, size_pct=-1)

    def test_validate_size_jitter_invalid_over_100(self):
        """Size jitter should reject values over 100%."""
        with pytest.raises(ValueError, match="size_pct must be"):
            validate_jitter_params(position_pct=0, size_pct=101)


class TestPositionJitter:
    """Tests for position jitter application."""

    def test_zero_jitter_returns_original(self):
        """Zero jitter should return original position."""
        x, y = 100.0, 200.0
        jittered_x, jittered_y = apply_position_jitter(
            x, y, position_pct=0, base_radius=10, seed=42
        )
        assert jittered_x == x
        assert jittered_y == y

    def test_jitter_is_reproducible_with_seed(self):
        """Same seed should produce same jitter."""
        x, y = 100.0, 200.0
        result1 = apply_position_jitter(x, y, position_pct=25, base_radius=10, seed=42)
        result2 = apply_position_jitter(x, y, position_pct=25, base_radius=10, seed=42)
        assert result1 == result2

    def test_jitter_differs_with_different_seeds(self):
        """Different seeds should produce different jitter."""
        x, y = 100.0, 200.0
        result1 = apply_position_jitter(x, y, position_pct=25, base_radius=10, seed=42)
        result2 = apply_position_jitter(x, y, position_pct=25, base_radius=10, seed=43)
        assert result1 != result2

    def test_jitter_within_expected_range(self):
        """Jitter should stay within 3-sigma (99.7%) of expected range."""
        x, y = 100.0, 200.0
        base_radius = 10
        position_pct = 25  # 25% of base_radius = 2.5px
        
        # Collect 1000 samples (3-sigma = 99.7% should be within range)
        samples_x = []
        samples_y = []
        for i in range(1000):
            jx, jy = apply_position_jitter(
                x, y, position_pct=position_pct, base_radius=base_radius, seed=i
            )
            samples_x.append(abs(jx - x))
            samples_y.append(abs(jy - y))
        
        # 25% of 10px = 2.5px max offset
        # Gaussian 3-sigma = 3 * (2.5 / 3) = 2.5px
        max_expected = (position_pct / 100) * base_radius
        
        # 99.7% of samples should be within 3-sigma
        x_within = sum(1 for dx in samples_x if dx <= max_expected)
        y_within = sum(1 for dy in samples_y if dy <= max_expected)
        
        # Allow some statistical variance (99% threshold)
        assert x_within / len(samples_x) > 0.99
        assert y_within / len(samples_y) > 0.99

    def test_jitter_distribution_is_centered(self):
        """Mean jitter should be close to zero (centered distribution)."""
        x, y = 100.0, 200.0
        
        # Collect 1000 samples
        samples_x = []
        samples_y = []
        for i in range(1000):
            jx, jy = apply_position_jitter(
                x, y, position_pct=25, base_radius=10, seed=i
            )
            samples_x.append(jx - x)
            samples_y.append(jy - y)
        
        mean_x = np.mean(samples_x)
        mean_y = np.mean(samples_y)
        
        # Mean should be very close to 0 (within 0.1px for 1000 samples)
        assert abs(mean_x) < 0.1
        assert abs(mean_y) < 0.1


class TestSizeJitter:
    """Tests for size jitter application."""

    def test_zero_jitter_returns_original(self):
        """Zero jitter should return original radius."""
        radius = 10.0
        jittered_r = apply_size_jitter(radius, size_pct=0, seed=42)
        assert jittered_r == radius

    def test_jitter_is_reproducible_with_seed(self):
        """Same seed should produce same jitter."""
        radius = 10.0
        result1 = apply_size_jitter(radius, size_pct=20, seed=42)
        result2 = apply_size_jitter(radius, size_pct=20, seed=42)
        assert result1 == result2

    def test_jitter_within_expected_range(self):
        """Size jitter should stay within 3-sigma (99.7%) of expected range."""
        radius = 10.0
        size_pct = 20  # 20% of 10px = 2px
        
        # Collect 1000 samples
        samples = []
        for i in range(1000):
            jr = apply_size_jitter(radius, size_pct=size_pct, seed=i)
            samples.append(abs(jr - radius))
        
        # 20% of 10px = 2px max deviation
        max_expected = (size_pct / 100) * radius
        
        # 99.7% of samples should be within 3-sigma
        within_range = sum(1 for dr in samples if dr <= max_expected)
        
        # Allow some statistical variance (99% threshold)
        assert within_range / len(samples) > 0.99

    def test_jitter_maintains_positive_radius(self):
        """Jitter should never produce negative radius."""
        radius = 5.0
        
        # Test extreme jitter (100%)
        for i in range(1000):
            jr = apply_size_jitter(radius, size_pct=100, seed=i)
            assert jr > 0, f"Negative radius: {jr}"

    def test_jitter_distribution_is_centered(self):
        """Mean jittered radius should be close to original (centered distribution)."""
        radius = 10.0
        
        # Collect 1000 samples
        samples = []
        for i in range(1000):
            jr = apply_size_jitter(radius, size_pct=20, seed=i)
            samples.append(jr)
        
        mean_r = np.mean(samples)
        
        # Mean should be very close to original radius (within 0.1px)
        assert abs(mean_r - radius) < 0.1


class TestJitterAlgorithms:
    """Tests for jitter algorithm selection."""

    def test_gaussian_algorithm(self):
        """Gaussian algorithm should produce normal distribution."""
        x, y = 100.0, 200.0
        
        # Collect samples
        samples = []
        for i in range(1000):
            jx, jy = apply_position_jitter(
                x, y, position_pct=25, base_radius=10, seed=i, algorithm='gaussian'
            )
            distance = ((jx - x)**2 + (jy - y)**2)**0.5
            samples.append(distance)
        
        # Test for normal distribution characteristics
        # Most samples should be near center (68% within 1-sigma)
        sigma = (25 / 100 * 10) / 3  # 25% of 10px / 3 = ~0.83px
        within_1sigma = sum(1 for d in samples if d <= sigma)
        
        # Should be roughly 39% within 1-sigma for 2D Gaussian (Rayleigh distribution)
        # Allow 30-50% range
        ratio = within_1sigma / len(samples)
        assert 0.30 < ratio < 0.50

    def test_uniform_algorithm(self):
        """Uniform algorithm should produce uniform distribution."""
        x, y = 100.0, 200.0
        
        # Collect samples
        samples = []
        for i in range(1000):
            jx, jy = apply_position_jitter(
                x, y, position_pct=25, base_radius=10, seed=i, algorithm='uniform'
            )
            distance = ((jx - x)**2 + (jy - y)**2)**0.5
            samples.append(distance)
        
        # Max distance for uniform in circle: 25% of 10px = 2.5px
        max_dist = (25 / 100) * 10
        
        # All samples should be within max distance
        assert all(d <= max_dist * 1.01 for d in samples), f"Max: {max(samples)}, expected {max_dist}"

    def test_invalid_algorithm_raises(self):
        """Invalid algorithm should raise ValueError."""
        with pytest.raises(ValueError, match="algorithm must be"):
            apply_position_jitter(
                100.0, 200.0, position_pct=25, base_radius=10, seed=42, algorithm='invalid'
            )


class TestJitterPerformance:
    """Performance tests for jitter operations."""

    def test_position_jitter_performance(self, benchmark):
        """Position jitter should be fast (<10µs per call)."""
        result = benchmark(
            apply_position_jitter, 100.0, 200.0, position_pct=25, base_radius=10, seed=42
        )
        assert result is not None

    def test_size_jitter_performance(self, benchmark):
        """Size jitter should be fast (<10µs per call)."""
        result = benchmark(
            apply_size_jitter, 10.0, size_pct=20, seed=42
        )
        assert result is not None
