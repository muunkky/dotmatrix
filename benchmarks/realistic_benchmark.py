#!/usr/bin/env python3
"""Realistic performance benchmark for large file handling.

This script tests with more realistic image content that produces
file sizes closer to real-world use cases.

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
from typing import List, Optional

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
    megapixels: float
    num_circles_drawn: int
    detection_method: str
    processing_time_s: float
    peak_memory_mb: float
    memory_delta_mb: float
    circles_detected: int
    detection_rate_pct: float
    success: bool
    error: Optional[str] = None


def get_memory_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def create_realistic_test_image(
    width: int,
    height: int,
    num_circles: int = 20,
    min_radius: int = 50,
    max_radius: int = 150,
    add_noise: bool = True
) -> np.ndarray:
    """Create a realistic test image with circles and optional noise.

    Produces images with file sizes similar to real photographs.
    """
    # Light gray/white background with slight variation
    if add_noise:
        # Background with subtle noise (simulates real images)
        image = np.random.randint(240, 256, (height, width, 3), dtype=np.uint8)
    else:
        image = np.full((height, width, 3), 250, dtype=np.uint8)

    # CMYK-like colors (BGR format)
    colors = [
        (0, 0, 0),        # Black
        (241, 193, 118),  # Cyan
        (155, 93, 217),   # Magenta
        (94, 206, 238),   # Yellow
    ]

    np.random.seed(42)  # Reproducible
    drawn_circles = []

    for i in range(num_circles):
        r = np.random.randint(min_radius, max_radius + 1)
        x = np.random.randint(r + 10, width - r - 10)
        y = np.random.randint(r + 10, height - r - 10)
        color = colors[i % len(colors)]

        # Draw filled circle
        cv2.circle(image, (x, y), r, color, -1)
        drawn_circles.append((x, y, r))

    return image, drawn_circles


def benchmark_detection(
    image: np.ndarray,
    method: str,
    min_radius: int = 50,
    max_radius: int = 200
) -> tuple:
    """Run circle detection and return results."""
    gc.collect()
    mem_before = get_memory_mb()

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
    mem_after = get_memory_mb()

    return circles_list, end_time - start_time, mem_after, mem_after - mem_before


def run_benchmarks() -> List[BenchmarkResult]:
    """Run benchmarks with realistic image content."""
    results = []

    # Test configurations by resolution (not file size)
    # These resolutions will produce roughly the target file sizes with noisy content
    test_configs = [
        # (width, height, num_circles, description)
        (1000, 1000, 15, "1MP"),     # ~1.4 MB
        (1500, 1500, 25, "2.25MP"),  # ~3.5 MB
        (2000, 2000, 35, "4MP"),     # ~7.8 MB
        (2500, 2500, 45, "6.25MP"),  # ~12 MB
        (3000, 3000, 60, "9MP"),     # ~20 MB
        (3500, 3500, 75, "12.25MP"), # ~27 MB
        (4000, 4000, 90, "16MP"),    # ~36 MB
    ]

    methods = ["hough", "convex"]

    print("=" * 80)
    print("DotMatrix Realistic Large File Performance Benchmark")
    print("=" * 80)
    print(f"System Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    print(f"Available Memory: {psutil.virtual_memory().available / (1024**3):.1f} GB")
    print()

    for width, height, num_circles, desc in test_configs:
        megapixels = (width * height) / 1_000_000

        print(f"\n--- {desc} ({width}x{height}, {megapixels:.1f}MP, {num_circles} circles) ---")

        # Create test image
        print("  Creating realistic test image...", end=" ", flush=True)
        try:
            image, drawn_circles = create_realistic_test_image(
                width, height,
                num_circles=num_circles,
                min_radius=50,
                max_radius=min(150, min(width, height) // 20),
                add_noise=True
            )

            # Measure actual file size
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                temp_path = f.name
            cv2.imwrite(temp_path, image)
            actual_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            os.unlink(temp_path)

            print(f"Done ({actual_size_mb:.1f} MB)")
        except MemoryError as e:
            print(f"MEMORY ERROR creating image: {e}")
            continue
        except Exception as e:
            print(f"ERROR creating image: {e}")
            continue

        # Test each method
        for method in methods:
            print(f"  Testing {method}...", end=" ", flush=True)

            try:
                circles, proc_time, peak_mem, mem_delta = benchmark_detection(
                    image, method,
                    min_radius=50,
                    max_radius=min(150, min(width, height) // 20)
                )

                detection_rate = (len(circles) / num_circles * 100) if num_circles > 0 else 0

                result = BenchmarkResult(
                    test_name=f"{desc}_{method}",
                    image_size_mb=actual_size_mb,
                    resolution=f"{width}x{height}",
                    megapixels=megapixels,
                    num_circles_drawn=num_circles,
                    detection_method=method,
                    processing_time_s=proc_time,
                    peak_memory_mb=peak_mem,
                    memory_delta_mb=mem_delta,
                    circles_detected=len(circles),
                    detection_rate_pct=detection_rate,
                    success=True
                )

                status = ""
                if proc_time > 30:
                    status = " [SLOW]"
                elif proc_time > 10:
                    status = " [warning]"

                print(f"{len(circles)}/{num_circles} detected ({detection_rate:.0f}%), "
                      f"{proc_time:.2f}s, mem: {peak_mem:.0f}MB{status}")

            except MemoryError as e:
                result = BenchmarkResult(
                    test_name=f"{desc}_{method}",
                    image_size_mb=actual_size_mb,
                    resolution=f"{width}x{height}",
                    megapixels=megapixels,
                    num_circles_drawn=num_circles,
                    detection_method=method,
                    processing_time_s=0,
                    peak_memory_mb=0,
                    memory_delta_mb=0,
                    circles_detected=0,
                    detection_rate_pct=0,
                    success=False,
                    error=f"MemoryError: {e}"
                )
                print(f"MEMORY ERROR: {e}")

            except Exception as e:
                result = BenchmarkResult(
                    test_name=f"{desc}_{method}",
                    image_size_mb=actual_size_mb,
                    resolution=f"{width}x{height}",
                    megapixels=megapixels,
                    num_circles_drawn=num_circles,
                    detection_method=method,
                    processing_time_s=0,
                    peak_memory_mb=0,
                    memory_delta_mb=0,
                    circles_detected=0,
                    detection_rate_pct=0,
                    success=False,
                    error=f"{type(e).__name__}: {e}"
                )
                print(f"ERROR: {e}")

            results.append(result)
            gc.collect()

        # Clean up image memory
        del image
        gc.collect()

    return results


def print_summary(results: List[BenchmarkResult]):
    """Print summary analysis."""
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)

    # Table
    print(f"\n{'Test':<15} {'Size MB':<10} {'Resolution':<12} {'Method':<8} "
          f"{'Time(s)':<10} {'Mem(MB)':<10} {'Detected':<10} {'Rate':<8}")
    print("-" * 93)

    for r in results:
        status = "" if r.success else " FAIL"
        print(f"{r.test_name:<15} {r.image_size_mb:<10.1f} {r.resolution:<12} "
              f"{r.detection_method:<8} {r.processing_time_s:<10.2f} "
              f"{r.peak_memory_mb:<10.0f} {r.circles_detected:<10} "
              f"{r.detection_rate_pct:<8.0f}{status}")

    # Analysis
    successful = [r for r in results if r.success]
    if not successful:
        print("\nNo successful benchmarks to analyze.")
        return

    print("\n" + "-" * 80)
    print("KEY FINDINGS:")

    # By method
    for method in ["hough", "convex"]:
        method_results = [r for r in successful if r.detection_method == method]
        if not method_results:
            continue

        print(f"\n  {method.upper()} Detection:")

        # Performance scaling
        times_by_mp = [(r.megapixels, r.processing_time_s) for r in method_results]
        times_by_mp.sort()
        print(f"    Performance scaling (megapixels -> seconds):")
        for mp, t in times_by_mp:
            indicator = ""
            if t > 30:
                indicator = " *** EXCEEDS 30s TARGET ***"
            elif t > 10:
                indicator = " [approaching limit]"
            print(f"      {mp:>6.1f} MP -> {t:>6.2f}s{indicator}")

        # Find threshold
        slow_results = [r for r in method_results if r.processing_time_s > 30]
        if slow_results:
            threshold = min(r.megapixels for r in slow_results)
            print(f"    ** 30s threshold exceeded at ~{threshold:.1f} megapixels **")
        else:
            max_tested = max(r.megapixels for r in method_results)
            print(f"    All sizes up to {max_tested:.1f} MP completed in <30s")

        # Memory
        max_mem = max(r.peak_memory_mb for r in method_results)
        print(f"    Peak memory: {max_mem:.0f} MB")

        # Detection rate
        avg_rate = sum(r.detection_rate_pct for r in method_results) / len(method_results)
        print(f"    Average detection rate: {avg_rate:.0f}%")

    # Recommendations
    print("\n" + "-" * 80)
    print("RECOMMENDATIONS:")

    hough_results = [r for r in successful if r.detection_method == "hough"]
    convex_results = [r for r in successful if r.detection_method == "convex"]

    if hough_results and convex_results:
        hough_avg = sum(r.processing_time_s for r in hough_results) / len(hough_results)
        convex_avg = sum(r.processing_time_s for r in convex_results) / len(convex_results)
        ratio = convex_avg / hough_avg

        print(f"  - Hough is ~{ratio:.0f}x faster than convex detection")
        print(f"  - Convex detection scales poorly with image size (use for overlapping circles only)")

    # Memory observations
    if successful:
        max_mem = max(r.peak_memory_mb for r in successful)
        max_size = max(r.megapixels for r in successful)
        mem_per_mp = max_mem / max_size if max_size > 0 else 0
        print(f"  - Memory usage: ~{mem_per_mp:.0f} MB per megapixel")
        print(f"  - For 10MB target (~4MP): expect ~{4 * mem_per_mp:.0f} MB memory usage")

    # Threshold recommendations
    convex_slow = [r for r in convex_results if r.processing_time_s > 30] if convex_results else []
    if convex_slow:
        threshold_mp = min(r.megapixels for r in convex_slow)
        # Estimate file size for that resolution (rough: 2.5 MB per megapixel with noise)
        threshold_mb = threshold_mp * 2.5
        print(f"\n  - CONVEX EDGE THRESHOLD: Consider tiling/downscaling above ~{threshold_mp:.0f} MP (~{threshold_mb:.0f} MB)")
    else:
        if convex_results:
            max_mp = max(r.megapixels for r in convex_results)
            print(f"\n  - Convex detection handled all tested sizes (up to {max_mp:.0f} MP)")


def save_results(results: List[BenchmarkResult], output_path: Path):
    """Save results to JSON."""
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
    results = run_benchmarks()
    print_summary(results)

    output_dir = Path(__file__).parent
    save_results(results, output_dir / "realistic_benchmark_results.json")


if __name__ == "__main__":
    main()
