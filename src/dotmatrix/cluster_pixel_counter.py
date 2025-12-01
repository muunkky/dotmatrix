"""CMYK Cluster Pixel Counting.

This module implements pixel-level analysis of CMYK halftone images by:
1. Completing midtone masks (include RGB overlaps for clustering)
2. Clustering pixels around black (K) dot centers
3. Counting pixels per cluster with deduplication

Output format per cluster: [x, y, cyan, magenta, yellow, black, red, green, blue]
where x,y is the black dot center and counts have no double-counting.

ADR: See .gitban/cards/CLUSTERING-*-adr-cluster-pixel-counting-architecture-*.md
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

import cv2
import numpy as np
from scipy.ndimage import label as ndimage_label
from scipy.spatial import KDTree


@dataclass
class ClusterResult:
    """Result for a single halftone cluster.

    Attributes:
        x, y: Center point of the black dot (anchor)
        cyan, magenta, yellow: Pure midtone pixel counts (RGB subtracted)
        black: Black ink pixel count
        red, green, blue: Overlap pixel counts (M∩Y, C∩Y, C∩M)
        partial: True if cluster is at image edge (may have incomplete counts)
        bbox: Bounding box as (x_min, y_min, x_max, y_max), or None if not computed
    """
    x: int
    y: int
    cyan: int
    magenta: int
    yellow: int
    black: int
    red: int
    green: int
    blue: int
    partial: bool = False
    bbox: Optional[Tuple[int, int, int, int]] = None

    def to_list(self) -> List[int]:
        """Convert to [x, y, C, M, Y, K, R, G, B] list."""
        return [self.x, self.y, self.cyan, self.magenta, self.yellow,
                self.black, self.red, self.green, self.blue]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'center': [self.x, self.y],
            'pixel_counts': {
                'cyan': self.cyan,
                'magenta': self.magenta,
                'yellow': self.yellow,
                'black': self.black,
                'red': self.red,
                'green': self.green,
                'blue': self.blue,
            },
            'partial': self.partial,
            'bbox': list(self.bbox) if self.bbox else None
        }


def complete_midtone_masks(
    cyan_mask: np.ndarray,
    magenta_mask: np.ndarray,
    yellow_mask: np.ndarray,
    black_mask: np.ndarray
) -> Dict[str, np.ndarray]:
    """Complete midtone masks by including RGB overlap pixels.

    Phase 1 of the algorithm: For clustering purposes, we need complete
    circles. RGB overlaps fragment the midtone masks, so we include them
    temporarily to enable nearest-neighbor clustering.

    Args:
        cyan_mask: Binary mask of cyan ink pixels
        magenta_mask: Binary mask of magenta ink pixels
        yellow_mask: Binary mask of yellow ink pixels
        black_mask: Binary mask of black ink pixels

    Returns:
        Dict with 'cyan', 'magenta', 'yellow' completed masks.
        Each mask includes its RGB children:
        - Cyan += Green (C∩Y) + Blue (C∩M)
        - Magenta += Red (M∩Y) + Blue (C∩M)
        - Yellow += Red (M∩Y) + Green (C∩Y)
    """
    # Compute overlap masks
    red_mask = (magenta_mask > 0) & (yellow_mask > 0)      # M ∩ Y
    green_mask = (cyan_mask > 0) & (yellow_mask > 0)       # C ∩ Y
    blue_mask = (cyan_mask > 0) & (magenta_mask > 0)       # C ∩ M

    # Complete each midtone by including overlaps
    cyan_complete = (cyan_mask > 0) | green_mask | blue_mask
    magenta_complete = (magenta_mask > 0) | red_mask | blue_mask
    yellow_complete = (yellow_mask > 0) | red_mask | green_mask

    return {
        'cyan': (cyan_complete * 255).astype(np.uint8),
        'magenta': (magenta_complete * 255).astype(np.uint8),
        'yellow': (yellow_complete * 255).astype(np.uint8),
    }


def find_black_dot_centers(black_mask: np.ndarray) -> List[Tuple[int, int]]:
    """Find center points of black dots.

    Uses connected component analysis to find each black dot,
    then computes the centroid of each component.

    Args:
        black_mask: Binary mask of black ink pixels

    Returns:
        List of (x, y) center coordinates for each black dot
    """
    if np.sum(black_mask) == 0:
        return []

    # Find connected components
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        black_mask, connectivity=8
    )

    centers = []
    for i in range(1, num_labels):  # Skip background (label 0)
        cx, cy = centroids[i]
        centers.append((int(round(cx)), int(round(cy))))

    return centers


def find_black_dot_centers_distance_transform(
    black_mask: np.ndarray,
    min_distance: int = 10,
    threshold_ratio: float = 0.5
) -> List[Tuple[int, int]]:
    """Find center points of black dots using distance transform.

    Uses distance transform with local maxima detection to separate
    merged/overlapping black dots. This is more robust than connected
    component centroids for dense halftone patterns where dots touch.

    Algorithm:
    1. Apply distance transform (distance from each pixel to edge)
    2. Find local maxima (peaks = circle centers)
    3. Filter by minimum distance between peaks

    Args:
        black_mask: Binary mask of black ink pixels
        min_distance: Minimum distance between detected centers (pixels)
        threshold_ratio: Minimum peak height as ratio of max (0-1)

    Returns:
        List of (x, y) center coordinates for each black dot
    """
    from scipy.ndimage import maximum_filter

    if np.sum(black_mask) == 0:
        return []

    # Ensure binary mask
    binary = (black_mask > 0).astype(np.uint8)

    # Distance transform: each pixel gets distance to nearest edge
    dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 5)

    if dist_transform.max() == 0:
        return []

    # Threshold to get significant peaks only
    threshold = threshold_ratio * dist_transform.max()

    # Find local maxima using maximum filter
    # A pixel is a local max if it equals the max in its neighborhood
    neighborhood_size = max(3, min_distance)
    local_max = maximum_filter(dist_transform, size=neighborhood_size)

    # Peaks are where distance transform equals local max AND above threshold
    peaks = (dist_transform == local_max) & (dist_transform > threshold) & binary.astype(bool)

    # Get peak coordinates
    peak_coords = np.argwhere(peaks)  # (y, x) format

    if len(peak_coords) == 0:
        # Fall back to connected components if no peaks found
        return find_black_dot_centers(black_mask)

    # Convert to (x, y) format
    centers = [(int(x), int(y)) for y, x in peak_coords]

    # Non-maximum suppression to ensure min_distance between centers
    if min_distance > 0 and len(centers) > 1:
        centers = _nms_centers(centers, dist_transform, min_distance)

    return centers


def _nms_centers(
    centers: List[Tuple[int, int]],
    dist_transform: np.ndarray,
    min_distance: int
) -> List[Tuple[int, int]]:
    """Apply non-maximum suppression to center points.

    Keeps centers with highest distance transform value when multiple
    centers are within min_distance of each other.
    """
    if len(centers) <= 1:
        return centers

    # Sort by distance transform value (descending)
    scores = [dist_transform[y, x] for x, y in centers]
    sorted_indices = np.argsort(scores)[::-1]

    kept = []
    suppressed = set()

    for idx in sorted_indices:
        if idx in suppressed:
            continue

        x, y = centers[idx]
        kept.append((x, y))

        # Suppress nearby centers
        for other_idx in sorted_indices:
            if other_idx in suppressed or other_idx == idx:
                continue
            ox, oy = centers[other_idx]
            dist = np.sqrt((x - ox)**2 + (y - oy)**2)
            if dist < min_distance:
                suppressed.add(other_idx)

    return kept


def create_cluster_labels_from_centers(
    centers: List[Tuple[int, int]],
    image_shape: Tuple[int, int],
    max_distance: Optional[float] = None
) -> np.ndarray:
    """Create cluster label image based on nearest center point.

    Unlike create_cluster_labels (which uses connected component labels),
    this function assigns each pixel to the nearest CENTER from a provided
    list. This allows properly separating merged blobs when centers are
    found using distance transform.

    Args:
        centers: List of (x, y) center coordinates
        image_shape: (height, width) of the image
        max_distance: Maximum distance to assign to a cluster. Pixels
                     farther than this get label -1. If None, all pixels
                     are assigned.

    Returns:
        Label image where each pixel value is the cluster ID (0-indexed).
        Pixels beyond max_distance get label -1.
    """
    h, w = image_shape

    if not centers:
        return np.full((h, w), -1, dtype=np.int32)

    # Build KDTree from centers
    centers_array = np.array(centers)  # Already (x, y) format
    tree = KDTree(centers_array)

    # For each pixel, find nearest center
    all_coords = np.mgrid[0:h, 0:w].reshape(2, -1).T  # All (y, x) coords
    all_coords_xy = all_coords[:, ::-1]  # Convert to (x, y)

    # Query nearest center for each point
    distances, indices = tree.query(all_coords_xy)

    # Reshape to image
    labels = indices.reshape(h, w)

    # Apply max_distance threshold if specified
    if max_distance is not None:
        distances = distances.reshape(h, w)
        labels[distances > max_distance] = -1

    return labels.astype(np.int32)


def create_cluster_labels(black_mask: np.ndarray) -> np.ndarray:
    """Create cluster label image based on nearest black pixel.

    Phase 2: For each pixel in the image, assign it to the cluster
    of the nearest black pixel. Uses KDTree for efficient nearest
    neighbor lookup.

    Args:
        black_mask: Binary mask of black ink pixels

    Returns:
        Label image where each pixel value is the cluster ID (0-indexed).
        Background pixels (far from any black) get label -1.
    """
    h, w = black_mask.shape

    # Find all black pixel coordinates
    black_coords = np.argwhere(black_mask > 0)  # (N, 2) array of (y, x)

    if len(black_coords) == 0:
        return np.full((h, w), -1, dtype=np.int32)

    # First, label each black connected component
    num_labels, component_labels = cv2.connectedComponents(black_mask, connectivity=8)

    # Create mapping from black pixel coordinate to its component label
    # Build KDTree from black pixel coordinates
    # Note: KDTree expects (x, y) but argwhere gives (y, x)
    black_coords_xy = black_coords[:, ::-1]  # Convert to (x, y)
    tree = KDTree(black_coords_xy)

    # For each pixel, find nearest black pixel and get its component
    all_coords = np.mgrid[0:h, 0:w].reshape(2, -1).T  # All (y, x) coords
    all_coords_xy = all_coords[:, ::-1]  # Convert to (x, y)

    # Query nearest black pixel for each point
    distances, indices = tree.query(all_coords_xy)

    # Get the component label for each nearest black pixel
    nearest_black_yx = black_coords[indices]
    cluster_labels = component_labels[nearest_black_yx[:, 0], nearest_black_yx[:, 1]]

    # Reshape back to image
    labels = cluster_labels.reshape(h, w)

    # Subtract 1 so labels are 0-indexed (component 0 was background)
    labels = labels - 1

    return labels.astype(np.int32)


def count_cluster_pixels(
    cluster_id: int,
    labels: np.ndarray,
    cyan_mask: np.ndarray,
    magenta_mask: np.ndarray,
    yellow_mask: np.ndarray,
    black_mask: np.ndarray,
    center: Tuple[int, int]
) -> ClusterResult:
    """Count pixels in a single cluster with RGB deduplication.

    Phase 3: Count pixels for each color channel, then subtract
    RGB overlaps from their parent CMY masks to avoid double counting.

    Args:
        cluster_id: The cluster label to count
        labels: Cluster label image from create_cluster_labels()
        cyan_mask: Original cyan ink mask
        magenta_mask: Original magenta ink mask
        yellow_mask: Original yellow ink mask
        black_mask: Original black ink mask
        center: (x, y) center of the black dot

    Returns:
        ClusterResult with deduplicated pixel counts
    """
    # Mask for this cluster
    cluster_mask = labels == cluster_id

    # Get pixels in this cluster for each ink
    c_pixels = cluster_mask & (cyan_mask > 0)
    m_pixels = cluster_mask & (magenta_mask > 0)
    y_pixels = cluster_mask & (yellow_mask > 0)
    k_pixels = cluster_mask & (black_mask > 0)

    # Compute bounding box from actual ink pixels (not Voronoi region)
    ink_mask = c_pixels | m_pixels | y_pixels | k_pixels
    coords = np.argwhere(ink_mask)
    if len(coords) > 0:
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        bbox = (int(x_min), int(y_min), int(x_max), int(y_max))
    else:
        bbox = None

    # Count RGB overlaps (these are definitive, no deduplication needed)
    red_pixels = m_pixels & y_pixels & ~c_pixels    # M ∩ Y - C (pure red)
    green_pixels = c_pixels & y_pixels & ~m_pixels  # C ∩ Y - M (pure green)
    blue_pixels = c_pixels & m_pixels & ~y_pixels   # C ∩ M - Y (pure blue)

    # Triple overlap (C ∩ M ∩ Y) - count separately or assign to one channel
    # For now, we'll count it as part of the overlap totals
    cmy_triple = c_pixels & m_pixels & y_pixels

    red_count = int(np.sum(red_pixels))
    green_count = int(np.sum(green_pixels))
    blue_count = int(np.sum(blue_pixels))

    # Count pure CMY (excluding ALL overlaps)
    cyan_pure = c_pixels & ~m_pixels & ~y_pixels
    magenta_pure = m_pixels & ~c_pixels & ~y_pixels
    yellow_pure = y_pixels & ~c_pixels & ~m_pixels

    cyan_count = int(np.sum(cyan_pure))
    magenta_count = int(np.sum(magenta_pure))
    yellow_count = int(np.sum(yellow_pure))
    black_count = int(np.sum(k_pixels))

    return ClusterResult(
        x=center[0],
        y=center[1],
        cyan=cyan_count,
        magenta=magenta_count,
        yellow=yellow_count,
        black=black_count,
        red=red_count,
        green=green_count,
        blue=blue_count,
        partial=False,  # Will be set by caller if needed
        bbox=bbox
    )


def count_cluster_pixels_cmyk(
    cluster_id: int,
    labels: np.ndarray,
    cyan_mask: np.ndarray,
    magenta_mask: np.ndarray,
    yellow_mask: np.ndarray,
    black_mask: np.ndarray,
    center: Tuple[int, int]
) -> ClusterResult:
    """Count pixels in CMYK-only mode (no RGB overlap detection).

    In CMYK mode, each ink channel is counted independently without
    subtracting overlaps. This is useful for halftone separation printing
    where overlaps occur naturally during physical printing.

    Args:
        cluster_id: The cluster label to count
        labels: Cluster label image from create_cluster_labels()
        cyan_mask: Original cyan ink mask
        magenta_mask: Original magenta ink mask
        yellow_mask: Original yellow ink mask
        black_mask: Original black ink mask
        center: (x, y) center of the black dot

    Returns:
        ClusterResult with CMYK counts only (RGB always 0)
    """
    # Mask for this cluster
    cluster_mask = labels == cluster_id

    # Get ink pixels for this cluster
    c_pixels = cluster_mask & (cyan_mask > 0)
    m_pixels = cluster_mask & (magenta_mask > 0)
    y_pixels = cluster_mask & (yellow_mask > 0)
    k_pixels = cluster_mask & (black_mask > 0)

    # Compute bounding box from actual ink pixels (not Voronoi region)
    ink_mask = c_pixels | m_pixels | y_pixels | k_pixels
    coords = np.argwhere(ink_mask)
    if len(coords) > 0:
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0)
        bbox = (int(x_min), int(y_min), int(x_max), int(y_max))
    else:
        bbox = None

    # Count all pixels with each ink (no overlap subtraction)
    cyan_count = int(np.sum(c_pixels))
    magenta_count = int(np.sum(m_pixels))
    yellow_count = int(np.sum(y_pixels))
    black_count = int(np.sum(k_pixels))

    return ClusterResult(
        x=center[0],
        y=center[1],
        cyan=cyan_count,
        magenta=magenta_count,
        yellow=yellow_count,
        black=black_count,
        red=0,
        green=0,
        blue=0,
        partial=False,  # Will be set by caller if needed
        bbox=bbox
    )


def is_edge_cluster(
    x: int,
    y: int,
    radius_estimate: int,
    image_shape: Tuple[int, int]
) -> bool:
    """Check if a cluster is at the image edge.

    Args:
        x, y: Center coordinates
        radius_estimate: Approximate radius of the cluster
        image_shape: (height, width) of the image

    Returns:
        True if cluster touches or extends beyond image boundary
    """
    h, w = image_shape
    margin = radius_estimate

    if x - margin < 0 or x + margin >= w:
        return True
    if y - margin < 0 or y + margin >= h:
        return True

    return False


def estimate_cluster_radius(
    cluster_id: int,
    labels: np.ndarray,
    black_mask: np.ndarray
) -> int:
    """Estimate the radius of a cluster based on its black dot."""
    cluster_mask = (labels == cluster_id) & (black_mask > 0)
    area = np.sum(cluster_mask)
    if area == 0:
        return 10  # Default estimate
    return int(np.sqrt(area / np.pi))


def cluster_and_count_pixels(
    cyan_mask: np.ndarray,
    magenta_mask: np.ndarray,
    yellow_mask: np.ndarray,
    black_mask: np.ndarray,
    image_shape: Optional[Tuple[int, int]] = None,
    color_mode: str = 'full',
    separation_method: str = 'connected',
    min_dot_distance: int = 10,
    anchor_method: str = 'centroid'
) -> List[ClusterResult]:
    """Main entry point: cluster CMYK pixels and count per cluster.

    Complete pipeline:
    1. Complete midtone masks (for clustering)
    2. Find black dot centers
    3. Create cluster labels (based on anchor_method)
    4. Count pixels per cluster with deduplication
    5. Flag edge clusters

    Args:
        cyan_mask: Binary mask of cyan ink pixels
        magenta_mask: Binary mask of magenta ink pixels
        yellow_mask: Binary mask of yellow ink pixels
        black_mask: Binary mask of black ink pixels
        image_shape: (height, width) for edge detection. If None, uses mask shape.
        color_mode: 'full' for 7-color mode with RGB overlaps,
                   'cmyk' for 4-color mode without overlap detection,
                   'absolute' for CMYK only (alias for 'cmyk').
        separation_method: Method for separating merged black dots:
                   'connected' (default) - connected component centroids
                   'distance_transform' - distance transform local maxima
        min_dot_distance: Minimum distance between black dot centers when
                   using distance_transform method (default: 10 pixels)
        anchor_method: Method for assigning pixels to clusters:
                   'centroid' (default) - assign to nearest black dot center
                   'nearest_pixel' - assign to nearest black pixel (legacy)

    Returns:
        List of ClusterResult, one per black dot cluster.
        Output format: [x, y, C, M, Y, K, R, G, B] with no double counting.
    """
    if image_shape is None:
        image_shape = black_mask.shape

    # Validate anchor_method
    valid_anchor_methods = ('centroid', 'nearest_pixel')
    if anchor_method not in valid_anchor_methods:
        raise ValueError(
            f"anchor_method must be one of {valid_anchor_methods}, got '{anchor_method}'"
        )

    # Normalize color_mode alias
    if color_mode == 'absolute':
        color_mode = 'cmyk'

    # Phase 1: Complete midtone masks (used for clustering reference)
    # Note: We don't actually need the completed masks for counting,
    # just for understanding - the counting uses original masks
    _ = complete_midtone_masks(cyan_mask, magenta_mask, yellow_mask, black_mask)

    # Phase 2: Find black dot centers based on separation_method
    if separation_method == 'distance_transform':
        # Use distance transform for better separation of merged dots
        centers = find_black_dot_centers_distance_transform(
            black_mask,
            min_distance=min_dot_distance,
            threshold_ratio=0.3  # Lower threshold to catch more dots
        )
    else:
        # Default: connected component analysis
        centers = find_black_dot_centers(black_mask)

    # Create cluster labels based on anchor_method (decoupled from separation_method)
    if anchor_method == 'centroid':
        # Assign pixels to nearest center point (more stable, default)
        labels = create_cluster_labels_from_centers(centers, image_shape)
    else:
        # 'nearest_pixel': Assign to nearest black pixel (legacy behavior)
        labels = create_cluster_labels(black_mask)

    if not centers:
        return []

    # Choose counting function based on color mode
    if color_mode == 'cmyk':
        count_func = count_cluster_pixels_cmyk
    else:
        count_func = count_cluster_pixels

    # Phase 3: Count pixels per cluster
    results = []

    for i, center in enumerate(centers):
        result = count_func(
            cluster_id=i,
            labels=labels,
            cyan_mask=cyan_mask,
            magenta_mask=magenta_mask,
            yellow_mask=yellow_mask,
            black_mask=black_mask,
            center=center
        )

        # Check if edge cluster
        radius = estimate_cluster_radius(i, labels, black_mask)
        if is_edge_cluster(center[0], center[1], radius, image_shape):
            result.partial = True

        results.append(result)

    return results
