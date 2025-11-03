"""Color-based image separation for independent circle detection."""

from typing import List, Tuple, Dict
import numpy as np
from collections import Counter


def get_dominant_colors(
    image: np.ndarray,
    n_colors: int = 4,
    exclude_background: bool = True,
    background_threshold: int = 240,
    min_pixel_count: int = 10000
) -> List[Tuple[int, int, int]]:
    """Get the most common colors in an image using clustering.

    Uses k-means clustering on all non-background pixels to find dominant
    color groups, handling anti-aliasing automatically.

    Args:
        image: RGB image as numpy array (H, W, 3)
        n_colors: Number of dominant colors to return
        exclude_background: If True, exclude near-white pixels
        background_threshold: RGB threshold for background detection
        min_pixel_count: Minimum pixels for a cluster to be considered

    Returns:
        List of RGB tuples for the most dominant colors
    """
    from sklearn.cluster import KMeans

    # Flatten to pixel list
    pixels = image.reshape(-1, 3)

    # Filter background if requested
    if exclude_background:
        mask = (pixels[:, 0] < background_threshold) | \
               (pixels[:, 1] < background_threshold) | \
               (pixels[:, 2] < background_threshold)
        pixels = pixels[mask]

    if len(pixels) < n_colors:
        return []

    # Use k-means to find dominant color clusters
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    kmeans.fit(pixels.astype(np.float32))

    # Get cluster centers
    centers = kmeans.cluster_centers_.astype(int)

    # Count pixels per cluster
    labels = kmeans.labels_
    label_counts = Counter(labels)

    # Filter out small clusters and sort by size
    dominant = []
    for label, count in label_counts.most_common():
        if count >= min_pixel_count:
            color = tuple(int(v) for v in centers[label])
            # Clamp to RGB range
            color = tuple(max(0, min(255, v)) for v in color)
            dominant.append(color)
        if len(dominant) >= n_colors:
            break

    return dominant


def create_color_mask(
    image: np.ndarray,
    target_color: Tuple[int, int, int],
    tolerance: int = 30
) -> np.ndarray:
    """Create a binary mask for pixels matching a target color within tolerance.

    Args:
        image: RGB image as numpy array (H, W, 3)
        target_color: RGB tuple to match
        tolerance: Maximum color distance to consider a match

    Returns:
        Binary mask (H, W) where True = matches target color
    """
    # Calculate color distance
    color_diff = np.abs(image.astype(np.int16) - np.array(target_color))
    distance = np.sqrt(np.sum(color_diff ** 2, axis=2))

    # Create mask where distance is within tolerance
    mask = distance <= tolerance

    return mask


def separate_by_color(
    image: np.ndarray,
    colors: List[Tuple[int, int, int]],
    tolerance: int = 30
) -> Dict[Tuple[int, int, int], np.ndarray]:
    """Separate image into multiple single-color images.

    Creates one image per color where only pixels matching that color
    (within tolerance) are preserved, others are set to white.

    Args:
        image: RGB image as numpy array (H, W, 3)
        colors: List of RGB tuples to separate
        tolerance: Color matching tolerance

    Returns:
        Dictionary mapping color -> separated image
    """
    h, w = image.shape[:2]
    separated = {}

    for color in colors:
        # Create mask for this color
        mask = create_color_mask(image, color, tolerance)

        # Create white background image
        color_image = np.full((h, w, 3), 255, dtype=np.uint8)

        # Copy matching pixels
        color_image[mask] = image[mask]

        separated[color] = color_image

    return separated
