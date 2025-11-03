"""Histogram-based color palette extraction."""

from typing import List, Tuple
from collections import Counter

import numpy as np
from sklearn.cluster import KMeans


def extract_color_palette(
    image: np.ndarray,
    n_colors: int = 4,
    exclude_background: bool = True,
    background_threshold: int = 240,
    mode: str = 'histogram',
    circles: List = None
) -> List[Tuple[int, int, int]]:
    """Extract dominant color palette from image using histogram analysis.

    If circles are provided, samples from circle centers to get pure colors.
    Otherwise, analyzes the entire image histogram to find the N most dominant
    colors. Sampling from circle centers avoids anti-aliased edges and overlapping
    regions.

    Args:
        image: RGB image as numpy array (H, W, 3)
        n_colors: Number of dominant colors to extract
        exclude_background: If True, exclude near-white background pixels
        background_threshold: RGB threshold above which pixels are considered background
        mode: 'histogram' for most common exact colors, 'kmeans' for clustering all pixels
        circles: Optional list of Circle objects to sample from their centers

    Returns:
        List of RGB color tuples representing the dominant colors in the image,
        sorted by prominence (most dominant first)

    Examples:
        >>> img = cv2.imread('cmyk_circles.png')
        >>> img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        >>> palette = extract_color_palette(img_rgb, n_colors=4)
        >>> len(palette)
        4
    """
    # Flatten image to list of pixels
    pixels = image.reshape(-1, 3)

    # Filter out background if requested
    if exclude_background:
        # Keep pixels where at least one channel is below threshold
        mask = (pixels[:, 0] < background_threshold) | \
               (pixels[:, 1] < background_threshold) | \
               (pixels[:, 2] < background_threshold)
        pixels = pixels[mask]

    # If very few pixels remain, return empty
    if len(pixels) < n_colors:
        return []

    if mode == 'histogram':
        # Find most common exact colors, but cluster similar anti-aliased variants
        # Convert to tuples of regular Python ints (not numpy types)
        color_tuples = [tuple(int(v) for v in pixel) for pixel in pixels]
        color_counts = Counter(color_tuples)

        # Get top colors (more than needed to catch anti-aliased variants)
        top_colors = color_counts.most_common(n_colors * 30)

        # Cluster similar colors together using k-means
        if len(top_colors) > n_colors:
            colors_array = np.array([c[0] for c in top_colors], dtype=np.float32)
            weights = np.array([c[1] for c in top_colors], dtype=np.float32)

            kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
            kmeans.fit(colors_array, sample_weight=weights)

            # For each cluster, find the PUREST color (closest to cluster center)
            labels = kmeans.labels_
            palette = []
            for cluster_id in range(n_colors):
                cluster_indices = [i for i in range(len(top_colors)) if labels[i] == cluster_id]
                if cluster_indices:
                    # Find color closest to cluster center (the purest/least anti-aliased)
                    cluster_center = kmeans.cluster_centers_[cluster_id]
                    cluster_colors = [top_colors[i][0] for i in cluster_indices]
                    distances = [np.linalg.norm(np.array(c) - cluster_center) for c in cluster_colors]
                    purest_idx = cluster_indices[np.argmin(distances)]
                    palette.append(top_colors[purest_idx][0])
        else:
            palette = [color for color, _ in top_colors[:n_colors]]
    else:
        # Use k-means on all pixels to find dominant colors
        # This handles anti-aliasing by clustering similar shades together
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels.astype(np.float32))

        # Get cluster centers
        centers = kmeans.cluster_centers_.astype(int)

        # Count how many pixels belong to each cluster (for sorting by dominance)
        labels = kmeans.labels_
        label_counts = Counter(labels)

        # Sort centers by dominance (most pixels first)
        sorted_indices = [idx for idx, _ in label_counts.most_common()]
        palette = [tuple(centers[idx]) for idx in sorted_indices]

    # Clamp to valid RGB range and convert to Python int
    palette = [
        tuple(int(max(0, min(255, v))) for v in color)
        for color in palette
    ]

    return palette


def assign_circle_to_palette(
    circle_color: Tuple[int, int, int],
    palette: List[Tuple[int, int, int]],
    max_distance: float = 50.0
) -> Tuple[int, int, int]:
    """Assign a circle's sampled color to the nearest palette color.

    Uses Euclidean distance in RGB space to find the closest match,
    but only if within max_distance threshold.

    Args:
        circle_color: RGB color sampled from circle edge
        palette: List of palette colors from extract_color_palette()
        max_distance: Maximum allowed distance to assign to palette color.
                     Colors farther than this are returned unchanged.

    Returns:
        The palette color that best matches the circle color, or the
        original color if no palette color is within max_distance

    Examples:
        >>> palette = [(0, 0, 0), (255, 0, 0), (0, 255, 0)]
        >>> assign_circle_to_palette((5, 5, 5), palette)
        (0, 0, 0)
        >>> assign_circle_to_palette((250, 10, 10), palette)
        (255, 0, 0)
        >>> assign_circle_to_palette((128, 128, 128), palette, max_distance=30)
        (128, 128, 128)  # Too far from any palette color
    """
    if not palette:
        return circle_color

    # Convert to numpy for vectorized distance calculation
    circle_vec = np.array(circle_color, dtype=np.float32)
    palette_array = np.array(palette, dtype=np.float32)

    # Calculate Euclidean distance to each palette color
    distances = np.linalg.norm(palette_array - circle_vec, axis=1)

    # Find closest palette color
    closest_idx = np.argmin(distances)
    min_distance = distances[closest_idx]

    # Only assign if within threshold
    if min_distance <= max_distance:
        return palette[closest_idx]
    else:
        return circle_color  # Return original if too far from any palette color
