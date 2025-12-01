#!/usr/bin/env python3
"""GPU vs CPU performance benchmarks for dotmatrix flower renderer.

Benchmarks measure:
- Render time (CPU vs GPU)
- Speedup factor
- Memory usage
- Performance across different image sizes and cluster counts

Usage:
    python benchmarks/gpu_benchmark.py
    python benchmarks/gpu_benchmark.py --runs 5 --output results.json
"""

import argparse
import gc
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotmatrix.cluster_pixel_counter import ClusterResult
from dotmatrix.circle_renderer import render_flower_global_blend
from dotmatrix.gpu_renderer import render_flower_global_blend_gpu
from dotmatrix.gpu import is_gpu_available, get_gpu_info


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""
    image_size: tuple
    num_clusters: int
    cpu_time_ms: float
    gpu_time_ms: float
    speedup: float
    max_pixel_diff: int
    memory_mb: float


def make_test_clusters(num_clusters: int, image_shape: tuple) -> List[ClusterResult]:
    """Generate test clusters distributed across the image."""
    h, w = image_shape
    clusters = []

    # Calculate grid dimensions
    grid_size = int(np.ceil(np.sqrt(num_clusters)))
    cell_h = h // grid_size
    cell_w = w // grid_size

    for i in range(num_clusters):
        row = i // grid_size
        col = i % grid_size

        # Center in cell
        x = col * cell_w + cell_w // 2
        y = row * cell_h + cell_h // 2

        # Vary pixel counts based on position
        clusters.append(ClusterResult(
            x=x,
            y=y,
            black=200 + (row + col) * 20,
            cyan=100 + col * 10,
            magenta=100 + row * 10,
            yellow=80 + (row * col) % 50,
            red=0,
            green=0,
            blue=0,
            partial=False,
        ))

    return clusters


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0.0


def run_benchmark(
    image_shape: tuple,
    num_clusters: int,
    warmup_runs: int = 1,
    timed_runs: int = 3,
) -> BenchmarkResult:
    """Run a single benchmark configuration."""
    clusters = make_test_clusters(num_clusters, image_shape)

    # Warmup runs (not timed)
    for _ in range(warmup_runs):
        _ = render_flower_global_blend(clusters, image_shape)
        _ = render_flower_global_blend_gpu(clusters, image_shape, use_gpu=True)

    gc.collect()

    # Timed CPU runs
    cpu_times = []
    for _ in range(timed_runs):
        gc.collect()
        start = time.perf_counter()
        cpu_result = render_flower_global_blend(clusters, image_shape)
        cpu_times.append((time.perf_counter() - start) * 1000)

    # Timed GPU runs
    gpu_times = []
    for _ in range(timed_runs):
        gc.collect()
        start = time.perf_counter()
        gpu_result = render_flower_global_blend_gpu(clusters, image_shape, use_gpu=True)
        gpu_times.append((time.perf_counter() - start) * 1000)

    # Calculate metrics
    cpu_time_ms = np.median(cpu_times)
    gpu_time_ms = np.median(gpu_times)
    speedup = cpu_time_ms / gpu_time_ms if gpu_time_ms > 0 else 0

    # Verify equivalence
    diff = np.abs(cpu_result.astype(int) - gpu_result.astype(int))
    max_diff = int(np.max(diff))

    # Memory usage
    memory_mb = get_memory_usage_mb()

    return BenchmarkResult(
        image_size=image_shape,
        num_clusters=num_clusters,
        cpu_time_ms=cpu_time_ms,
        gpu_time_ms=gpu_time_ms,
        speedup=speedup,
        max_pixel_diff=max_diff,
        memory_mb=memory_mb,
    )


def run_all_benchmarks(
    runs: int = 3,
    verbose: bool = True,
) -> List[BenchmarkResult]:
    """Run benchmarks across multiple configurations."""
    configs = [
        # (image_size, num_clusters)
        ((100, 100), 4),      # Small
        ((100, 100), 16),     # Small, more clusters
        ((500, 500), 25),     # Medium
        ((500, 500), 100),    # Medium, many clusters
        ((1000, 1000), 100),  # Large
        ((1000, 1000), 400),  # Large, many clusters
        ((2000, 2000), 400),  # Very large
    ]

    results = []

    if verbose:
        print("\n" + "=" * 80)
        print("GPU vs CPU Flower Renderer Benchmark")
        print("=" * 80)

        gpu_info = get_gpu_info()
        print(f"\nGPU Available: {gpu_info['gpu_available']}")
        if gpu_info['gpu_available']:
            print(f"Device: {gpu_info.get('device_name', 'Unknown')}")
            print(f"CuPy Version: {gpu_info.get('cupy_version', 'Unknown')}")
        else:
            print(f"Note: {gpu_info.get('error', 'GPU not available')}")

        print(f"\nRuns per configuration: {runs}")
        print("\n" + "-" * 80)
        print(f"{'Image Size':<15} {'Clusters':<10} {'CPU (ms)':<12} {'GPU (ms)':<12} {'Speedup':<10} {'Max Diff'}")
        print("-" * 80)

    for image_size, num_clusters in configs:
        result = run_benchmark(
            image_shape=image_size,
            num_clusters=num_clusters,
            warmup_runs=1,
            timed_runs=runs,
        )
        results.append(result)

        if verbose:
            size_str = f"{image_size[0]}x{image_size[1]}"
            print(f"{size_str:<15} {num_clusters:<10} {result.cpu_time_ms:<12.2f} {result.gpu_time_ms:<12.2f} {result.speedup:<10.2f}x {result.max_pixel_diff}")

    if verbose:
        print("-" * 80)

        # Summary statistics
        avg_speedup = np.mean([r.speedup for r in results])
        print(f"\nAverage speedup: {avg_speedup:.2f}x")
        print(f"Max pixel difference across all tests: {max(r.max_pixel_diff for r in results)}")

        # Note about GPU performance
        if not is_gpu_available():
            print("\nNote: GPU not available - GPU times show CPU fallback performance")
        else:
            print("\nNote: GPU renderer currently uses optimized CPU path internally")
            print("      (GPU transfer overhead exceeds benefit for local ROI operations)")

    return results


def save_results(results: List[BenchmarkResult], output_path: str):
    """Save benchmark results to JSON file."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "gpu_available": is_gpu_available(),
        "gpu_info": get_gpu_info(),
        "results": [
            {
                "image_size": list(r.image_size),
                "num_clusters": r.num_clusters,
                "cpu_time_ms": r.cpu_time_ms,
                "gpu_time_ms": r.gpu_time_ms,
                "speedup": r.speedup,
                "max_pixel_diff": r.max_pixel_diff,
                "memory_mb": r.memory_mb,
            }
            for r in results
        ],
    }

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nResults saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark GPU vs CPU flower renderer performance"
    )
    parser.add_argument(
        "--runs", type=int, default=3,
        help="Number of timed runs per configuration (default: 3)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output JSON file for results"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress verbose output"
    )

    args = parser.parse_args()

    results = run_all_benchmarks(
        runs=args.runs,
        verbose=not args.quiet,
    )

    if args.output:
        save_results(results, args.output)

    # Return success if all tests had acceptable pixel differences
    max_diff = max(r.max_pixel_diff for r in results)
    if max_diff > 1:
        print(f"\nWarning: Max pixel difference ({max_diff}) exceeds threshold (1)")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
