"""CMYK Cluster Bullseye Renderer.

Renders detected CMYK clusters as visual patterns (concentric circles)
to validate detection quality and create artistic representations.

The bullseye pattern draws concentric circles for each cluster:
- Yellow (outermost) → Magenta → Cyan → Black (innermost)
- Circle radii are proportional to pixel counts (area-based)
- RGB overlaps emerge naturally at circle intersections
"""

import math
from typing import Dict, List, Tuple

import cv2
import numpy as np

from dotmatrix.cluster_pixel_counter import ClusterResult


# CMYK colors in RGB format
COLORS = {
    'yellow': (255, 255, 0),
    'magenta': (255, 0, 255),
    'cyan': (0, 255, 255),
    'black': (0, 0, 0),
}


def calculate_cumulative_radii(cluster: ClusterResult) -> Dict[str, float]:
    """Calculate cumulative radii for each CMYK layer.

    Each layer's radius is based on cumulative pixel area from innermost
    to outermost. Black is innermost, then cyan, magenta, yellow.

    The formula is: radius = sqrt(cumulative_area / pi)

    Args:
        cluster: ClusterResult with pixel counts for each channel

    Returns:
        Dict with 'black', 'cyan', 'magenta', 'yellow' radius values
    """
    # Calculate cumulative areas from innermost to outermost
    # Black is innermost
    k_area = cluster.black

    # Cyan includes: K + C + overlaps with C (blue=C∩M, green=C∩Y)
    c_area = k_area + cluster.cyan + cluster.blue + cluster.green

    # Magenta includes: above + M + overlaps with M (red=M∩Y, blue already counted)
    m_area = c_area + cluster.magenta + cluster.red

    # Yellow includes: above + Y + overlaps with Y (red, green already counted)
    y_area = m_area + cluster.yellow

    def radius_from_area(area: float) -> float:
        """Convert pixel area to circle radius."""
        if area <= 0:
            return 0.0
        return math.sqrt(area / math.pi)

    return {
        'black': radius_from_area(k_area),
        'cyan': radius_from_area(c_area),
        'magenta': radius_from_area(m_area),
        'yellow': radius_from_area(y_area),
    }


def render_single_cluster(
    cluster: ClusterResult,
    image_shape: Tuple[int, int],
    background: np.ndarray = None
) -> np.ndarray:
    """Render a single cluster as a bullseye pattern.

    Draws concentric circles from outermost (yellow) to innermost (black).
    This layering order ensures the correct visual appearance.

    Args:
        cluster: ClusterResult with pixel counts and center position
        image_shape: (height, width) of the output image
        background: Optional existing image to draw on. If None, creates white.

    Returns:
        RGB numpy array with the rendered cluster
    """
    h, w = image_shape

    if background is None:
        # Create white background
        output = np.full((h, w, 3), 255, dtype=np.uint8)
    else:
        output = background

    # Calculate radii for each layer
    radii = calculate_cumulative_radii(cluster)

    # Get center coordinates
    cx, cy = cluster.x, cluster.y

    # Draw from outermost to innermost (Y → M → C → K)
    # This ensures inner layers appear on top
    layer_order = ['yellow', 'magenta', 'cyan', 'black']

    for layer in layer_order:
        radius = int(round(radii[layer]))
        if radius > 0:
            color = COLORS[layer]
            # cv2.circle uses BGR, but we want RGB output
            # Since we're drawing to RGB array directly, use RGB color
            cv2.circle(output, (cx, cy), radius, color, thickness=-1)

    return output


def render_bullseye(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    skip_partial: bool = False
) -> np.ndarray:
    """Render multiple clusters as bullseye patterns.

    Main entry point for reconstituting cluster data as a visual image.
    Each cluster is rendered as concentric circles centered at its
    black dot position.

    Args:
        clusters: List of ClusterResult from cluster_pixel_counter
        image_shape: (height, width) of the output image
        skip_partial: If True, skip clusters marked as partial (at edges)

    Returns:
        RGB numpy array with all clusters rendered
    """
    h, w = image_shape

    # Create white background
    output = np.full((h, w, 3), 255, dtype=np.uint8)

    if not clusters:
        return output

    # Render each cluster
    for cluster in clusters:
        # Skip partial clusters if requested
        if skip_partial and cluster.partial:
            continue

        render_single_cluster(cluster, image_shape, background=output)

    return output
