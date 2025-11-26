"""Convex edge detection for overlapping circles.

This module implements circle detection using convex edge analysis,
which is specifically designed for heavily overlapping circles where
traditional Hough transform fails.

The algorithm:
1. Quantize image to a limited color palette
2. Filter by each color to isolate circle segments
3. Detect convex edges (excluding overlapped concave regions)
4. Fit circles to convex edges only
5. Deduplicate similar circles

This approach was validated to successfully detect all 16 overlapping
CMYK circles in test images where standard detection found incorrect results.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import numpy as np
import cv2
from scipy.spatial import KDTree


# Preset color palettes
PALETTES = {
    'cmyk': [
        (255, 255, 255),  # White (background)
        (0, 0, 0),        # Black (K)
        (118, 193, 241),  # Cyan (C)
        (217, 93, 155),   # Magenta (M)
        (238, 206, 94),   # Yellow (Y)
    ],
    'rgb': [
        (255, 255, 255),  # White (background)
        (0, 0, 0),        # Black
        (255, 0, 0),      # Red
        (0, 255, 0),      # Green
        (0, 0, 255),      # Blue
    ],
    'grayscale': [
        (255, 255, 255),  # White
        (0, 0, 0),        # Black
        (128, 128, 128),  # Gray
    ],
}


@dataclass
class DetectedCircle:
    """A detected circle with position, size, and color."""
    x: int
    y: int
    radius: int
    color: Tuple[int, int, int]
    confidence: float = 100.0

    def __iter__(self):
        """Allow unpacking as (x, y, radius)."""
        return iter((self.x, self.y, self.radius))


def parse_palette(palette_spec: str) -> List[Tuple[int, int, int]]:
    """Parse a palette specification string.

    Args:
        palette_spec: Either a preset name ('cmyk', 'rgb') or
                     semicolon-separated RGB values like '255,0,0;0,255,0'

    Returns:
        List of RGB tuples

    Raises:
        ValueError: If palette_spec is invalid
    """
    # Check for preset
    if palette_spec.lower() in PALETTES:
        return PALETTES[palette_spec.lower()]

    # Parse custom palette
    try:
        colors = []
        # Always include white as background
        colors.append((255, 255, 255))

        for color_str in palette_spec.split(';'):
            parts = color_str.strip().split(',')
            if len(parts) != 3:
                raise ValueError(f"Invalid color format: {color_str}")
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                raise ValueError(f"RGB values must be 0-255: {color_str}")
            colors.append((r, g, b))

        return colors
    except Exception as e:
        raise ValueError(f"Invalid palette specification: {palette_spec}. "
                        f"Use preset name (cmyk, rgb) or 'R,G,B;R,G,B' format. "
                        f"Error: {e}")


def quantize_to_palette(
    image: np.ndarray,
    palette: List[Tuple[int, int, int]]
) -> np.ndarray:
    """Map all pixels to their nearest palette color.

    Uses Euclidean distance in RGB space to find the closest
    palette color for each pixel.

    Args:
        image: RGB image as numpy array (H, W, 3)
        palette: List of RGB tuples to quantize to

    Returns:
        Quantized image with same shape as input
    """
    h, w = image.shape[:2]
    pixels = image.reshape(-1, 3).astype(np.float32)
    palette_array = np.array(palette, dtype=np.float32)

    # Calculate Euclidean distances from each pixel to each palette color
    # Shape: (num_pixels, num_colors)
    distances = np.sqrt(
        ((pixels[:, np.newaxis, :] - palette_array[np.newaxis, :, :]) ** 2).sum(axis=2)
    )

    # Find nearest color for each pixel
    nearest_indices = np.argmin(distances, axis=1)

    # Map pixels to their nearest palette color
    quantized_pixels = palette_array[nearest_indices].astype(np.uint8)
    quantized_img = quantized_pixels.reshape(h, w, 3)

    return quantized_img


def filter_by_color(
    quantized: np.ndarray,
    target_color: Tuple[int, int, int]
) -> np.ndarray:
    """Create binary mask for pixels matching target color exactly.

    Args:
        quantized: Quantized image (exact palette colors only)
        target_color: RGB tuple to match

    Returns:
        Binary mask (H, W) where 255 = matches, 0 = doesn't match
    """
    mask = np.all(quantized == target_color, axis=2)
    return (mask * 255).astype(np.uint8)


def deduplicate_circles_kdtree(
    circles: List[Tuple[int, int, int]],
    color: Tuple[int, int, int],
    dedup_distance: int = 20
) -> List[DetectedCircle]:
    """Deduplicate circles using KD-tree for O(n log n) performance.

    Replaces the O(n²) nested loop deduplication with spatial indexing.
    Circles with centers within dedup_distance of each other are considered
    duplicates, and only the first one (in input order) is kept.

    Args:
        circles: List of (x, y, radius) tuples
        color: RGB color tuple to assign to returned DetectedCircle objects
        dedup_distance: Maximum distance between circle centers to be
                       considered duplicates (default: 20 pixels)

    Returns:
        List of DetectedCircle objects with duplicates removed

    Performance:
        - KD-tree build: O(n log n)
        - Query per circle: O(log n) average
        - Total: O(n log n)
        - Benchmarks: 10k circles in <0.2s, 100k circles in <0.6s
    """
    if not circles:
        return []

    # Build KD-tree from circle centers
    centers = np.array([(c[0], c[1]) for c in circles])
    tree = KDTree(centers)

    # Deduplicate using spatial queries
    used = set()
    final_circles = []

    for i, (x, y, r) in enumerate(circles):
        if i in used:
            continue

        # Keep this circle
        final_circles.append(DetectedCircle(x, y, r, color))

        # Mark all nearby circles as duplicates
        nearby = tree.query_ball_point([x, y], dedup_distance)
        used.update(nearby)

    return final_circles


def detect_circles_from_convex_edges(
    color_mask: np.ndarray,
    color: Tuple[int, int, int],
    min_radius: int = 80,
    max_radius: int = 350,
    min_blob_area: int = 1000,
    defect_depth_threshold: int = 5,
    non_convex_margin: int = 20,
    dedup_distance: int = 20
) -> List[DetectedCircle]:
    """Detect circles from a single-color mask using convex edge analysis.

    This is the core algorithm that handles overlapping circles by:
    1. Finding connected components (blobs)
    2. Identifying convex vs concave edges using convexity defects
    3. Fitting circles to convex edges only
    4. Selecting the best circle per blob
    5. Deduplicating similar circles

    Args:
        color_mask: Binary mask (255 = color present, 0 = absent)
        color: RGB tuple for this color (attached to results)
        min_radius: Minimum circle radius in pixels
        max_radius: Maximum circle radius in pixels
        min_blob_area: Minimum blob area to consider (filters noise)
        defect_depth_threshold: Minimum defect depth in pixels to mark as concave
        non_convex_margin: Points within this distance of defects are non-convex
        dedup_distance: Circles with centers this close are deduplicated

    Returns:
        List of DetectedCircle objects
    """
    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        color_mask, connectivity=8
    )

    candidate_circles = []

    for label_id in range(1, num_labels):  # Skip background (0)
        area = stats[label_id, cv2.CC_STAT_AREA]
        if area < min_blob_area:
            continue

        # Create mask for this component only
        component_mask = (labels == label_id).astype(np.uint8) * 255

        # Find contour
        contours, _ = cv2.findContours(
            component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )

        if len(contours) == 0:
            continue

        contour = contours[0]
        if len(contour) < 5:
            continue

        # Get convex hull indices
        hull_indices = cv2.convexHull(contour, returnPoints=False)

        if len(hull_indices) < 4:
            # Not enough points for convexity analysis, use all points
            convex_points = contour
        else:
            # Find convexity defects
            try:
                defects = cv2.convexityDefects(contour, hull_indices)
            except cv2.error:
                # Fall back to using all contour points
                convex_points = contour
                defects = None

            if defects is None:
                # No defects = fully convex, use all points
                convex_points = contour
            else:
                # Mark regions near significant defects as non-convex
                convex_mask = np.ones(len(contour), dtype=bool)

                for i in range(defects.shape[0]):
                    s, e, f, d = defects[i, 0]
                    # d is depth * 256, so divide to get actual pixel depth
                    depth = d / 256.0
                    if depth > defect_depth_threshold:
                        # Mark points near this defect as non-convex
                        start = max(0, s - non_convex_margin)
                        end = min(len(contour), e + non_convex_margin)
                        convex_mask[start:end] = False

                # Extract only convex points
                convex_points = contour[convex_mask]

        if len(convex_points) < 20:
            # Not enough convex points to fit a circle
            continue

        # Create image with just convex points
        temp_img = np.zeros_like(component_mask)
        for pt in convex_points:
            x, y = pt[0]
            cv2.circle(temp_img, (x, y), 1, 255, -1)

        # Detect circles from convex edge points
        blurred = cv2.GaussianBlur(temp_img, (9, 9), 2)
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=30,
            param2=20,  # Lower threshold for partial arcs
            minRadius=min_radius,
            maxRadius=max_radius
        )

        if circles is None:
            continue

        # Select best circle for this blob based on convex point coverage
        best_circle = None
        best_score = -1

        for circle in circles[0]:
            cx, cy, r = circle

            # Score based on how many convex points lie on this circle
            score = 0
            for pt in convex_points:
                px, py = pt[0]
                dist_to_circle = abs(np.sqrt((px - cx)**2 + (py - cy)**2) - r)
                if dist_to_circle < 10:  # Within 10 pixels of circle edge
                    score += 1

            # Normalize by expected arc length (assume ~30% visible)
            expected_points = 2 * np.pi * r * 0.3
            normalized_score = score / max(expected_points, 1)

            if normalized_score > best_score:
                best_score = normalized_score
                best_circle = (int(cx), int(cy), int(r))

        if best_circle is not None:
            candidate_circles.append(best_circle)

    # Deduplicate using KD-tree for O(n log n) performance
    return deduplicate_circles_kdtree(candidate_circles, color, dedup_distance)


def detect_all_circles(
    image: np.ndarray,
    palette: List[Tuple[int, int, int]],
    min_radius: int = 80,
    max_radius: int = 350,
    exclude_background: bool = True,
    debug_callback: Optional[callable] = None
) -> Tuple[List[DetectedCircle], np.ndarray]:
    """Detect all circles using convex edge analysis.

    Main entry point for convex edge detection. Processes each color
    in the palette separately and combines results.

    Args:
        image: RGB image as numpy array (H, W, 3)
        palette: List of RGB tuples (first is assumed to be background)
        min_radius: Minimum circle radius in pixels
        max_radius: Maximum circle radius in pixels
        exclude_background: If True, skip the first palette color (background)
        debug_callback: Optional function(color_name, mask, circles) for debugging

    Returns:
        Tuple of (list of DetectedCircle, quantized image)
    """
    # Quantize image to palette
    quantized = quantize_to_palette(image, palette)

    all_circles = []

    # Process each color (skip background if requested)
    start_idx = 1 if exclude_background else 0

    for color in palette[start_idx:]:
        # Filter to this color only
        mask = filter_by_color(quantized, color)

        # Detect circles from convex edges
        circles = detect_circles_from_convex_edges(
            mask,
            color,
            min_radius=min_radius,
            max_radius=max_radius
        )

        if debug_callback:
            debug_callback(color, mask, circles)

        all_circles.extend(circles)

    return all_circles, quantized


def get_color_name(color: Tuple[int, int, int]) -> str:
    """Get a human-readable name for a color.

    Args:
        color: RGB tuple

    Returns:
        Color name string
    """
    # Check against known colors
    color_names = {
        (255, 255, 255): 'white',
        (0, 0, 0): 'black',
        (118, 193, 241): 'cyan',
        (217, 93, 155): 'magenta',
        (238, 206, 94): 'yellow',
        (255, 0, 0): 'red',
        (0, 255, 0): 'green',
        (0, 0, 255): 'blue',
        (128, 128, 128): 'gray',
    }

    if color in color_names:
        return color_names[color]

    # Return RGB string for unknown colors
    return f'rgb_{color[0]}_{color[1]}_{color[2]}'


def generate_tiles(
    image_shape: Tuple[int, int],
    chunk_size: int,
    overlap: int
) -> List[Tuple[int, int, int, int]]:
    """Generate overlapping tile coordinates for chunked processing.

    Creates a grid of tiles that cover the entire image with overlap to ensure
    circles on boundaries are detected. Each tile is (x1, y1, x2, y2) in pixels.

    Args:
        image_shape: (height, width) of the image
        chunk_size: Size of each tile in pixels
        overlap: Overlap between adjacent tiles in pixels

    Returns:
        List of (x1, y1, x2, y2) tile coordinates
    """
    h, w = image_shape[:2]
    tiles = []

    # Calculate step size (chunk_size minus overlap)
    step = max(1, chunk_size - overlap)

    for y in range(0, h, step):
        for x in range(0, w, step):
            x1 = x
            y1 = y
            x2 = min(x + chunk_size, w)
            y2 = min(y + chunk_size, h)
            tiles.append((x1, y1, x2, y2))

    return tiles


def calculate_chunk_size(
    image_shape: Tuple[int, int],
    max_radius: int,
    target_megapixels: float = 4.0
) -> int:
    """Calculate optimal chunk size based on image and circle parameters.

    Uses a formula based on max_radius to ensure tiles are large enough to
    contain complete circles while keeping memory usage reasonable.

    Args:
        image_shape: (height, width) of the image
        max_radius: Maximum expected circle radius in pixels
        target_megapixels: Target megapixels per chunk (default: 4 MP)

    Returns:
        Chunk size in pixels
    """
    h, w = image_shape[:2]

    # Base size: at least 50x max_radius to contain multiple circles
    min_size = max(2000, max_radius * 50)

    # Calculate size based on target megapixels
    target_size = int(np.sqrt(target_megapixels * 1e6))

    # Use larger of minimum and target
    chunk_size = max(min_size, target_size)

    # Cap at image dimensions
    chunk_size = min(chunk_size, h, w)

    return int(chunk_size)


def process_chunked(
    image: np.ndarray,
    palette: List[Tuple[int, int, int]],
    chunk_size: int,
    max_radius: int,
    min_radius: int = 80,
    exclude_background: bool = True,
    progress_callback: Optional[callable] = None,
    debug_callback: Optional[callable] = None
) -> List[DetectedCircle]:
    """Process large image in chunks with overlapping tiles.

    Splits the image into overlapping tiles, processes each independently,
    then merges results with boundary deduplication.

    Args:
        image: RGB image as numpy array (H, W, 3)
        palette: List of RGB tuples (first is assumed to be background)
        chunk_size: Size of each tile in pixels
        max_radius: Maximum circle radius in pixels
        min_radius: Minimum circle radius in pixels
        exclude_background: If True, skip the first palette color (background)
        progress_callback: Optional function(tile_num, total_tiles) for progress
        debug_callback: Optional function(color_name, mask, circles) for debugging

    Returns:
        List of DetectedCircle objects with global coordinates
    """
    h, w = image.shape[:2]

    # Calculate overlap based on max_radius (ensure boundary circles detected)
    # Overlap should be at least 2x max_radius to catch boundary circles
    overlap = max_radius * 2

    # Ensure chunk_size is larger than overlap (at least 3x overlap for efficiency)
    min_chunk_size = overlap * 3
    if chunk_size < min_chunk_size:
        chunk_size = min_chunk_size

    # Generate tiles
    tiles = generate_tiles((h, w), chunk_size, overlap)
    total_tiles = len(tiles)

    # If only one tile, process directly without chunking overhead
    if total_tiles == 1:
        circles, _ = detect_all_circles(
            image, palette, min_radius, max_radius,
            exclude_background, debug_callback
        )
        return circles

    all_circles = []

    for i, (x1, y1, x2, y2) in enumerate(tiles):
        if progress_callback:
            progress_callback(i + 1, total_tiles)

        # Extract tile
        tile = image[y1:y2, x1:x2]

        # Process tile
        tile_circles, _ = detect_all_circles(
            tile, palette, min_radius, max_radius,
            exclude_background, debug_callback
        )

        # Offset coordinates to global image space
        for circle in tile_circles:
            # Create new circle with offset coordinates
            global_circle = DetectedCircle(
                x=circle.x + x1,
                y=circle.y + y1,
                radius=circle.radius,
                color=circle.color,
                confidence=circle.confidence
            )
            all_circles.append(global_circle)

    # Deduplicate circles from overlapping regions
    # Convert to tuples for deduplication
    circle_tuples = [(c.x, c.y, c.radius) for c in all_circles]
    color_map = {(c.x, c.y, c.radius): c.color for c in all_circles}

    # Group by color for deduplication
    circles_by_color: Dict[Tuple[int, int, int], List[Tuple[int, int, int]]] = {}
    for circle in all_circles:
        color = circle.color
        if color not in circles_by_color:
            circles_by_color[color] = []
        circles_by_color[color].append((circle.x, circle.y, circle.radius))

    # Deduplicate each color group
    final_circles = []
    dedup_distance = max_radius // 2  # Tighter threshold for boundary dedup

    for color, circles in circles_by_color.items():
        deduped = deduplicate_circles_kdtree(circles, color, dedup_distance)
        final_circles.extend(deduped)

    return final_circles
