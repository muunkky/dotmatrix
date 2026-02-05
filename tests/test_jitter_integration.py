"""Unit tests for jitter rendering integration."""
import pytest
import numpy as np
from dotmatrix.circle_renderer import render_flower
from dotmatrix.cluster_pixel_counter import ClusterResult


def create_test_cluster(x=100, y=100):
    """Create a simple test cluster."""
    return ClusterResult(
        x=x, y=y,
        cyan=800, magenta=0, yellow=0, black=800,
        red=0, green=0, blue=0,
        partial=False
    )


def test_jitter_changes_output():
    """Verify jitter produces different output than baseline."""
    cluster = create_test_cluster()
    
    # Render without jitter
    img_baseline = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=0, jitter_size=0, jitter_seed=1
    )
    
    # Render with position jitter
    img_jittered = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=25, jitter_size=0, jitter_seed=1
    )
    
    # Images should be different
    assert not np.array_equal(img_baseline, img_jittered), \
        "Jittered image should differ from baseline"
    
    # Calculate difference
    diff = np.sum(np.abs(img_baseline.astype(int) - img_jittered.astype(int)))
    assert diff > 0, f"No visual difference detected (diff={diff})"
    print(f"✓ Position jitter creates visual difference (pixel diff: {diff:,})")


def test_size_jitter_changes_output():
    """Verify size jitter produces different output."""
    cluster = create_test_cluster()
    
    # Render without jitter
    img_baseline = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=0, jitter_size=0, jitter_seed=1
    )
    
    # Render with size jitter
    img_jittered = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=0, jitter_size=20, jitter_seed=1
    )
    
    # Images should be different
    assert not np.array_equal(img_baseline, img_jittered), \
        "Size jittered image should differ from baseline"
    
    diff = np.sum(np.abs(img_baseline.astype(int) - img_jittered.astype(int)))
    assert diff > 0, f"No visual difference detected (diff={diff})"
    print(f"✓ Size jitter creates visual difference (pixel diff: {diff:,})")


def test_different_seeds_produce_different_results():
    """Verify different seeds produce different jitter patterns."""
    cluster = create_test_cluster()
    
    img_seed1 = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=25, jitter_size=20, jitter_seed=1
    )
    
    img_seed2 = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=25, jitter_size=20, jitter_seed=2
    )
    
    # Different seeds should produce different results
    assert not np.array_equal(img_seed1, img_seed2), \
        "Different seeds should produce different jitter patterns"
    
    diff = np.sum(np.abs(img_seed1.astype(int) - img_seed2.astype(int)))
    print(f"✓ Different seeds produce different output (pixel diff: {diff:,})")


def test_same_seed_produces_identical_results():
    """Verify reproducibility with same seed."""
    cluster = create_test_cluster()
    
    img_a = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=25, jitter_size=20, jitter_seed=42
    )
    
    img_b = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=25, jitter_size=20, jitter_seed=42
    )
    
    # Same seed should produce identical results
    assert np.array_equal(img_a, img_b), \
        "Same seed should produce identical results"
    print("✓ Same seed produces reproducible output")


def test_zero_jitter_produces_baseline():
    """Verify 0% jitter produces same output."""
    cluster = create_test_cluster()
    
    img_zero_jitter = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=0, jitter_size=0, jitter_seed=1
    )
    
    img_zero_jitter_again = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=0, jitter_size=0, jitter_seed=999
    )
    
    # 0% jitter should always produce same result regardless of seed
    assert np.array_equal(img_zero_jitter, img_zero_jitter_again), \
        "0% jitter should produce identical output with any seed"
    print("✓ Zero jitter produces consistent baseline")


def test_increasing_jitter_increases_variation():
    """Verify larger jitter percentages create more variation."""
    cluster = create_test_cluster()
    
    img_baseline = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=0, jitter_size=0, jitter_seed=1
    )
    
    img_small = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=10, jitter_size=0, jitter_seed=1
    )
    
    img_large = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=40, jitter_size=0, jitter_seed=1
    )
    
    diff_small = np.sum(np.abs(img_baseline.astype(int) - img_small.astype(int)))
    diff_large = np.sum(np.abs(img_baseline.astype(int) - img_large.astype(int)))
    
    # Larger jitter should create more difference
    assert diff_large > diff_small, \
        f"Larger jitter should create more variation (small={diff_small:,}, large={diff_large:,})"
    print(f"✓ Larger jitter creates more variation (10%: {diff_small:,}, 40%: {diff_large:,})")


def test_multiple_clusters_jitter_independently():
    """Verify each cluster gets unique jitter."""
    clusters = [
        create_test_cluster(x=50, y=50),
        create_test_cluster(x=150, y=50),
        create_test_cluster(x=50, y=150),
        create_test_cluster(x=150, y=150),
    ]
    
    img_baseline = render_flower(
        clusters, (200, 200),
        scale=1.0, jitter_position=0, jitter_size=0, jitter_seed=1
    )
    
    img_jittered = render_flower(
        clusters, (200, 200),
        scale=1.0, jitter_position=25, jitter_size=0, jitter_seed=1
    )
    
    # Should see differences across multiple regions
    assert not np.array_equal(img_baseline, img_jittered), \
        "Multiple clusters should show jitter"
    
    diff = np.sum(np.abs(img_baseline.astype(int) - img_jittered.astype(int)))
    print(f"✓ Multiple clusters jitter independently (diff: {diff:,})")


def test_jitter_works_with_blend_overlaps():
    """Verify jitter works in blend_overlaps mode (global blend path)."""
    cluster = create_test_cluster()
    
    # Render without jitter (blend mode)
    img_baseline = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=0, jitter_size=0, jitter_seed=1,
        blend_overlaps=True
    )
    
    # Render with jitter (blend mode)
    img_jittered = render_flower(
        [cluster], (200, 200),
        scale=1.0, jitter_position=25, jitter_size=20, jitter_seed=1,
        blend_overlaps=True
    )
    
    # Images should be different
    assert not np.array_equal(img_baseline, img_jittered), \
        "Jitter should work in blend_overlaps mode"
    
    diff = np.sum(np.abs(img_baseline.astype(int) - img_jittered.astype(int)))
    assert diff > 0, f"No visual difference in blend mode (diff={diff})"
    print(f"✓ Jitter works with blend_overlaps=True (pixel diff: {diff:,})")


if __name__ == "__main__":
    print("Running jitter integration tests...\n")
    
    test_jitter_changes_output()
    test_size_jitter_changes_output()
    test_different_seeds_produce_different_results()
    test_same_seed_produces_identical_results()
    test_zero_jitter_produces_baseline()
    test_increasing_jitter_increases_variation()
    test_multiple_clusters_jitter_independently()
    test_jitter_works_with_blend_overlaps()
    
    print("\n✅ All jitter integration tests passed!")
