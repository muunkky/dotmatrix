"""Sliding window processing for large CMYK halftone images.

V1 Implementation - Process large images in overlapping tiles to manage memory
while maintaining accuracy at tile boundaries.

Strategy:
- Detect circles in full window (including overlap region)
- Cluster and count pixels in full window
- Render ALL clusters in the tile (including overlap region)
- Copy only the core region to output (avoiding duplicates)

This ensures:
- Boundary circles are detected by both adjacent tiles
- Each circle's CENTER determines which tile "owns" it for statistics
- Flower petals from overlap clusters extend into copied core region
- No seam artifacts from clipped flowers at tile boundaries
"""

import math
from typing import Tuple, List, Dict, Optional, Callable
from pathlib import Path

import cv2
import numpy as np

from .convex_detector import (
    detect_circles_cmyk_separation,
    separate_cmyk_inks,
    generate_tiles,
)
from .cluster_pixel_counter import cluster_and_count_pixels, ClusterResult
from .circle_renderer import render_flower_global_blend


def process_sliding_window(
    image_bgr: np.ndarray,
    window_size: int = 500,
    overlap: int = 100,
    min_radius: int = 10,
    max_radius: int = 50,
    petal_distance: float = 0.35,
    render_scale: int = 1,
    color_mode: str = 'absolute',
    debug: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Tuple[np.ndarray, List[ClusterResult], Dict]:
    """Process large image using sliding window approach.

    Args:
        image_bgr: Input image in BGR format (cv2 native)
        window_size: Size of each processing window in pixels
        overlap: Overlap between adjacent windows (should be >= 2*max_radius)
        min_radius: Minimum circle radius for detection
        max_radius: Maximum circle radius for detection
        petal_distance: Petal center distance as fraction of black radius
        render_scale: Output scale multiplier
        color_mode: 'full' (7-color) or 'absolute' (CMYK only)
        debug: Enable debug output
        progress_callback: Optional callback(tile_num, total_tiles, status)

    Returns:
        Tuple of:
        - reconstituted: Rendered output image (BGR)
        - all_clusters: List of all ClusterResult objects (global coordinates)
        - stats: Dictionary with processing statistics
    """
    h, w = image_bgr.shape[:2]

    # Convert to RGB for detection
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

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

    # Output image (at render_scale)
    out_h = h * render_scale
    out_w = w * render_scale
    output = np.ones((out_h, out_w, 3), dtype=np.uint8) * 255  # White background

    # Collect all clusters for statistics
    all_clusters = []

    # Statistics
    stats = {
        'total_tiles': total_tiles,
        'window_size': window_size,
        'overlap': overlap,
        'clusters_per_tile': [],
        'clusters_rendered_per_tile': [],
    }

    for tile_idx, (x1, y1, x2, y2) in enumerate(tiles):
        if progress_callback:
            progress_callback(tile_idx + 1, total_tiles, f"Processing tile {tile_idx + 1}/{total_tiles}")

        if debug:
            print(f"\nTile {tile_idx + 1}/{total_tiles}: ({x1},{y1}) to ({x2},{y2})")

        # Extract tile (BGR for ink separation)
        tile_bgr = image_bgr[y1:y2, x1:x2]
        tile_rgb = image_rgb[y1:y2, x1:x2]
        tile_h, tile_w = tile_bgr.shape[:2]

        # Calculate core region (exclude overlap from rendering)
        # Core is where this tile is responsible for rendering
        core_x1 = overlap // 2 if x1 > 0 else 0
        core_y1 = overlap // 2 if y1 > 0 else 0
        core_x2 = tile_w - overlap // 2 if x2 < w else tile_w
        core_y2 = tile_h - overlap // 2 if y2 < h else tile_h

        if debug:
            print(f"  Core region: ({core_x1},{core_y1}) to ({core_x2},{core_y2})")

        # 1. Get ink masks for this tile
        ink_masks = separate_cmyk_inks(tile_bgr)

        # 2. Cluster and count pixels
        tile_clusters = cluster_and_count_pixels(
            cyan_mask=ink_masks['cyan'],
            magenta_mask=ink_masks['magenta'],
            yellow_mask=ink_masks['yellow'],
            black_mask=ink_masks['black'],
            image_shape=(tile_h, tile_w),
            color_mode=color_mode.lower()
        )

        stats['clusters_per_tile'].append(len(tile_clusters))

        if debug:
            print(f"  Found {len(tile_clusters)} clusters")

        # 3. Filter to clusters whose center is in core region
        core_clusters = []
        for cluster in tile_clusters:
            cx, cy = cluster.x, cluster.y
            if core_x1 <= cx < core_x2 and core_y1 <= cy < core_y2:
                core_clusters.append(cluster)

        stats['clusters_rendered_per_tile'].append(len(core_clusters))

        if debug:
            print(f"  Rendering {len(core_clusters)} clusters (center in core)")

        # 4. Render ALL clusters in tile (not just core)
        # This ensures flowers in the overlap region contribute petals
        # that extend into the core region. We still only COPY the core
        # region to output, but rendering all clusters prevents clipping.
        if tile_clusters:
            # Render this tile's contribution
            tile_output = render_flower_global_blend(
                tile_clusters,  # Changed from core_clusters
                (tile_h, tile_w),
                petal_distance=petal_distance,
                scale=render_scale,
                skip_partial=False,
                rotation_mode='fixed',
                base_rotation=0.0
            )

            # Copy rendered clusters to output (only core region)
            # Scale coordinates for output
            out_x1 = (x1 + core_x1) * render_scale
            out_y1 = (y1 + core_y1) * render_scale
            out_x2 = (x1 + core_x2) * render_scale
            out_y2 = (y1 + core_y2) * render_scale

            # Source region from tile output
            src_x1 = core_x1 * render_scale
            src_y1 = core_y1 * render_scale
            src_x2 = core_x2 * render_scale
            src_y2 = core_y2 * render_scale

            # Copy with blending (multiply for subtractive)
            src_region = tile_output[src_y1:src_y2, src_x1:src_x2]

            # Simple overwrite for now (clusters don't cross boundaries)
            # Only copy non-white pixels to preserve existing content
            mask = np.any(src_region < 255, axis=2)
            output[out_y1:out_y2, out_x1:out_x2][mask] = src_region[mask]

        # 5. Add clusters to global list (with coordinate offset)
        for cluster in tile_clusters:
            # Create offset cluster for global coordinates
            offset_cluster = ClusterResult(
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
            all_clusters.append(offset_cluster)

    # Summary stats
    stats['total_clusters'] = len(all_clusters)
    stats['total_rendered'] = sum(stats['clusters_rendered_per_tile'])

    if debug:
        print(f"\nSummary:")
        print(f"  Total clusters detected: {len(all_clusters)}")
        print(f"  Total clusters rendered: {stats['total_rendered']}")

    return output, all_clusters, stats


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
