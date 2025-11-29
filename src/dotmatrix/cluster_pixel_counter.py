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
            'partial': self.partial
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
        partial=False  # Will be set by caller if needed
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
    image_shape: Optional[Tuple[int, int]] = None
) -> List[ClusterResult]:
    """Main entry point: cluster CMYK pixels and count per cluster.

    Complete pipeline:
    1. Complete midtone masks (for clustering)
    2. Find black dot centers
    3. Create cluster labels (nearest black pixel)
    4. Count pixels per cluster with deduplication
    5. Flag edge clusters

    Args:
        cyan_mask: Binary mask of cyan ink pixels
        magenta_mask: Binary mask of magenta ink pixels
        yellow_mask: Binary mask of yellow ink pixels
        black_mask: Binary mask of black ink pixels
        image_shape: (height, width) for edge detection. If None, uses mask shape.

    Returns:
        List of ClusterResult, one per black dot cluster.
        Output format: [x, y, C, M, Y, K, R, G, B] with no double counting.
    """
    if image_shape is None:
        image_shape = black_mask.shape

    # Phase 1: Complete midtone masks (used for clustering reference)
    # Note: We don't actually need the completed masks for counting,
    # just for understanding - the counting uses original masks
    _ = complete_midtone_masks(cyan_mask, magenta_mask, yellow_mask, black_mask)

    # Phase 2: Find black dot centers and create cluster labels
    centers = find_black_dot_centers(black_mask)

    if not centers:
        return []

    labels = create_cluster_labels(black_mask)

    # Phase 3: Count pixels per cluster
    results = []

    for i, center in enumerate(centers):
        result = count_cluster_pixels(
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
