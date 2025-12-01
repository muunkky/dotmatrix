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
from typing import List, Tuple, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import json
import hashlib
import warnings

import cv2
import numpy as np
from scipy.ndimage import label as ndimage_label
from scipy.spatial import KDTree

# Import GPU functions for acceleration (auto-fallback to CPU if unavailable)
from .gpu import (
    is_gpu_available,
    gpu_nms_centers,
    gpu_create_cluster_labels,
    gpu_count_cluster_colors,
)


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

    @classmethod
    def from_dict(cls, data: Dict) -> 'ClusterResult':
        """Create ClusterResult from dictionary.

        Args:
            data: Dictionary with 'center', 'pixel_counts', and optionally
                  'partial' and 'bbox' keys.

        Returns:
            ClusterResult instance
        """
        center = data['center']
        counts = data['pixel_counts']
        bbox_list = data.get('bbox')

        return cls(
            x=center[0],
            y=center[1],
            cyan=counts['cyan'],
            magenta=counts['magenta'],
            yellow=counts['yellow'],
            black=counts['black'],
            red=counts['red'],
            green=counts['green'],
            blue=counts['blue'],
            partial=data.get('partial', False),
            bbox=tuple(bbox_list) if bbox_list else None
        )


# =============================================================================
# Cluster Cache Functions
# =============================================================================

CACHE_VERSION = "1.0"


def save_clusters(
    clusters: List[ClusterResult],
    path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Save cluster results to JSON file with metadata.

    Args:
        clusters: List of ClusterResult objects to save
        path: Output file path (will be created, including parent dirs)
        metadata: Optional metadata dict with keys like:
            - source_image_hash: SHA256 hash of source image
            - detection_params: Dict of detection parameters
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    cache_data = {
        'version': CACHE_VERSION,
        'cluster_count': len(clusters),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'metadata': metadata or {},
        'clusters': [c.to_dict() for c in clusters]
    }

    with open(path, 'w') as f:
        json.dump(cache_data, f, indent=2)


def load_clusters(path: Path) -> Tuple[List[ClusterResult], Dict[str, Any]]:
    """Load cluster results from JSON cache file.

    Args:
        path: Path to cache file

    Returns:
        Tuple of (clusters list, metadata dict)

    Raises:
        FileNotFoundError: If cache file doesn't exist
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Cluster cache file not found: {path}")

    with open(path, 'r') as f:
        cache_data = json.load(f)

    clusters = [ClusterResult.from_dict(d) for d in cache_data.get('clusters', [])]
    metadata = cache_data.get('metadata', {})

    return clusters, metadata


def validate_cluster_cache(
    path: Path,
    expected_hash: str
) -> Dict[str, Any]:
    """Validate cluster cache file against expected source image hash.

    Loads the cache file and checks if the source image hash in metadata
    matches the expected hash.

    Args:
        path: Path to cache file
        expected_hash: Expected SHA256 hash of source image

    Returns:
        Dict with:
            - valid: True if cache is usable
            - hash_match: True if hash matches, False otherwise
            - warning: Present if hash mismatch (string message)
    """
    path = Path(path)
    with open(path, 'r') as f:
        cache_data = json.load(f)

    metadata = cache_data.get('metadata', {})
    cached_hash = metadata.get('source_image_hash')

    result = {
        'valid': True,  # Cache is always usable, just may not match
    }

    if cached_hash is None:
        # No hash stored, can't validate match
        result['hash_match'] = False
        return result

    if cached_hash != expected_hash:
        result['hash_match'] = False
        result['warning'] = (
            f"Cluster cache source image hash mismatch. "
            f"Cached: {cached_hash[:16]}..., Expected: {expected_hash[:16]}..."
        )
        return result

    result['hash_match'] = True
    return result


def compute_image_hash(image_path: Path) -> str:
    """Compute SHA256 hash of an image file.

    Args:
        image_path: Path to image file

    Returns:
        Hex-encoded SHA256 hash string
    """
    hasher = hashlib.sha256()
    with open(image_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


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
    threshold_ratio: float = 0.5,
    use_gpu: bool = True
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
        use_gpu: If True, use GPU acceleration for NMS when available

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
    # Use ratio of max, but floor at 0.5 to catch single-pixel dots (dist_transform=1)
    threshold = max(0.5, threshold_ratio * dist_transform.max())

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
        centers = _nms_centers(centers, dist_transform, min_distance, use_gpu=use_gpu)

    return centers


def _nms_centers(
    centers: List[Tuple[int, int]],
    dist_transform: np.ndarray,
    min_distance: int,
    use_gpu: bool = True
) -> List[Tuple[int, int]]:
    """Apply non-maximum suppression to center points.

    Keeps centers with highest distance transform value when multiple
    centers are within min_distance of each other.

    Args:
        centers: List of (x, y) center coordinates
        dist_transform: Distance transform array for scoring
        min_distance: Minimum distance between kept centers
        use_gpu: If True, use GPU acceleration when available

    Returns:
        Filtered list of (x, y) center coordinates
    """
    if len(centers) <= 1:
        return centers

    # Extract scores from distance transform
    scores = np.array([dist_transform[y, x] for x, y in centers])
    centers_array = np.array(centers, dtype=np.float64)

    # Use GPU-accelerated NMS when available and enabled
    if use_gpu:
        result = gpu_nms_centers(centers_array, scores, float(min_distance))
        return [(int(x), int(y)) for x, y in result]

    # CPU fallback
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
    max_distance: Optional[float] = None,
    use_gpu: bool = True
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
        use_gpu: If True, use GPU acceleration when available

    Returns:
        Label image where each pixel value is the cluster ID (0-indexed).
        Pixels beyond max_distance get label -1.
    """
    h, w = image_shape

    if not centers:
        return np.full((h, w), -1, dtype=np.int32)

    centers_array = np.array(centers, dtype=np.float32)  # Already (x, y) format

    # Use GPU-accelerated label creation when available and enabled
    if use_gpu and max_distance is None:
        # GPU path - uses Voronoi tessellation via nearest center
        labels = gpu_create_cluster_labels(image_shape, centers_array)
        return labels.astype(np.int32)

    # CPU fallback - uses KDTree
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
    separation_method: str = 'distance_transform',
    min_dot_distance: int = 10,
    anchor_method: str = 'centroid',
    return_debug_info: bool = False,
    use_gpu: bool = True
):
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
        return_debug_info: If True, returns (results, debug_info) tuple with
                   debug_info containing 'labels' and 'centers' for visualization.
        use_gpu: If True, use GPU acceleration when available. Default True.
                 GPU is used for NMS, cluster labeling, and color counting.

    Returns:
        If return_debug_info=False (default):
            List of ClusterResult, one per black dot cluster.
        If return_debug_info=True:
            Tuple of (results, debug_info) where debug_info is a dict with
            'labels' (np.ndarray) and 'centers' (list of (x,y) tuples).
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
            threshold_ratio=0.3,  # Lower threshold to catch more dots
            use_gpu=use_gpu
        )
    else:
        # Default: connected component analysis
        centers = find_black_dot_centers(black_mask)

    # Create cluster labels based on anchor_method (decoupled from separation_method)
    if anchor_method == 'centroid':
        # Assign pixels to nearest center point (more stable, default)
        labels = create_cluster_labels_from_centers(centers, image_shape, use_gpu=use_gpu)
    else:
        # 'nearest_pixel': Assign to nearest black pixel (legacy behavior)
        labels = create_cluster_labels(black_mask)

    if not centers:
        if return_debug_info:
            return [], {'labels': labels, 'centers': []}
        return []

    # Phase 3: Count pixels per cluster
    n_clusters = len(centers)

    # Helper function to compute bbox for a cluster
    def _compute_bbox(cluster_id: int) -> Optional[Tuple[int, int, int, int]]:
        """Compute bounding box from ink pixels in cluster."""
        cluster_mask = labels == cluster_id
        ink_mask = cluster_mask & (
            (cyan_mask > 0) | (magenta_mask > 0) |
            (yellow_mask > 0) | (black_mask > 0)
        )
        coords = np.argwhere(ink_mask)
        if len(coords) > 0:
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            return (int(x_min), int(y_min), int(x_max), int(y_max))
        return None

    # Use GPU-accelerated batch counting when available
    if use_gpu and color_mode == 'cmyk':
        # CMYK mode: simple batch counting without overlap detection
        color_masks = {
            'C': cyan_mask > 0,
            'M': magenta_mask > 0,
            'Y': yellow_mask > 0,
            'K': black_mask > 0,
        }
        counts = gpu_count_cluster_colors(labels, color_masks, n_clusters)

        results = []
        for i, center in enumerate(centers):
            result = ClusterResult(
                x=center[0],
                y=center[1],
                cyan=int(counts['C'][i]),
                magenta=int(counts['M'][i]),
                yellow=int(counts['Y'][i]),
                black=int(counts['K'][i]),
                red=0,
                green=0,
                blue=0,
                partial=False,
                bbox=_compute_bbox(i)
            )

            # Check if edge cluster
            radius = estimate_cluster_radius(i, labels, black_mask)
            if is_edge_cluster(center[0], center[1], radius, image_shape):
                result.partial = True

            results.append(result)

    elif use_gpu and color_mode == 'full':
        # Full mode with GPU: compute overlap masks, then batch count
        # Pre-compute overlap masks
        c_mask = cyan_mask > 0
        m_mask = magenta_mask > 0
        y_mask = yellow_mask > 0
        k_mask = black_mask > 0

        # Pure colors (excluding overlaps)
        cyan_pure = c_mask & ~m_mask & ~y_mask
        magenta_pure = m_mask & ~c_mask & ~y_mask
        yellow_pure = y_mask & ~c_mask & ~m_mask

        # RGB overlaps (exactly 2 colors, not 3)
        red_mask = m_mask & y_mask & ~c_mask     # M ∩ Y - C
        green_mask = c_mask & y_mask & ~m_mask   # C ∩ Y - M
        blue_mask = c_mask & m_mask & ~y_mask    # C ∩ M - Y

        color_masks = {
            'C': cyan_pure,
            'M': magenta_pure,
            'Y': yellow_pure,
            'K': k_mask,
            'R': red_mask,
            'G': green_mask,
            'B': blue_mask,
        }
        counts = gpu_count_cluster_colors(labels, color_masks, n_clusters)

        results = []
        for i, center in enumerate(centers):
            result = ClusterResult(
                x=center[0],
                y=center[1],
                cyan=int(counts['C'][i]),
                magenta=int(counts['M'][i]),
                yellow=int(counts['Y'][i]),
                black=int(counts['K'][i]),
                red=int(counts['R'][i]),
                green=int(counts['G'][i]),
                blue=int(counts['B'][i]),
                partial=False,
                bbox=_compute_bbox(i)
            )

            # Check if edge cluster
            radius = estimate_cluster_radius(i, labels, black_mask)
            if is_edge_cluster(center[0], center[1], radius, image_shape):
                result.partial = True

            results.append(result)

    else:
        # CPU fallback: per-cluster counting
        if color_mode == 'cmyk':
            count_func = count_cluster_pixels_cmyk
        else:
            count_func = count_cluster_pixels

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

    if return_debug_info:
        return results, {'labels': labels, 'centers': centers}
    return results


# =============================================================================
# Debug Visualization Functions
# =============================================================================

def generate_cluster_colors(n_clusters: int) -> List[Tuple[int, int, int]]:
    """Generate N visually distinct colors for cluster visualization.

    Uses HSV color space with evenly spaced hues for maximum visual
    distinction between clusters.

    Args:
        n_clusters: Number of distinct colors needed

    Returns:
        List of BGR color tuples (OpenCV format)
    """
    if n_clusters == 0:
        return []

    colors = []
    for i in range(n_clusters):
        # Evenly space hues around the color wheel (OpenCV hue: 0-180)
        hue = int(180 * i / n_clusters)
        # High saturation and value for visibility
        hsv_color = np.array([[[hue, 255, 200]]], dtype=np.uint8)
        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0, 0]
        colors.append(tuple(int(c) for c in bgr_color))

    return colors


def generate_cluster_debug_image(
    labels: np.ndarray,
    centers: List[Tuple[int, int]],
    partial_flags: List[bool],
    original_image: Optional[np.ndarray] = None,
    overlay_alpha: float = 0.5
) -> np.ndarray:
    """Generate a debug visualization image showing cluster assignments.

    Creates a color-coded image where each cluster is drawn in a unique,
    visually distinct color. Cluster centers are marked with crosshairs.

    Args:
        labels: 2D array where each pixel contains its cluster ID (0-indexed),
                or -1 for background/unassigned pixels
        centers: List of (x, y) center coordinates for each cluster
        partial_flags: List of booleans indicating if each cluster is partial
        original_image: Optional BGR image to overlay clusters on
        overlay_alpha: Transparency for overlay mode (0=fully transparent, 1=opaque)

    Returns:
        BGR image with color-coded clusters and marked centers
    """
    h, w = labels.shape[:2]

    # Find unique cluster IDs (excluding -1 background)
    unique_ids = np.unique(labels)
    cluster_ids = [cid for cid in unique_ids if cid >= 0]
    n_clusters = len(cluster_ids)

    # Generate distinct colors for each cluster
    colors = generate_cluster_colors(max(n_clusters, 1))

    # Create output image
    debug_img = np.zeros((h, w, 3), dtype=np.uint8)

    # Fill each cluster with its color
    for idx, cluster_id in enumerate(cluster_ids):
        color = colors[idx % len(colors)]
        mask = labels == cluster_id
        debug_img[mask] = color

    # If overlay mode, blend with original image
    if original_image is not None:
        # Ensure original is BGR and same size
        if len(original_image.shape) == 2:
            original_bgr = cv2.cvtColor(original_image, cv2.COLOR_GRAY2BGR)
        else:
            original_bgr = original_image

        if original_bgr.shape[:2] != (h, w):
            original_bgr = cv2.resize(original_bgr, (w, h))

        debug_img = cv2.addWeighted(
            debug_img, overlay_alpha,
            original_bgr, 1 - overlay_alpha,
            0
        )

    # Mark cluster centers with crosshairs
    crosshair_color = (255, 255, 255)  # White
    crosshair_size = 5

    for i, (cx, cy) in enumerate(centers):
        # Ensure center is within image bounds
        if 0 <= cx < w and 0 <= cy < h:
            # Draw crosshair
            cv2.line(debug_img,
                     (cx - crosshair_size, cy),
                     (cx + crosshair_size, cy),
                     crosshair_color, 1)
            cv2.line(debug_img,
                     (cx, cy - crosshair_size),
                     (cx, cy + crosshair_size),
                     crosshair_color, 1)

            # Mark partial clusters with a circle
            if i < len(partial_flags) and partial_flags[i]:
                cv2.circle(debug_img, (cx, cy), crosshair_size + 2,
                          (0, 0, 255), 1)  # Red circle for partial

    return debug_img
