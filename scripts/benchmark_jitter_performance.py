"""Benchmark jitter performance overhead."""
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotmatrix.jitter import apply_position_jitter, apply_size_jitter
import random

def benchmark_jitter_operations(num_iterations=100000):
    """Measure jitter operation overhead."""
    
    print(f"Benchmarking jitter operations ({num_iterations:,} iterations)")
    print("=" * 60)
    
    # Test data
    x, y = 100.0, 100.0
    radius = 50.0
    seed = 42
    
    # Benchmark position jitter
    start = time.perf_counter()
    for i in range(num_iterations):
        apply_position_jitter(x, y, position_pct=25, base_radius=radius, seed=seed+i, algorithm='gaussian')
    elapsed_pos = time.perf_counter() - start
    
    # Benchmark size jitter
    start = time.perf_counter()
    for i in range(num_iterations):
        apply_size_jitter(radius, size_pct=20, seed=seed+i, algorithm='gaussian')
    elapsed_size = time.perf_counter() - start
    
    # Benchmark both together (typical usage)
    start = time.perf_counter()
    for i in range(num_iterations):
        apply_position_jitter(x, y, position_pct=25, base_radius=radius, seed=seed+i, algorithm='gaussian')
        apply_size_jitter(radius, size_pct=20, seed=seed+i, algorithm='gaussian')
    elapsed_both = time.perf_counter() - start
    
    # Results
    print(f"\nPosition jitter: {elapsed_pos:.3f}s ({elapsed_pos/num_iterations*1e6:.2f} µs/call)")
    print(f"Size jitter:     {elapsed_size:.3f}s ({elapsed_size/num_iterations*1e6:.2f} µs/call)")
    print(f"Both operations: {elapsed_both:.3f}s ({elapsed_both/num_iterations*1e6:.2f} µs/call)")
    
    # Estimate overhead for typical render
    clusters_1k = 1000
    clusters_10k = 10000
    clusters_100k = 100000
    
    overhead_1k = (elapsed_both / num_iterations) * clusters_1k
    overhead_10k = (elapsed_both / num_iterations) * clusters_10k
    overhead_100k = (elapsed_both / num_iterations) * clusters_100k
    
    print(f"\n{'Cluster Count':<15} {'Jitter Overhead':<20} {'% of 1s render':<20}")
    print("-" * 60)
    print(f"{clusters_1k:<15,} {overhead_1k*1000:.2f} ms{'':<15} {overhead_1k*100:.2f}%")
    print(f"{clusters_10k:<15,} {overhead_10k*1000:.2f} ms{'':<15} {overhead_10k*100:.2f}%")
    print(f"{clusters_100k:<15,} {overhead_100k:.2f} s{'':<16} {overhead_100k*100:.2f}%")
    
    print(f"\n{'Target:':<15} <5% overhead for typical 10k cluster render")
    if overhead_10k < 0.05:
        print(f"{'Result:':<15} ✓ PASS ({overhead_10k*100:.2f}% < 5%)")
    else:
        print(f"{'Result:':<15} ✗ FAIL ({overhead_10k*100:.2f}% >= 5%)")
    
    return {
        'position_us': elapsed_pos / num_iterations * 1e6,
        'size_us': elapsed_size / num_iterations * 1e6,
        'both_us': elapsed_both / num_iterations * 1e6,
        'overhead_10k_pct': overhead_10k * 100,
        'pass': overhead_10k < 0.05
    }

if __name__ == "__main__":
    results = benchmark_jitter_operations()
    print(f"\n{'='*60}")
    print("Benchmark complete!")
