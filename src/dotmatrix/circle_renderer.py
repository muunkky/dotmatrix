"""Circle-based CMYK Cluster Renderer.

Renders detected CMYK clusters as circles instead of squares.
Supports multiple layouts:
- flower: Black center with color "petals" around it
- concentric: Nested circles (rings)
- scattered: Random positions within cluster bounds

The flower pattern places the black dot at center with C, M, Y circles
positioned around it like petals. Overlaps can naturally create RGB
secondary colors through subtractive blending.

V1 BASELINE (2024-11-30)
========================
Locked parameters for V1 benchmark. Future optimizations should compare against this baseline.

Parameters:
- petal_distance = 0.35 (fraction of black radius for petal center placement)
- petal_angles = [0°, 90°, 180°] (N/E/S - 90° apart to reduce neighbor overlap)
- render_method = flower (with global CMY blending)
- cmyk_mode = absolute (count each CMYK channel separately)

Baseline Accuracy:
- chunk_center.png: C +0.2%, M -1.2%, Y -0.6%, K +0.0% (Total: 2.0%)
- source_quantized.png: C -0.3%, M -0.4%, Y -0.6%, K +0.0% (Total: 1.3%)

Key algorithms:
- Global black mask: Build all black circles first, then optimize petals against global mask
- Exposed area optimization: Test cv2.circle renders against global black mask
- CMYK decomposition: C=C+G+B, M=M+R+B, Y=Y+R+G (secondaries contribute to primaries)
"""

import math
import hashlib
import random
from typing import Dict, List, Tuple, Optional, Callable
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
# Black at center, CMY at 90° apart (N/E/S) to reduce neighbor black overlap
PETAL_ANGLES = {
    'cyan': 0,       # Top (North)
    'magenta': 90,   # Right (East)
    'yellow': 180,   # Bottom (South)
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


def find_best_radius_for_pixels(
    target_pixels: int,
    image_size: Tuple[int, int] = (100, 100),
    center: Optional[Tuple[int, int]] = None
) -> Tuple[int, int, int]:
    """Find integer radius that draws closest to target pixel count.

    cv2.circle with LINE_AA draws more pixels than theoretical area (π*r²).
    This function tests actual cv2 rendering to find the best integer radius.

    Args:
        target_pixels: Desired number of pixels
        image_size: Canvas size for testing (h, w)
        center: Circle center for testing (defaults to image center)

    Returns:
        Tuple of (best_radius, actual_pixels, error) where error = actual - target
    """
    if target_pixels <= 0:
        return (0, 0, 0)

    h, w = image_size
    if center is None:
        cx, cy = w // 2, h // 2
    else:
        cx, cy = center

    # Start with theoretical radius
    theoretical_r = radius_from_pixels(target_pixels)
    r_low = max(1, int(theoretical_r) - 2)
    r_high = int(theoretical_r) + 2

    best_radius = r_low
    best_actual = 0
    best_error = float('inf')

    for r in range(r_low, r_high + 1):
        if r <= 0:
            continue
        # Test actual pixel count
        test_img = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(test_img, (cx, cy), r, 255, thickness=-1, lineType=cv2.LINE_AA)
        actual = int(np.sum(test_img > 0))
        error = abs(actual - target_pixels)

        if error < best_error:
            best_error = error
            best_radius = r
            best_actual = actual

    return (best_radius, best_actual, best_actual - target_pixels)


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

    # Maximum: when petal center is inside black (petal_distance < 1),
    # most of the petal is hidden. Need larger upper bound.
    # 10x is safe for typical petal_distance=0.5 configurations.
    r_max = radius_from_pixels(target_exposed * 10)

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
        """Calculate the area of this circle in pixels.

        Returns:
            Area as π * r² (floating point)
        """
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
    petal_distance: float = 0.35,
    scale: int = 1,
    rotation_offset: float = 0.0,
    blend_overlaps: bool = False
) -> Dict[str, int]:
    """Render a single cluster as a flower pattern.

    Algorithm (CMYK Flower Rendering):
        1. Decompose RGB overlaps into CMY primaries:
           Co = cyan + green + blue (all pixels containing cyan ink)
           Mo = magenta + red + blue (all pixels containing magenta ink)
           Yo = yellow + red + green (all pixels containing yellow ink)
        2. Black circle at center with radius Rb where π*Rb² = Ko
        3. Petals placed at distance Rb * petal_distance (center inside black)
        4. Each petal radius sized so EXPOSED area = target pixel count
           (exposed area = petal area - lens overlap with black)
        5. Draw petals with subtractive CMY blending (overlaps create RGB)

    Args:
        image: BGR image to draw on (modified in place)
        cluster: Cluster data with CMYK and RGB pixel counts
        used: Boolean array tracking used pixels
        petal_distance: Fraction of black radius for petal center placement
            (0.5 = center halfway to edge, inside black circle)
        scale: Scale factor for positioning
        rotation_offset: Angle offset in degrees to rotate all petals
        blend_overlaps: If True, use subtractive CMY blending at petal overlaps
            (C+M=Blue, C+Y=Green, M+Y=Red, C+M+Y≈Black)

    Returns:
        Dict of actual pixels drawn per color
    """
    cx = cluster.x * scale
    cy = cluster.y * scale

    drawn = {}
    h, w = image.shape[:2]

    # Calculate black radius first (always uses simple formula)
    black_radius = radius_from_pixels(cluster.black)

    # CMYK Decomposition: Add RGB overlaps to their parent CMY primaries
    # Co = cyan + green (C∩Y) + blue (C∩M)
    # Mo = magenta + red (M∩Y) + blue (C∩M)
    # Yo = yellow + red (M∩Y) + green (C∩Y)
    decomposed_counts = {
        'cyan': cluster.cyan + cluster.green + cluster.blue,
        'magenta': cluster.magenta + cluster.red + cluster.blue,
        'yellow': cluster.yellow + cluster.red + cluster.green,
    }

    # Calculate radii and positions for each color
    radii = {'black': black_radius}
    positions = {}

    for color in ['yellow', 'magenta', 'cyan']:
        pixel_count = decomposed_counts[color]
        if pixel_count <= 0:
            radii[color] = 0
            positions[color] = (cx, cy)
            continue

        # Calculate preliminary radius to compute distance
        preliminary_radius = radius_from_pixels(pixel_count)
        if preliminary_radius <= 0:
            radii[color] = 0
            positions[color] = (cx, cy)
            continue

        # Position petal with rotation offset
        angle_deg = PETAL_ANGLES[color] + rotation_offset
        angle_rad = math.radians(angle_deg - 90)  # -90 to start from top

        # Distance from center: fraction of black radius (places petal center inside black)
        dist = black_radius * petal_distance

        # Calculate petal radius so EXPOSED area equals target pixel count
        # (exposed area = petal area - lens overlap with black circle)
        if black_radius > 0 and dist < black_radius + preliminary_radius:
            # Petal overlaps with black - use exposed area formula
            petal_radius = radius_for_exposed_pixels(pixel_count, black_radius, dist)
        else:
            # No overlap with black - simple area formula
            petal_radius = preliminary_radius

        radii[color] = petal_radius
        petal_x = cx + dist * math.cos(angle_rad)
        petal_y = cy + dist * math.sin(angle_rad)
        positions[color] = (petal_x, petal_y)

    if blend_overlaps:
        # Subtractive CMY blending mode
        # CORRECT ORDER: Black first, then CMY petals around it (exposed crescent only)

        def make_circle_mask_with_radius(center_x, center_y, int_radius):
            """Create circle mask using pre-computed integer radius."""
            mask = np.zeros((h, w), dtype=bool)
            if int_radius > 0:
                temp = np.zeros((h, w), dtype=np.uint8)
                cv2.circle(temp, (int(center_x), int(center_y)),
                          int_radius, 255, thickness=-1, lineType=cv2.LINE_AA)
                mask = temp > 0
            return mask

        # Find optimal integer radii that minimize pixel count error
        # This accounts for cv2.circle drawing more pixels than theoretical area
        black_int_r, black_actual, black_error = find_best_radius_for_pixels(
            cluster.black, (h, w), (int(cx), int(cy))
        )

        # 1. Draw black center FIRST
        black_mask = make_circle_mask_with_radius(cx, cy, black_int_r)
        if cluster.black > 0:
            image[black_mask & ~used] = COLORS_BGR['black']
            drawn['black'] = int(np.sum(black_mask & ~used))
            used[black_mask] = True

        # 2. Create CMY petal masks with optimized radii
        # For petals, we need to find radii such that EXPOSED area = target
        # This is more complex since exposed = petal_circle - black_circle intersection
        petal_int_radii = {}
        petal_errors = {}
        for color in ['cyan', 'magenta', 'yellow']:
            target = decomposed_counts[color]
            if target <= 0:
                petal_int_radii[color] = 0
                petal_errors[color] = 0
                continue
            # Find radius that gives approximately correct exposed pixels
            # Start with the theoretical radius and test nearby integer values
            px, py = positions[color]
            best_r, best_exposed, best_err = 0, 0, float('inf')
            theoretical_r = radii[color]
            for test_r in range(max(1, int(theoretical_r) - 3), int(theoretical_r) + 4):
                # Compute actual exposed pixels with this integer radius
                test_mask = make_circle_mask_with_radius(px, py, test_r)
                exposed_count = int(np.sum(test_mask & ~black_mask))
                err = abs(exposed_count - target)
                if err < best_err:
                    best_err = err
                    best_r = test_r
                    best_exposed = exposed_count
            petal_int_radii[color] = best_r
            petal_errors[color] = best_exposed - target

        mask_c = make_circle_mask_with_radius(*positions['cyan'], petal_int_radii['cyan'])
        mask_m = make_circle_mask_with_radius(*positions['magenta'], petal_int_radii['magenta'])
        mask_y = make_circle_mask_with_radius(*positions['yellow'], petal_int_radii['yellow'])

        # 3. Get EXPOSED area only (subtract black circle)
        exposed_c = mask_c & ~black_mask
        exposed_m = mask_m & ~black_mask
        exposed_y = mask_y & ~black_mask

        # 4. Apply subtractive CMY blending to exposed areas
        any_exposed = exposed_c | exposed_m | exposed_y
        if np.any(any_exposed):
            # Create local blend buffer starting with white
            blend_result = np.full((h, w, 3), 255, dtype=np.uint8)

            # Subtractive: each ink removes its complementary RGB channel
            # Cyan removes Red (channel 2 in BGR)
            blend_result[exposed_c, 2] = 0
            # Magenta removes Green (channel 1 in BGR)
            blend_result[exposed_m, 1] = 0
            # Yellow removes Blue (channel 0 in BGR)
            blend_result[exposed_y, 0] = 0

            # Copy blended result to image (only unused pixels)
            update_mask = any_exposed & ~used
            image[update_mask] = blend_result[update_mask]
            used[any_exposed] = True

            # Count drawn pixels per color (exposed area only)
            drawn['cyan'] = int(np.sum(exposed_c)) if radii['cyan'] > 0 else 0
            drawn['magenta'] = int(np.sum(exposed_m)) if radii['magenta'] > 0 else 0
            drawn['yellow'] = int(np.sum(exposed_y)) if radii['yellow'] > 0 else 0
    else:
        # Original non-blending mode: draw each petal directly
        # Order: Y, M, C (so cyan is most visible, typically largest)
        for color in ['yellow', 'magenta', 'cyan']:
            pixel_count = decomposed_counts[color]
            if pixel_count <= 0:
                continue

            petal_x, petal_y = positions[color]
            if radii[color] <= 0:
                continue

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
    petal_distance: float = 0.35,
    scale: int = 1,
    skip_partial: bool = False,
    rotation_mode: str = 'fixed',
    base_rotation: float = 0.0,
    rotation_seed: Optional[int] = None,
    blend_overlaps: bool = False,
    use_exposed_area: bool = True  # Deprecated, kept for backward compatibility
) -> np.ndarray:
    """Render all clusters as flower patterns.

    Each cluster becomes a flower with black center and CMY petals.
    Petal radii are automatically sized so their EXPOSED area (after
    black circle overlap) matches the target pixel count.

    Args:
        clusters: List of ClusterResult from detection
        image_shape: (height, width) of original image
        petal_distance: Fraction of black radius for petal center placement
            (0.5 = center halfway to edge of black, inside black circle)
        scale: Output scale factor
        skip_partial: If True, skip edge clusters
        rotation_mode: 'fixed', 'random', or 'cluster-hash'
        base_rotation: Base angle offset in degrees
        rotation_seed: Random seed for 'random' mode
        blend_overlaps: If True, use subtractive CMY blending at petal overlaps
            (C+M=Blue, C+Y=Green, M+Y=Red, C+M+Y≈Black)
        use_exposed_area: Deprecated - exposed area sizing is always used

    Returns:
        BGR numpy array with rendered flowers
    """
    # When blending overlaps globally, use dedicated function
    # This ensures cross-cluster overlaps blend correctly
    if blend_overlaps:
        return render_flower_global_blend(
            clusters=clusters,
            image_shape=image_shape,
            petal_distance=petal_distance,
            scale=scale,
            skip_partial=skip_partial,
            rotation_mode=rotation_mode,
            base_rotation=base_rotation,
            rotation_seed=rotation_seed,
        )

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
            blend_overlaps=blend_overlaps
        )

        for color, count in drawn.items():
            total_drawn[color] = total_drawn.get(color, 0) + count

    return output


def render_flower_global_blend(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    petal_distance: float = 0.35,
    scale: int = 1,
    skip_partial: bool = False,
    rotation_mode: str = 'fixed',
    base_rotation: float = 0.0,
    rotation_seed: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, str, Optional[dict]], None]] = None,
) -> np.ndarray:
    """Render all clusters with global CMY subtractive blending.

    Unlike render_flower() which processes clusters sequentially, this function
    collects ALL petal geometry first, then blends globally. This ensures
    cross-cluster overlaps blend correctly (e.g., cyan from cluster A overlapping
    magenta from cluster B creates blue).

    Algorithm:
        1. Phase 1 - Collect geometry: Calculate positions and radii for all
           petals and black circles from all clusters
        2. Phase 2 - Build global masks: Create mask images for each CMY color
           containing ALL circles of that color from ALL clusters
        3. Phase 3 - Subtractive blend: Start with white, subtract channels
           based on global ink coverage:
           - Remove R where cyan ink exists
           - Remove G where magenta ink exists
           - Remove B where yellow ink exists
        4. Phase 4 - Add black: Draw all black circles on top

    Args:
        clusters: List of ClusterResult from detection
        image_shape: (height, width) of original image
        petal_distance: Fraction of black radius for petal center placement
        scale: Output scale factor
        skip_partial: If True, skip edge clusters
        rotation_mode: 'fixed', 'random', or 'cluster-hash'
        base_rotation: Base angle offset in degrees
        rotation_seed: Random seed for 'random' mode
        progress_callback: Optional callback function for progress updates.
            Called with (current, total, phase_name, metadata) where:
            - current: Current progress count
            - total: Total count for this phase
            - phase_name: String describing current phase (e.g., 'petal_optimization')
            - metadata: Optional dict with additional info

    Returns:
        BGR numpy array with globally blended flowers
    """
    h, w = image_shape
    out_h, out_w = h * scale, w * scale

    # Phase 1a: Collect all BLACK geometry first
    # We need the global black mask before optimizing petal radii
    black_circles = []  # (cx, cy, float_radius)
    cluster_data = []   # Store cluster info for Phase 1c

    for cluster in clusters:
        if skip_partial and cluster.partial:
            continue

        cx = cluster.x * scale
        cy = cluster.y * scale

        # Compute rotation for this cluster
        rotation = compute_cluster_rotation(
            cluster.x, cluster.y,
            mode=rotation_mode,
            base_rotation=base_rotation,
            seed=rotation_seed
        )

        # Calculate black radius
        black_radius = radius_from_pixels(cluster.black)
        if cluster.black > 0 and black_radius > 0:
            black_circles.append((cx, cy, black_radius))

        # CMYK Decomposition for petal sizing
        decomposed_counts = {
            'cyan': cluster.cyan + cluster.green + cluster.blue,
            'magenta': cluster.magenta + cluster.red + cluster.blue,
            'yellow': cluster.yellow + cluster.red + cluster.green,
        }

        # Store for Phase 1c
        cluster_data.append({
            'cx': cx, 'cy': cy,
            'black_radius': black_radius,
            'rotation': rotation,
            'decomposed_counts': decomposed_counts,
        })

    # Phase 1b: Build GLOBAL black mask
    # This accounts for ALL black circles, not just the cluster's own
    def build_global_black_mask(circle_list):
        """Build a boolean mask of all black circles for exposed pixel calculations.

        Creates a composite mask where pixels covered by any black circle are True.
        Uses find_best_radius_for_pixels for accurate circle sizing.

        Args:
            circle_list: List of (center_x, center_y, radius) tuples

        Returns:
            Boolean numpy array (out_h, out_w) where True = black coverage
        """
        mask = np.zeros((out_h, out_w), dtype=np.uint8)
        for cx, cy, r in circle_list:
            if r > 0:
                target_pixels = int(math.pi * r * r)
                best_r, _, _ = find_best_radius_for_pixels(
                    target_pixels, (out_h, out_w), (int(cx), int(cy))
                )
                cv2.circle(mask, (int(cx), int(cy)), best_r,
                          255, thickness=-1, lineType=cv2.LINE_AA)
        return mask > 0

    global_black_mask = build_global_black_mask(black_circles)

    # Phase 1c: Optimize petal radii against GLOBAL black mask
    cyan_circles = []
    magenta_circles = []
    yellow_circles = []

    def count_exposed_pixels_local(center_x, center_y, radius):
        """Count exposed pixels using local ROI instead of full canvas.

        OPTIMIZATION: Instead of creating a full (out_h, out_w) mask and doing
        a full-canvas boolean operation, we only work with a small local region
        around the petal center. This reduces complexity from O(canvas_size) to
        O(flower_size) per test - approximately 10,000x faster for large images.
        """
        if radius <= 0:
            return 0

        int_r = int(radius)
        margin = int_r + 2  # Small margin for anti-aliasing

        # Compute local ROI bounds
        x1 = max(0, int(center_x) - margin)
        y1 = max(0, int(center_y) - margin)
        x2 = min(out_w, int(center_x) + margin + 1)
        y2 = min(out_h, int(center_y) + margin + 1)

        # Skip if completely out of bounds
        if x1 >= x2 or y1 >= y2:
            return 0

        # Create small local mask
        local_h, local_w = y2 - y1, x2 - x1
        local_mask = np.zeros((local_h, local_w), dtype=np.uint8)

        # Circle center in local coordinates
        local_cx = center_x - x1
        local_cy = center_y - y1

        cv2.circle(local_mask, (int(local_cx), int(local_cy)), int_r,
                  255, thickness=-1, lineType=cv2.LINE_AA)

        # Extract local ROI from global black mask
        local_black = global_black_mask[y1:y2, x1:x2]

        # Count exposed pixels (petal pixels not covered by black)
        exposed_count = int(np.sum((local_mask > 0) & ~local_black))
        return exposed_count

    total_clusters = len(cluster_data)
    log_interval = max(1, total_clusters // 20)  # Log every 5%

    for cluster_idx, data in enumerate(cluster_data):
        # Progress callback and logging every 5%
        if cluster_idx % log_interval == 0 or cluster_idx == total_clusters - 1:
            pct = (cluster_idx + 1) * 100 // total_clusters
            if progress_callback:
                progress_callback(
                    cluster_idx + 1,
                    total_clusters,
                    'petal_optimization',
                    {'percentage': pct}
                )
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

            # Calculate preliminary radius
            preliminary_radius = radius_from_pixels(pixel_count)
            if preliminary_radius <= 0:
                continue

            # Position petal with rotation offset
            angle_deg = PETAL_ANGLES[color] + rotation
            angle_rad = math.radians(angle_deg - 90)

            # Distance from center
            dist = black_radius * petal_distance

            # Calculate theoretical petal radius for exposed area
            if black_radius > 0 and dist < black_radius + preliminary_radius:
                theoretical_r = radius_for_exposed_pixels(pixel_count, black_radius, dist)
            else:
                theoretical_r = preliminary_radius

            if theoretical_r <= 0:
                continue

            petal_x = cx + dist * math.cos(angle_rad)
            petal_y = cy + dist * math.sin(angle_rad)

            # Find optimal integer radius by testing actual exposed pixels
            # against GLOBAL black mask (includes ALL neighboring blacks)
            # Note: Narrow search range works better because petals are centered near
            # their own cluster - aggressive radius increase doesn't help reach distant
            # neighboring blacks, it just adds extra non-overlapping area
            #
            # OPTIMIZED: Uses local ROI instead of full-canvas mask operations.
            # This reduces per-test complexity from O(canvas_size) to O(flower_size).
            best_r, best_exposed, best_err = 0, 0, float('inf')
            for test_r in range(max(1, int(theoretical_r) - 3), int(theoretical_r) + 4):
                exposed_count = count_exposed_pixels_local(petal_x, petal_y, test_r)
                err = abs(exposed_count - pixel_count)
                if err < best_err:
                    best_err = err
                    best_r = test_r
                    best_exposed = exposed_count

            # Store optimized integer radius
            if color == 'cyan':
                cyan_circles.append((petal_x, petal_y, best_r))
            elif color == 'magenta':
                magenta_circles.append((petal_x, petal_y, best_r))
            elif color == 'yellow':
                yellow_circles.append((petal_x, petal_y, best_r))

    # Phase 2: Build global petal masks
    def build_petal_mask(circle_list):
        """Build mask for petal circles (radii already optimized in Phase 1c)."""
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
    # Reuse global_black_mask from Phase 1b
    global_black = global_black_mask

    # Phase 3: Subtractive CMY blending
    # Start with white (255, 255, 255)
    output = np.full((out_h, out_w, 3), 255, dtype=np.uint8)

    # Get exposed petal areas (excluding black overlap)
    exposed_cyan = global_cyan & ~global_black
    exposed_magenta = global_magenta & ~global_black
    exposed_yellow = global_yellow & ~global_black

    # Apply subtractive blending to exposed areas
    # Cyan removes Red (channel 2 in BGR)
    output[exposed_cyan, 2] = 0
    # Magenta removes Green (channel 1 in BGR)
    output[exposed_magenta, 1] = 0
    # Yellow removes Blue (channel 0 in BGR)
    output[exposed_yellow, 0] = 0

    # Phase 4: Draw black on top
    output[global_black] = COLORS_BGR['black']

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
        """Create a boolean circle mask at the specified position and radius.

        Args:
            center_x: X coordinate of circle center
            center_y: Y coordinate of circle center
            radius: Circle radius in pixels

        Returns:
            Boolean numpy array (h, w) where True = inside circle
        """
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
