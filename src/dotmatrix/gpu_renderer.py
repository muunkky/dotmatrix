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
from typing import List, Tuple, Optional, Dict, Any, Callable

import numpy as np
import cv2

from dotmatrix.gpu import is_gpu_available, get_array_module, to_gpu, to_cpu, synchronize
from dotmatrix.cluster_pixel_counter import ClusterResult
from dotmatrix.circle_renderer import (
    COLORS_BGR,
    PETAL_ANGLES,
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
    # Optimized: Use integer radius directly instead of expensive find_best_radius_for_pixels
    # The mask is only used for exposed pixel calculation, exact pixel count not critical
    def build_global_black_mask(circle_list):
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

    # Phase 2: Build global petal masks
    def build_petal_mask(circle_list):
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
