"""Block-based CMYK Cluster Renderer.

Renders detected CMYK clusters as horizontally stacked color bars for
100% pixel accuracy in reconstituted images.

Unlike the bullseye renderer (concentric circles), this renderer uses
rectangles which can exactly match any pixel count since:
    area = width × height (both integers)

Each cluster is rendered as vertically stacked color rows:
- Each color gets a row of fixed height (segment_height)
- Row width = pixel_count / segment_height
- Colors stacked top-to-bottom in LAYER_ORDER

This approach is designed for midtone printer overlap where each color
layer can be printed separately and stacked.

ADR: See docs/adr/ADR-003-block-renderer.md
"""

from typing import Dict, List, Tuple

import cv2
import numpy as np

from dotmatrix.cluster_pixel_counter import ClusterResult


# All 7 colors in BGR format (for cv2 compatibility)
# Same as cluster_renderer.py for consistency
COLORS = {
    'yellow': (0, 255, 255),    # BGR: B=0, G=255, R=255
    'red': (0, 0, 255),         # BGR: B=0, G=0, R=255 (M∩Y overlap)
    'green': (0, 255, 0),       # BGR: B=0, G=255, R=0 (C∩Y overlap)
    'magenta': (255, 0, 255),   # BGR: B=255, G=0, R=255
    'blue': (255, 0, 0),        # BGR: B=255, G=0, R=0 (C∩M overlap)
    'cyan': (255, 255, 0),      # BGR: B=255, G=255, R=0
    'black': (0, 0, 0),         # BGR: B=0, G=0, R=0
}

# Drawing order: top to bottom (outermost to innermost in terms of halftone)
# Yellow first (largest coverage), black last (smallest/innermost)
LAYER_ORDER = ['yellow', 'red', 'green', 'magenta', 'blue', 'cyan', 'black']

# CMYK-only mode: 4 colors without RGB overlaps
LAYER_ORDER_CMYK = ['yellow', 'magenta', 'cyan', 'black']


def calculate_bar_dimensions(
    cluster: ClusterResult,
    segment_height: int = 10,
    color_mode: str = 'full'
) -> Dict[str, Tuple[int, int, int, int]]:
    """Calculate rectangle bounds for each color segment.

    In fixed-segment mode (default), each color gets a horizontal stripe
    of fixed height. The stripe width is proportional to pixel count:
        width = pixel_count // segment_height

    Colors are stacked vertically from top to bottom in LAYER_ORDER.

    Args:
        cluster: ClusterResult with pixel counts and center position
        segment_height: Height in pixels for each color row (default 10)
        color_mode: 'full' for 7 colors, 'cmyk' for 4 colors only

    Returns:
        Dict mapping color name to (x1, y1, x2, y2) bounds for cv2.rectangle.
        x1, y1 is top-left corner; x2, y2 is bottom-right corner.
    """
    # Get pixel counts based on color mode
    if color_mode == 'cmyk':
        counts = {
            'yellow': cluster.yellow,
            'magenta': cluster.magenta,
            'cyan': cluster.cyan,
            'black': cluster.black,
        }
        layer_order = LAYER_ORDER_CMYK
    else:
        counts = {
            'yellow': cluster.yellow,
            'red': cluster.red,
            'green': cluster.green,
            'magenta': cluster.magenta,
            'blue': cluster.blue,
            'cyan': cluster.cyan,
            'black': cluster.black,
        }
        layer_order = LAYER_ORDER

    # Calculate bounds for each color row
    # Rows are centered horizontally at cluster.x
    # Rows are stacked vertically starting at cluster.y
    bounds = {}
    current_y = cluster.y

    for color in layer_order:
        pixel_count = counts[color]
        width = pixel_count // segment_height if segment_height > 0 else 0

        if width > 0:
            # Center the row horizontally at cluster.x
            x1 = cluster.x - width // 2
            # cv2.rectangle endpoint is inclusive, so x2 = x1 + width - 1
            x2 = x1 + width - 1
            y1 = current_y
            # cv2.rectangle endpoint is inclusive, so y2 = y1 + height - 1
            y2 = current_y + segment_height - 1
            bounds[color] = (x1, y1, x2, y2)
            current_y += segment_height
        else:
            # Zero-width segment
            bounds[color] = (cluster.x, current_y, cluster.x, current_y)

    return bounds


def render_single_block(
    cluster: ClusterResult,
    image: np.ndarray,
    segment_height: int = 10,
    color_mode: str = 'full'
) -> np.ndarray:
    """Render a single cluster as stacked color bars.

    Each color is rendered as a horizontal rectangle of fixed height,
    with width proportional to its pixel count.

    Args:
        cluster: ClusterResult with pixel counts and center position
        image: BGR numpy array to draw on (modified in place)
        segment_height: Height in pixels for each color row
        color_mode: 'full' for 7 colors, 'cmyk' for 4 colors only

    Returns:
        The modified image (same array as input)
    """
    # Calculate bounds for each color
    bounds = calculate_bar_dimensions(cluster, segment_height=segment_height, color_mode=color_mode)

    # Choose layer order based on color mode
    layer_order = LAYER_ORDER_CMYK if color_mode == 'cmyk' else LAYER_ORDER

    # Draw each color rectangle
    for color in layer_order:
        x1, y1, x2, y2 = bounds[color]

        # Only draw if width > 0
        if x2 > x1:
            cv2.rectangle(image, (x1, y1), (x2, y2), COLORS[color], thickness=-1)

    return image


def render_blocks(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    segment_height: int = 10,
    skip_partial: bool = False,
    color_mode: str = 'full'
) -> np.ndarray:
    """Render multiple clusters as stacked color bar patterns.

    Main entry point for block-based reconstitution. Each cluster is
    rendered as vertically stacked color rows centered at its position.

    Args:
        clusters: List of ClusterResult from cluster_pixel_counter
        image_shape: (height, width) of the output image
        segment_height: Height in pixels for each color row (default 10)
        skip_partial: If True, skip clusters marked as partial (at edges)
        color_mode: 'full' for 7 colors, 'cmyk' for 4 colors only

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

        render_single_block(cluster, output, segment_height=segment_height, color_mode=color_mode)

    return output
