"""GPU-accelerated flower renderer for dotmatrix.

This module provides GPU-accelerated rendering using CuPy for CUDA-enabled systems.
Falls back gracefully to CPU implementation when GPU is unavailable.

The GPU acceleration targets Phase 1c of render_flower_global_blend() - the petal
radius optimization loop which is the primary bottleneck (7 radius tests x 3 colors
x N clusters).

Strategy:
- Upload global_black_mask to GPU once
- Batch all petal position/radius combinations across all clusters
- Use CuPy vectorized operations for exposed pixel counting
- Transfer optimized radii back to CPU for Phase 2-4

Performance:
- CPU: O(clusters * colors * radius_tests * roi_size) - sequential
- GPU: O(batch_size * roi_size) with parallelism - ~5-20x speedup
"""

import math
import random
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Callable

import numpy as np
import cv2

from dotmatrix.gpu import is_gpu_available, get_array_module, to_gpu, to_cpu, synchronize
from dotmatrix.cluster_pixel_counter import ClusterResult
from dotmatrix.colors import COLORS_BGR, PETAL_ANGLES
from dotmatrix.circle_renderer import (
    radius_from_pixels,
    radius_for_exposed_pixels,
    find_best_radius_for_pixels,
    compute_cluster_rotation,
)


def _batch_count_exposed_pixels_gpu(
    global_black_mask: np.ndarray,
    petal_tests: List[Tuple[float, float, int, int, int]],  # (px, py, radius, cluster_idx, color_idx)
    target_pixels: List[int],
) -> List[Tuple[int, int, int, int]]:
    """Count exposed pixels for a batch of petal tests using GPU parallelism.

    Uses a custom CUDA kernel to process ALL tests in parallel - one thread per test.
    For 15K+ clusters with ~330K total tests, this provides 10-50x speedup.

    Args:
        global_black_mask: Boolean mask (H, W) of global black coverage
        petal_tests: List of (petal_x, petal_y, test_radius, cluster_idx, color_idx)
        target_pixels: List of target pixel counts (same length as petal_tests)

    Returns:
        List of (best_radius, best_exposed, cluster_idx, color_idx) for each unique key
    """
    try:
        import cupy as cp
    except ImportError:
        return _batch_count_exposed_pixels_cpu(global_black_mask, petal_tests, target_pixels)

    if len(petal_tests) == 0:
        return []

    out_h, out_w = global_black_mask.shape
    n_tests = len(petal_tests)

    # CUDA kernel that counts exposed pixels for each test
    # Each thread handles one test - true parallelism
    # Note: Uses (r + 0.5)^2 to approximate cv2.circle with LINE_AA pixel counting
    count_kernel = cp.RawKernel(r'''
    extern "C" __global__
    void count_exposed_pixels(
        const bool* black_mask,
        const float* px_arr, const float* py_arr,
        const int* radius_arr,
        int* exposed_counts,
        int n_tests, int width, int height
    ) {
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= n_tests) return;

        float px = px_arr[idx];
        float py = py_arr[idx];
        int radius = radius_arr[idx];

        if (radius <= 0) {
            exposed_counts[idx] = 0;
            return;
        }

        // ROI bounds
        int margin = radius + 2;
        int x1 = max(0, (int)px - margin);
        int y1 = max(0, (int)py - margin);
        int x2 = min(width, (int)px + margin + 1);
        int y2 = min(height, (int)py + margin + 1);

        // Use (r + 0.5)^2 to match cv2.circle LINE_AA pixel counting behavior
        // cv2.circle with anti-aliasing fills ~20-30% more pixels than pure r^2
        float effective_r = radius + 0.5f;
        float radius_sq = effective_r * effective_r;
        int count = 0;

        // Count pixels in circle that are not black
        for (int y = y1; y < y2; y++) {
            for (int x = x1; x < x2; x++) {
                float dx = x - px;
                float dy = y - py;
                float dist_sq = dx * dx + dy * dy;

                // Within circle AND not in black mask
                if (dist_sq <= radius_sq && !black_mask[y * width + x]) {
                    count++;
                }
            }
        }

        exposed_counts[idx] = count;
    }
    ''', 'count_exposed_pixels')

    # Upload data to GPU
    black_mask_gpu = cp.asarray(global_black_mask.astype(np.bool_))

    # Convert test parameters to arrays
    tests_array = np.array(petal_tests, dtype=np.float32)
    px_gpu = cp.asarray(tests_array[:, 0].astype(np.float32))
    py_gpu = cp.asarray(tests_array[:, 1].astype(np.float32))
    radius_gpu = cp.asarray(tests_array[:, 2].astype(np.int32))
    exposed_gpu = cp.zeros(n_tests, dtype=cp.int32)

    # Launch kernel - one thread per test
    block_size = 256
    grid_size = (n_tests + block_size - 1) // block_size

    count_kernel(
        (grid_size,), (block_size,),
        (black_mask_gpu, px_gpu, py_gpu, radius_gpu, exposed_gpu,
         n_tests, out_w, out_h)
    )

    # Copy results back
    exposed_counts = cp.asnumpy(exposed_gpu)

    # Find best radius for each (cluster_idx, color_idx) pair
    results = {}
    for i, (px, py, radius, cluster_idx, color_idx) in enumerate(petal_tests):
        key = (int(cluster_idx), int(color_idx))
        target = target_pixels[i]
        exposed = int(exposed_counts[i])
        err = abs(exposed - target)

        if key not in results or err < results[key][2]:
            results[key] = (int(radius), exposed, err)

    output = []
    for (cluster_idx, color_idx), (best_r, best_exp, _) in results.items():
        output.append((best_r, best_exp, cluster_idx, color_idx))

    return output


def _batch_count_exposed_pixels_cpu(
    global_black_mask: np.ndarray,
    petal_tests: List[Tuple[float, float, int, int, int]],
    target_pixels: List[int],
) -> List[Tuple[int, int, int, int]]:
    """CPU fallback for batch exposed pixel counting.

    Uses same distance-squared algorithm as GPU for exact consistency.
    The actual circle rendering (Phase 2-4) still uses cv2.circle with anti-aliasing.
    """
    out_h, out_w = global_black_mask.shape
    results = {}

    for i, (px, py, radius, cluster_idx, color_idx) in enumerate(petal_tests):
        target = target_pixels[i]
        key = (cluster_idx, color_idx)

        if radius <= 0:
            exposed = 0
        else:
            int_r = int(radius)
            margin = int_r + 2

            x1 = max(0, int(px) - margin)
            y1 = max(0, int(py) - margin)
            x2 = min(out_w, int(px) + margin + 1)
            y2 = min(out_h, int(py) + margin + 1)

            if x1 >= x2 or y1 >= y2:
                exposed = 0
            else:
                # Use (r + 0.5)^2 to match cv2.circle LINE_AA behavior (GPU consistency)
                effective_r = int_r + 0.5
                radius_sq = effective_r * effective_r
                local_black = global_black_mask[y1:y2, x1:x2]

                # Create coordinate grids
                y_coords, x_coords = np.ogrid[y1:y2, x1:x2]
                dx = x_coords - px
                dy = y_coords - py
                dist_sq = dx * dx + dy * dy

                # Count: inside circle AND not black
                in_circle = dist_sq <= radius_sq
                exposed = int(np.sum(in_circle & ~local_black))

        err = abs(exposed - target)
        if key not in results or err < results[key][2]:
            results[key] = (radius, exposed, err)

    output = []
    for (cluster_idx, color_idx), (best_r, best_exp, _) in results.items():
        output.append((best_r, best_exp, cluster_idx, color_idx))

    return output


def _apply_drift_compensation(
    cluster_data: List[Dict[str, Any]],
    cyan_circles: List[Tuple[float, float, float]],
    magenta_circles: List[Tuple[float, float, float]],
    yellow_circles: List[Tuple[float, float, float]],
    black_circles: List[Tuple[float, float, float]],
    image_shape: Tuple[int, int],
    jitter_position: int,
    jitter_size: int,
    jitter_seed: Optional[int],
    jitter_algorithm: str,
    drift_tolerance: float,
    max_iterations: int,
    max_step_size: Optional[float] = None,
) -> Tuple[List[Tuple[float, float, float]], List[Tuple[float, float, float]], List[Tuple[float, float, float]]]:
    """Apply drift-balanced jitter with iterative size compensation.
    
    Strategy:
    1. Apply jitter to positions
    2. For each cluster, measure actual color mass per petal (render in isolation)
    3. Compare to target masses, adjust sizes
    4. Iterate until balanced or max iterations reached
    
    Args:
        cluster_data: List of cluster metadata dicts from Phase 1a
        cyan_circles, magenta_circles, yellow_circles: Initial circle lists (x, y, r)
        black_circles: Black circle list for overlap calculation
        image_shape: (height, width) for rendering
        jitter_position: Position jitter strength (percentage)
        jitter_size: Size jitter strength (percentage)
        jitter_seed: Random seed
        jitter_algorithm: 'gaussian' or 'uniform'
        drift_tolerance: Acceptable deviation from target mass (0.0-1.0)
        max_iterations: Maximum balancing iterations
        max_step_size: Optional maximum scale_factor per iteration (e.g., 2.0 = max 2x growth/shrink)
    
    Returns:
        Tuple of (cyan_circles, magenta_circles, yellow_circles) with adjusted sizes
    """
    h, w = image_shape
    
    # Build petal-to-cluster mapping (track which circles belong to which cluster)
    # Each cluster has 3 petals (cyan, magenta, yellow) at specific indices
    cluster_petal_map = []  # List of (cluster_idx, color, petal_idx_in_color_list)
    cyan_idx, magenta_idx, yellow_idx = 0, 0, 0
    
    for cluster_idx, data in enumerate(cluster_data):
        decomposed_counts = data['decomposed_counts']
        cluster_petals = {}
        
        if decomposed_counts['cyan'] > 0:
            cluster_petals['cyan'] = (cyan_idx, decomposed_counts['cyan'])
            cyan_idx += 1
        if decomposed_counts['magenta'] > 0:
            cluster_petals['magenta'] = (magenta_idx, decomposed_counts['magenta'])
            magenta_idx += 1
        if decomposed_counts['yellow'] > 0:
            cluster_petals['yellow'] = (yellow_idx, decomposed_counts['yellow'])
            yellow_idx += 1
        
        cluster_petal_map.append(cluster_petals)
    
    # Convert circle lists to mutable lists for adjustment
    cyan_circles = list(cyan_circles)
    magenta_circles = list(magenta_circles)
    yellow_circles = list(yellow_circles)
    
    # Initialize RNG for jitter
    if jitter_seed is not None:
        random.seed(jitter_seed)
    
    # Iteration 0: Apply jitter to positions and sizes
    def apply_jitter_to_list(circles, color_offset):
        """Apply jitter to position and size."""
        jittered = []
        if jitter_seed is not None:
            random.seed(jitter_seed + color_offset)
        
        for cx, cy, r in circles:
            # Position jitter
            if jitter_position > 0:
                jitter_amount = r * (jitter_position / 100.0)
                if jitter_algorithm == 'gaussian':
                    dx = random.gauss(0, jitter_amount / 2.0)
                    dy = random.gauss(0, jitter_amount / 2.0)
                else:
                    dx = random.uniform(-jitter_amount, jitter_amount)
                    dy = random.uniform(-jitter_amount, jitter_amount)
                cx += dx
                cy += dy
            
            # Size jitter
            if jitter_size > 0:
                jitter_amount = r * (jitter_size / 100.0)
                if jitter_algorithm == 'gaussian':
                    dr = random.gauss(0, jitter_amount / 2.0)
                else:
                    dr = random.uniform(-jitter_amount, jitter_amount)
                r = max(1, r + dr)
            
            jittered.append((cx, cy, r))
        return jittered
    
    cyan_circles = apply_jitter_to_list(cyan_circles, 100)
    magenta_circles = apply_jitter_to_list(magenta_circles, 200)
    yellow_circles = apply_jitter_to_list(yellow_circles, 300)
    
    # Iterate to balance
    for iteration in range(max_iterations):
        all_balanced = True
        
        # For each cluster, measure actual masses and adjust
        for cluster_idx, cluster_petals in enumerate(cluster_petal_map):
            if not cluster_petals:
                continue
            
            # Get cluster's black circle for occlusion
            cx_cluster, cy_cluster, black_r = black_circles[cluster_idx] if cluster_idx < len(black_circles) else (0, 0, 0)
            
            # Measure actual color masses for this cluster's petals
            for color in ['cyan', 'magenta', 'yellow']:
                if color not in cluster_petals:
                    continue
                
                petal_idx, target_pixels = cluster_petals[color]
                
                # Get current circle
                if color == 'cyan':
                    cx, cy, r = cyan_circles[petal_idx]
                elif color == 'magenta':
                    cx, cy, r = magenta_circles[petal_idx]
                else:  # yellow
                    cx, cy, r = yellow_circles[petal_idx]
                
                # Measure actual mass (cluster-local rendering - option B)
                actual_pixels = _measure_cluster_local_mass(cx, cy, r, black_r, cx_cluster, cy_cluster, h, w)
                
                # Skip if measurement failed or is too small to trust
                if actual_pixels < 5:
                    continue
                
                # Calculate deviation
                deviation = (actual_pixels - target_pixels) / target_pixels if target_pixels > 0 else 0
                
                if abs(deviation) > drift_tolerance:
                    all_balanced = False
                    
                    # Adjust size to compensate
                    # If actual > target (too much mass), shrink
                    # If actual < target (too little mass), grow
                    scale_factor = math.sqrt(target_pixels / actual_pixels) if actual_pixels > 0 else 1.0
                    
                    # Optionally clamp scale_factor if max_step_size specified
                    if max_step_size is not None:
                        scale_factor = max(1.0 / max_step_size, min(max_step_size, scale_factor))
                    
                    new_r = max(1, r * scale_factor)
                    
                    # Update circle
                    if color == 'cyan':
                        cyan_circles[petal_idx] = (cx, cy, new_r)
                    elif color == 'magenta':
                        magenta_circles[petal_idx] = (cx, cy, new_r)
                    else:  # yellow
                        yellow_circles[petal_idx] = (cx, cy, new_r)
        
        if all_balanced:
            break
    
    return cyan_circles, magenta_circles, yellow_circles


def _measure_cluster_local_mass(
    petal_x: float,
    petal_y: float,
    petal_r: float,
    black_r: float,
    black_x: float,
    black_y: float,
    h: int,
    w: int,
) -> int:
    """Measure actual pixel mass for a petal in cluster-local rendering (option B).
    
    Renders just the petal and its cluster's black circle in isolation,
    counts exposed pixels (petal - black overlap).
    
    Args:
        petal_x, petal_y, petal_r: Petal circle parameters
        black_r, black_x, black_y: Black circle parameters
        h, w: Canvas dimensions
    
    Returns:
        Number of exposed pixels
    """
    # Create local mask for this petal
    petal_mask = np.zeros((h, w), dtype=np.uint8)
    if petal_r > 0:
        cv2.circle(petal_mask, (int(petal_x), int(petal_y)), int(petal_r),
                  255, thickness=-1, lineType=cv2.LINE_AA)
    
    # Create local mask for black (if exists)
    if black_r > 0:
        black_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(black_mask, (int(black_x), int(black_y)), int(black_r),
                  255, thickness=-1, lineType=cv2.LINE_AA)
        # Subtract black from petal
        exposed = petal_mask & ~(black_mask > 0)
    else:
        exposed = petal_mask > 0
    
    return np.count_nonzero(exposed)


def render_flower_global_blend_gpu(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    petal_distance: float = 0.35,
    scale: int = 1,
    skip_partial: bool = False,
    rotation_mode: str = 'fixed',
    base_rotation: float = 0.0,
    rotation_seed: Optional[int] = None,
    use_gpu: bool = True,
    progress_callback: Optional[Callable[[int, int, str, Optional[dict]], None]] = None,
    jitter_position: int = 0,
    jitter_size: int = 0,
    jitter_seed: Optional[int] = None,
    jitter_algorithm: str = 'gaussian',
    jitter_exclude: str = '',
    drift: bool = False,
    drift_tolerance: float = 0.2,
    drift_max_iterations: int = 10,
    drift_max_step: float = 2.0,
    jitter_steps: int = 1,
    target_image: Optional[Path] = None,
    target_weight: float = 0.5,
) -> np.ndarray:
    """GPU-accelerated global CMY blending flower renderer.

    Drop-in replacement for render_flower_global_blend() with GPU acceleration
    for the radius optimization phase (Phase 1c).

    Args:
        clusters: List of ClusterResult from detection
        image_shape: (height, width) of original image
        petal_distance: Fraction of black radius for petal center placement
        scale: Output scale factor
        skip_partial: If True, skip edge clusters
        rotation_mode: 'fixed', 'random', or 'cluster-hash'
        base_rotation: Base angle offset in degrees
        rotation_seed: Random seed for 'random' mode
        use_gpu: If True and GPU available, use GPU acceleration
        progress_callback: Optional callback function for progress updates.
            Called with (current, total, phase_name, metadata) where:
            - current: Current progress count
            - total: Total count for this phase
            - phase_name: String describing current phase (e.g., 'petal_optimization')
            - metadata: Optional dict with additional info (e.g., 'gpu': True/False)
        jitter_position: Position jitter strength (percentage of radius)
        jitter_size: Size jitter strength (percentage of radius)
        jitter_seed: Random seed for reproducible jitter
        jitter_algorithm: 'gaussian' or 'uniform' distribution
        drift: If True, enable drift-balanced jitter (size compensation for color balance)
        drift_tolerance: Tolerance for color mass deviation (0.0-1.0, default 0.2)

    Returns:
        BGR numpy array with globally blended flowers
    """
    h, w = image_shape
    out_h, out_w = h * scale, w * scale

    gpu_available = is_gpu_available() and use_gpu

    # Phase 1a: Collect all BLACK geometry first
    black_circles = []
    cluster_data = []

    for cluster in clusters:
        if skip_partial and cluster.partial:
            continue

        cx = cluster.x * scale
        cy = cluster.y * scale

        rotation = compute_cluster_rotation(
            cluster.x, cluster.y,
            mode=rotation_mode,
            base_rotation=base_rotation,
            seed=rotation_seed
        )

        black_radius = radius_from_pixels(cluster.black)
        if cluster.black > 0 and black_radius > 0:
            black_circles.append((cx, cy, black_radius))

        # CMYK Decomposition
        decomposed_counts = {
            'cyan': cluster.cyan + cluster.green + cluster.blue,
            'magenta': cluster.magenta + cluster.red + cluster.blue,
            'yellow': cluster.yellow + cluster.red + cluster.green,
        }

        cluster_data.append({
            'cx': cx, 'cy': cy,
            'black_radius': black_radius,
            'rotation': rotation,
            'decomposed_counts': decomposed_counts,
        })

    # Phase 1b: Build GLOBAL black mask
    def build_global_black_mask(circle_list):
        """Build a boolean mask of all black circles for exposed pixel calculations.

        Creates a mask where pixels covered by any black circle are True.
        Uses integer radius rounding for efficiency since exact pixel count
        is not critical for exposed area calculations.

        Args:
            circle_list: List of (center_x, center_y, radius) tuples

        Returns:
            Boolean numpy array (out_h, out_w) where True = black coverage
        """
        mask = np.zeros((out_h, out_w), dtype=np.uint8)
        for cx, cy, r in circle_list:
            if r > 0:
                int_r = max(1, int(round(r)))
                cv2.circle(mask, (int(cx), int(cy)), int_r,
                          255, thickness=-1, lineType=cv2.LINE_AA)
        return mask > 0

    global_black_mask = build_global_black_mask(black_circles)

    # Phase 1c: Optimize petal radii - GPU ACCELERATED
    cyan_circles = []
    magenta_circles = []
    yellow_circles = []

    color_indices = {'cyan': 0, 'magenta': 1, 'yellow': 2}

    if gpu_available:
        # GPU path: Batch all petal tests
        total_clusters = len(cluster_data)
        if progress_callback:
            progress_callback(0, total_clusters, 'petal_optimization', {'gpu': True, 'percentage': 0})
        else:
            print(f"    Phase 1c: Using GPU acceleration for {total_clusters} clusters", flush=True)

        # Build batch of all petal tests
        petal_tests = []  # (px, py, test_radius, cluster_idx, color_idx)
        target_pixels_list = []
        petal_info = []  # (cluster_idx, color, petal_x, petal_y, pixel_count)

        for cluster_idx, data in enumerate(cluster_data):
            cx, cy = data['cx'], data['cy']
            black_radius = data['black_radius']
            rotation = data['rotation']
            decomposed_counts = data['decomposed_counts']

            for color in ['cyan', 'magenta', 'yellow']:
                pixel_count = decomposed_counts[color]
                if pixel_count <= 0:
                    continue

                preliminary_radius = radius_from_pixels(pixel_count)
                if preliminary_radius <= 0:
                    continue

                angle_deg = PETAL_ANGLES[color] + rotation
                angle_rad = math.radians(angle_deg - 90)
                dist = black_radius * petal_distance

                if black_radius > 0 and dist < black_radius + preliminary_radius:
                    theoretical_r = radius_for_exposed_pixels(pixel_count, black_radius, dist)
                else:
                    theoretical_r = preliminary_radius

                if theoretical_r <= 0:
                    continue

                petal_x = cx + dist * math.cos(angle_rad)
                petal_y = cy + dist * math.sin(angle_rad)

                # Store petal info for later
                petal_info.append((cluster_idx, color, petal_x, petal_y, pixel_count))

                # Add all radius tests for this petal
                for test_r in range(max(1, int(theoretical_r) - 3), int(theoretical_r) + 4):
                    petal_tests.append((petal_x, petal_y, test_r, cluster_idx, color_indices[color]))
                    target_pixels_list.append(pixel_count)

        # Run GPU batch processing
        results = _batch_count_exposed_pixels_gpu(
            global_black_mask, petal_tests, target_pixels_list
        )

        # Build result lookup
        result_lookup = {}
        for best_r, best_exp, cluster_idx, color_idx in results:
            result_lookup[(cluster_idx, color_idx)] = (best_r, best_exp)

        # Extract optimized radii
        for cluster_idx, color, petal_x, petal_y, pixel_count in petal_info:
            key = (cluster_idx, color_indices[color])
            if key in result_lookup:
                best_r, _ = result_lookup[key]
            else:
                best_r = int(radius_from_pixels(pixel_count))

            if color == 'cyan':
                cyan_circles.append((petal_x, petal_y, best_r))
            elif color == 'magenta':
                magenta_circles.append((petal_x, petal_y, best_r))
            elif color == 'yellow':
                yellow_circles.append((petal_x, petal_y, best_r))

        if progress_callback:
            progress_callback(total_clusters, total_clusters, 'petal_optimization', {'gpu': True, 'percentage': 100, 'tests': len(petal_tests)})
        else:
            print(f"    Phase 1c: GPU processed {len(petal_tests)} radius tests", flush=True)

    else:
        # CPU fallback path (matches original implementation)
        total_clusters = len(cluster_data)
        log_interval = max(1, total_clusters // 20)

        def count_exposed_pixels_local(center_x, center_y, radius):
            """Count pixels in a petal circle that are not covered by black circles.

            Uses local ROI extraction for efficiency - only processes the region
            around the petal rather than the full image. This is the CPU fallback
            path when GPU is unavailable.

            Args:
                center_x: X coordinate of petal center
                center_y: Y coordinate of petal center
                radius: Radius of the petal circle

            Returns:
                Integer count of exposed (non-black) pixels in the petal
            """
            if radius <= 0:
                return 0

            int_r = int(radius)
            margin = int_r + 2

            x1 = max(0, int(center_x) - margin)
            y1 = max(0, int(center_y) - margin)
            x2 = min(out_w, int(center_x) + margin + 1)
            y2 = min(out_h, int(center_y) + margin + 1)

            if x1 >= x2 or y1 >= y2:
                return 0

            local_h, local_w = y2 - y1, x2 - x1
            local_mask = np.zeros((local_h, local_w), dtype=np.uint8)

            local_cx = center_x - x1
            local_cy = center_y - y1

            cv2.circle(local_mask, (int(local_cx), int(local_cy)), int_r,
                      255, thickness=-1, lineType=cv2.LINE_AA)

            local_black = global_black_mask[y1:y2, x1:x2]
            exposed_count = int(np.sum((local_mask > 0) & ~local_black))
            return exposed_count

        for cluster_idx, data in enumerate(cluster_data):
            if cluster_idx % log_interval == 0 or cluster_idx == total_clusters - 1:
                pct = (cluster_idx + 1) * 100 // total_clusters
                if progress_callback:
                    progress_callback(cluster_idx + 1, total_clusters, 'petal_optimization', {'gpu': False, 'percentage': pct})
                else:
                    print(f"    Phase 1c: Optimizing petals {cluster_idx + 1}/{total_clusters} ({pct}%)", flush=True)

            cx, cy = data['cx'], data['cy']
            black_radius = data['black_radius']
            rotation = data['rotation']
            decomposed_counts = data['decomposed_counts']

            for color in ['cyan', 'magenta', 'yellow']:
                pixel_count = decomposed_counts[color]
                if pixel_count <= 0:
                    continue

                preliminary_radius = radius_from_pixels(pixel_count)
                if preliminary_radius <= 0:
                    continue

                angle_deg = PETAL_ANGLES[color] + rotation
                angle_rad = math.radians(angle_deg - 90)
                dist = black_radius * petal_distance

                if black_radius > 0 and dist < black_radius + preliminary_radius:
                    theoretical_r = radius_for_exposed_pixels(pixel_count, black_radius, dist)
                else:
                    theoretical_r = preliminary_radius

                if theoretical_r <= 0:
                    continue

                petal_x = cx + dist * math.cos(angle_rad)
                petal_y = cy + dist * math.sin(angle_rad)

                best_r, best_exposed, best_err = 0, 0, float('inf')
                for test_r in range(max(1, int(theoretical_r) - 3), int(theoretical_r) + 4):
                    exposed_count = count_exposed_pixels_local(petal_x, petal_y, test_r)
                    err = abs(exposed_count - pixel_count)
                    if err < best_err:
                        best_err = err
                        best_r = test_r
                        best_exposed = exposed_count

                if color == 'cyan':
                    cyan_circles.append((petal_x, petal_y, best_r))
                elif color == 'magenta':
                    magenta_circles.append((petal_x, petal_y, best_r))
                elif color == 'yellow':
                    yellow_circles.append((petal_x, petal_y, best_r))

    # Phase 1d: Drift-balanced jitter (if enabled)
    if drift and (jitter_position > 0 or jitter_size > 0):
        for step in range(jitter_steps):
            step_seed = (jitter_seed + step) if jitter_seed is not None else None
            if jitter_steps > 1:
                print(f"[DRIFT] Step {step + 1}/{jitter_steps} (seed={step_seed})", flush=True)
            if progress_callback:
                progress_callback(step, jitter_steps, 'drift_balancing', {'gpu': gpu_available, 'step': step + 1, 'total_steps': jitter_steps})
            
            # Apply jitter first, then iteratively adjust sizes to maintain balance
            cyan_circles, magenta_circles, yellow_circles = _apply_drift_compensation(
                cluster_data=cluster_data,
                cyan_circles=cyan_circles,
                magenta_circles=magenta_circles,
                yellow_circles=yellow_circles,
                black_circles=black_circles,
                image_shape=(out_h, out_w),
                jitter_position=jitter_position,
                jitter_size=jitter_size,
                jitter_seed=step_seed,
                jitter_algorithm=jitter_algorithm,
                drift_tolerance=drift_tolerance,
                max_iterations=drift_max_iterations,
            )
        if jitter_steps > 1:
            print(f"[DRIFT] Completed {jitter_steps} steps", flush=True)
    elif jitter_position > 0 or jitter_size > 0:
        # Jitter without drift - apply directly to circles
        if jitter_seed is not None:
            random.seed(jitter_seed)
        
        def apply_jitter(circles, color_offset):
            """Apply position and size jitter to circle list."""
            jittered = []
            # Set per-petal seed for independent randomization
            if jitter_seed is not None:
                random.seed(jitter_seed + color_offset)
            
            for cx, cy, r in circles:
                # Position jitter
                if jitter_position > 0:
                    jitter_amount = r * (jitter_position / 100.0)
                    if jitter_algorithm == 'gaussian':
                        dx = random.gauss(0, jitter_amount / 2.0)
                        dy = random.gauss(0, jitter_amount / 2.0)
                    else:  # uniform
                        dx = random.uniform(-jitter_amount, jitter_amount)
                        dy = random.uniform(-jitter_amount, jitter_amount)
                    cx += dx
                    cy += dy
                
                # Size jitter
                if jitter_size > 0:
                    jitter_amount = r * (jitter_size / 100.0)
                    if jitter_algorithm == 'gaussian':
                        dr = random.gauss(0, jitter_amount / 2.0)
                    else:  # uniform
                        dr = random.uniform(-jitter_amount, jitter_amount)
                    r = max(1, r + dr)
                
                jittered.append((cx, cy, r))
            return jittered
        
        cyan_circles = apply_jitter(cyan_circles, 100)
        magenta_circles = apply_jitter(magenta_circles, 200)
        yellow_circles = apply_jitter(yellow_circles, 300)

    # Phase 2: Build global petal masks
    def build_petal_mask(circle_list):
        """Build a boolean mask of all petal circles for a single color channel.

        Creates a composite mask where pixels covered by any circle in the list
        are True. Used for global CMY blending in Phase 3.

        Args:
            circle_list: List of (center_x, center_y, radius) tuples

        Returns:
            Boolean numpy array (out_h, out_w) where True = color coverage
        """
        mask = np.zeros((out_h, out_w), dtype=np.uint8)
        for cx, cy, r in circle_list:
            if r > 0:
                int_r = max(1, int(r))
                cv2.circle(mask, (int(cx), int(cy)), int_r,
                          255, thickness=-1, lineType=cv2.LINE_AA)
        return mask > 0

    global_cyan = build_petal_mask(cyan_circles)
    global_magenta = build_petal_mask(magenta_circles)
    global_yellow = build_petal_mask(yellow_circles)
    global_black = global_black_mask

    # Phase 3: Subtractive CMY blending
    output = np.full((out_h, out_w, 3), 255, dtype=np.uint8)

    exposed_cyan = global_cyan & ~global_black
    exposed_magenta = global_magenta & ~global_black
    exposed_yellow = global_yellow & ~global_black

    output[exposed_cyan, 2] = 0
    output[exposed_magenta, 1] = 0
    output[exposed_yellow, 0] = 0

    # Phase 4: Draw black on top
    output[global_black] = COLORS_BGR['black']

    return output


def apply_drift_gpu(
    circles_by_color: Dict[str, List[Tuple[float, float, float]]],
    cluster_metadata: List[Dict[str, Any]],
    cluster_circle_map: List[Dict[str, Tuple[int, int]]],
    image_shape: Tuple[int, int],
    drift_tolerance: float,
    max_iterations: int,
    max_step_size: Optional[float] = None,
    jitter_seed: Optional[int] = None,
) -> Dict[str, List[Tuple[float, float, float]]]:
    """GPU-accelerated drift correction with optimized memory transfers.
    
    Batches all measurements per iteration and processes them in parallel on GPU.
    For 15K+ clusters, this provides 10-50x speedup vs CPU serial processing.
    
    Optimizations (v2):
    - Position arrays (px, py) uploaded once before loop (they don't change)
    - Target pixels array uploaded once (constant across iterations)
    - Radii array updated in-place on GPU each iteration
    - Adjustment calculation done on GPU via CUDA kernel (eliminates CPU loop)
    - Measurement index arrays pre-built once before loop
    
    Args:
        circles_by_color: Dict mapping colors to list of (x, y, r) tuples
        cluster_metadata: List of cluster info dicts
        cluster_circle_map: List of dicts mapping color -> (circle_index, target_pixels)
        image_shape: (height, width) for rendering
        drift_tolerance: Acceptable deviation from target mass
        max_iterations: Maximum balancing iterations
        max_step_size: Optional maximum scale factor per iteration
    
    Returns:
        Updated circles_by_color dict with adjusted radii
    """
    try:
        import cupy as cp
    except ImportError:
        # Fallback to CPU version
        from .circle_renderer import _apply_drift_to_svg_circles
        return _apply_drift_to_svg_circles(
            circles_by_color, cluster_metadata, cluster_circle_map,
            image_shape, drift_tolerance, max_iterations, max_step_size, None,
            jitter_seed
        )
    
    import math
    
    h, w = image_shape
    
    # Convert to mutable lists
    circles_by_color = {
        color: list(circles)
        for color, circles in circles_by_color.items()
    }
    
    # Build global black mask once (all black circles)
    black_mask = np.zeros((h, w), dtype=np.uint8)
    for cx, cy, r in circles_by_color.get('black', []):
        if r > 0:
            cv2.circle(black_mask, (int(cx), int(cy)), max(1, int(r)),
                      255, thickness=-1, lineType=cv2.LINE_AA)
    black_mask_bool = black_mask > 0
    black_mask_gpu = cp.asarray(black_mask_bool)
    
    # CUDA kernel for measuring exposed pixels of petals
    # Measures how much of each petal is visible (not covered by black)
    measure_kernel = cp.RawKernel(r'''
    extern "C" __global__
    void measure_exposed_petals(
        const bool* black_mask,
        const float* px_arr, const float* py_arr, const float* pr_arr,
        int* exposed_counts,
        int n_petals, int width, int height
    ) {
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= n_petals) return;
        
        float px = px_arr[idx];
        float py = py_arr[idx];
        float radius = pr_arr[idx];
        
        if (radius <= 0.5f) {
            exposed_counts[idx] = 0;
            return;
        }
        
        // ROI bounds
        int margin = (int)radius + 2;
        int x1 = max(0, (int)px - margin);
        int y1 = max(0, (int)py - margin);
        int x2 = min(width, (int)px + margin + 1);
        int y2 = min(height, (int)py + margin + 1);
        
        // Match cv2.circle LINE_AA behavior with (r + 0.5)^2
        float effective_r = radius + 0.5f;
        float radius_sq = effective_r * effective_r;
        int count = 0;
        
        // Count pixels in circle NOT covered by black
        for (int y = y1; y < y2; y++) {
            for (int x = x1; x < x2; x++) {
                float dx = x - px;
                float dy = y - py;
                float dist_sq = dx * dx + dy * dy;
                
                if (dist_sq <= radius_sq && !black_mask[y * width + x]) {
                    count++;
                }
            }
        }
        
        exposed_counts[idx] = count;
    }
    ''', 'measure_exposed_petals')
    
    # CUDA kernel for calculating radius adjustments on GPU
    # Eliminates CPU-side serial loop - all adjustments computed in parallel
    adjust_kernel = cp.RawKernel(r'''
    extern "C" __global__
    void calculate_adjustments(
        const int* exposed_counts,
        const int* target_pixels,
        float* radii,
        int* needs_adjustment,
        float* squared_errors,
        float drift_tolerance,
        float min_scale,
        float max_scale,
        int n_petals
    ) {
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        if (idx >= n_petals) return;
        
        int actual = exposed_counts[idx];
        int target = target_pixels[idx];
        
        // Skip if completely occluded or measurement unreliable
        if (actual < 5 || target <= 0) {
            needs_adjustment[idx] = 0;
            squared_errors[idx] = 0.0f;
            return;
        }
        
        // Calculate deviation
        float deviation = (float)(actual - target) / (float)target;
        squared_errors[idx] = deviation * deviation;
        
        if (fabsf(deviation) > drift_tolerance) {
            // Adjust size: scale by sqrt ratio
            float scale = sqrtf((float)target / (float)actual);
            
            // Clamp scale factor to limit change per iteration
            scale = fmaxf(min_scale, fminf(max_scale, scale));
            
            // Update radius in-place (min 0.5)
            radii[idx] = fmaxf(0.5f, radii[idx] * scale);
            needs_adjustment[idx] = 1;
        } else {
            needs_adjustment[idx] = 0;
        }
    }
    ''', 'calculate_adjustments')
    
    # ==========================================================================
    # OPTIMIZATION: Pre-build measurement arrays ONCE before iteration loop
    # These arrays define the structure of measurements and don't change
    # ==========================================================================
    
    # Build measurement index arrays once (color indices, circle indices, targets)
    # Maps: measurement_idx -> (color_code, circle_idx_in_color, target_pixels)
    color_codes = []      # 0=cyan, 1=magenta, 2=yellow
    circle_indices = []   # Index into circles_by_color[color]
    target_pixels_list = []
    px_list = []
    py_list = []
    pr_list = []
    
    color_to_code = {'cyan': 0, 'magenta': 1, 'yellow': 2}
    
    for cluster_idx, circle_map in enumerate(cluster_circle_map):
        if not circle_map:
            continue
        
        for color in ['cyan', 'magenta', 'yellow']:
            if color not in circle_map:
                continue
            
            circle_idx, target = circle_map[color]
            cx, cy, r = circles_by_color[color][circle_idx]
            
            color_codes.append(color_to_code[color])
            circle_indices.append(circle_idx)
            target_pixels_list.append(target)
            px_list.append(cx)
            py_list.append(cy)
            pr_list.append(r)
    
    n_petals = len(color_codes)
    if n_petals == 0:
        return circles_by_color
    
    # Convert to numpy arrays
    color_codes_arr = np.array(color_codes, dtype=np.int32)
    circle_indices_arr = np.array(circle_indices, dtype=np.int32)
    target_pixels_arr = np.array(target_pixels_list, dtype=np.int32)
    px_arr = np.array(px_list, dtype=np.float32)
    py_arr = np.array(py_list, dtype=np.float32)
    pr_arr = np.array(pr_list, dtype=np.float32)
    
    # ==========================================================================
    # OPTIMIZATION: Upload position and target arrays to GPU ONCE
    # Only radii change during iteration - positions and targets are constant
    # ==========================================================================
    px_gpu = cp.asarray(px_arr)  # Uploaded once, never changes
    py_gpu = cp.asarray(py_arr)  # Uploaded once, never changes
    target_gpu = cp.asarray(target_pixels_arr)  # Uploaded once, never changes
    
    # Radii array - will be updated in-place on GPU each iteration
    pr_gpu = cp.asarray(pr_arr)
    
    # Output arrays (reused each iteration)
    exposed_gpu = cp.zeros(n_petals, dtype=cp.int32)
    needs_adjustment_gpu = cp.zeros(n_petals, dtype=cp.int32)
    squared_errors_gpu = cp.zeros(n_petals, dtype=cp.float32)
    
    # Calculate scale bounds based on max_step_size
    if max_step_size is not None:
        if max_step_size < 1.0:
            # Small step mode: 0.02 means ±2% change
            min_scale = 1.0 - max_step_size
            max_scale_val = 1.0 + max_step_size
        else:
            # Large step mode: 2.0 means 0.5x to 2x
            min_scale = 1.0 / max_step_size
            max_scale_val = max_step_size
    else:
        # Default: 0.5x to 2x (same as legacy behavior)
        min_scale = 0.5
        max_scale_val = 2.0
    
    # Kernel launch parameters
    block_size = 256
    grid_size = (n_petals + block_size - 1) // block_size
    
    # ==========================================================================
    # Iteration loop - now with minimal GPU↔CPU transfers
    # Only transfers per iteration: exposed_counts download for convergence check
    # ==========================================================================
    for iteration in range(max_iterations):
        # Launch measurement kernel
        measure_kernel(
            (grid_size,), (block_size,),
            (black_mask_gpu, px_gpu, py_gpu, pr_gpu, exposed_gpu,
             n_petals, w, h)
        )
        
        # Launch adjustment kernel (replaces CPU serial loop)
        adjust_kernel(
            (grid_size,), (block_size,),
            (exposed_gpu, target_gpu, pr_gpu, needs_adjustment_gpu, squared_errors_gpu,
             np.float32(drift_tolerance), np.float32(min_scale), np.float32(max_scale_val),
             n_petals)
        )
        
        # Check convergence using GPU reduction (minimal transfer)
        adjustments_made = int(cp.sum(needs_adjustment_gpu))
        
        # Calculate RMS error on GPU
        sum_squared_error = float(cp.sum(squared_errors_gpu))
        # Count valid measurements (where squared_error > 0 means it was measured)
        total_circles = int(cp.sum(squared_errors_gpu > 0))
        rms_error = math.sqrt(sum_squared_error / total_circles) if total_circles > 0 else 0.0
        
        print(f"\r[DRIFT GPU] Iteration {iteration}: adjusted {adjustments_made} circles, RMS error={rms_error:.4f}", end='', flush=True)
        
        if adjustments_made == 0:
            print(f"\n[DRIFT GPU] Converged after {iteration + 1} iterations", flush=True)
            break
    else:
        # Did not converge
        print(f"\n[DRIFT GPU] Did not converge after {max_iterations} iterations (RMS error={rms_error:.4f})", flush=True)
    
    # ==========================================================================
    # OPTIMIZATION: Copy final radii back to CPU only ONCE at the end
    # ==========================================================================
    final_radii = cp.asnumpy(pr_gpu)
    
    # Update circles_by_color with final adjusted radii
    for i in range(n_petals):
        color_code = color_codes_arr[i]
        circle_idx = circle_indices_arr[i]
        new_r = float(final_radii[i])
        
        color = ['cyan', 'magenta', 'yellow'][color_code]
        cx, cy, _ = circles_by_color[color][circle_idx]
        circles_by_color[color][circle_idx] = (cx, cy, new_r)
    
    return circles_by_color
