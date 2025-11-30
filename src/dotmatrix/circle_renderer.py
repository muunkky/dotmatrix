"""Circle-based CMYK Cluster Renderer.

Renders detected CMYK clusters as circles instead of squares.
Supports multiple layouts:
- flower: Black center with color "petals" around it
- concentric: Nested circles (rings)
- scattered: Random positions within cluster bounds

The flower pattern places the black dot at center with C, M, Y circles
positioned around it like petals. Overlaps can naturally create RGB
secondary colors through subtractive blending.
"""

import math
import hashlib
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import cv2
import numpy as np

from dotmatrix.cluster_pixel_counter import ClusterResult


def compute_cluster_rotation(
    cluster_x: int,
    cluster_y: int,
    mode: str = 'fixed',
    base_rotation: float = 0.0,
    seed: Optional[int] = None
) -> float:
    """Compute rotation offset for a cluster based on mode.

    Args:
        cluster_x, cluster_y: Cluster center position
        mode: Rotation mode - 'fixed', 'random', or 'cluster-hash'
        base_rotation: Base angle offset in degrees (added to all modes)
        seed: Random seed for 'random' mode (for reproducibility)

    Returns:
        Rotation offset in degrees (0-360)
    """
    if mode == 'fixed':
        return base_rotation

    elif mode == 'random':
        # Use random rotation (optionally seeded)
        if seed is not None:
            rng = random.Random(seed + cluster_x * 10000 + cluster_y)
        else:
            rng = random.Random()
        return base_rotation + rng.uniform(0, 360)

    elif mode == 'cluster-hash':
        # Deterministic rotation based on position hash
        # Hash the position to get a consistent angle
        pos_str = f"{cluster_x},{cluster_y}"
        hash_bytes = hashlib.md5(pos_str.encode()).digest()
        # Use first 4 bytes as unsigned int, normalize to 0-360
        hash_val = int.from_bytes(hash_bytes[:4], 'little')
        rotation = (hash_val % 3600) / 10.0  # 0.0 to 360.0 degrees
        return base_rotation + rotation

    else:
        return base_rotation


# CMYK colors in BGR format (for cv2)
COLORS_BGR = {
    'cyan': (255, 255, 0),      # BGR
    'magenta': (255, 0, 255),   # BGR
    'yellow': (0, 255, 255),    # BGR
    'black': (0, 0, 0),         # BGR
    'white': (255, 255, 255),   # BGR
    # Secondary colors from overlaps
    'red': (0, 0, 255),         # M + Y
    'green': (0, 255, 0),       # C + Y
    'blue': (255, 0, 0),        # C + M
}

# Petal angles for flower layout (degrees from top, clockwise)
# Black at center, CMY at 120° apart
PETAL_ANGLES = {
    'cyan': 0,       # Top
    'magenta': 120,  # Bottom-right
    'yellow': 240,   # Bottom-left
}


def radius_from_pixels(pixel_count: int) -> float:
    """Calculate circle radius to achieve given pixel count.

    Area = π * r²
    r = sqrt(Area / π)
    """
    if pixel_count <= 0:
        return 0.0
    return math.sqrt(pixel_count / math.pi)


def pixels_from_radius(radius: float) -> int:
    """Calculate pixel count from circle radius."""
    if radius <= 0:
        return 0
    return int(math.pi * radius * radius)


def lens_area(r1: float, r2: float, d: float) -> float:
    """Calculate intersection area of two overlapping circles.

    Args:
        r1: Radius of first circle
        r2: Radius of second circle
        d: Distance between circle centers

    Returns:
        Area of the lens-shaped intersection region.
    """
    if d <= 0:
        # Concentric circles - intersection is smaller circle
        return math.pi * min(r1, r2) ** 2

    if d >= r1 + r2:
        # No overlap
        return 0.0

    if d <= abs(r1 - r2):
        # One circle fully inside the other
        return math.pi * min(r1, r2) ** 2

    # General lens area formula (two circular segments)
    # https://mathworld.wolfram.com/Circle-CircleIntersection.html
    try:
        part1 = r1**2 * math.acos((d**2 + r1**2 - r2**2) / (2 * d * r1))
        part2 = r2**2 * math.acos((d**2 + r2**2 - r1**2) / (2 * d * r2))
        part3 = 0.5 * math.sqrt((r1 + r2 - d) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))
        return part1 + part2 - part3
    except (ValueError, ZeroDivisionError):
        # Numerical edge cases
        return 0.0


def exposed_area(petal_radius: float, black_radius: float, distance: float) -> float:
    """Calculate the visible area of a petal after overlap with black circle.

    Args:
        petal_radius: Radius of the petal circle
        black_radius: Radius of the black center circle
        distance: Distance between petal center and black center

    Returns:
        Exposed (visible) area of the petal circle.
    """
    total_area = math.pi * petal_radius ** 2
    overlap = lens_area(petal_radius, black_radius, distance)
    return max(0.0, total_area - overlap)


def radius_for_exposed_pixels(
    target_exposed: int,
    black_radius: float,
    distance: float,
    tolerance: float = 0.5,
    max_iterations: int = 50
) -> float:
    """Find petal radius such that exposed area equals target pixel count.

    Uses binary search to find the radius that, after subtracting overlap
    with the black circle, gives the target exposed area.

    Args:
        target_exposed: Target number of exposed (visible) pixels
        black_radius: Radius of the black center circle
        distance: Distance from petal center to black center
        tolerance: Acceptable error in pixels (default 0.5)
        max_iterations: Maximum binary search iterations (default 50)

    Returns:
        Radius that achieves the target exposed area.
    """
    if target_exposed <= 0:
        return 0.0

    if black_radius <= 0:
        # No black circle to hide behind
        return radius_from_pixels(target_exposed)

    # Binary search bounds
    # Minimum: radius that gives target area without any overlap
    r_min = radius_from_pixels(target_exposed)

    # Maximum: assume worst case where half the circle is hidden
    # Need radius that gives 2x the target area
    r_max = radius_from_pixels(target_exposed * 3)

    for _ in range(max_iterations):
        r_mid = (r_min + r_max) / 2
        current_exposed = exposed_area(r_mid, black_radius, distance)

        if abs(current_exposed - target_exposed) <= tolerance:
            return r_mid

        if current_exposed < target_exposed:
            r_min = r_mid
        else:
            r_max = r_mid

    return (r_min + r_max) / 2


@dataclass
class Circle:
    """A circle with position and radius."""
    x: float
    y: float
    radius: float
    color: str

    @property
    def area(self) -> float:
        return math.pi * self.radius * self.radius


def draw_circle_exact(
    image: np.ndarray,
    cx: float,
    cy: float,
    target_pixels: int,
    color_bgr: Tuple[int, int, int],
    used: Optional[np.ndarray] = None
) -> int:
    """Draw a filled circle with exact pixel count.

    Uses anti-aliased circle drawing, then counts actual pixels filled.
    If used array provided, skips already-used pixels.

    Returns actual number of pixels drawn.
    """
    if target_pixels <= 0:
        return 0

    h, w = image.shape[:2]
    radius = radius_from_pixels(target_pixels)

    # Draw filled circle
    cx_int, cy_int = int(round(cx)), int(round(cy))
    radius_int = max(1, int(round(radius)))

    # Create mask for this circle
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, (cx_int, cy_int), radius_int, 255, thickness=-1, lineType=cv2.LINE_AA)

    # Find pixels in circle
    circle_pixels = np.where(mask > 0)

    drawn = 0
    for py, px in zip(circle_pixels[0], circle_pixels[1]):
        if used is not None and used[py, px]:
            continue
        image[py, px] = color_bgr
        if used is not None:
            used[py, px] = True
        drawn += 1
        if drawn >= target_pixels:
            break

    return drawn


def render_flower_cluster(
    image: np.ndarray,
    cluster: ClusterResult,
    used: np.ndarray,
    petal_distance: float = 0.7,
    scale: int = 1,
    rotation_offset: float = 0.0,
    use_exposed_area: bool = False
) -> Dict[str, int]:
    """Render a single cluster as a flower pattern.

    Black circle at center, CMY circles as petals around it.
    Petals are positioned at 120° intervals, with distance from center
    proportional to their radii.

    Args:
        image: BGR image to draw on (modified in place)
        cluster: Cluster data with pixel counts
        used: Boolean array tracking used pixels
        petal_distance: How far petals extend (0.5 = touching, 1.0 = separated)
        scale: Scale factor for positioning
        rotation_offset: Angle offset in degrees to rotate all petals
        use_exposed_area: If True, size petals based on visible area after
            black overlap (requires larger radius to show same pixel count)

    Returns:
        Dict of actual pixels drawn per color
    """
    cx = cluster.x * scale
    cy = cluster.y * scale

    drawn = {}

    # Calculate black radius first (always uses simple formula)
    black_radius = radius_from_pixels(cluster.black)

    # Calculate radii for each color
    # For petals, we need to know the distance to black center to use exposed area
    radii = {'black': black_radius}

    # Draw petals first (behind black)
    # Order: Y, M, C (so cyan is most visible, typically largest)
    for color in ['yellow', 'magenta', 'cyan']:
        pixel_count = getattr(cluster, color)
        if pixel_count <= 0:
            continue

        # Calculate preliminary radius to compute distance
        preliminary_radius = radius_from_pixels(pixel_count)
        if preliminary_radius <= 0:
            continue

        # Position petal with rotation offset
        angle_deg = PETAL_ANGLES[color] + rotation_offset
        angle_rad = math.radians(angle_deg - 90)  # -90 to start from top

        # Distance from center: black radius + petal radius * distance factor
        dist = black_radius + preliminary_radius * petal_distance

        # Now calculate the actual radius
        if use_exposed_area and black_radius > 0:
            # Use exposed area formula - radius needed so visible area = pixel_count
            petal_radius = radius_for_exposed_pixels(pixel_count, black_radius, dist)
        else:
            petal_radius = preliminary_radius

        radii[color] = petal_radius

        petal_x = cx + dist * math.cos(angle_rad)
        petal_y = cy + dist * math.sin(angle_rad)

        # Draw with target pixel count (draw_circle_exact will draw up to this many)
        drawn[color] = draw_circle_exact(
            image, petal_x, petal_y,
            pixel_count, COLORS_BGR[color], used
        )

    # Draw black center last (on top)
    if cluster.black > 0:
        drawn['black'] = draw_circle_exact(
            image, cx, cy,
            cluster.black, COLORS_BGR['black'], used
        )

    return drawn


def render_flower(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    petal_distance: float = 0.7,
    scale: int = 1,
    skip_partial: bool = False,
    rotation_mode: str = 'fixed',
    base_rotation: float = 0.0,
    rotation_seed: Optional[int] = None,
    use_exposed_area: bool = False
) -> np.ndarray:
    """Render all clusters as flower patterns.

    Each cluster becomes a flower with black center and CMY petals.

    Args:
        clusters: List of ClusterResult from detection
        image_shape: (height, width) of original image
        petal_distance: How far petals extend from center (0.5-1.0)
        scale: Output scale factor
        skip_partial: If True, skip edge clusters
        rotation_mode: 'fixed', 'random', or 'cluster-hash'
        base_rotation: Base angle offset in degrees
        rotation_seed: Random seed for 'random' mode
        use_exposed_area: If True, size petals based on visible area after
            black overlap (more accurate visual proportions)

    Returns:
        BGR numpy array with rendered flowers
    """
    h, w = image_shape
    out_h, out_w = h * scale, w * scale

    # White background
    output = np.full((out_h, out_w, 3), 255, dtype=np.uint8)
    used = np.zeros((out_h, out_w), dtype=bool)

    total_drawn = {'cyan': 0, 'magenta': 0, 'yellow': 0, 'black': 0}

    for cluster in clusters:
        if skip_partial and cluster.partial:
            continue

        # Compute rotation for this cluster
        rotation = compute_cluster_rotation(
            cluster.x, cluster.y,
            mode=rotation_mode,
            base_rotation=base_rotation,
            seed=rotation_seed
        )

        drawn = render_flower_cluster(
            output, cluster, used,
            petal_distance=petal_distance,
            scale=scale,
            rotation_offset=rotation,
            use_exposed_area=use_exposed_area
        )

        for color, count in drawn.items():
            total_drawn[color] = total_drawn.get(color, 0) + count

    return output


def render_cmyk_blend_cluster(
    image: np.ndarray,
    cluster: ClusterResult,
    scale: int = 1
) -> None:
    """Render cluster with true CMYK subtractive blending.

    Draws CMY circles that overlap to create secondary colors naturally:
    - C ∩ M = Blue
    - C ∩ Y = Green
    - M ∩ Y = Red
    - C ∩ M ∩ Y ≈ Black

    The black circle is drawn separately on top.
    """
    cx = cluster.x * scale
    cy = cluster.y * scale

    h, w = image.shape[:2]

    # Create float image for blending (CMY subtractive)
    # Start with white (no ink)
    cmy_layer = np.ones((h, w, 3), dtype=np.float32)

    # Calculate radii
    r_cyan = radius_from_pixels(cluster.cyan)
    r_magenta = radius_from_pixels(cluster.magenta)
    r_yellow = radius_from_pixels(cluster.yellow)
    r_black = radius_from_pixels(cluster.black)

    # Create masks for each CMY color
    def make_mask(center_x, center_y, radius):
        mask = np.zeros((h, w), dtype=np.uint8)
        if radius > 0:
            cv2.circle(mask, (int(center_x), int(center_y)),
                      int(radius), 255, thickness=-1, lineType=cv2.LINE_AA)
        return mask > 0

    # Position CMY circles around center (same as flower but tighter)
    petal_dist = 0.5  # Closer together for more overlap

    positions = {}
    for color, angle_deg in PETAL_ANGLES.items():
        angle_rad = math.radians(angle_deg - 90)
        r = {'cyan': r_cyan, 'magenta': r_magenta, 'yellow': r_yellow}[color]
        dist = r * petal_dist
        positions[color] = (cx + dist * math.cos(angle_rad),
                           cy + dist * math.sin(angle_rad))

    # Apply CMY as subtractive (multiply)
    # Cyan removes Red channel
    mask_c = make_mask(*positions['cyan'], r_cyan)
    cmy_layer[mask_c, 2] = 0  # Remove R where cyan

    # Magenta removes Green channel
    mask_m = make_mask(*positions['magenta'], r_magenta)
    cmy_layer[mask_m, 1] = 0  # Remove G where magenta

    # Yellow removes Blue channel
    mask_y = make_mask(*positions['yellow'], r_yellow)
    cmy_layer[mask_y, 0] = 0  # Remove B where yellow

    # Convert back to uint8
    result = (cmy_layer * 255).astype(np.uint8)

    # Copy to image where we drew
    any_ink = mask_c | mask_m | mask_y
    image[any_ink] = result[any_ink]

    # Draw black circle on top
    if r_black > 0:
        cv2.circle(image, (int(cx), int(cy)), int(r_black),
                  COLORS_BGR['black'], thickness=-1, lineType=cv2.LINE_AA)


def render_cmyk_blend(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    scale: int = 1,
    skip_partial: bool = False
) -> np.ndarray:
    """Render clusters with true CMYK subtractive blending.

    CMY circles overlap to create secondary colors naturally.
    Black is drawn on top of the blended CMY.

    Args:
        clusters: List of ClusterResult from detection
        image_shape: (height, width) of original image
        scale: Output scale factor
        skip_partial: If True, skip edge clusters

    Returns:
        BGR numpy array with rendered image
    """
    h, w = image_shape
    out_h, out_w = h * scale, w * scale

    # White background
    output = np.full((out_h, out_w, 3), 255, dtype=np.uint8)

    for cluster in clusters:
        if skip_partial and cluster.partial:
            continue
        render_cmyk_blend_cluster(output, cluster, scale=scale)

    return output
