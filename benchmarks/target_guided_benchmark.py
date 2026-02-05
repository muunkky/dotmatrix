"""Benchmark: Target-Guided Optimization Performance.

Measures overhead of target-guided optimization compared to standard drift.
Acceptance criteria: <2x overhead.

Usage:
    python benchmarks/target_guided_benchmark.py
"""

import time
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np

from dotmatrix.target_guided import (
    TargetCircle,
    TargetGuidedConfig,
    TargetCircleIndex,
    apply_target_guided_optimization,
)


def generate_test_data(num_clusters: int = 100):
    """Generate synthetic test data for benchmarking."""
    np.random.seed(42)  # Reproducible
    
    circles_by_color = {
        'cyan': [],
        'magenta': [],
        'yellow': [],
        'black': [],
    }
    cluster_metadata = []
    cluster_circle_map = []
    
    for i in range(num_clusters):
        cx = np.random.uniform(0, 1000)
        cy = np.random.uniform(0, 1000)
        black_r = np.random.uniform(10, 30)
        
        # Add black circle
        circles_by_color['black'].append((cx, cy, black_r))
        
        # Add CMY petals
        for color_idx, color in enumerate(['cyan', 'magenta', 'yellow']):
            angle = (color_idx * 120) * np.pi / 180
            petal_x = cx + black_r * 0.35 * np.cos(angle)
            petal_y = cy + black_r * 0.35 * np.sin(angle)
            petal_r = np.random.uniform(5, 15)
            
            circle_idx = len(circles_by_color[color])
            circles_by_color[color].append((petal_x, petal_y, petal_r))
        
        cluster_metadata.append({
            'cx': cx,
            'cy': cy,
            'black_radius': black_r,
            'black_circle_idx': i,
        })
        
        cluster_circle_map.append({
            'cyan': (len(circles_by_color['cyan']) - 1, 100),
            'magenta': (len(circles_by_color['magenta']) - 1, 100),
            'yellow': (len(circles_by_color['yellow']) - 1, 100),
        })
    
    return circles_by_color, cluster_metadata, cluster_circle_map


def generate_target_index(num_targets: int = 150):
    """Generate target circles for optimization."""
    np.random.seed(123)
    
    targets = []
    for _ in range(num_targets):
        for color in ['cyan', 'magenta', 'yellow']:
            targets.append(TargetCircle(
                x=np.random.uniform(0, 1000),
                y=np.random.uniform(0, 1000),
                radius=np.random.uniform(5, 15),
                color=color,
            ))
    
    return TargetCircleIndex(targets)


def benchmark_standard_drift(circles_by_color, cluster_metadata, cluster_circle_map,
                             iterations: int = 10):
    """Simulate standard drift without target guidance."""
    # Standard drift just adjusts radii without target matching
    # We simulate this by running optimization with target_weight=0
    config = TargetGuidedConfig(
        target_image_path=Path("dummy.png"),
        target_weight=0.0,  # Pure drift, no target
        step_size=0.1,
        max_iterations=iterations,
    )
    
    # Create minimal target index (won't be used with weight=0)
    target_index = TargetCircleIndex([])
    
    start = time.perf_counter()
    
    # Make a copy to avoid modifying original
    circles_copy = {
        color: list(circles)
        for color, circles in circles_by_color.items()
    }
    
    apply_target_guided_optimization(
        circles_copy,
        cluster_metadata,
        cluster_circle_map,
        target_index,
        image_shape=(1000, 1000),
        config=config,
    )
    
    return time.perf_counter() - start


def benchmark_target_guided(circles_by_color, cluster_metadata, cluster_circle_map,
                            target_index, iterations: int = 10):
    """Benchmark target-guided optimization."""
    config = TargetGuidedConfig(
        target_image_path=Path("dummy.png"),
        target_weight=0.5,  # Balanced
        step_size=0.1,
        max_iterations=iterations,
    )
    
    start = time.perf_counter()
    
    # Make a copy
    circles_copy = {
        color: list(circles)
        for color, circles in circles_by_color.items()
    }
    
    apply_target_guided_optimization(
        circles_copy,
        cluster_metadata,
        cluster_circle_map,
        target_index,
        image_shape=(1000, 1000),
        config=config,
    )
    
    return time.perf_counter() - start


def run_benchmark():
    """Run the full benchmark suite."""
    print("=" * 60)
    print("Target-Guided Optimization Performance Benchmark")
    print("=" * 60)
    print()
    
    # Test configurations
    configs = [
        (50, 10, "Small (50 clusters, 10 iterations)"),
        (100, 20, "Medium (100 clusters, 20 iterations)"),
        (200, 50, "Large (200 clusters, 50 iterations)"),
    ]
    
    results = []
    
    for num_clusters, iterations, label in configs:
        print(f"\n{label}")
        print("-" * 40)
        
        # Generate test data
        circles, metadata, circle_map = generate_test_data(num_clusters)
        target_index = generate_target_index(num_clusters)
        
        # Warm-up run
        _ = benchmark_standard_drift(circles, metadata, circle_map, iterations=2)
        _ = benchmark_target_guided(circles, metadata, circle_map, target_index, iterations=2)
        
        # Benchmark runs (average of 3)
        drift_times = []
        target_times = []
        
        for run in range(3):
            drift_time = benchmark_standard_drift(circles, metadata, circle_map, iterations)
            target_time = benchmark_target_guided(circles, metadata, circle_map, target_index, iterations)
            drift_times.append(drift_time)
            target_times.append(target_time)
        
        avg_drift = sum(drift_times) / len(drift_times)
        avg_target = sum(target_times) / len(target_times)
        overhead = avg_target / avg_drift if avg_drift > 0 else float('inf')
        
        print(f"  Standard drift:     {avg_drift*1000:.2f} ms")
        print(f"  Target-guided:      {avg_target*1000:.2f} ms")
        print(f"  Overhead ratio:     {overhead:.2f}x")
        print(f"  Status:             {'✓ PASS' if overhead < 2.0 else '✗ FAIL'} (<2x required)")
        
        results.append({
            'label': label,
            'drift_ms': avg_drift * 1000,
            'target_ms': avg_target * 1000,
            'overhead': overhead,
            'passed': overhead < 2.0,
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = all(r['passed'] for r in results)
    max_overhead = max(r['overhead'] for r in results)
    
    print(f"\nMax overhead: {max_overhead:.2f}x")
    print(f"Requirement:  <2.0x")
    print(f"\nOverall:      {'✓ PASS - Performance requirement met!' if all_passed else '✗ FAIL - Performance needs optimization'}")
    
    return all_passed


if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
