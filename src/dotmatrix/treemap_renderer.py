"""Treemap-based CMYK Cluster Renderer.

Renders detected CMYK clusters as treemap-style subdivided rectangles
where each color gets a proportional area within cluster bounds.

Unlike the block renderer (stacked horizontal bars), this renderer:
- Can use fixed OR dynamic rectangular regions for each cluster
- Uses slice-and-dice algorithm to subdivide proportionally
- Never overflows cluster boundaries
- Produces WinDirStat-style visualization

Key modes:
- Fixed size: All clusters use same cluster_size (fast but loses pixels)
- Dynamic size: Each cluster sized to fit its exact pixel count (accurate)

ADR: See docs/adr/ADR-004-treemap-renderer.md
"""

import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import cv2
import numpy as np

from dotmatrix.cluster_pixel_counter import ClusterResult


# All 7 colors in BGR format (for cv2 compatibility)
COLORS = {
    'yellow': (0, 255, 255),    # BGR: B=0, G=255, R=255
    'red': (0, 0, 255),         # BGR: B=0, G=0, R=255 (M∩Y overlap)
    'green': (0, 255, 0),       # BGR: B=0, G=255, R=0 (C∩Y overlap)
    'magenta': (255, 0, 255),   # BGR: B=255, G=0, R=255
    'blue': (255, 0, 0),        # BGR: B=255, G=0, R=0 (C∩M overlap)
    'cyan': (255, 255, 0),      # BGR: B=255, G=255, R=0
    'black': (0, 0, 0),         # BGR: B=0, G=0, R=0
}

# Drawing order: largest to smallest coverage typically
# Yellow first (usually largest), black last
LAYER_ORDER = ['yellow', 'red', 'green', 'magenta', 'blue', 'cyan', 'black']

# CMYK-only mode: 4 colors without RGB overlaps
LAYER_ORDER_CMYK = ['yellow', 'magenta', 'cyan', 'black']


@dataclass
class Rectangle:
    """A rectangle with position and size."""
    x: int
    y: int
    width: int
    height: int

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def x2(self) -> int:
        """Right edge (exclusive)."""
        return self.x + self.width

    @property
    def y2(self) -> int:
        """Bottom edge (exclusive)."""
        return self.y + self.height


def slice_and_dice(
    rect: Rectangle,
    values: List[Tuple[str, int]],
    horizontal: bool = True
) -> Dict[str, Rectangle]:
    """Subdivide a rectangle using slice-and-dice algorithm.

    Slice-and-dice is the simplest treemap algorithm:
    - Alternates between horizontal and vertical splits
    - Each value gets proportional area
    - Simple but may produce elongated rectangles

    Args:
        rect: The rectangle to subdivide
        values: List of (name, count) tuples to allocate space for
        horizontal: If True, first split is horizontal (top to bottom)

    Returns:
        Dict mapping name to Rectangle for each value
    """
    if not values:
        return {}

    # Filter out zero values
    non_zero = [(name, count) for name, count in values if count > 0]
    if not non_zero:
        return {name: Rectangle(rect.x, rect.y, 0, 0) for name, _ in values}

    total = sum(count for _, count in non_zero)
    if total == 0:
        return {name: Rectangle(rect.x, rect.y, 0, 0) for name, _ in values}

    result = {}
    current_x = rect.x
    current_y = rect.y
    remaining_width = rect.width
    remaining_height = rect.height

    for i, (name, count) in enumerate(non_zero):
        # Calculate proportional size
        proportion = count / total

        is_last = (i == len(non_zero) - 1)

        if horizontal:
            # Split top to bottom
            if is_last:
                # Last item gets remaining height to avoid rounding gaps
                height = remaining_height
            else:
                height = max(1, int(rect.height * proportion))
                height = min(height, remaining_height)

            result[name] = Rectangle(rect.x, current_y, rect.width, height)
            current_y += height
            remaining_height -= height
        else:
            # Split left to right
            if is_last:
                # Last item gets remaining width to avoid rounding gaps
                width = remaining_width
            else:
                width = max(1, int(rect.width * proportion))
                width = min(width, remaining_width)

            result[name] = Rectangle(current_x, rect.y, width, rect.height)
            current_x += width
            remaining_width -= width

        # Recalculate total for remaining items
        total -= count

    # Add zero-sized rectangles for zero values
    for name, count in values:
        if name not in result:
            result[name] = Rectangle(rect.x, rect.y, 0, 0)

    return result


def render_exact_pixels(
    image: np.ndarray,
    center_x: int,
    center_y: int,
    values: List[Tuple[str, int]],
    max_width: int = 50
) -> None:
    """Render exact pixel counts for each color, centered at position.

    Instead of fitting into a fixed rectangle, this renders EXACTLY the
    requested number of pixels for each color by using horizontal strips
    of 1 pixel height.

    Args:
        image: BGR numpy array to draw on (modified in place)
        center_x, center_y: Center position for the cluster
        values: List of (color_name, pixel_count) tuples
        max_width: Maximum width per strip (affects aspect ratio)
    """
    # Filter out zero values
    non_zero = [(name, count) for name, count in values if count > 0]
    if not non_zero:
        return

    h, w = image.shape[:2]

    # Calculate total height needed (sum of all strip heights)
    total_height = sum(math.ceil(count / max_width) for _, count in non_zero)
    start_y = center_y - total_height // 2

    current_y = start_y
    for color_name, pixel_count in non_zero:
        if pixel_count <= 0:
            continue

        color_bgr = COLORS[color_name]

        # Fill strips of max_width until all pixels are placed
        remaining = pixel_count
        while remaining > 0:
            strip_width = min(remaining, max_width)
            strip_x = center_x - strip_width // 2

            # Clip to image bounds
            x1 = max(0, strip_x)
            x2 = min(w, strip_x + strip_width)
            y1 = max(0, current_y)
            y2 = min(h, current_y + 1)

            if x2 > x1 and y2 > y1:
                actual_width = x2 - x1
                image[y1:y2, x1:x2] = color_bgr
                remaining -= actual_width
            else:
                # Outside image bounds, just decrement
                remaining -= strip_width

            current_y += 1


def calculate_cluster_total(cluster: ClusterResult, color_mode: str = 'full') -> int:
    """Calculate total pixel count for a cluster.

    Args:
        cluster: ClusterResult with pixel counts
        color_mode: 'full' for 7 colors, 'cmyk' for 4 colors only

    Returns:
        Total pixel count to render
    """
    if color_mode == 'cmyk':
        return cluster.cyan + cluster.magenta + cluster.yellow + cluster.black
    else:
        return (cluster.cyan + cluster.magenta + cluster.yellow + cluster.black +
                cluster.red + cluster.green + cluster.blue)


def calculate_dynamic_size(total_pixels: int) -> int:
    """Calculate the square size needed to fit all pixels.

    For exact pixel count accuracy, we need a square with area >= total_pixels.

    Args:
        total_pixels: Total number of pixels to render

    Returns:
        Side length of square that can fit all pixels
    """
    if total_pixels <= 0:
        return 1
    return math.ceil(math.sqrt(total_pixels))


def get_cluster_bounds(
    cluster: ClusterResult,
    cluster_size: int
) -> Rectangle:
    """Calculate the bounding rectangle for a cluster.

    Centers the rectangle at (cluster.x, cluster.y) with the given size.

    Args:
        cluster: ClusterResult with center position
        cluster_size: Width and height of the cluster rectangle

    Returns:
        Rectangle centered at cluster position
    """
    half = cluster_size // 2
    return Rectangle(
        x=cluster.x - half,
        y=cluster.y - half,
        width=cluster_size,
        height=cluster_size
    )


def render_single_treemap(
    cluster: ClusterResult,
    image: np.ndarray,
    cluster_size: int = 20,
    horizontal: bool = True,
    color_mode: str = 'full',
    dynamic: bool = False
) -> np.ndarray:
    """Render a single cluster as a treemap.

    Each color gets a proportional area within the cluster bounds.
    Uses slice-and-dice algorithm for subdivision.

    Args:
        cluster: ClusterResult with pixel counts and center position
        image: BGR numpy array to draw on (modified in place)
        cluster_size: Size of the cluster rectangle (ignored if dynamic=True)
        horizontal: If True, first split is horizontal
        color_mode: 'full' for 7 colors, 'cmyk' for 4 colors only
        dynamic: If True, calculate cluster_size from actual pixel count

    Returns:
        The modified image (same array as input)
    """
    # Calculate cluster size - dynamic or fixed
    if dynamic:
        total_pixels = calculate_cluster_total(cluster, color_mode)
        actual_size = calculate_dynamic_size(total_pixels)
    else:
        actual_size = cluster_size

    # Get cluster bounds
    bounds = get_cluster_bounds(cluster, actual_size)

    # Get pixel counts based on color mode
    if color_mode == 'cmyk':
        values = [
            ('yellow', cluster.yellow),
            ('magenta', cluster.magenta),
            ('cyan', cluster.cyan),
            ('black', cluster.black),
        ]
    else:
        values = [
            ('yellow', cluster.yellow),
            ('red', cluster.red),
            ('green', cluster.green),
            ('magenta', cluster.magenta),
            ('blue', cluster.blue),
            ('cyan', cluster.cyan),
            ('black', cluster.black),
        ]

    # Subdivide using slice-and-dice
    subdivisions = slice_and_dice(bounds, values, horizontal=horizontal)

    # Draw each color rectangle
    for color, rect in subdivisions.items():
        if rect.width > 0 and rect.height > 0:
            # Clip to image bounds
            x1 = max(0, rect.x)
            y1 = max(0, rect.y)
            x2 = min(image.shape[1], rect.x2)
            y2 = min(image.shape[0], rect.y2)

            if x2 > x1 and y2 > y1:
                # cv2.rectangle endpoint is inclusive
                cv2.rectangle(image, (x1, y1), (x2 - 1, y2 - 1), COLORS[color], thickness=-1)

    return image


def render_treemap(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    cluster_size: int = 20,
    skip_partial: bool = False,
    horizontal: bool = True,
    color_mode: str = 'full',
    dynamic: bool = False
) -> np.ndarray:
    """Render multiple clusters as treemap patterns.

    Main entry point for treemap-based reconstitution. Each cluster is
    rendered as a subdivided rectangle with proportional color areas.

    Args:
        clusters: List of ClusterResult from cluster_pixel_counter
        image_shape: (height, width) of the output image
        cluster_size: Size of each cluster rectangle (ignored if dynamic=True)
        skip_partial: If True, skip clusters marked as partial (at edges)
        horizontal: If True, first split is horizontal
        color_mode: 'full' for 7 colors, 'cmyk' for 4 colors only
        dynamic: If True, size each cluster to fit its exact pixel count

    Returns:
        BGR numpy array with all clusters rendered (cv2 native format)
    """
    h, w = image_shape

    # Create white background
    output = np.full((h, w, 3), 255, dtype=np.uint8)

    if not clusters:
        return output

    # Render each cluster
    for cluster in clusters:
        if skip_partial and cluster.partial:
            continue

        render_single_treemap(
            cluster, output,
            cluster_size=cluster_size,
            horizontal=horizontal,
            color_mode=color_mode,
            dynamic=dynamic
        )

    return output


def render_exact(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    skip_partial: bool = False,
    color_mode: str = 'full',
    scale: int = 2
) -> np.ndarray:
    """Render clusters with EXACT pixel counts per color.

    Each cluster is rendered as a square block centered at its original
    (x, y) position (scaled). Within each block, colors are stacked row by row.

    Uses scale factor to ensure clusters don't overlap. At scale=2, there's
    enough room between cluster positions to fit all pixels without overlap.

    Args:
        clusters: List of ClusterResult from cluster_pixel_counter
        image_shape: (height, width) of the ORIGINAL image
        skip_partial: If True, skip clusters marked as partial (at edges)
        color_mode: 'full' for 7 colors, 'cmyk' for 4 colors only
        scale: Output scale factor. Use scale>=2 for no overlap.

    Returns:
        BGR numpy array with all clusters rendered.
        Output size is (height * scale, width * scale).
    """
    h, w = image_shape
    out_h, out_w = h * scale, w * scale

    # Create white background at scaled size
    output = np.full((out_h, out_w, 3), 255, dtype=np.uint8)

    # Track which pixels are already used (to prevent overlap loss)
    used = np.zeros((out_h, out_w), dtype=bool)

    if not clusters:
        return output

    # Filter clusters
    active_clusters = [c for c in clusters if not (skip_partial and c.partial)]
    if not active_clusters:
        return output

    # Render each cluster at its scaled position
    for cluster in active_clusters:
        # Get cluster's pixel counts
        if color_mode == 'cmyk':
            values = [
                ('yellow', cluster.yellow),
                ('magenta', cluster.magenta),
                ('cyan', cluster.cyan),
                ('black', cluster.black),
            ]
        else:
            values = [
                ('yellow', cluster.yellow),
                ('red', cluster.red),
                ('green', cluster.green),
                ('magenta', cluster.magenta),
                ('blue', cluster.blue),
                ('cyan', cluster.cyan),
                ('black', cluster.black),
            ]

        # Calculate total pixels and block size
        total_pixels = sum(count for _, count in values)
        if total_pixels <= 0:
            continue

        block_size = math.ceil(math.sqrt(total_pixels))

        # Calculate centroid of filled pixels (relative to block origin)
        # Pixels fill row by row, so we can calculate centroid analytically
        centroid_x = 0.0
        centroid_y = 0.0
        pixel_idx = 0
        for _, count in values:
            for _ in range(count):
                lx = pixel_idx % block_size
                ly = pixel_idx // block_size
                centroid_x += lx
                centroid_y += ly
                pixel_idx += 1
        if total_pixels > 0:
            centroid_x /= total_pixels
            centroid_y /= total_pixels

        # Position block so centroid aligns with cluster center
        center_x = cluster.x * scale
        center_y = cluster.y * scale
        block_x = int(center_x - centroid_x)
        block_y = int(center_y - centroid_y)

        # Clamp block position to stay within image bounds (prevents pixel loss)
        if block_x < 0:
            block_x = 0
        elif block_x + block_size > out_w:
            block_x = out_w - block_size
        if block_y < 0:
            block_y = 0
        elif block_y + block_size > out_h:
            block_y = out_h - block_size

        # Fill block with colors (row by row within block)
        # If a pixel is already used, find next available spot
        local_x = 0
        local_y = 0

        for color_name, target_pixels in values:
            if target_pixels <= 0:
                continue

            color_bgr = COLORS[color_name]
            placed = 0

            while placed < target_pixels:
                px = block_x + local_x
                py = block_y + local_y

                # Check if within bounds and not already used
                if 0 <= py < out_h and 0 <= px < out_w and not used[py, px]:
                    output[py, px] = color_bgr
                    used[py, px] = True
                    placed += 1

                # Move to next position in block
                local_x += 1
                if local_x >= block_size:
                    local_x = 0
                    local_y += 1

                # If we've exhausted the block, spiral outward to find space
                if local_y >= block_size:
                    # Find nearest unused pixel
                    found = False
                    for radius in range(1, max(out_h, out_w)):
                        for dy in range(-radius, radius + 1):
                            for dx in range(-radius, radius + 1):
                                if abs(dx) == radius or abs(dy) == radius:
                                    ny = block_y + block_size // 2 + dy
                                    nx = block_x + block_size // 2 + dx
                                    if 0 <= ny < out_h and 0 <= nx < out_w and not used[ny, nx]:
                                        output[ny, nx] = color_bgr
                                        used[ny, nx] = True
                                        placed += 1
                                        found = True
                                        break
                            if found:
                                break
                        if found:
                            break
                    if not found:
                        break  # No more space

    return output
