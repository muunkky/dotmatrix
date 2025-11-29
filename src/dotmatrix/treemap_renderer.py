"""Treemap-based CMYK Cluster Renderer.

Renders detected CMYK clusters as treemap-style subdivided rectangles
where each color gets a proportional area within fixed cluster bounds.

Unlike the block renderer (stacked horizontal bars), this renderer:
- Fills a fixed rectangular region for each cluster
- Uses slice-and-dice algorithm to subdivide proportionally
- Never overflows cluster boundaries
- Produces WinDirStat-style visualization

ADR: See docs/adr/ADR-004-treemap-renderer.md
"""

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
    horizontal: bool = True
) -> np.ndarray:
    """Render a single cluster as a treemap.

    Each color gets a proportional area within the cluster bounds.
    Uses slice-and-dice algorithm for subdivision.

    Args:
        cluster: ClusterResult with pixel counts and center position
        image: BGR numpy array to draw on (modified in place)
        cluster_size: Size of the cluster rectangle
        horizontal: If True, first split is horizontal

    Returns:
        The modified image (same array as input)
    """
    # Get cluster bounds
    bounds = get_cluster_bounds(cluster, cluster_size)

    # Get pixel counts for all colors
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
    horizontal: bool = True
) -> np.ndarray:
    """Render multiple clusters as treemap patterns.

    Main entry point for treemap-based reconstitution. Each cluster is
    rendered as a subdivided rectangle with proportional color areas.

    Args:
        clusters: List of ClusterResult from cluster_pixel_counter
        image_shape: (height, width) of the output image
        cluster_size: Size of each cluster rectangle
        skip_partial: If True, skip clusters marked as partial (at edges)
        horizontal: If True, first split is horizontal

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

        render_single_treemap(cluster, output, cluster_size=cluster_size, horizontal=horizontal)

    return output
