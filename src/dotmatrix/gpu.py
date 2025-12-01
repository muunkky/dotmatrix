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

        # Get memory info from device (actual GPU memory, not mempool)
        try:
            mem_info = device.mem_info
            info['gpu_memory_free'] = mem_info[0] // (1024 * 1024)  # MB
            info['gpu_memory_total'] = mem_info[1] // (1024 * 1024)  # MB
            info['gpu_memory_used'] = info['gpu_memory_total'] - info['gpu_memory_free']
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

    # Always use GPU when available (no thresholds - user wants GPU for everything)
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
        chunk_size: Number of pixels to process per GPU batch (auto-adjusted)
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

    # Always use GPU when available (no thresholds - user wants GPU for everything)
    if not _GPU_AVAILABLE:
        from scipy.spatial import KDTree
        tree = KDTree(centers)
        _, labels = tree.query(pixel_coords)
        return labels.astype(np.int32)

    import cupy as cp

    # Adaptive chunk sizing based on GPU memory and number of centers
    # Memory per chunk: chunk_size × n_centers × 2 × 4 bytes (diff array)
    #                 + chunk_size × n_centers × 4 bytes (dist_sq array)
    # Total: chunk_size × n_centers × 12 bytes
    # Target max ~1GB per chunk to leave room for other operations
    MAX_CHUNK_MEMORY = 1_000_000_000  # 1 GB
    bytes_per_pixel = n_centers * 12  # 12 bytes per pixel per center
    adaptive_chunk_size = max(10000, min(chunk_size, MAX_CHUNK_MEMORY // bytes_per_pixel))

    try:
        # Transfer centers to GPU (stays for all chunks)
        centers_gpu = cp.asarray(centers, dtype=cp.float32)

        # Pre-allocate output
        labels = np.empty(n_pixels, dtype=np.int32)

        # Process in chunks to manage GPU memory
        for start in range(0, n_pixels, adaptive_chunk_size):
            end = min(start + adaptive_chunk_size, n_pixels)
            chunk = cp.asarray(pixel_coords[start:end], dtype=cp.float32)

            # Compute squared distances (skip sqrt since we only need argmin)
            # Shape: (chunk_size, n_centers)
            diff = chunk[:, None, :] - centers_gpu[None, :, :]
            dist_sq = (diff ** 2).sum(axis=2)

            # Find nearest center for each pixel
            labels[start:end] = cp.asnumpy(cp.argmin(dist_sq, axis=1))

            # Free GPU memory after each chunk
            del chunk, diff, dist_sq
            cp.get_default_memory_pool().free_all_blocks()

        return labels

    except cp.cuda.memory.OutOfMemoryError:
        # GPU OOM - fallback to CPU
        from scipy.spatial import KDTree
        tree = KDTree(centers)
        _, labels = tree.query(pixel_coords)
        return labels.astype(np.int32)


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
    # Always use GPU when available (no thresholds - user wants GPU for everything)
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
    # Always use GPU when available (no thresholds - user wants GPU for everything)
    if not _GPU_AVAILABLE:
        return np.bincount(labels.ravel(), minlength=n_clusters)

    import cupy as cp
    labels_gpu = cp.asarray(labels.ravel(), dtype=cp.int32)
    return cp.asnumpy(cp.bincount(labels_gpu, minlength=n_clusters))


# =============================================================================
# GPU-Accelerated Image Processing (Distance Transform, Maximum Filter)
# =============================================================================

def gpu_distance_transform(
    binary_mask: np.ndarray,
    force_gpu: bool = False
) -> np.ndarray:
    """GPU-accelerated distance transform using CuPy.

    Computes the Euclidean distance transform of a binary image.
    Each pixel gets the distance to the nearest zero pixel.

    Args:
        binary_mask: 2D binary mask (0/1 or boolean)
        force_gpu: Force GPU path

    Returns:
        Distance transform array (float32)
    """
    if not _GPU_AVAILABLE:
        import cv2
        binary = (binary_mask > 0).astype(np.uint8)
        return cv2.distanceTransform(binary, cv2.DIST_L2, 5).astype(np.float32)

    import cupy as cp
    from cupyx.scipy import ndimage as cp_ndimage

    # Transfer to GPU
    binary_gpu = cp.asarray(binary_mask > 0)

    # CuPy distance transform
    dist = cp_ndimage.distance_transform_edt(binary_gpu)

    return cp.asnumpy(dist).astype(np.float32)


def gpu_maximum_filter(
    image: np.ndarray,
    size: int,
    force_gpu: bool = False
) -> np.ndarray:
    """GPU-accelerated maximum filter using CuPy.

    For each pixel, finds the maximum value in a neighborhood.
    Used for finding local maxima in distance transform.

    Args:
        image: Input image
        size: Size of the filter neighborhood
        force_gpu: Force GPU path

    Returns:
        Filtered image with local maxima
    """
    if not _GPU_AVAILABLE:
        from scipy.ndimage import maximum_filter
        return maximum_filter(image, size=size)

    import cupy as cp
    from cupyx.scipy import ndimage as cp_ndimage

    # Transfer to GPU
    image_gpu = cp.asarray(image)

    # CuPy maximum filter
    result = cp_ndimage.maximum_filter(image_gpu, size=size)

    return cp.asnumpy(result)


# =============================================================================
# GPU-Accelerated CMYK Quantization and Ink Separation
# =============================================================================

# CMYK+RGB palette in BGR format (for cv2 compatibility)
_CMYK_RGB_PALETTE_BGR = np.array([
    [255, 255, 255],  # White
    [0, 0, 0],        # Black
    [255, 255, 0],    # Cyan (BGR)
    [255, 0, 255],    # Magenta (BGR)
    [0, 255, 255],    # Yellow (BGR)
    [0, 0, 255],      # Red (BGR)
    [0, 255, 0],      # Green (BGR)
    [255, 0, 0],      # Blue (BGR)
], dtype=np.float32)


def gpu_quantize_to_cmyk_rgb(
    image: np.ndarray,
    force_gpu: bool = False
) -> np.ndarray:
    """GPU-accelerated quantization to CMYK+RGB palette.

    Maps each pixel to the nearest color from the 8-color palette using
    GPU parallel distance computation.

    Args:
        image: BGR image as numpy array (H, W, 3)
        force_gpu: Force GPU path

    Returns:
        Quantized BGR image with only 8 possible colors
    """
    h, w = image.shape[:2]

    if not _GPU_AVAILABLE:
        # CPU fallback - same as original quantize_to_cmyk_rgb
        palette = _CMYK_RGB_PALETTE_BGR
        pixels = image.reshape(-1, 1, 3).astype(np.float32)
        diff = pixels - palette
        distances = np.sum(diff ** 2, axis=2)
        nearest_idx = np.argmin(distances, axis=1)
        quantized = palette[nearest_idx].astype(np.uint8)
        return quantized.reshape(h, w, 3)

    import cupy as cp

    # Transfer to GPU
    image_gpu = cp.asarray(image, dtype=cp.float32)
    palette_gpu = cp.asarray(_CMYK_RGB_PALETTE_BGR, dtype=cp.float32)

    # Reshape for broadcasting: (H*W, 1, 3)
    pixels_gpu = image_gpu.reshape(-1, 1, 3)

    # Calculate squared distance to each palette color: (H*W, 8)
    diff = pixels_gpu - palette_gpu  # Broadcasting: (H*W, 8, 3)
    distances = cp.sum(diff ** 2, axis=2)  # (H*W, 8)

    # Find nearest color index for each pixel
    nearest_idx = cp.argmin(distances, axis=1)  # (H*W,)

    # Map to palette colors
    quantized_gpu = palette_gpu[nearest_idx].astype(cp.uint8)

    # Transfer back to CPU
    result = cp.asnumpy(quantized_gpu).reshape(h, w, 3)

    # Free GPU memory
    del image_gpu, palette_gpu, pixels_gpu, diff, distances, nearest_idx, quantized_gpu
    cp.get_default_memory_pool().free_all_blocks()

    return result


def gpu_separate_cmyk_inks(
    image: np.ndarray,
    quantize: bool = True,
    force_gpu: bool = False
) -> Dict[str, np.ndarray]:
    """GPU-accelerated CMYK ink separation.

    Separates image into CMYK ink masks using GPU-accelerated operations.
    Optionally quantizes to clean palette first (also GPU-accelerated).

    Args:
        image: BGR image as numpy array (H, W, 3)
        quantize: If True, quantize to nearest CMYK+RGB color first
        force_gpu: Force GPU path

    Returns:
        Dictionary mapping ink names to binary masks (255=ink present, 0=absent)
    """
    # Quantize if requested (GPU-accelerated)
    if quantize:
        if _GPU_AVAILABLE:
            image = gpu_quantize_to_cmyk_rgb(image)
        else:
            # CPU fallback quantization
            palette = _CMYK_RGB_PALETTE_BGR
            h, w = image.shape[:2]
            pixels = image.reshape(-1, 1, 3).astype(np.float32)
            diff = pixels - palette
            distances = np.sum(diff ** 2, axis=2)
            nearest_idx = np.argmin(distances, axis=1)
            image = palette[nearest_idx].astype(np.uint8).reshape(h, w, 3)

    if not _GPU_AVAILABLE:
        # CPU fallback - same logic as convex_detector.separate_cmyk_inks
        b = image[:, :, 0]
        g = image[:, :, 1]
        r = image[:, :, 2]

        black_mask = (r == 0) & (g == 0) & (b == 0)
        white_mask = (r == 255) & (g == 255) & (b == 255)
        colored = ~black_mask & ~white_mask

        cyan_mask = colored & (r == 0)
        magenta_mask = colored & (g == 0)
        yellow_mask = colored & (b == 0)

        return {
            'cyan': (cyan_mask * 255).astype(np.uint8),
            'magenta': (magenta_mask * 255).astype(np.uint8),
            'yellow': (yellow_mask * 255).astype(np.uint8),
            'black': (black_mask * 255).astype(np.uint8),
        }

    import cupy as cp

    # Transfer to GPU
    image_gpu = cp.asarray(image)

    # Extract channels (BGR format)
    b = image_gpu[:, :, 0]
    g = image_gpu[:, :, 1]
    r = image_gpu[:, :, 2]

    # Black ink: all channels are 0
    black_mask = (r == 0) & (g == 0) & (b == 0)

    # White background: all channels are 255
    white_mask = (r == 255) & (g == 255) & (b == 255)

    # Colored region (not black or white)
    colored = ~black_mask & ~white_mask

    # Cyan ink: red channel absorbed (R=0) in colored region
    cyan_mask = colored & (r == 0)

    # Magenta ink: green channel absorbed (G=0) in colored region
    magenta_mask = colored & (g == 0)

    # Yellow ink: blue channel absorbed (B=0) in colored region
    yellow_mask = colored & (b == 0)

    # Convert to uint8 and transfer back to CPU
    result = {
        'cyan': cp.asnumpy((cyan_mask * 255).astype(cp.uint8)),
        'magenta': cp.asnumpy((magenta_mask * 255).astype(cp.uint8)),
        'yellow': cp.asnumpy((yellow_mask * 255).astype(cp.uint8)),
        'black': cp.asnumpy((black_mask * 255).astype(cp.uint8)),
    }

    # Free GPU memory
    del image_gpu, b, g, r, black_mask, white_mask, colored, cyan_mask, magenta_mask, yellow_mask
    cp.get_default_memory_pool().free_all_blocks()

    return result


if __name__ == '__main__':
    print_gpu_status()
