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

V2 ENHANCEMENTS (2026-01-05)
=============================
Jitter/randomization support for breaking up grid patterns:
- Position jitter: Add Gaussian noise to circle positions
- Size jitter: Add Gaussian noise to circle radii
- Reproducible with seed parameter
- Default: disabled (jitter_position=0, jitter_size=0)
"""

import math
import hashlib
import random
import time
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from dotmatrix.cluster_pixel_counter import ClusterResult
from dotmatrix.logger import get_logger
from dotmatrix.jitter import apply_position_jitter, apply_size_jitter
from dotmatrix.centroid_drift import compute_color_centroid_from_mask, apply_centroid_position


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
        rotation = base_rotation + rng.uniform(0, 360)
        return rotation

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


from dotmatrix.colors import COLORS_BGR, PETAL_ANGLES


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
    blend_overlaps: bool = False,
    jitter_position: float = 0.0,
    jitter_size: float = 0.0,
    jitter_seed: Optional[int] = None,
    jitter_algorithm: str = 'gaussian'
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
        jitter_position: Position jitter strength (0-100, percentage of black radius)
        jitter_size: Size jitter strength (0-100, percentage of radius)
        jitter_seed: Random seed for reproducible jitter (optional)
        jitter_algorithm: 'gaussian' or 'uniform' distribution

    Returns:
        Dict of actual pixels drawn per color
    """
    cx = cluster.x * scale
    cy = cluster.y * scale

    # Apply position jitter to cluster center if enabled
    if jitter_position > 0 and jitter_seed is not None:
        # Generate unique seed for this cluster based on position
        cluster_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y)
        black_radius = radius_from_pixels(cluster.black)
        cx, cy = apply_position_jitter(
            cx, cy,
            position_pct=jitter_position,
            base_radius=black_radius * scale,
            seed=cluster_seed,
            algorithm=jitter_algorithm
        )

    drawn = {}
    h, w = image.shape[:2]

    # Calculate black radius first (always uses simple formula)
    black_radius = radius_from_pixels(cluster.black)

    # Apply size jitter to black radius if enabled
    if jitter_size > 0 and jitter_seed is not None:
        cluster_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y)
        black_radius = apply_size_jitter(
            black_radius,
            size_pct=jitter_size,
            seed=cluster_seed,
            algorithm=jitter_algorithm
        )

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
    use_exposed_area: bool = True,  # Deprecated, kept for backward compatibility
    jitter_position: float = 0.0,
    jitter_size: float = 0.0,
    jitter_seed: Optional[int] = None,
    jitter_algorithm: str = 'gaussian',
    jitter_exclude: str = '',
    drift: bool = False,
    drift_tolerance: float = 0.2,
    drift_max_iterations: int = 10,
    drift_max_step: float = 2.0,
    jitter_steps: int = 1,
    target_image: Optional[Path] = None,
    target_weight: float = 0.5,
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
        jitter_position: Position jitter strength (0-100, percentage of radius)
        jitter_size: Size jitter strength (0-100, percentage of radius)
        jitter_seed: Random seed for reproducible jitter (optional)
        jitter_algorithm: 'gaussian' or 'uniform' distribution
        target_image: Optional target halftone PNG for style transfer
        target_weight: Target matching strength (0.0-1.0, default: 0.5)

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
            jitter_position=jitter_position,
            jitter_size=jitter_size,
            jitter_seed=jitter_seed,
            jitter_algorithm=jitter_algorithm,
            jitter_exclude=jitter_exclude,
            drift=drift,
            drift_tolerance=drift_tolerance,
            drift_max_iterations=drift_max_iterations,
            drift_max_step=drift_max_step,
            jitter_steps=jitter_steps,
            target_image=target_image,
            target_weight=target_weight,
        )

    h, w = image_shape
    out_h, out_w = int(h * scale), int(w * scale)

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
            blend_overlaps=blend_overlaps,
            jitter_position=jitter_position,
            jitter_size=jitter_size,
            jitter_seed=jitter_seed,
            jitter_algorithm=jitter_algorithm
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
    jitter_position: float = 0.0,
    jitter_size: float = 0.0,
    jitter_seed: Optional[int] = None,
    jitter_algorithm: str = 'gaussian',
    jitter_exclude: str = '',
    drift: bool = False,
    drift_tolerance: float = 0.2,
    drift_max_iterations: int = 10,
    drift_max_step: float = 2.0,
    jitter_steps: int = 1,
    target_image: Optional[Path] = None,
    target_weight: float = 0.5,
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
    out_h, out_w = int(h * scale), int(w * scale)

    # Phase 1a: Collect all BLACK geometry first
    # We need the global black mask before optimizing petal radii
    black_circles = []  # (cx, cy, float_radius)
    cluster_data = []   # Store cluster info for Phase 1c

    for cluster in clusters:
        if skip_partial and cluster.partial:
            continue

        cx = cluster.x * scale
        cy = cluster.y * scale

        # Apply position jitter to cluster center if enabled
        if jitter_position > 0 and jitter_seed is not None:
            # Generate unique seed for this cluster based on position
            cluster_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y)
            black_radius_for_jitter = radius_from_pixels(cluster.black)
            cx, cy = apply_position_jitter(
                cx, cy,
                position_pct=jitter_position,
                base_radius=black_radius_for_jitter * scale,
                seed=cluster_seed,
                algorithm=jitter_algorithm
            )

        # Compute rotation for this cluster
        rotation = compute_cluster_rotation(
            cluster.x, cluster.y,
            mode=rotation_mode,
            base_rotation=base_rotation,
            seed=rotation_seed
        )

        # Calculate black radius
        black_radius = radius_from_pixels(cluster.black)
        
        # Apply size jitter to black radius if enabled
        if jitter_size > 0 and jitter_seed is not None:
            cluster_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y)
            black_radius = apply_size_jitter(
                black_radius,
                size_pct=jitter_size,
                seed=cluster_seed,
                algorithm=jitter_algorithm
            )
        
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
    phase_start_time = time.time()

    for cluster_idx, data in enumerate(cluster_data):
        # Progress callback and logging every 5%
        if cluster_idx % log_interval == 0 or cluster_idx == total_clusters - 1:
            current = cluster_idx + 1
            pct = current * 100 // total_clusters
            elapsed = time.time() - phase_start_time
            
            # Calculate throughput and ETA
            throughput = current / elapsed if elapsed > 0 else 0
            remaining = total_clusters - current
            eta_seconds = remaining / throughput if throughput > 0 else 0
            
            metadata = {
                'percentage': pct,
                'elapsed_seconds': elapsed,
                'throughput_per_second': throughput,
                'eta_seconds': eta_seconds,
            }
            
            if progress_callback:
                progress_callback(
                    current,
                    total_clusters,
                    'petal_optimization',
                    metadata
                )
            else:
                logger = get_logger(__name__)
                logger.info(f"    Phase 1c: Optimizing petals {current}/{total_clusters} ({pct}%) "
                           f"[{throughput:.1f} clusters/sec, ETA {eta_seconds:.1f}s]")

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
    out_h, out_w = int(h * scale), int(w * scale)

    # White background
    output = np.full((out_h, out_w, 3), 255, dtype=np.uint8)

    for cluster in clusters:
        if skip_partial and cluster.partial:
            continue
        render_cmyk_blend_cluster(output, cluster, scale=scale)

    return output


def _apply_jitter_to_circles(
    circles_by_color: Dict[str, List[Tuple[float, float, float]]],
    cluster_metadata: List[Dict[str, Any]],
    cluster_circle_map: List[Dict[str, Tuple[int, int]]],
    jitter_position: float,
    jitter_size: float,
    jitter_seed: int,
    jitter_algorithm: str,
    excluded_colors: set,
    scale: int,
) -> Dict[str, List[Tuple[float, float, float]]]:
    """Apply position and size jitter to existing circles.
    
    Used in multi-step jitter-drift pipeline to re-jitter circles at each step
    with a different seed, compounding the randomization effect.
    
    Args:
        circles_by_color: Dict mapping colors to list of (x, y, r) tuples
        cluster_metadata: List of cluster info dicts (cx, cy, black_radius, etc.)
        cluster_circle_map: List of dicts mapping color -> (circle_index, target_pixels)
        jitter_position: Position jitter percentage (0-100)
        jitter_size: Size jitter percentage (0-100)
        jitter_seed: Random seed for this jitter step
        jitter_algorithm: 'gaussian' or 'uniform'
        excluded_colors: Set of color names to exclude from jitter
        scale: Scale factor applied to coordinates
    
    Returns:
        Updated circles_by_color dict with jittered positions and sizes
    """
    # Convert to mutable lists
    circles_by_color = {
        color: list(circles)
        for color, circles in circles_by_color.items()
    }
    
    # Apply jitter to each cluster's circles
    for cluster_idx, circle_indices in enumerate(cluster_circle_map):
        if not circle_indices:
            continue
        
        metadata = cluster_metadata[cluster_idx]
        cluster_x = metadata.get('original_x', metadata['cx'] / scale)
        cluster_y = metadata.get('original_y', metadata['cy'] / scale)
        
        # Apply jitter to petal circles (CMY)
        for color in ['cyan', 'magenta', 'yellow']:
            if color in circle_indices and color not in excluded_colors:
                circle_idx, target_pixels = circle_indices[color]
                cx, cy, r = circles_by_color[color][circle_idx]
                
                # Position jitter
                if jitter_position > 0:
                    # Generate unique seed for this circle
                    color_offset = {'cyan': 100, 'magenta': 200, 'yellow': 300}[color]
                    circle_seed = jitter_seed + int(cluster_x) * 10000 + int(cluster_y) + color_offset
                    
                    # Jitter amount based on radius
                    jitter_amount = (r / scale) * (jitter_position / 100.0) * scale
                    
                    cx, cy = apply_position_jitter(
                        cx, cy,
                        position_pct=jitter_position,
                        base_radius=r,
                        seed=circle_seed,
                        algorithm=jitter_algorithm
                    )
                
                # Size jitter
                if jitter_size > 0:
                    color_offset = {'cyan': 100, 'magenta': 200, 'yellow': 300}[color]
                    circle_seed = jitter_seed + int(cluster_x) * 10000 + int(cluster_y) + color_offset + 1000
                    
                    r = apply_size_jitter(
                        r,
                        size_pct=jitter_size,
                        seed=circle_seed,
                        algorithm=jitter_algorithm
                    )
                
                circles_by_color[color][circle_idx] = (cx, cy, r)
        
        # Apply jitter to black circle if not excluded
        if 'black' not in excluded_colors:
            black_idx = metadata.get('black_circle_idx')
            if black_idx is not None:
                cx, cy, r = circles_by_color['black'][black_idx]
                
                if jitter_position > 0:
                    circle_seed = jitter_seed + int(cluster_x) * 10000 + int(cluster_y)
                    cx, cy = apply_position_jitter(
                        cx, cy,
                        position_pct=jitter_position,
                        base_radius=r,
                        seed=circle_seed,
                        algorithm=jitter_algorithm
                    )
                
                if jitter_size > 0:
                    circle_seed = jitter_seed + int(cluster_x) * 10000 + int(cluster_y) + 1000
                    r = apply_size_jitter(
                        r,
                        size_pct=jitter_size,
                        seed=circle_seed,
                        algorithm=jitter_algorithm
                    )
                
                circles_by_color['black'][black_idx] = (cx, cy, r)
    
    return circles_by_color


def _apply_drift_to_svg_circles(
    circles_by_color: Dict[str, List[Tuple[float, float, float]]],
    cluster_metadata: List[Dict[str, Any]],
    cluster_circle_map: List[Dict[str, Tuple[int, int]]],
    image_shape: Tuple[int, int],
    drift_tolerance: float,
    max_iterations: int,
    max_step_size: Optional[float] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, List[Tuple[float, float, float]]]:
    """Apply drift-balanced size compensation to SVG circles.
    
    Uses cluster-local rendering (option B) to measure actual vs target pixel masses,
    then iteratively adjusts circle radii to maintain color balance.
    
    Args:
        circles_by_color: Dict mapping colors to list of (x, y, r) tuples
        cluster_metadata: List of cluster info dicts (cx, cy, black_radius, decomposed_counts)
        cluster_circle_map: List of dicts mapping color -> (circle_index, target_pixels)
        image_shape: (height, width) for rendering
        drift_tolerance: Acceptable deviation from target mass (0.0-1.0)
        max_iterations: Maximum balancing iterations
        max_step_size: Optional maximum scale_factor per iteration (e.g., 2.0 = max 2x growth/shrink)
    
    Returns:
        Updated circles_by_color dict with adjusted radii
    """
    import numpy as np
    import cv2
    
    h, w = image_shape
    
    # Convert to mutable lists
    circles_by_color = {
        color: list(circles)
        for color, circles in circles_by_color.items()
    }
    
    # Iterate to balance
    for iteration in range(max_iterations):
        all_balanced = True
        adjustments_made = 0
        sum_squared_error = 0.0
        total_circles = 0
        
        # For each cluster, measure and adjust
        for cluster_idx, circle_indices in enumerate(cluster_circle_map):
            if not circle_indices:
                continue
            
            metadata = cluster_metadata[cluster_idx]
            cx_cluster = metadata['cx']
            cy_cluster = metadata['cy']
            black_r = metadata['black_radius']
            black_idx = metadata['black_circle_idx']
            
            # Get actual black circle (may be jittered)
            if black_idx is not None:
                black_circle = circles_by_color['black'][black_idx]
            else:
                # No black circle for this cluster
                black_circle = (cx_cluster, cy_cluster, black_r)
            
            # Gather all circles for this flower
            flower_circles = {
                'cyan': None,
                'magenta': None,
                'yellow': None,
                'black': black_circle  # Use actual jittered black circle
            }
            
            # Get current petal circles
            for color in ['cyan', 'magenta', 'yellow']:
                if color in circle_indices:
                    circle_idx, target_pixels = circle_indices[color]
                    flower_circles[color] = circles_by_color[color][circle_idx]
            
            # Measure exposed areas for full flower
            exposed_counts = _measure_full_flower_exposure(
                flower_circles['cyan'],
                flower_circles['magenta'],
                flower_circles['yellow'],
                flower_circles['black'],
                h, w
            )
            
            # Adjust each petal
            for color in ['cyan', 'magenta', 'yellow']:
                if color not in circle_indices:
                    continue
                
                circle_idx, target_pixels = circle_indices[color]
                cx, cy, r = circles_by_color[color][circle_idx]
                actual_pixels = exposed_counts[color]
                
                # If petal is completely occluded (actual=0), size adjustment can't fix it.
                # This happens when jitter moved it completely under black. Skip it.
                if actual_pixels == 0:
                    continue
                
                # If measurement is unreliable (<5 pixels), skip it
                if actual_pixels < 5:
                    continue
                
                # Calculate deviation and accumulate squared error
                deviation = (actual_pixels - target_pixels) / target_pixels if target_pixels > 0 else 0
                sum_squared_error += deviation * deviation
                total_circles += 1
                
                if abs(deviation) > drift_tolerance:
                    all_balanced = False
                    
                    # Adjust size: scale by sqrt ratio
                    scale_factor = math.sqrt(target_pixels / actual_pixels) if actual_pixels > 0 else 1.0
                    
                    # Clamp scale_factor to limit change per iteration
                    # max_step_size represents max multiplier (e.g., 2.0 = allow 2x growth or 0.5x shrink)
                    if max_step_size is not None:
                        # Clamp to range [1 - max_step_size, 1 + max_step_size] for small steps
                        # Or [1 / max_step_size, max_step_size] for large steps (old behavior)
                        if max_step_size < 1.0:
                            # Small step mode: 0.02 means ±2% change (0.98x to 1.02x)
                            min_scale = 1.0 - max_step_size
                            max_scale = 1.0 + max_step_size
                        else:
                            # Large step mode: 2.0 means 0.5x to 2x
                            min_scale = 1.0 / max_step_size
                            max_scale = max_step_size
                        scale_factor = max(min_scale, min(max_scale, scale_factor))
                    
                    cx, cy, r = circles_by_color[color][circle_idx]
                    new_r = max(0.5, r * scale_factor)
                    
                    adjustments_made += 1
                    
                    # Update circle
                    circles_by_color[color][circle_idx] = (cx, cy, new_r)
        
        # Calculate RMS error for convergence metric
        rms_error = math.sqrt(sum_squared_error / total_circles) if total_circles > 0 else 0.0
        print(f"\r[DRIFT] Iteration {iteration}: adjusted {adjustments_made} circles, RMS error={rms_error:.4f}", end='', flush=True)
        
        if all_balanced:
            print(f"\n[DRIFT] Converged after {iteration + 1} iterations", flush=True)
            break
    
    if not all_balanced:
        rms_error = math.sqrt(sum_squared_error / total_circles) if total_circles > 0 else 0.0
        print(f"\n[DRIFT] Did not converge after {max_iterations} iterations (RMS error={rms_error:.4f})", flush=True)
    
    # Save final cluster states for debugging - EXACT data that went into SVG
    final_states = []
    for cluster_idx, metadata in enumerate(cluster_metadata):
        cluster_state = {
            'cluster_id': cluster_idx,
            'center': (metadata['cx'], metadata['cy']),
            'black': {'radius': metadata['black_radius']},
            'circles': {}
        }
        
        # Find all circles belonging to this cluster by matching positions
        cx, cy = metadata['cx'], metadata['cy']
        for color in ['cyan', 'magenta', 'yellow']:
            cluster_state['circles'][color] = []
            for circle_cx, circle_cy, circle_r in circles_by_color[color]:
                # Match circles within distance of cluster center (account for jitter)
                if abs(circle_cx - cx) < 50 and abs(circle_cy - cy) < 50:
                    cluster_state['circles'][color].append({
                        'position': (float(circle_cx), float(circle_cy)),
                        'radius': float(circle_r)
                    })
        
        final_states.append(cluster_state)
    
    import json
    if output_dir:
        debug_file = output_dir / 'drift_debug_clusters.json'
    else:
        debug_file = Path('drift_debug_clusters.json')
    with open(debug_file, 'w') as f:
        json.dump(final_states, f, indent=2)
    print(f"[DRIFT] Saved debug data: {debug_file.name}", flush=True)
    
    return circles_by_color


def _measure_full_flower_exposure(
    cyan_circle: Optional[Tuple[float, float, float]],
    magenta_circle: Optional[Tuple[float, float, float]],
    yellow_circle: Optional[Tuple[float, float, float]],
    black_circle: Tuple[float, float, float],
    h: int,
    w: int,
) -> Dict[str, int]:
    """Measure exposed pixels for each color in a full flower (with all occlusion).
    
    Renders the complete flower with proper layering (CMY under, black on top),
    counts visible pixels of each color considering all overlaps.
    
    OPTIMIZED: Only renders in local bounding box around the flower, not full image.
    
    Args:
        cyan_circle, magenta_circle, yellow_circle: Optional (x, y, r) tuples
        black_circle: (x, y, r) tuple for black circle
        h, w: Canvas dimensions (for bounds checking only)
    
    Returns:
        Dict with keys 'cyan', 'magenta', 'yellow', 'black' and exposed pixel counts
    """
    import numpy as np
    import cv2
    
    # Find bounding box for all circles
    min_x, max_x = black_circle[0] - black_circle[2], black_circle[0] + black_circle[2]
    min_y, max_y = black_circle[1] - black_circle[2], black_circle[1] + black_circle[2]
    
    for circle in [cyan_circle, magenta_circle, yellow_circle]:
        if circle is not None and circle[2] > 0:
            min_x = min(min_x, circle[0] - circle[2])
            max_x = max(max_x, circle[0] + circle[2])
            min_y = min(min_y, circle[1] - circle[2])
            max_y = max(max_y, circle[1] + circle[2])
    
    # Add padding and clamp to image bounds
    padding = 5
    min_x = max(0, int(min_x) - padding)
    max_x = min(w, int(max_x) + padding)
    min_y = max(0, int(min_y) - padding)
    max_y = min(h, int(max_y) + padding)
    
    local_w = max_x - min_x
    local_h = max_y - min_y
    
    if local_w <= 0 or local_h <= 0:
        return {'cyan': 0, 'magenta': 0, 'yellow': 0, 'black': 0}
    
    # Create local masks (offset coordinates to local space)
    masks = {}
    
    for color, circle in [('cyan', cyan_circle), ('magenta', magenta_circle), 
                          ('yellow', yellow_circle)]:
        if circle is not None and circle[2] > 0:
            mask = np.zeros((local_h, local_w), dtype=np.uint8)
            local_x = int(circle[0]) - min_x
            local_y = int(circle[1]) - min_y
            cv2.circle(mask, (local_x, local_y), int(circle[2]),
                      255, thickness=-1, lineType=cv2.LINE_AA)
            masks[color] = mask
        else:
            masks[color] = np.zeros((local_h, local_w), dtype=np.uint8)
    
    # Black circle mask (offset to local space)
    if black_circle[2] > 0:
        black_mask = np.zeros((local_h, local_w), dtype=np.uint8)
        local_x = int(black_circle[0]) - min_x
        local_y = int(black_circle[1]) - min_y
        cv2.circle(black_mask, (local_x, local_y), int(black_circle[2]),
                  255, thickness=-1, lineType=cv2.LINE_AA)
        masks['black'] = black_mask
    else:
        masks['black'] = np.zeros((local_h, local_w), dtype=np.uint8)
    
    # Calculate exposed areas (black occludes everything)
    black_pixels = masks['black'] > 0
    exposed = {}
    
    for color in ['cyan', 'magenta', 'yellow']:
        # Petal minus black occlusion
        exposed[color] = masks[color] & ~black_pixels
    
    exposed['black'] = black_pixels
    
    # Count pixels
    return {
        color: int(np.sum(mask))
        for color, mask in exposed.items()
    }


def _measure_svg_circle_mass(
    petal_x: float,
    petal_y: float,
    petal_r: float,
    black_r: float,
    black_x: float,
    black_y: float,
    h: int,
    w: int,
) -> int:
    """Measure actual pixel mass for a circle in cluster-local rendering.
    
    Renders just the petal and its cluster's black circle in isolation,
    counts exposed pixels (petal - black overlap).
    
    Args:
        petal_x, petal_y, petal_r: Petal circle parameters
        black_r, black_x, black_y: Black circle parameters
        h, w: Canvas dimensions
    
    Returns:
        Number of exposed pixels
    """
    import numpy as np
    import cv2
    
    # Create local mask for this petal
    petal_mask = np.zeros((h, w), dtype=np.uint8)
    if petal_r > 0:
        cv2.circle(petal_mask, (int(petal_x), int(petal_y)), int(petal_r),
                  255, thickness=-1, lineType=cv2.LINE_AA)
    
    # Create local mask for black (if exists)
    if black_r > 0:
        black_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(black_mask, (int(black_x), int(black_y)), int(black_r),
                  255, thickness=-1, lineType=cv2.LINE_AA)
        # Subtract black from petal
        exposed = petal_mask & ~(black_mask > 0)
    else:
        exposed = petal_mask > 0
    
    return np.count_nonzero(exposed)


def render_flower_svg(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    petal_distance: float = 0.35,
    scale: float = 1.0,
    skip_partial: bool = False,
    rotation_mode: str = 'fixed',
    base_rotation: float = 0.0,
    rotation_seed: Optional[int] = None,
    jitter_position: float = 0.0,
    jitter_size: float = 0.0,
    jitter_seed: Optional[int] = None,
    jitter_algorithm: str = 'gaussian',
    jitter_exclude: str = '',
    drift: bool = False,
    drift_tolerance: float = 0.2,
    drift_max_iterations: int = 10,
    drift_max_step: float = 2.0,
    jitter_steps: int = 1,
    target_image: Optional[Path] = None,
    target_weight: float = 0.5,
    centroid_drift: bool = False,
    centroid_step: float = 0.5,
    ink_masks: Optional[Dict[str, np.ndarray]] = None,
    precision: int = 1,
    output_dir: Optional[Path] = None,
) -> str:
    """Render flower clusters directly as SVG (no rasterization).
    
    This is the native SVG rendering path that generates vector output directly
    from circle geometry without intermediate numpy array. Uses the same
    positioning, rotation, and jitter logic as render_flower(), but outputs
    SVG with proper CMYK layer structure and blend modes.
    
    Architecture: Detection → Vector data → SVG (lossless, first-class output)
    
    Args:
        clusters: List of ClusterResult from detection
        image_shape: (height, width) of original image
        petal_distance: Fraction of black radius for petal center placement
        scale: Output scale factor
        skip_partial: If True, skip edge clusters
        rotation_mode: 'fixed', 'random', or 'cluster-hash'
        base_rotation: Base angle offset in degrees
        rotation_seed: Random seed for 'random' mode
        jitter_position: Position jitter strength (0-100, percentage of radius)
        jitter_size: Size jitter strength (0-100, percentage of radius)
        jitter_seed: Random seed for reproducible jitter (optional)
        jitter_algorithm: 'gaussian' or 'uniform' distribution
        drift: If True, enable drift-balanced jitter (size compensation for color balance)
        drift_tolerance: Tolerance for color mass deviation (0.0-1.0, default 0.2)
        target_image: Path to target halftone PNG for style transfer (optional)
        target_weight: Balance between target matching and color accuracy (0.0-1.0)
        centroid_drift: If True, move petals toward color centroids instead of random jitter
        centroid_step: Fraction of distance to move toward centroid (0.0-1.0)
        ink_masks: Pre-separated CMYK masks from separate_cmyk_inks() (required for centroid_drift)
        precision: Decimal places for coordinates (default 1)
    
    Returns:
        Complete SVG document as string
    """
    h, w = image_shape
    out_h, out_w = int(h * scale), int(w * scale)
    
    # CMYK colors in RGB hex for SVG
    COLORS_HEX = {
        'cyan': '#00FFFF',
        'magenta': '#FF00FF',
        'yellow': '#FFFF00',
        'black': '#000000'
    }
    
    # Collect circles by color for layer grouping
    circles_by_color = {
        'yellow': [],
        'magenta': [],
        'cyan': [],
        'black': []
    }
    
    # For drift: track cluster metadata and circle-to-cluster mapping
    cluster_metadata = []  # List of dicts with cluster info
    cluster_circle_map = []  # List of dicts mapping colors to their index in circles_by_color
    
    # Parse jitter exclusion list (c=cyan, m=magenta, y=yellow, k=black)
    color_map = {'c': 'cyan', 'm': 'magenta', 'y': 'yellow', 'k': 'black'}
    excluded_colors = set()
    if jitter_exclude:
        for char in jitter_exclude.lower():
            if char in color_map:
                excluded_colors.add(color_map[char])
    
    for cluster_idx, cluster in enumerate(clusters):
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
        
        # Debug logging for first few clusters
        if cluster_idx < 5:
            print(f"[ROTATION DEBUG] Cluster {cluster_idx} at ({cluster.x}, {cluster.y}): mode={rotation_mode}, seed={rotation_seed}, rotation={rotation:.1f}°", flush=True)
        
        # Apply position jitter to cluster center if enabled
        if jitter_position > 0 and jitter_seed is not None and 'black' not in excluded_colors:
            cluster_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y)
            black_radius = radius_from_pixels(cluster.black)
            cx, cy = apply_position_jitter(
                cx, cy,
                position_pct=jitter_position,
                base_radius=black_radius * scale,
                seed=cluster_seed,
                algorithm=jitter_algorithm
            )
        
        # Calculate black radius
        black_radius = radius_from_pixels(cluster.black)
        
        # Apply size jitter to black radius if enabled
        if jitter_size > 0 and jitter_seed is not None and 'black' not in excluded_colors:
            cluster_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y)
            black_radius = apply_size_jitter(
                black_radius,
                size_pct=jitter_size,
                seed=cluster_seed,
                algorithm=jitter_algorithm
            )
        
        # CMYK Decomposition: Add RGB overlaps to CMY primaries
        decomposed_counts = {
            'cyan': cluster.cyan + cluster.green + cluster.blue,
            'magenta': cluster.magenta + cluster.red + cluster.blue,
            'yellow': cluster.yellow + cluster.red + cluster.green,
        }
        
        # Track cluster metadata for drift
        # Store original coordinates (pre-jitter) for reproducible multi-step jitter
        cluster_info = {
            'cx': cx,
            'cy': cy,
            'original_x': cluster.x,  # Original coordinates for consistent seeding
            'original_y': cluster.y,
            'black_radius': black_radius * scale,
            'decomposed_counts': decomposed_counts,
            'black_circle_idx': None,  # Will be set when we add black circle
        }
        cluster_metadata.append(cluster_info)
        
        # Track which circles belong to this cluster
        circle_indices = {}
        
        # Generate circles for each color
        for color in ['yellow', 'magenta', 'cyan']:
            pixel_count = decomposed_counts[color]
            if pixel_count <= 0:
                continue
            
            # Calculate preliminary radius
            preliminary_radius = radius_from_pixels(pixel_count)
            if preliminary_radius <= 0:
                continue
            
            # Position petal with rotation offset
            angle_deg = PETAL_ANGLES[color] + rotation
            angle_rad = math.radians(angle_deg - 90)  # -90 to start from top
            
            # Distance from center: fraction of black radius
            dist = black_radius * petal_distance
            
            # Calculate petal radius so EXPOSED area equals target pixel count
            if black_radius > 0 and dist < black_radius + preliminary_radius:
                # Petal overlaps with black - use exposed area formula
                petal_radius = radius_for_exposed_pixels(pixel_count, black_radius, dist)
            else:
                # No overlap with black - simple area formula
                petal_radius = preliminary_radius
            
            # Apply size jitter to petal radius if enabled
            if jitter_size > 0 and jitter_seed is not None and color not in excluded_colors:
                # Use different seed offset per color to vary each petal
                color_offset = {'cyan': 100, 'magenta': 200, 'yellow': 300}[color]
                petal_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y) + color_offset
                petal_radius = apply_size_jitter(
                    petal_radius,
                    size_pct=jitter_size,
                    seed=petal_seed,
                    algorithm=jitter_algorithm
                )
            
            petal_x = cx + dist * math.cos(angle_rad)
            petal_y = cy + dist * math.sin(angle_rad)
            
            # Apply centroid-guided position drift if enabled
            if centroid_drift and ink_masks is not None and color in ink_masks:
                # Find centroid of this color's pixels in local region using pre-separated mask
                search_radius = black_radius * 2.0 * scale  # Search 2x black radius
                centroid = compute_color_centroid_from_mask(
                    color_mask=ink_masks[color],
                    cluster_cx=petal_x / scale,  # Convert back to source coords
                    cluster_cy=petal_y / scale,
                    search_radius=search_radius / scale,
                )
                if centroid is not None:
                    # Move petal toward centroid
                    new_x, new_y = apply_centroid_position(
                        petal_x=petal_x / scale,
                        petal_y=petal_y / scale,
                        centroid_x=centroid[0],
                        centroid_y=centroid[1],
                        step_size=centroid_step,
                    )
                    petal_x = new_x * scale
                    petal_y = new_y * scale
            
            if petal_radius > 0.5:  # Skip tiny circles
                circle_idx = len(circles_by_color[color])
                circles_by_color[color].append((petal_x, petal_y, petal_radius * scale))
                circle_indices[color] = (circle_idx, pixel_count)  # Store index and target pixels
        
        # Add black center
        if cluster.black > 0 and black_radius > 0.5:
            black_idx = len(circles_by_color['black'])
            circles_by_color['black'].append((cx, cy, black_radius * scale))
            cluster_metadata[-1]['black_circle_idx'] = black_idx
        
        # Store circle mapping for this cluster
        cluster_circle_map.append(circle_indices)
    
    # Apply drift balancing if enabled (iterate jitter_steps times)
    if drift and (jitter_position > 0 or jitter_size > 0):
        print(f"[DRIFT] Starting: {len(cluster_metadata)} clusters, {jitter_steps} step(s)", flush=True)
        
        # Use GPU acceleration if available
        from .gpu import is_gpu_available
        use_gpu = is_gpu_available()
        
        for step in range(jitter_steps):
            step_seed = (jitter_seed + step) if jitter_seed is not None else None
            if jitter_steps > 1:
                print(f"[DRIFT] Step {step + 1}/{jitter_steps} (seed={step_seed})", flush=True)
            
            # Apply jitter at each step (re-jitter from current positions)
            # This compounds the jitter effect across steps
            if step_seed is not None:
                circles_by_color = _apply_jitter_to_circles(
                    circles_by_color=circles_by_color,
                    cluster_metadata=cluster_metadata,
                    cluster_circle_map=cluster_circle_map,
                    jitter_position=jitter_position,
                    jitter_size=jitter_size,
                    jitter_seed=step_seed,
                    jitter_algorithm=jitter_algorithm,
                    excluded_colors=excluded_colors,
                    scale=scale,
                )
            
            if use_gpu:
                from .gpu_renderer import apply_drift_gpu
                circles_by_color = apply_drift_gpu(
                    circles_by_color=circles_by_color,
                    cluster_metadata=cluster_metadata,
                    cluster_circle_map=cluster_circle_map,
                    image_shape=(out_h, out_w),
                    drift_tolerance=drift_tolerance,
                    max_iterations=drift_max_iterations,
                    max_step_size=drift_max_step,
                    jitter_seed=step_seed,
                )
            else:
                circles_by_color = _apply_drift_to_svg_circles(
                    circles_by_color=circles_by_color,
                    cluster_metadata=cluster_metadata,
                    cluster_circle_map=cluster_circle_map,
                    image_shape=(out_h, out_w),
                    drift_tolerance=drift_tolerance,
                    max_iterations=drift_max_iterations,
                    max_step_size=drift_max_step,
                    output_dir=output_dir,
                    jitter_seed=step_seed,
                )
        print(f"[DRIFT] Completed", flush=True)
    
    # Apply target-guided optimization if target image provided
    if target_image is not None and drift:
        from .target_guided import (
            parse_target_image,
            apply_target_guided_optimization,
            TargetGuidedConfig,
        )
        print(f"[TARGET] Parsing target image: {target_image}", flush=True)
        target_index = parse_target_image(
            target_image,
            sensitivity='relaxed',
            min_radius=1,
            max_radius=100,
        )
        
        config = TargetGuidedConfig(
            target_image_path=target_image,
            target_weight=target_weight,
            step_size=0.1,
            max_iterations=drift_max_iterations,
            convergence_threshold=drift_tolerance,
        )
        
        circles_by_color = apply_target_guided_optimization(
            circles_by_color=circles_by_color,
            cluster_metadata=cluster_metadata,
            cluster_circle_map=cluster_circle_map,
            target_index=target_index,
            image_shape=(out_h, out_w),
            config=config,
        )
        print(f"[TARGET] Optimization complete", flush=True)
    
    # Build SVG document
    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                    f'width="{out_w}" height="{out_h}" '
                    f'viewBox="0 0 {out_w} {out_h}">')
    svg_lines.append(f'  <title>DotMatrix Flower Rendering</title>')
    svg_lines.append(f'  <desc>CMYK halftone with {len(clusters)} clusters</desc>')
    
    # White background
    svg_lines.append(f'  <rect width="{out_w}" height="{out_h}" fill="#FFFFFF"/>')
    
    # Draw CMYK layers in order (Y, M, C, K) with blend modes
    # Note: In SVG, later elements paint over earlier ones
    # Blend mode "multiply" handles overlaps correctly (subtractive mixing)
    for color in ['yellow', 'magenta', 'cyan', 'black']:
        circles = circles_by_color[color]
        if not circles:
            continue
        
        svg_lines.append(f'  <g id="{color}-layer" fill="{COLORS_HEX[color]}" '
                        f'style="mix-blend-mode: multiply">')
        
        for cx, cy, r in circles:
            # Format with specified precision
            cx_str = f'{cx:.{precision}f}'
            cy_str = f'{cy:.{precision}f}'
            r_str = f'{r:.{precision}f}'
            svg_lines.append(f'    <circle cx="{cx_str}" cy="{cy_str}" r="{r_str}"/>')
        
        svg_lines.append('  </g>')
    
    svg_lines.append('</svg>')
    
    return '\n'.join(svg_lines)


def render_planetary_svg(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    scale: float = 1.0,
    skip_partial: bool = False,
    rotation_mode: str = 'fixed',
    base_rotation: float = 0.0,
    rotation_seed: Optional[int] = None,
    jitter_position: float = 0.0,
    jitter_size: float = 0.0,
    jitter_seed: Optional[int] = None,
    jitter_algorithm: str = 'gaussian',
    jitter_exclude: str = '',
    drift: bool = False,
    drift_tolerance: float = 0.2,
    drift_max_iterations: int = 10,
    drift_max_step: float = 2.0,
    jitter_steps: int = 1,
    precision: int = 1,
    output_dir: Optional[Path] = None,
) -> str:
    """Render planetary clusters directly as SVG - CMY dots tangent to black surface.
    
    Like moons orbiting a planet, CMY dots sit ON the surface of the black circle
    rather than overlapping with it like flower mode. This creates a more "atomic"
    or "molecular" appearance with better color separation.
    
    Key difference from flower:
    - Flower: petal_distance = black_radius * fraction (dots overlap black)
    - Planetary: orbital_distance = black_radius + petal_radius (dots tangent)
    
    Args:
        clusters: List of ClusterResult from detection
        image_shape: (height, width) of original image
        scale: Output scale factor
        skip_partial: If True, skip edge clusters
        rotation_mode: 'fixed', 'random', or 'cluster-hash'
        base_rotation: Base angle offset in degrees
        rotation_seed: Random seed for 'random' mode
        jitter_position: Position jitter strength (0-100, percentage of radius)
        jitter_size: Size jitter strength (0-100, percentage of radius)
        jitter_seed: Random seed for reproducible jitter (optional)
        jitter_algorithm: 'gaussian' or 'uniform' distribution
        jitter_exclude: Colors to exclude from jitter (c=cyan, m=magenta, y=yellow, k=black)
        drift: If True, enable drift-balanced jitter
        drift_tolerance: Tolerance for color mass deviation (0.0-1.0)
        drift_max_iterations: Max drift iterations
        drift_max_step: Max drift step size
        jitter_steps: Number of jitter-drift iterations
        precision: Decimal places for coordinates (default 1)
        output_dir: Optional output directory for debug files
    
    Returns:
        Complete SVG document as string
    """
    h, w = image_shape
    out_h, out_w = int(h * scale), int(w * scale)
    
    # CMYK colors in RGB hex for SVG
    COLORS_HEX = {
        'cyan': '#00FFFF',
        'magenta': '#FF00FF',
        'yellow': '#FFFF00',
        'black': '#000000'
    }
    
    # Collect circles by color for layer grouping
    circles_by_color = {
        'yellow': [],
        'magenta': [],
        'cyan': [],
        'black': []
    }
    
    # For drift: track cluster metadata and circle-to-cluster mapping
    cluster_metadata = []
    cluster_circle_map = []
    
    # Parse jitter exclusion list
    color_map = {'c': 'cyan', 'm': 'magenta', 'y': 'yellow', 'k': 'black'}
    excluded_colors = set()
    if jitter_exclude:
        for char in jitter_exclude.lower():
            if char in color_map:
                excluded_colors.add(color_map[char])
    
    for cluster_idx, cluster in enumerate(clusters):
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
        
        # Apply position jitter to cluster center if enabled
        if jitter_position > 0 and jitter_seed is not None and 'black' not in excluded_colors:
            cluster_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y)
            black_radius = radius_from_pixels(cluster.black)
            cx, cy = apply_position_jitter(
                cx, cy,
                position_pct=jitter_position,
                base_radius=black_radius * scale,
                seed=cluster_seed,
                algorithm=jitter_algorithm
            )
        
        # Calculate black radius
        black_radius = radius_from_pixels(cluster.black)
        
        # Apply size jitter to black radius if enabled
        if jitter_size > 0 and jitter_seed is not None and 'black' not in excluded_colors:
            cluster_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y)
            black_radius = apply_size_jitter(
                black_radius,
                size_pct=jitter_size,
                seed=cluster_seed,
                algorithm=jitter_algorithm
            )
        
        # CMYK Decomposition: Add RGB overlaps to CMY primaries
        decomposed_counts = {
            'cyan': cluster.cyan + cluster.green + cluster.blue,
            'magenta': cluster.magenta + cluster.red + cluster.blue,
            'yellow': cluster.yellow + cluster.red + cluster.green,
        }
        
        # Track cluster metadata for drift
        cluster_info = {
            'cx': cx,
            'cy': cy,
            'original_x': cluster.x,
            'original_y': cluster.y,
            'black_radius': black_radius * scale,
            'decomposed_counts': decomposed_counts,
            'black_circle_idx': None,
        }
        cluster_metadata.append(cluster_info)
        
        # Track which circles belong to this cluster
        circle_indices = {}
        
        # Generate circles for each color - PLANETARY POSITIONING
        for color in ['yellow', 'magenta', 'cyan']:
            pixel_count = decomposed_counts[color]
            if pixel_count <= 0:
                continue
            
            # Calculate petal radius (no exposed-area compensation needed - dots are fully visible)
            petal_radius = radius_from_pixels(pixel_count)
            if petal_radius <= 0:
                continue
            
            # Position petal with rotation offset
            angle_deg = PETAL_ANGLES[color] + rotation
            angle_rad = math.radians(angle_deg - 90)  # -90 to start from top
            
            # PLANETARY: Distance = black_radius + petal_radius (tangent to black surface)
            # This ensures CMY dots touch but don't overlap the black circle
            dist = black_radius + petal_radius
            
            # Apply size jitter to petal radius if enabled
            if jitter_size > 0 and jitter_seed is not None and color not in excluded_colors:
                color_offset = {'cyan': 100, 'magenta': 200, 'yellow': 300}[color]
                petal_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y) + color_offset
                petal_radius = apply_size_jitter(
                    petal_radius,
                    size_pct=jitter_size,
                    seed=petal_seed,
                    algorithm=jitter_algorithm
                )
                # Recalculate distance with jittered radius
                dist = black_radius + petal_radius
            
            petal_x = cx + dist * math.cos(angle_rad)
            petal_y = cy + dist * math.sin(angle_rad)
            
            if petal_radius > 0.5:  # Skip tiny circles
                circle_idx = len(circles_by_color[color])
                circles_by_color[color].append((petal_x, petal_y, petal_radius * scale))
                circle_indices[color] = (circle_idx, pixel_count)
        
        # Add black center
        if cluster.black > 0 and black_radius > 0.5:
            black_idx = len(circles_by_color['black'])
            circles_by_color['black'].append((cx, cy, black_radius * scale))
            cluster_metadata[-1]['black_circle_idx'] = black_idx
        
        # Store circle mapping for this cluster
        cluster_circle_map.append(circle_indices)
    
    # Apply drift balancing if enabled (iterate jitter_steps times)
    # Note: Drift may have less impact on planetary since dots don't overlap black
    if drift and (jitter_position > 0 or jitter_size > 0):
        print(f"[DRIFT] Starting planetary: {len(cluster_metadata)} clusters, {jitter_steps} step(s)", flush=True)
        print(f"[DEBUG] jitter_position={jitter_position}, jitter_size={jitter_size}, excluded={excluded_colors}", flush=True)
        
        # Sample a circle before jitter for debugging
        if circles_by_color['cyan']:
            sample_before = circles_by_color['cyan'][0]
            print(f"[DEBUG] Sample cyan circle BEFORE jitter: {sample_before}", flush=True)
        
        from .gpu import is_gpu_available
        use_gpu = is_gpu_available()
        
        for step in range(jitter_steps):
            step_seed = (jitter_seed + step) if jitter_seed is not None else None
            if jitter_steps > 1:
                print(f"[DRIFT] Step {step + 1}/{jitter_steps} (seed={step_seed})", flush=True)
            
            if step_seed is not None:
                circles_by_color = _apply_jitter_to_circles(
                    circles_by_color=circles_by_color,
                    cluster_metadata=cluster_metadata,
                    cluster_circle_map=cluster_circle_map,
                    jitter_position=jitter_position,
                    jitter_size=jitter_size,
                    jitter_seed=step_seed,
                    jitter_algorithm=jitter_algorithm,
                    excluded_colors=excluded_colors,
                    scale=scale,
                )
                # Debug: show sample after jitter
                if circles_by_color['cyan']:
                    print(f"[DEBUG] Cyan[0] after jitter step {step+1}: {circles_by_color['cyan'][0]}", flush=True)
            
            if use_gpu:
                from .gpu_renderer import apply_drift_gpu
                circles_by_color = apply_drift_gpu(
                    circles_by_color=circles_by_color,
                    cluster_metadata=cluster_metadata,
                    cluster_circle_map=cluster_circle_map,
                    image_shape=(out_h, out_w),
                    drift_tolerance=drift_tolerance,
                    max_iterations=drift_max_iterations,
                    max_step_size=drift_max_step,
                    jitter_seed=step_seed,
                )
                # Debug: show sample after drift
                if circles_by_color['cyan']:
                    print(f"[DEBUG] Cyan[0] after drift step {step+1}: {circles_by_color['cyan'][0]}", flush=True)
            else:
                circles_by_color = _apply_drift_to_svg_circles(
                    circles_by_color=circles_by_color,
                    cluster_metadata=cluster_metadata,
                    cluster_circle_map=cluster_circle_map,
                    image_shape=(out_h, out_w),
                    drift_tolerance=drift_tolerance,
                    max_iterations=drift_max_iterations,
                    max_step_size=drift_max_step,
                    output_dir=output_dir,
                    jitter_seed=step_seed,
                )
                # Debug: show sample after drift (CPU)
                if circles_by_color['cyan']:
                    print(f"[DEBUG] Cyan[0] after drift step {step+1}: {circles_by_color['cyan'][0]}", flush=True)
        
        # Debug: final sample before SVG generation
        if circles_by_color['cyan']:
            print(f"[DEBUG] Cyan[0] FINAL (before SVG): {circles_by_color['cyan'][0]}", flush=True)
        print(f"[DRIFT] Completed", flush=True)
    
    # Build SVG document
    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                    f'width="{out_w}" height="{out_h}" '
                    f'viewBox="0 0 {out_w} {out_h}">')
    svg_lines.append(f'  <title>DotMatrix Planetary Rendering</title>')
    svg_lines.append(f'  <desc>CMYK halftone with {len(clusters)} clusters (planetary mode)</desc>')
    
    # White background
    svg_lines.append(f'  <rect width="{out_w}" height="{out_h}" fill="#FFFFFF"/>')
    
    # Draw CMYK layers in order (Y, M, C, K) with blend modes
    for color in ['yellow', 'magenta', 'cyan', 'black']:
        circles = circles_by_color[color]
        if not circles:
            continue
        
        svg_lines.append(f'  <g id="{color}-layer" fill="{COLORS_HEX[color]}" '
                        f'style="mix-blend-mode: multiply">')
        
        for cx, cy, r in circles:
            cx_str = f'{cx:.{precision}f}'
            cy_str = f'{cy:.{precision}f}'
            r_str = f'{r:.{precision}f}'
            svg_lines.append(f'    <circle cx="{cx_str}" cy="{cy_str}" r="{r_str}"/>')
        
        svg_lines.append('  </g>')
    
    svg_lines.append('</svg>')
    
    return '\n'.join(svg_lines)


def render_planetary(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    scale: int = 1,
    skip_partial: bool = False,
    rotation_mode: str = 'fixed',
    base_rotation: float = 0.0,
    rotation_seed: Optional[int] = None,
    blend_overlaps: bool = False,
    jitter_position: float = 0.0,
    jitter_size: float = 0.0,
    jitter_seed: Optional[int] = None,
    jitter_algorithm: str = 'gaussian',
    jitter_exclude: str = '',
) -> np.ndarray:
    """Render all clusters as planetary patterns (PNG output).
    
    Each cluster becomes a planet with black center and CMY moons orbiting
    tangent to the surface (not overlapping like flower mode).
    
    Args:
        clusters: List of ClusterResult from detection
        image_shape: (height, width) of original image
        scale: Output scale factor
        skip_partial: If True, skip edge clusters
        rotation_mode: 'fixed', 'random', or 'cluster-hash'
        base_rotation: Base angle offset in degrees
        rotation_seed: Random seed for 'random' mode
        blend_overlaps: If True, use subtractive CMY blending at petal overlaps
        jitter_position: Position jitter strength (0-100)
        jitter_size: Size jitter strength (0-100)
        jitter_seed: Random seed for reproducible jitter
        jitter_algorithm: 'gaussian' or 'uniform' distribution
        jitter_exclude: Colors to exclude from jitter
    
    Returns:
        BGR numpy array with rendered planetary patterns
    """
    h, w = image_shape
    out_h, out_w = int(h * scale), int(w * scale)
    
    # White background
    output = np.full((out_h, out_w, 3), 255, dtype=np.uint8)
    
    # Parse jitter exclusion list
    color_map = {'c': 'cyan', 'm': 'magenta', 'y': 'yellow', 'k': 'black'}
    excluded_colors = set()
    if jitter_exclude:
        for char in jitter_exclude.lower():
            if char in color_map:
                excluded_colors.add(color_map[char])
    
    for cluster in clusters:
        if skip_partial and cluster.partial:
            continue
        
        cx = cluster.x * scale
        cy = cluster.y * scale
        
        # Compute rotation
        rotation = compute_cluster_rotation(
            cluster.x, cluster.y,
            mode=rotation_mode,
            base_rotation=base_rotation,
            seed=rotation_seed
        )
        
        # Apply position jitter to cluster center
        if jitter_position > 0 and jitter_seed is not None and 'black' not in excluded_colors:
            cluster_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y)
            black_radius = radius_from_pixels(cluster.black)
            cx, cy = apply_position_jitter(
                cx, cy,
                position_pct=jitter_position,
                base_radius=black_radius * scale,
                seed=cluster_seed,
                algorithm=jitter_algorithm
            )
        
        # Calculate black radius
        black_radius = radius_from_pixels(cluster.black)
        
        # Apply size jitter to black
        if jitter_size > 0 and jitter_seed is not None and 'black' not in excluded_colors:
            cluster_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y)
            black_radius = apply_size_jitter(
                black_radius,
                size_pct=jitter_size,
                seed=cluster_seed,
                algorithm=jitter_algorithm
            )
        
        # CMYK Decomposition
        decomposed_counts = {
            'cyan': cluster.cyan + cluster.green + cluster.blue,
            'magenta': cluster.magenta + cluster.red + cluster.blue,
            'yellow': cluster.yellow + cluster.red + cluster.green,
        }
        
        # Draw CMY moons first (so black can overlay if needed)
        for color in ['yellow', 'magenta', 'cyan']:
            pixel_count = decomposed_counts[color]
            if pixel_count <= 0:
                continue
            
            petal_radius = radius_from_pixels(pixel_count)
            if petal_radius <= 0:
                continue
            
            # Position with rotation
            angle_deg = PETAL_ANGLES[color] + rotation
            angle_rad = math.radians(angle_deg - 90)
            
            # PLANETARY: tangent to black surface
            dist = black_radius + petal_radius
            
            # Apply size jitter
            if jitter_size > 0 and jitter_seed is not None and color not in excluded_colors:
                color_offset = {'cyan': 100, 'magenta': 200, 'yellow': 300}[color]
                petal_seed = jitter_seed + int(cluster.x) * 10000 + int(cluster.y) + color_offset
                petal_radius = apply_size_jitter(
                    petal_radius,
                    size_pct=jitter_size,
                    seed=petal_seed,
                    algorithm=jitter_algorithm
                )
                dist = black_radius + petal_radius
            
            petal_x = cx + dist * math.cos(angle_rad)
            petal_y = cy + dist * math.sin(angle_rad)
            
            # Draw the moon
            if petal_radius > 0:
                int_radius = max(1, int(round(petal_radius * scale)))
                cv2.circle(output, (int(petal_x), int(petal_y)), int_radius,
                          COLORS_BGR[color], thickness=-1, lineType=cv2.LINE_AA)
        
        # Draw black center
        if cluster.black > 0 and black_radius > 0:
            int_radius = max(1, int(round(black_radius * scale)))
            cv2.circle(output, (int(cx), int(cy)), int_radius,
                      COLORS_BGR['black'], thickness=-1, lineType=cv2.LINE_AA)
    
    return output
