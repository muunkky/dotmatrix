#!/usr/bin/env python3
"""Performance benchmark for large file handling.

This script establishes baseline performance metrics for DotMatrix
circle detection across various image sizes.

Part of spike w804xa: Large File Handling Performance Research
"""

import gc
import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional
import traceback

import cv2
import numpy as np
import psutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotmatrix.image_loader import load_image
from dotmatrix.circle_detector import detect_circles
from dotmatrix.convex_detector import detect_all_circles, PALETTES


@dataclass
class BenchmarkResult:
    """Result from a single benchmark run."""
    test_name: str
    image_size_mb: float
    resolution: str
    num_circles: int
    detection_method: str
    processing_time_s: float
    peak_memory_mb: float
    memory_delta_mb: float
    circles_detected: int
    success: bool
    error: Optional[str] = None


def get_memory_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def create_test_image(
    width: int,
    height: int,
    num_circles: int = 20,
    min_radius: int = 50,
    max_radius: int = 150
) -> np.ndarray:
    """Create a test image with random circles.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        num_circles: Number of circles to draw
        min_radius: Minimum circle radius
        max_radius: Maximum circle radius

    Returns:
        BGR image as numpy array
    """
    # White background
    image = np.full((height, width, 3), 255, dtype=np.uint8)

    # Define colors for circles
    colors = [
        (0, 0, 0),        # Black (BGR)
        (241, 193, 118),  # Cyan (BGR)
        (155, 93, 217),   # Magenta (BGR)
        (94, 206, 238),   # Yellow (BGR)
    ]

    np.random.seed(42)  # Reproducible

    for i in range(num_circles):
        # Random position (keep circles within bounds)
        r = np.random.randint(min_radius, max_radius + 1)
        x = np.random.randint(r, width - r)
        y = np.random.randint(r, height - r)

        # Cycle through colors
        color = colors[i % len(colors)]

        # Draw filled circle
        cv2.circle(image, (x, y), r, color, -1)

    return image


def estimate_file_size_mb(width: int, height: int, channels: int = 3) -> float:
    """Estimate PNG file size (rough approximation).

    PNG compression varies, but for test images with circles,
    we can estimate roughly 30-50% of raw size.
    """
    raw_size_mb = (width * height * channels) / (1024 * 1024)
    # Estimate 40% compression for typical test images
    return raw_size_mb * 0.4


def get_dimensions_for_size(target_mb: float) -> tuple:
    """Calculate image dimensions for approximate target file size."""
    # PNG with circles compresses to ~40% of raw
    # raw = width * height * 3 bytes
    # target_mb = raw * 0.4 / (1024*1024)
    # raw = target_mb * 1024 * 1024 / 0.4
    raw_bytes = target_mb * 1024 * 1024 / 0.4
    pixels = raw_bytes / 3
    side = int(np.sqrt(pixels))
    return (side, side)


def benchmark_detection(
    image: np.ndarray,
    method: str,
    min_radius: int = 50,
    max_radius: int = 200
) -> tuple:
    """Run circle detection and return (circles, time, memory).

    Args:
        image: BGR image array
        method: "hough" or "convex"
        min_radius: Minimum circle radius
        max_radius: Maximum circle radius

    Returns:
        Tuple of (circles_list, processing_time_seconds, peak_memory_mb)
    """
    gc.collect()
    mem_before = get_memory_mb()
    peak_memory = mem_before

    start_time = time.perf_counter()

    if method == "hough":
        circles = detect_circles(
            image,
            min_radius=min_radius,
            max_radius=max_radius,
            sensitivity="normal"
        )
        circles_list = [(c.center_x, c.center_y, c.radius) for c in circles]
    elif method == "convex":
        # Convert BGR to RGB for convex detector
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        circles, _ = detect_all_circles(
            rgb_image,
            PALETTES['cmyk'],
            min_radius=min_radius,
            max_radius=max_radius
        )
        circles_list = [(c.x, c.y, c.radius) for c in circles]
    else:
        raise ValueError(f"Unknown method: {method}")

    end_time = time.perf_counter()

    # Sample memory a few times during processing isn't possible
    # so we just measure before/after
    mem_after = get_memory_mb()
    peak_memory = max(peak_memory, mem_after)

    processing_time = end_time - start_time

    return circles_list, processing_time, peak_memory, mem_after - mem_before


def run_benchmark_suite() -> List[BenchmarkResult]:
    """Run full benchmark suite across various image sizes."""
    results = []

    # Define test configurations
    # Format: (target_mb, num_circles)
    test_configs = [
        (0.5, 10),   # Small - baseline
        (1, 20),     # 1 MB
        (2, 30),     # 2 MB
        (5, 50),     # 5 MB
        (10, 80),    # 10 MB - target
        (15, 100),   # 15 MB - stretch goal
        (20, 120),   # 20 MB - stress test
    ]

    methods = ["hough", "convex"]

    print("=" * 70)
    print("DotMatrix Large File Performance Benchmark")
    print("=" * 70)
    print()

    for target_mb, num_circles in test_configs:
        width, height = get_dimensions_for_size(target_mb)

        print(f"\n--- Testing ~{target_mb}MB ({width}x{height}) with {num_circles} circles ---")

        # Create test image
        print("  Creating test image...", end=" ", flush=True)
        try:
            image = create_test_image(
                width, height,
                num_circles=num_circles,
                min_radius=50,
                max_radius=min(150, min(width, height) // 10)
            )

            # Save to get actual file size
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                temp_path = f.name
            cv2.imwrite(temp_path, image)
            actual_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            os.unlink(temp_path)

            print(f"Done (actual: {actual_size_mb:.2f} MB)")
        except Exception as e:
            print(f"FAILED: {e}")
            continue

        # Test each method
        for method in methods:
            print(f"  Testing {method} detection...", end=" ", flush=True)

            try:
                circles, proc_time, peak_mem, mem_delta = benchmark_detection(
                    image, method,
                    min_radius=50,
                    max_radius=min(150, min(width, height) // 10)
                )

                result = BenchmarkResult(
                    test_name=f"{target_mb}MB_{method}",
                    image_size_mb=actual_size_mb,
                    resolution=f"{width}x{height}",
                    num_circles=num_circles,
                    detection_method=method,
                    processing_time_s=proc_time,
                    peak_memory_mb=peak_mem,
                    memory_delta_mb=mem_delta,
                    circles_detected=len(circles),
                    success=True
                )

                print(f"Done - {len(circles)} circles in {proc_time:.2f}s, "
                      f"peak mem: {peak_mem:.0f}MB (+{mem_delta:.0f}MB)")

            except MemoryError as e:
                result = BenchmarkResult(
                    test_name=f"{target_mb}MB_{method}",
                    image_size_mb=actual_size_mb,
                    resolution=f"{width}x{height}",
                    num_circles=num_circles,
                    detection_method=method,
                    processing_time_s=0,
                    peak_memory_mb=0,
                    memory_delta_mb=0,
                    circles_detected=0,
                    success=False,
                    error=f"MemoryError: {e}"
                )
                print(f"MEMORY ERROR: {e}")

            except Exception as e:
                result = BenchmarkResult(
                    test_name=f"{target_mb}MB_{method}",
                    image_size_mb=actual_size_mb,
                    resolution=f"{width}x{height}",
                    num_circles=num_circles,
                    detection_method=method,
                    processing_time_s=0,
                    peak_memory_mb=0,
                    memory_delta_mb=0,
                    circles_detected=0,
                    success=False,
                    error=f"{type(e).__name__}: {e}"
                )
                print(f"ERROR: {e}")
                traceback.print_exc()

            results.append(result)
            gc.collect()

    return results


def print_summary(results: List[BenchmarkResult]):
    """Print a summary table of benchmark results."""
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    print(f"\n{'Test Name':<20} {'Size':<10} {'Method':<10} {'Time(s)':<10} "
          f"{'Memory(MB)':<12} {'Detected':<10} {'Status':<10}")
    print("-" * 92)

    for r in results:
        status = "OK" if r.success else "FAILED"
        print(f"{r.test_name:<20} {r.image_size_mb:<10.2f} {r.detection_method:<10} "
              f"{r.processing_time_s:<10.2f} {r.peak_memory_mb:<12.0f} "
              f"{r.circles_detected:<10} {status:<10}")

    # Summary statistics
    print("\n" + "-" * 70)
    print("KEY FINDINGS:")

    successful = [r for r in results if r.success]
    if successful:
        # Find threshold where processing exceeds 30s
        slow_results = [r for r in successful if r.processing_time_s > 30]
        if slow_results:
            threshold = min(r.image_size_mb for r in slow_results)
            print(f"  - Processing time exceeds 30s at ~{threshold:.1f}MB")
        else:
            max_tested = max(r.image_size_mb for r in successful)
            print(f"  - All sizes up to {max_tested:.1f}MB completed in <30s")

        # Memory trends
        max_mem = max(r.peak_memory_mb for r in successful)
        print(f"  - Peak memory usage: {max_mem:.0f}MB")

        # Method comparison
        hough_times = [r.processing_time_s for r in successful if r.detection_method == "hough"]
        convex_times = [r.processing_time_s for r in successful if r.detection_method == "convex"]
        if hough_times and convex_times:
            avg_hough = sum(hough_times) / len(hough_times)
            avg_convex = sum(convex_times) / len(convex_times)
            faster = "hough" if avg_hough < avg_convex else "convex"
            ratio = max(avg_hough, avg_convex) / min(avg_hough, avg_convex)
            print(f"  - {faster} is {ratio:.1f}x faster on average")

    # Failures
    failures = [r for r in results if not r.success]
    if failures:
        print(f"\n  FAILURES ({len(failures)}):")
        for r in failures:
            print(f"    - {r.test_name}: {r.error}")


def save_results(results: List[BenchmarkResult], output_path: Path):
    """Save benchmark results to JSON file."""
    data = {
        "benchmark_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system_info": {
            "total_memory_mb": psutil.virtual_memory().total / (1024 * 1024),
            "available_memory_mb": psutil.virtual_memory().available / (1024 * 1024),
            "cpu_count": psutil.cpu_count(),
        },
        "results": [asdict(r) for r in results]
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\nResults saved to: {output_path}")


def main():
    """Run benchmarks and save results."""
    print("Starting Large File Performance Benchmark")
    print(f"System Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    print(f"Available Memory: {psutil.virtual_memory().available / (1024**3):.1f} GB")
    print()

    results = run_benchmark_suite()
    print_summary(results)

    # Save results
    output_dir = Path(__file__).parent
    output_dir.mkdir(exist_ok=True)
    save_results(results, output_dir / "benchmark_results.json")

    return results


if __name__ == "__main__":
    main()
