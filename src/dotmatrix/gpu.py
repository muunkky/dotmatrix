"""GPU acceleration utilities for dotmatrix.

This module provides GPU acceleration via CuPy for CUDA-enabled systems.
Falls back gracefully to CPU (NumPy) when GPU is unavailable.

Requirements:
- NVIDIA GPU with CUDA support
- cupy-cuda12x package (pip install dotmatrix[gpu])
- CUDA runtime libraries (installed via pip with cupy)

Usage:
    from dotmatrix.gpu import get_array_module, is_gpu_available

    xp = get_array_module(use_gpu=True)  # Returns cupy or numpy
    arr = xp.zeros((100, 100))  # Works on GPU or CPU
"""

import os
import sys
import ctypes
from typing import Tuple, Optional, Dict, List

# Try to set up CUDA library path before importing cupy
# This is needed because cupy looks for libnvrtc.so in standard paths
_cuda_lib_paths = []
_site_packages = None

# Find site-packages location
for path in sys.path:
    if 'site-packages' in path:
        nvidia_path = os.path.join(path, 'nvidia')
        if os.path.exists(nvidia_path):
            _site_packages = path
            break

if _site_packages:
    # Add NVIDIA CUDA library paths from pip packages
    _nvidia_libs = [
        'cuda_nvrtc/lib',
        'cuda_runtime/lib',
        'cublas/lib',
        'cufft/lib',
        'cusparse/lib',
    ]
    for lib_dir in _nvidia_libs:
        lib_path = os.path.join(_site_packages, 'nvidia', lib_dir)
        if os.path.exists(lib_path):
            _cuda_lib_paths.append(lib_path)

    # Update LD_LIBRARY_PATH if we found CUDA libs
    if _cuda_lib_paths:
        existing = os.environ.get('LD_LIBRARY_PATH', '')
        new_paths = ':'.join(_cuda_lib_paths)
        if existing:
            os.environ['LD_LIBRARY_PATH'] = f"{new_paths}:{existing}"
        else:
            os.environ['LD_LIBRARY_PATH'] = new_paths

        # Pre-load the libraries using ctypes so they're available
        # This is necessary because LD_LIBRARY_PATH changes after Python starts
        # don't affect dlopen() calls
        for lib_path in _cuda_lib_paths:
            nvrtc_path = os.path.join(lib_path, 'libnvrtc.so.12')
            if os.path.exists(nvrtc_path):
                try:
                    ctypes.CDLL(nvrtc_path, mode=ctypes.RTLD_GLOBAL)
                except Exception:
                    pass  # Will try next path or fail later
                break

# Now try to import cupy
_GPU_AVAILABLE = False
_GPU_ERROR = None

try:
    import cupy as cp
    # Test if CUDA is actually available
    if cp.cuda.is_available():
        # Try a simple operation to verify runtime works
        _test = cp.array([1, 2, 3])
        _ = _test + 1
        cp.cuda.Stream.null.synchronize()
        _GPU_AVAILABLE = True
        del _test
except ImportError as e:
    _GPU_ERROR = f"CuPy not installed: {e}"
except Exception as e:
    _GPU_ERROR = f"GPU initialization failed: {e}"

# Always import numpy as fallback
import numpy as np


def is_gpu_available() -> bool:
    """Check if GPU acceleration is available.

    Returns:
        True if CuPy is installed and CUDA is working.
    """
    return _GPU_AVAILABLE


def get_gpu_info() -> dict:
    """Get information about the GPU environment.

    Returns:
        Dictionary with GPU status, device info, and any errors.
    """
    info = {
        'gpu_available': _GPU_AVAILABLE,
        'error': _GPU_ERROR,
        'cuda_lib_paths': _cuda_lib_paths,
    }

    if _GPU_AVAILABLE:
        import cupy as cp
        device = cp.cuda.Device(0)
        info.update({
            'device_name': device.name if hasattr(device, 'name') else 'Unknown',
            'device_id': device.id,
            'compute_capability': device.compute_capability,
            'cupy_version': cp.__version__,
        })

        # Get memory info
        try:
            mempool = cp.get_default_memory_pool()
            info['gpu_memory_used'] = mempool.used_bytes()
            info['gpu_memory_total'] = mempool.total_bytes()
        except Exception:
            pass

    return info


def get_array_module(use_gpu: bool = True):
    """Get the appropriate array module (CuPy for GPU, NumPy for CPU).

    Args:
        use_gpu: If True and GPU available, return CuPy. Otherwise NumPy.

    Returns:
        cupy module if GPU requested and available, numpy otherwise.
    """
    if use_gpu and _GPU_AVAILABLE:
        import cupy as cp
        return cp
    return np


def to_gpu(arr: np.ndarray) -> 'cp.ndarray':
    """Transfer numpy array to GPU.

    Args:
        arr: NumPy array

    Returns:
        CuPy array on GPU

    Raises:
        RuntimeError: If GPU is not available
    """
    if not _GPU_AVAILABLE:
        raise RuntimeError(f"GPU not available: {_GPU_ERROR}")
    import cupy as cp
    return cp.asarray(arr)


def to_cpu(arr) -> np.ndarray:
    """Transfer array from GPU to CPU.

    Args:
        arr: CuPy or NumPy array

    Returns:
        NumPy array on CPU
    """
    if _GPU_AVAILABLE:
        import cupy as cp
        if isinstance(arr, cp.ndarray):
            return cp.asnumpy(arr)
    return np.asarray(arr)


def synchronize():
    """Wait for all GPU operations to complete.

    Call this before timing GPU operations or before transferring results
    to ensure all GPU kernels have finished.
    """
    if _GPU_AVAILABLE:
        import cupy as cp
        cp.cuda.Stream.null.synchronize()


def print_gpu_status():
    """Print GPU status information to stdout."""
    info = get_gpu_info()

    print("=" * 60)
    print("GPU Status")
    print("=" * 60)

    if info['gpu_available']:
        print(f"GPU Available: YES")
        print(f"Device: {info.get('device_name', 'Unknown')}")
        print(f"Compute Capability: {info.get('compute_capability', 'Unknown')}")
        print(f"CuPy Version: {info.get('cupy_version', 'Unknown')}")
        if 'gpu_memory_used' in info:
            used_mb = info['gpu_memory_used'] / (1024 * 1024)
            total_mb = info['gpu_memory_total'] / (1024 * 1024)
            print(f"Memory Pool: {used_mb:.1f} MB used / {total_mb:.1f} MB total")
    else:
        print(f"GPU Available: NO")
        print(f"Error: {info.get('error', 'Unknown')}")

    if info['cuda_lib_paths']:
        print(f"\nCUDA Library Paths ({len(info['cuda_lib_paths'])}):")
        for path in info['cuda_lib_paths'][:3]:  # Show first 3
            print(f"  {path}")
        if len(info['cuda_lib_paths']) > 3:
            print(f"  ... and {len(info['cuda_lib_paths']) - 3} more")

    print("=" * 60)


# =============================================================================
# GPU-Accelerated NMS (Non-Maximum Suppression)
# =============================================================================

def _cpu_nms_centers(
    centers: np.ndarray,
    scores: np.ndarray,
    min_distance: float
) -> np.ndarray:
    """CPU implementation of Non-Maximum Suppression.

    Args:
        centers: (N, 2) array of (x, y) coordinates
        scores: (N,) array of scores for each center (higher = better)
        min_distance: Minimum distance between retained centers

    Returns:
        Filtered centers array (M, 2) where M <= N
    """
    if len(centers) == 0:
        return centers
    if len(centers) == 1:
        return centers

    # Sort by score (descending)
    sorted_indices = np.argsort(scores)[::-1]

    kept = []
    suppressed = set()

    for idx in sorted_indices:
        if idx in suppressed:
            continue

        x, y = centers[idx]
        kept.append([x, y])

        # Suppress nearby centers
        for other_idx in sorted_indices:
            if other_idx in suppressed or other_idx == idx:
                continue
            ox, oy = centers[other_idx]
            dist = np.sqrt((x - ox)**2 + (y - oy)**2)
            if dist < min_distance:
                suppressed.add(other_idx)

    return np.array(kept) if kept else np.array([]).reshape(0, 2)


def gpu_nms_centers(
    centers: np.ndarray,
    scores: np.ndarray,
    min_distance: float,
    force_gpu: bool = False
) -> np.ndarray:
    """GPU-accelerated Non-Maximum Suppression for centroid discovery.

    Computes full N×N distance matrix on GPU and applies vectorized NMS.
    Falls back to CPU for small inputs or when GPU unavailable.

    Args:
        centers: (N, 2) array of (x, y) coordinates
        scores: (N,) array of scores for each center (higher = better)
        min_distance: Minimum distance between retained centers
        force_gpu: If True, forces GPU path even for small inputs

    Returns:
        Filtered centers array (M, 2) where M <= N
    """
    n = len(centers)

    # Handle edge cases
    if n == 0:
        return np.array([]).reshape(0, 2)
    if n == 1:
        return centers.copy()

    # Use CPU for small inputs or when GPU unavailable
    if not force_gpu and (not _GPU_AVAILABLE or n < 100):
        return _cpu_nms_centers(centers, scores, min_distance)

    if not _GPU_AVAILABLE:
        return _cpu_nms_centers(centers, scores, min_distance)

    import cupy as cp

    # Transfer to GPU
    coords = cp.asarray(centers, dtype=cp.float32)
    scores_gpu = cp.asarray(scores, dtype=cp.float32)

    # Sort by score (descending) - get sorted indices
    sorted_indices = cp.argsort(scores_gpu)[::-1]
    sorted_coords = coords[sorted_indices]

    # Compute full distance matrix: (N, N)
    # Using broadcasting: (N, 1, 2) - (1, N, 2) -> (N, N, 2) -> sum -> sqrt -> (N, N)
    diff = sorted_coords[:, None, :] - sorted_coords[None, :, :]
    dist_matrix = cp.sqrt((diff ** 2).sum(axis=2))

    # NMS: keep if not suppressed by a higher-ranked (lower-indexed) point
    keep_mask = cp.ones(n, dtype=cp.bool_)

    # Vectorized suppression: for each kept point, suppress all later points within distance
    # Process in order of score (already sorted)
    for i in range(n):
        if keep_mask[i]:
            # Suppress all points j > i that are within min_distance
            suppress_mask = (dist_matrix[i, i+1:] < min_distance)
            keep_mask[i+1:] &= ~suppress_mask

    # Get kept centers
    result = cp.asnumpy(sorted_coords[keep_mask])

    return result


# =============================================================================
# GPU-Accelerated Nearest Center Labeling (KDTree replacement)
# =============================================================================

def gpu_nearest_center_labels(
    pixel_coords: np.ndarray,
    centers: np.ndarray,
    chunk_size: int = 500_000,
    force_gpu: bool = False
) -> np.ndarray:
    """GPU-accelerated nearest center labeling.

    For each pixel, find the index of the nearest center using GPU
    broadcast distance computation. Processes in chunks to manage memory.

    Args:
        pixel_coords: (M, 2) array of (x, y) pixel coordinates
        centers: (N, 2) array of center coordinates
        chunk_size: Number of pixels to process per GPU batch
        force_gpu: If True, forces GPU path even when fallback would be used

    Returns:
        (M,) array of center indices for each pixel
    """
    n_pixels = len(pixel_coords)
    n_centers = len(centers)

    if n_pixels == 0:
        return np.array([], dtype=np.int32)

    if n_centers == 0:
        return np.zeros(n_pixels, dtype=np.int32)

    # Use CPU/KDTree for small inputs or when GPU unavailable
    if not force_gpu and (not _GPU_AVAILABLE or n_pixels < 10000 or n_centers < 10):
        from scipy.spatial import KDTree
        tree = KDTree(centers)
        _, labels = tree.query(pixel_coords)
        return labels.astype(np.int32)

    if not _GPU_AVAILABLE:
        from scipy.spatial import KDTree
        tree = KDTree(centers)
        _, labels = tree.query(pixel_coords)
        return labels.astype(np.int32)

    import cupy as cp

    # Transfer centers to GPU (stays for all chunks)
    centers_gpu = cp.asarray(centers, dtype=cp.float32)

    # Pre-allocate output
    labels = np.empty(n_pixels, dtype=np.int32)

    # Process in chunks to manage GPU memory
    # Memory per chunk: chunk_size × n_centers × 4 bytes (float32)
    for start in range(0, n_pixels, chunk_size):
        end = min(start + chunk_size, n_pixels)
        chunk = cp.asarray(pixel_coords[start:end], dtype=cp.float32)

        # Compute squared distances (skip sqrt since we only need argmin)
        # Shape: (chunk_size, n_centers)
        diff = chunk[:, None, :] - centers_gpu[None, :, :]
        dist_sq = (diff ** 2).sum(axis=2)

        # Find nearest center for each pixel
        labels[start:end] = cp.asnumpy(cp.argmin(dist_sq, axis=1))

    return labels


def gpu_create_cluster_labels(
    image_shape: Tuple[int, int],
    centers: np.ndarray,
    chunk_size: int = 500_000,
    force_gpu: bool = False
) -> np.ndarray:
    """Create cluster label image using GPU acceleration.

    Assigns each pixel to its nearest center using Voronoi tessellation.

    Args:
        image_shape: (H, W) tuple of image dimensions
        centers: (N, 2) array of center coordinates in (x, y) format
        chunk_size: Pixels per GPU batch
        force_gpu: Force GPU path

    Returns:
        (H, W) label array where each pixel contains its nearest center index
    """
    h, w = image_shape

    # Generate all pixel coordinates as (x, y) pairs
    yy, xx = np.mgrid[0:h, 0:w]
    pixel_coords = np.column_stack([xx.ravel(), yy.ravel()]).astype(np.float32)

    # Get labels and reshape to image
    labels = gpu_nearest_center_labels(pixel_coords, centers, chunk_size, force_gpu)
    return labels.reshape(h, w)


# =============================================================================
# GPU-Accelerated Cluster Color Counting
# =============================================================================

def _cpu_count_cluster_colors(
    labels: np.ndarray,
    color_masks: Dict[str, np.ndarray],
    n_clusters: int
) -> Dict[str, np.ndarray]:
    """CPU implementation of per-cluster color counting.

    Args:
        labels: (H, W) array of cluster indices
        color_masks: Dict mapping color names to (H, W) boolean masks
        n_clusters: Total number of clusters

    Returns:
        Dict mapping color names to (n_clusters,) count arrays
    """
    flat_labels = labels.ravel()
    counts = {}

    for color, mask in color_masks.items():
        flat_mask = mask.ravel().astype(np.int32)
        counts[color] = np.bincount(
            flat_labels,
            weights=flat_mask,
            minlength=n_clusters
        ).astype(np.int64)

    return counts


def gpu_count_cluster_colors(
    labels: np.ndarray,
    color_masks: Dict[str, np.ndarray],
    n_clusters: int,
    force_gpu: bool = False
) -> Dict[str, np.ndarray]:
    """GPU-accelerated per-cluster color pixel counting.

    Uses cupy.bincount with color masks as weights for single-pass counting.

    Args:
        labels: (H, W) array of cluster indices
        color_masks: Dict mapping color names to (H, W) boolean masks
        n_clusters: Total number of clusters
        force_gpu: Force GPU path

    Returns:
        Dict mapping color names to (n_clusters,) count arrays
    """
    # Use CPU for small inputs or when GPU unavailable
    if not force_gpu and (not _GPU_AVAILABLE or labels.size < 100000):
        return _cpu_count_cluster_colors(labels, color_masks, n_clusters)

    if not _GPU_AVAILABLE:
        return _cpu_count_cluster_colors(labels, color_masks, n_clusters)

    import cupy as cp

    # Transfer labels to GPU
    labels_gpu = cp.asarray(labels.ravel(), dtype=cp.int32)
    counts = {}

    for color, mask in color_masks.items():
        mask_gpu = cp.asarray(mask.ravel().astype(np.int32))

        # bincount with mask as weights: count color pixels per cluster
        color_counts = cp.bincount(
            labels_gpu,
            weights=mask_gpu,
            minlength=n_clusters
        )
        counts[color] = cp.asnumpy(color_counts).astype(np.int64)

    return counts


def gpu_count_cluster_totals(
    labels: np.ndarray,
    n_clusters: int,
    force_gpu: bool = False
) -> np.ndarray:
    """Count total pixels per cluster using GPU bincount.

    Args:
        labels: (H, W) array of cluster indices
        n_clusters: Total number of clusters
        force_gpu: Force GPU path

    Returns:
        (n_clusters,) array of total pixel counts per cluster
    """
    if not force_gpu and (not _GPU_AVAILABLE or labels.size < 100000):
        return np.bincount(labels.ravel(), minlength=n_clusters)

    if not _GPU_AVAILABLE:
        return np.bincount(labels.ravel(), minlength=n_clusters)

    import cupy as cp
    labels_gpu = cp.asarray(labels.ravel(), dtype=cp.int32)
    return cp.asnumpy(cp.bincount(labels_gpu, minlength=n_clusters))


if __name__ == '__main__':
    print_gpu_status()
