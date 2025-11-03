"""K-means color clustering for intelligent color grouping."""

from typing import Dict, List, Tuple

import numpy as np
from sklearn.cluster import KMeans


def cluster_colors(
    colors: List[Tuple[int, int, int]],
    n_clusters: int
) -> Dict[Tuple[int, int, int], Tuple[int, int, int]]:
    """Cluster colors using k-means to reduce to N groups.

    Uses k-means clustering in RGB space to intelligently group similar
    colors. Useful for reducing many unique colors to a smaller set of
    representative colors (e.g., 20 colors -> 4 color groups).

    Args:
        colors: List of RGB color tuples (r, g, b) where each channel is 0-255
        n_clusters: Target number of color clusters

    Returns:
        Dictionary mapping original colors to their cluster center colors.
        Keys are original RGB tuples, values are cluster center RGB tuples.

    Examples:
        >>> colors = [(255, 0, 0), (250, 5, 5), (0, 255, 0)]
        >>> mapping = cluster_colors(colors, n_clusters=2)
        >>> len(set(mapping.values()))  # Number of unique clusters
        2

    Edge Cases:
        - Empty list: Returns empty dict
        - Fewer colors than clusters: Returns clusters <= len(colors)
        - Single color: Maps to itself
    """
    # Handle empty input
    if not colors:
        return {}

    # Handle single color
    if len(colors) == 1:
        return {colors[0]: colors[0]}

    # Adjust n_clusters if we have fewer colors than requested
    actual_clusters = min(n_clusters, len(colors))

    # Convert to numpy array for sklearn
    colors_array = np.array(colors, dtype=np.float32)

    # Perform k-means clustering
    kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
    kmeans.fit(colors_array)

    # Get cluster centers and labels
    cluster_centers = kmeans.cluster_centers_.astype(int)
    labels = kmeans.labels_

    # Create mapping from original colors to cluster centers
    mapping = {}
    for i, color in enumerate(colors):
        cluster_idx = labels[i]
        cluster_center = tuple(cluster_centers[cluster_idx])
        # Ensure values are in valid RGB range [0, 255]
        cluster_center = tuple(max(0, min(255, v)) for v in cluster_center)
        mapping[color] = cluster_center

    return mapping
