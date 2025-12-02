"""Orphan pixel diagnostic tool.

Identifies and visualizes non-white pixels that are not covered by any
detected cluster. Essential for debugging detection failures and validating
improvements to the detection algorithm.

Usage:
    from dotmatrix.orphan_diagnostic import OrphanDiagnostic
    
    diagnostic = OrphanDiagnostic(
        image_path="input.png",
        cluster_json_path="clusters.json",
        threshold=50.0,
    )
    result = diagnostic.run(output_dir="./output")
    print(f"Found {result.stats.total_orphans} orphan pixels")
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional, Union
import json

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
import cv2


@dataclass
class OrphanStats:
    """Statistics about orphan pixels in an image."""
    
    total_orphans: int
    """Number of pixels that are orphans (far from all clusters)."""
    
    total_nonwhite: int
    """Total number of non-white pixels in the image."""
    
    orphan_percentage: float
    """Percentage of non-white pixels that are orphans."""
    
    region_bounds: Optional[Tuple[int, int, int, int]]
    """Bounding box of orphan region (x_min, y_min, x_max, y_max) or None if no orphans."""
    
    max_distance: float
    """Maximum distance from any orphan pixel to its nearest cluster."""
    
    mean_distance: float
    """Mean distance from orphan pixels to their nearest clusters."""


@dataclass
class DiagnosticResult:
    """Result of running orphan diagnostic."""
    
    stats: OrphanStats
    """Statistics about orphan pixels."""
    
    orphan_coords: List[Tuple[int, int]]
    """List of (y, x) coordinates of orphan pixels."""
    
    overlay_path: Optional[Path]
    """Path to overlay image if generated."""
    
    heatmap_path: Optional[Path]
    """Path to heatmap image if generated."""
    
    stats_json_path: Optional[Path]
    """Path to stats JSON file if generated."""


def compute_distance_map(
    image_shape: Tuple[int, int],
    cluster_centers: List[Tuple[int, int]],
) -> np.ndarray:
    """Compute distance from each pixel to nearest cluster center.
    
    Args:
        image_shape: (height, width) of the image.
        cluster_centers: List of (x, y) cluster center coordinates.
        
    Returns:
        2D array of distances, same shape as image.
    """
    height, width = image_shape
    
    if not cluster_centers:
        # No clusters - all pixels are infinitely far
        return np.full((height, width), np.inf, dtype=np.float32)
    
    # Build KDTree for efficient nearest-neighbor queries
    # Note: KDTree expects (y, x) order for image coordinates
    centers_array = np.array([(y, x) for x, y in cluster_centers])
    tree = cKDTree(centers_array)
    
    # Create coordinate grid
    y_coords, x_coords = np.mgrid[0:height, 0:width]
    pixel_coords = np.column_stack([y_coords.ravel(), x_coords.ravel()])
    
    # Query nearest neighbor distance for each pixel
    distances, _ = tree.query(pixel_coords, k=1)
    
    return distances.reshape((height, width)).astype(np.float32)


def find_orphan_pixels(
    image: np.ndarray,
    cluster_centers: List[Tuple[int, int]],
    threshold: float = 50.0,
    white_tolerance: int = 250,
) -> Tuple[List[Tuple[int, int]], OrphanStats]:
    """Find non-white pixels that are far from any cluster center.
    
    Args:
        image: RGB image as numpy array (H, W, 3).
        cluster_centers: List of (x, y) cluster center coordinates.
        threshold: Distance threshold - pixels farther than this are orphans.
        white_tolerance: Pixel values >= this in all channels are considered white.
        
    Returns:
        Tuple of (orphan_coords, stats):
        - orphan_coords: List of (y, x) coordinates of orphan pixels
        - stats: OrphanStats with summary statistics
    """
    height, width = image.shape[:2]
    
    # Find non-white pixels (not near pure white)
    is_white = np.all(image >= white_tolerance, axis=2)
    nonwhite_mask = ~is_white
    nonwhite_coords = np.argwhere(nonwhite_mask)  # (N, 2) array of (y, x)
    total_nonwhite = len(nonwhite_coords)
    
    if total_nonwhite == 0:
        return [], OrphanStats(
            total_orphans=0,
            total_nonwhite=0,
            orphan_percentage=0.0,
            region_bounds=None,
            max_distance=0.0,
            mean_distance=0.0,
        )
    
    # Compute distance map
    distance_map = compute_distance_map((height, width), cluster_centers)
    
    # Find orphans: non-white pixels with distance > threshold
    orphan_mask = nonwhite_mask & (distance_map > threshold)
    orphan_coords = np.argwhere(orphan_mask)  # (N, 2) array of (y, x)
    
    # Convert to list of tuples
    orphan_list = [(int(y), int(x)) for y, x in orphan_coords]
    
    # Compute stats
    total_orphans = len(orphan_list)
    
    if total_orphans == 0:
        return [], OrphanStats(
            total_orphans=0,
            total_nonwhite=total_nonwhite,
            orphan_percentage=0.0,
            region_bounds=None,
            max_distance=0.0,
            mean_distance=0.0,
        )
    
    # Compute region bounds (x_min, y_min, x_max, y_max)
    y_coords = orphan_coords[:, 0]
    x_coords = orphan_coords[:, 1]
    region_bounds = (
        int(x_coords.min()),
        int(y_coords.min()),
        int(x_coords.max()),
        int(y_coords.max()),
    )
    
    # Compute distance stats for orphans
    orphan_distances = distance_map[orphan_mask]
    max_distance = float(orphan_distances.max())
    mean_distance = float(orphan_distances.mean())
    
    stats = OrphanStats(
        total_orphans=total_orphans,
        total_nonwhite=total_nonwhite,
        orphan_percentage=100.0 * total_orphans / total_nonwhite,
        region_bounds=region_bounds,
        max_distance=max_distance,
        mean_distance=mean_distance,
    )
    
    return orphan_list, stats


def generate_overlay_image(
    original: np.ndarray,
    orphan_coords: List[Tuple[int, int]],
    orphan_color: Tuple[int, int, int] = (255, 0, 0),
) -> np.ndarray:
    """Generate overlay image with orphan pixels highlighted.
    
    Args:
        original: Original RGB image as numpy array.
        orphan_coords: List of (y, x) coordinates of orphan pixels.
        orphan_color: RGB color to use for orphan pixels (default: red).
        
    Returns:
        RGB image with orphan pixels colored.
    """
    overlay = original.copy()
    
    for y, x in orphan_coords:
        overlay[y, x] = orphan_color
    
    return overlay


def generate_heatmap(
    distance_map: np.ndarray,
    max_distance: float = 100.0,
    colormap: int = cv2.COLORMAP_JET,
) -> np.ndarray:
    """Generate heatmap showing distance from clusters.
    
    Args:
        distance_map: 2D array of distances from compute_distance_map.
        max_distance: Maximum distance for colormap scaling.
        colormap: OpenCV colormap to use.
        
    Returns:
        RGB heatmap image.
    """
    # Normalize distances to 0-255 range
    normalized = np.clip(distance_map / max_distance * 255, 0, 255).astype(np.uint8)
    
    # Apply colormap
    heatmap = cv2.applyColorMap(normalized, colormap)
    
    # Convert BGR to RGB
    return cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)


class OrphanDiagnostic:
    """Diagnostic tool for finding and visualizing orphan pixels.
    
    Orphan pixels are non-white pixels that are farther than a threshold
    distance from any detected cluster center. These represent detection
    failures that need to be addressed.
    
    Example:
        >>> diagnostic = OrphanDiagnostic(
        ...     image_path="input.png",
        ...     cluster_json_path="clusters.json",
        ...     threshold=50.0,
        ... )
        >>> result = diagnostic.run(output_dir="./output")
        >>> print(f"Found {result.stats.total_orphans} orphans")
    """
    
    def __init__(
        self,
        image_path: Union[str, Path],
        cluster_json_path: Union[str, Path],
        threshold: float = 50.0,
        white_tolerance: int = 250,
    ):
        """Initialize the diagnostic.
        
        Args:
            image_path: Path to the original image.
            cluster_json_path: Path to cluster detection JSON output.
            threshold: Distance threshold for orphan detection.
            white_tolerance: Pixel values >= this are considered white.
        """
        self.image_path = Path(image_path)
        self.cluster_json_path = Path(cluster_json_path)
        self.threshold = threshold
        self.white_tolerance = white_tolerance
        
        # Load image
        self.image = np.array(Image.open(self.image_path).convert("RGB"))
        
        # Load cluster centers from JSON
        self.cluster_centers = self._load_clusters()
    
    def _load_clusters(self) -> List[Tuple[int, int]]:
        """Load cluster centers from JSON file.
        
        Supports multiple JSON formats:
        - {"circles": [{"x": ..., "y": ...}, ...]}
        - [{"center": [x, y], ...}, ...]
        """
        with open(self.cluster_json_path) as f:
            data = json.load(f)
        
        centers = []
        
        # Handle list format: [{"center": [x, y], ...}, ...]
        if isinstance(data, list):
            for item in data:
                if "center" in item:
                    x, y = item["center"]
                    centers.append((int(x), int(y)))
                elif "x" in item and "y" in item:
                    centers.append((int(item["x"]), int(item["y"])))
        # Handle dict format: {"circles": [...]}
        elif isinstance(data, dict):
            circles = data.get("circles", [])
            for c in circles:
                if "center" in c:
                    x, y = c["center"]
                    centers.append((int(x), int(y)))
                elif "x" in c and "y" in c:
                    centers.append((int(c["x"]), int(c["y"])))
        
        return centers
    
    def run(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        generate_overlay: bool = True,
        generate_heatmap: bool = True,
    ) -> DiagnosticResult:
        """Run the diagnostic and optionally save outputs.
        
        Args:
            output_dir: Directory to save output files. If None, no files saved.
            generate_overlay: Whether to generate overlay image.
            generate_heatmap: Whether to generate distance heatmap.
            
        Returns:
            DiagnosticResult with stats, coordinates, and file paths.
        """
        # Find orphan pixels
        orphan_coords, stats = find_orphan_pixels(
            self.image,
            self.cluster_centers,
            self.threshold,
            self.white_tolerance,
        )
        
        overlay_path = None
        heatmap_path = None
        stats_json_path = None
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate and save overlay
            if generate_overlay:
                overlay = generate_overlay_image(self.image, orphan_coords)
                overlay_path = output_dir / "orphan_overlay.png"
                Image.fromarray(overlay).save(overlay_path)
            
            # Generate and save heatmap
            if generate_heatmap:
                distance_map = compute_distance_map(
                    self.image.shape[:2],
                    self.cluster_centers,
                )
                heatmap = globals()["generate_heatmap"](distance_map, self.threshold)
                heatmap_path = output_dir / "distance_heatmap.png"
                Image.fromarray(heatmap).save(heatmap_path)
            
            # Save stats JSON
            stats_dict = {
                "total_orphans": stats.total_orphans,
                "total_nonwhite": stats.total_nonwhite,
                "orphan_percentage": round(stats.orphan_percentage, 2),
                "region_bounds": stats.region_bounds,
                "max_distance": round(stats.max_distance, 2),
                "mean_distance": round(stats.mean_distance, 2),
                "threshold": self.threshold,
                "cluster_count": len(self.cluster_centers),
            }
            stats_json_path = output_dir / "orphan_stats.json"
            stats_json_path.write_text(json.dumps(stats_dict, indent=2))
        
        return DiagnosticResult(
            stats=stats,
            orphan_coords=orphan_coords,
            overlay_path=overlay_path,
            heatmap_path=heatmap_path,
            stats_json_path=stats_json_path,
        )


def main():
    """CLI entry point for orphan diagnostic."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Diagnose orphan pixels in halftone detection"
    )
    parser.add_argument("image", help="Path to original image")
    parser.add_argument("clusters", help="Path to cluster detection JSON")
    parser.add_argument("-o", "--output", default="./orphan_diagnostic",
                        help="Output directory")
    parser.add_argument("-t", "--threshold", type=float, default=50.0,
                        help="Distance threshold for orphan detection")
    parser.add_argument("-w", "--white-tolerance", type=int, default=250,
                        help="Pixel value threshold for white detection")
    
    args = parser.parse_args()
    
    diagnostic = OrphanDiagnostic(
        image_path=args.image,
        cluster_json_path=args.clusters,
        threshold=args.threshold,
        white_tolerance=args.white_tolerance,
    )
    
    result = diagnostic.run(output_dir=args.output)
    
    print(f"Orphan Pixel Diagnostic Results")
    print(f"================================")
    print(f"Total non-white pixels: {result.stats.total_nonwhite:,}")
    print(f"Orphan pixels: {result.stats.total_orphans:,}")
    print(f"Orphan percentage: {result.stats.orphan_percentage:.1f}%")
    if result.stats.region_bounds:
        x1, y1, x2, y2 = result.stats.region_bounds
        print(f"Orphan region: X={x1}-{x2}, Y={y1}-{y2}")
    print(f"Max distance: {result.stats.max_distance:.1f} px")
    print(f"Mean distance: {result.stats.mean_distance:.1f} px")
    print(f"\nOutput files saved to: {args.output}")


if __name__ == "__main__":
    main()
