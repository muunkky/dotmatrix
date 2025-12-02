"""Sliding window processing for large CMYK halftone images.

V2 Implementation - Two-phase approach:
1. Global Detection: Scan all tiles, collect cluster centers, deduplicate globally
2. Global Rendering: Render once from the deduplicated global cluster list

This eliminates seam artifacts by:
- Only keeping cluster centers that are in each tile's core region (not overlap)
- Global deduplication ensures each cluster is processed exactly once
- Single render pass means no tile stitching artifacts
"""

import math
from typing import Tuple, List, Dict, Optional, Callable
from pathlib import Path

import cv2
import numpy as np
from scipy.spatial import KDTree

from .convex_detector import (
    detect_circles_cmyk_separation,
    separate_cmyk_inks,
    generate_tiles,
)
from .cluster_pixel_counter import (
    cluster_and_count_pixels,
    ClusterResult,
    find_black_dot_centers_distance_transform,
    find_black_dot_centers,
)
from .circle_renderer import render_flower_global_blend
from .gpu import gpu_separate_cmyk_inks


def process_sliding_window(
    image_bgr: np.ndarray,
    window_size: int = 500,
    overlap: int = 100,
    min_radius: int = 1,
    max_radius: int = 50,
    petal_distance: float = 0.35,
    render_scale: int = 1,
    color_mode: str = 'absolute',
    separation_method: str = 'distance_transform',
    min_dot_distance: int = 10,
    anchor_method: str = 'centroid',
    debug: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    use_gpu: bool = False,
) -> Tuple[np.ndarray, List[ClusterResult], Dict]:
    """Process large image using two-phase sliding window approach.

    Phase 1: Global Detection
    - Scan all tiles for cluster centers
    - Only keep centers in each tile's core region (not overlap)
    - Deduplicate globally to ensure each cluster is processed once

    Phase 2: Global Rendering
    - Render all clusters in a single pass
    - No tile stitching = no seam artifacts

    Args:
        image_bgr: Input image in BGR format (cv2 native)
        window_size: Size of each processing window in pixels
        overlap: Overlap between adjacent windows (should be >= 2*max_radius)
        min_radius: Minimum circle radius for detection
        max_radius: Maximum circle radius for detection
        petal_distance: Petal center distance as fraction of black radius
        render_scale: Output scale multiplier
        color_mode: 'full' (7-color) or 'absolute' (CMYK only)
        separation_method: 'distance_transform' (default) or 'connected'
        min_dot_distance: Minimum distance between dot centers
        anchor_method: 'centroid' (default, uses dot centers) or 'nearest_pixel' (legacy)
        debug: Enable debug output
        progress_callback: Optional callback(tile_num, total_tiles, status)

    Returns:
        Tuple of:
        - reconstituted: Rendered output image (BGR)
        - all_clusters: List of all ClusterResult objects (global coordinates)
        - stats: Dictionary with processing statistics
    """
    h, w = image_bgr.shape[:2]

    # Ensure overlap is sufficient for boundary detection
    min_overlap = max_radius * 2
    if overlap < min_overlap:
        overlap = min_overlap
        if debug:
            print(f"Adjusted overlap to {overlap} (2x max_radius)")

    # Ensure window_size is larger than overlap (need room for core region)
    min_window = overlap * 2  # At least 2x overlap for meaningful core
    if window_size < min_window:
        window_size = min_window
        if debug:
            print(f"Adjusted window_size to {window_size} (2x overlap)")

    # Generate tiles
    tiles = generate_tiles((h, w), window_size, overlap)
    total_tiles = len(tiles)

    if debug:
        print(f"Image size: {w}x{h}")
        print(f"Window size: {window_size}, overlap: {overlap}")
        print(f"Generated {total_tiles} tiles")

    # Statistics
    stats = {
        'total_tiles': total_tiles,
        'window_size': window_size,
        'overlap': overlap,
        'clusters_per_tile': [],
        'clusters_rendered_per_tile': [],
    }

    # =========================================================================
    # PHASE 1: Global Detection - collect cluster centers from all tiles
    # =========================================================================
    if debug:
        print("\n=== PHASE 1: Global Detection ===")

    all_clusters: List[ClusterResult] = []

    for tile_idx, (x1, y1, x2, y2) in enumerate(tiles):
        if progress_callback:
            progress_callback(tile_idx + 1, total_tiles, f"Detecting tile {tile_idx + 1}/{total_tiles}")

        if debug:
            print(f"\nTile {tile_idx + 1}/{total_tiles}: ({x1},{y1}) to ({x2},{y2})")

        # Extract tile (BGR for ink separation)
        tile_bgr = image_bgr[y1:y2, x1:x2]
        tile_h, tile_w = tile_bgr.shape[:2]

        # Calculate core region - where this tile "owns" cluster centers
        # Clusters in the overlap region will be handled by adjacent tiles
        core_x1 = overlap // 2 if x1 > 0 else 0
        core_y1 = overlap // 2 if y1 > 0 else 0
        core_x2 = tile_w - overlap // 2 if x2 < w else tile_w
        core_y2 = tile_h - overlap // 2 if y2 < h else tile_h

        if debug:
            print(f"  Core region: ({core_x1},{core_y1}) to ({core_x2},{core_y2})")

        # Get ink masks for this tile (GPU-accelerated when enabled)
        if use_gpu:
            ink_masks = gpu_separate_cmyk_inks(tile_bgr)
        else:
            ink_masks = separate_cmyk_inks(tile_bgr)

        # Detect and count clusters
        tile_clusters = cluster_and_count_pixels(
            cyan_mask=ink_masks['cyan'],
            magenta_mask=ink_masks['magenta'],
            yellow_mask=ink_masks['yellow'],
            black_mask=ink_masks['black'],
            image_shape=(tile_h, tile_w),
            color_mode=color_mode.lower(),
            separation_method=separation_method,
            min_dot_distance=min_dot_distance,
            anchor_method=anchor_method,
            use_gpu=use_gpu,
            debug=debug
        )

        stats['clusters_per_tile'].append(len(tile_clusters))

        if debug:
            print(f"  Found {len(tile_clusters)} clusters in tile")

        # CRITICAL: Only keep clusters whose center is in CORE region
        # This ensures each cluster is owned by exactly one tile
        core_clusters = []
        for cluster in tile_clusters:
            cx, cy = cluster.x, cluster.y
            if core_x1 <= cx < core_x2 and core_y1 <= cy < core_y2:
                # Convert to global coordinates
                global_cluster = ClusterResult(
                    x=cluster.x + x1,
                    y=cluster.y + y1,
                    cyan=cluster.cyan,
                    magenta=cluster.magenta,
                    yellow=cluster.yellow,
                    black=cluster.black,
                    red=cluster.red,
                    green=cluster.green,
                    blue=cluster.blue,
                    partial=cluster.partial
                )
                core_clusters.append(global_cluster)

        stats['clusters_rendered_per_tile'].append(len(core_clusters))
        all_clusters.extend(core_clusters)

        if debug:
            print(f"  Kept {len(core_clusters)} clusters (center in core)")

    # Global deduplication using KD-tree (in case any edge effects)
    if len(all_clusters) > 1:
        all_clusters = _deduplicate_clusters(all_clusters, min_dot_distance // 2, debug)

    stats['total_clusters'] = len(all_clusters)
    stats['total_rendered'] = len(all_clusters)

    if debug:
        print(f"\n=== Phase 1 Complete ===")
        print(f"  Total clusters after dedup: {len(all_clusters)}")

    # =========================================================================
    # PHASE 2: Global Rendering - render all clusters in one pass
    # =========================================================================
    if debug:
        print("\n=== PHASE 2: Global Rendering ===")

    # Create render progress callback wrapper for CLI display
    def render_progress(current, total, phase, metadata=None):
        """Internal callback to display render progress."""
        if progress_callback:
            gpu_str = "GPU" if metadata and metadata.get('gpu') else "CPU"
            pct = metadata.get('percentage', 0) if metadata else 0
            progress_callback(
                current, total,
                f"[{gpu_str}] Rendering {len(all_clusters)} clusters ({pct}%)"
            )

    # Render all clusters globally - no tile stitching!
    if use_gpu:
        from .gpu_renderer import render_flower_global_blend_gpu
        output = render_flower_global_blend_gpu(
            all_clusters,
            (h, w),
            petal_distance=petal_distance,
            scale=render_scale,
            skip_partial=False,
            rotation_mode='fixed',
            base_rotation=0.0,
            use_gpu=True,
            progress_callback=render_progress,
        )
    else:
        output = render_flower_global_blend(
            all_clusters,
            (h, w),
            petal_distance=petal_distance,
            scale=render_scale,
            skip_partial=False,
            rotation_mode='fixed',
            base_rotation=0.0,
            progress_callback=render_progress,
        )

    if debug:
        print(f"\n=== Summary ===")
        print(f"  Total clusters: {len(all_clusters)}")
        print(f"  Output size: {output.shape[1]}x{output.shape[0]}")

    return output, all_clusters, stats


def _deduplicate_clusters(
    clusters: List[ClusterResult],
    min_distance: int,
    debug: bool = False
) -> List[ClusterResult]:
    """Remove duplicate clusters that are too close together.

    Uses KD-tree for efficient spatial queries. When duplicates are found,
    keeps the one with the most total pixels (most complete detection).

    Args:
        clusters: List of ClusterResult objects
        min_distance: Minimum distance between cluster centers
        debug: Enable debug output

    Returns:
        Deduplicated list of ClusterResult objects
    """
    if len(clusters) <= 1 or min_distance <= 0:
        return clusters

    # Build KD-tree from cluster positions
    positions = np.array([[c.x, c.y] for c in clusters])
    tree = KDTree(positions)

    # Find clusters to keep (mark duplicates)
    keep = [True] * len(clusters)

    for i, cluster in enumerate(clusters):
        if not keep[i]:
            continue

        # Find nearby clusters
        nearby_indices = tree.query_ball_point([cluster.x, cluster.y], min_distance)

        for j in nearby_indices:
            if j <= i or not keep[j]:
                continue

            # Compare total pixels - keep the one with more
            total_i = cluster.cyan + cluster.magenta + cluster.yellow + cluster.black
            total_j = clusters[j].cyan + clusters[j].magenta + clusters[j].yellow + clusters[j].black

            if total_j > total_i:
                keep[i] = False
                break
            else:
                keep[j] = False

    deduplicated = [c for c, k in zip(clusters, keep) if k]

    if debug and len(deduplicated) < len(clusters):
        print(f"  Deduplication: {len(clusters)} -> {len(deduplicated)} clusters")

    return deduplicated


def calculate_optimal_window_size(
    image_shape: Tuple[int, int],
    max_radius: int = 50,
    target_memory_mb: int = 500
) -> int:
    """Calculate optimal window size based on image and memory constraints.

    Args:
        image_shape: (height, width) of image
        max_radius: Maximum circle radius
        target_memory_mb: Target memory usage in MB

    Returns:
        Recommended window size in pixels
    """
    h, w = image_shape[:2]

    # Minimum window size (3x overlap = 6x max_radius)
    min_window = max_radius * 6

    # Estimate memory per pixel (rough: 3 channels + masks + temp buffers)
    bytes_per_pixel = 20  # Conservative estimate

    # Calculate window size for target memory
    target_pixels = (target_memory_mb * 1024 * 1024) // bytes_per_pixel
    target_window = int(math.sqrt(target_pixels))

    # Clamp to reasonable range
    window_size = max(min_window, min(target_window, min(h, w)))

    return window_size
