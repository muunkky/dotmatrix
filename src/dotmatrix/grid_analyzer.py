"""
Grid analyzer for detecting halftone screen parameters.

Analyzes dot positions to determine:
- Grid pitch (spacing between dots)
- Screen angle for each CMYK color
- Phase offset for grid alignment
"""

import json
import math
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import numpy as np


def load_clusters(cluster_file: Path) -> List[dict]:
    """Load cluster data from JSON file."""
    with open(cluster_file) as f:
        data = json.load(f)
    return data.get("clusters", [])


def get_dominant_color(pixel_counts: Dict[str, int]) -> str:
    """Determine the dominant CMYK color for a cluster."""
    cmyk_counts = {
        "cyan": pixel_counts.get("cyan", 0),
        "magenta": pixel_counts.get("magenta", 0),
        "yellow": pixel_counts.get("yellow", 0),
        "black": pixel_counts.get("black", 0),
    }
    return max(cmyk_counts, key=cmyk_counts.get)


def group_by_color(clusters: List[dict]) -> Dict[str, List[Tuple[float, float]]]:
    """Group cluster centers by their dominant CMYK color."""
    groups = defaultdict(list)
    
    for cluster in clusters:
        center = cluster["center"]
        pixel_counts = cluster.get("pixel_counts", {})
        color = get_dominant_color(pixel_counts)
        groups[color].append((float(center[0]), float(center[1])))
    
    return dict(groups)


def find_nearest_neighbors(points: List[Tuple[float, float]], k: int = 8) -> np.ndarray:
    """Find k nearest neighbor distances for each point."""
    if len(points) < k + 1:
        k = len(points) - 1
    if k < 1:
        return np.array([])
    
    points_arr = np.array(points)
    n = len(points)
    
    # For each point, find distances to all other points
    distances = []
    for i in range(n):
        dists = np.sqrt(np.sum((points_arr - points_arr[i])**2, axis=1))
        dists = np.sort(dists)[1:k+1]  # Exclude self (distance 0)
        distances.append(dists)
    
    return np.array(distances)


def estimate_grid_pitch(points: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Estimate grid pitch from point positions.
    
    Returns (pitch, std_dev) - the average spacing and its standard deviation.
    """
    if len(points) < 10:
        return 0.0, 0.0
    
    # Find nearest neighbor distances
    nn_distances = find_nearest_neighbors(points, k=4)
    
    if nn_distances.size == 0:
        return 0.0, 0.0
    
    # The primary grid pitch is typically the smallest consistent distance
    # (nearest neighbor in cardinal directions)
    primary_distances = nn_distances[:, 0]  # Closest neighbor for each point
    
    # Use median for robustness against outliers
    pitch = np.median(primary_distances)
    std = np.std(primary_distances)
    
    return float(pitch), float(std)


def estimate_grid_angle(points: List[Tuple[float, float]], pitch: float) -> Tuple[float, float]:
    """
    Estimate grid rotation angle from point positions.
    
    Uses FFT-based approach or vector analysis to detect the dominant angle.
    
    Returns (angle_degrees, confidence).
    """
    if len(points) < 20 or pitch < 1:
        return 0.0, 0.0
    
    points_arr = np.array(points)
    n = len(points)
    
    # Find vectors to nearest neighbors within pitch range
    angles = []
    tolerance = pitch * 0.3  # Allow 30% tolerance
    
    for i in range(min(n, 1000)):  # Sample for efficiency
        dists = np.sqrt(np.sum((points_arr - points_arr[i])**2, axis=1))
        
        # Find neighbors at approximately grid pitch distance
        mask = (dists > pitch * 0.7) & (dists < pitch * 1.3)
        neighbor_indices = np.where(mask)[0]
        
        for j in neighbor_indices:
            dx = points_arr[j, 0] - points_arr[i, 0]
            dy = points_arr[j, 1] - points_arr[i, 1]
            angle = math.degrees(math.atan2(dy, dx))
            # Normalize to 0-90 range (grid symmetry)
            angle = angle % 90
            angles.append(angle)
    
    if not angles:
        return 0.0, 0.0
    
    angles = np.array(angles)
    
    # Use histogram to find dominant angle
    hist, bins = np.histogram(angles, bins=90, range=(0, 90))
    peak_idx = np.argmax(hist)
    dominant_angle = (bins[peak_idx] + bins[peak_idx + 1]) / 2
    
    # Confidence based on how peaked the histogram is
    confidence = hist[peak_idx] / len(angles) * 4  # Scale factor
    confidence = min(1.0, confidence)
    
    return float(dominant_angle), float(confidence)


def analyze_grid(cluster_file: Path, sample_size: Optional[int] = None) -> Dict:
    """
    Analyze halftone grid parameters from cluster data.
    
    Args:
        cluster_file: Path to cluster JSON file
        sample_size: Optional limit on clusters to analyze (for speed)
    
    Returns:
        Dictionary with grid parameters for each CMYK color.
    """
    clusters = load_clusters(cluster_file)
    
    if sample_size and len(clusters) > sample_size:
        # Random sample for efficiency
        import random
        clusters = random.sample(clusters, sample_size)
    
    color_groups = group_by_color(clusters)
    
    results = {
        "total_clusters": len(clusters),
        "colors": {}
    }
    
    for color, points in color_groups.items():
        pitch, pitch_std = estimate_grid_pitch(points)
        angle, angle_confidence = estimate_grid_angle(points, pitch)
        
        results["colors"][color] = {
            "count": len(points),
            "grid_pitch": round(pitch, 2),
            "pitch_std_dev": round(pitch_std, 2),
            "angle_degrees": round(angle, 2),
            "angle_confidence": round(angle_confidence, 3),
        }
    
    return results


def generate_grid_overlay_svg(
    width: int,
    height: int,
    grid_params: Dict,
    output_path: Path,
    grid_colors: Optional[Dict[str, str]] = None
) -> None:
    """
    Generate an SVG with overlaid grids for each CMYK color.
    
    Args:
        width: Image width
        height: Image height
        grid_params: Dictionary with grid parameters per color
        output_path: Output SVG file path
        grid_colors: Optional color mapping for grid lines
    """
    if grid_colors is None:
        grid_colors = {
            "cyan": "#00FFFF",
            "magenta": "#FF00FF", 
            "yellow": "#FFFF00",
            "black": "#000000"
        }
    
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white" opacity="0"/>',
    ]
    
    # Calculate diagonal to ensure grid covers rotated area
    diagonal = math.sqrt(width**2 + height**2)
    
    for color, params in grid_params.get("colors", {}).items():
        pitch = params.get("grid_pitch", 100)
        angle = params.get("angle_degrees", 0)
        
        if pitch < 1:
            continue
        
        stroke_color = grid_colors.get(color, "#888888")
        
        # Create a group with rotation transform
        cx, cy = width / 2, height / 2
        
        svg_parts.append(f'<g id="grid-{color}" transform="rotate({angle} {cx} {cy})" opacity="0.5">')
        
        # Draw grid lines
        num_lines = int(diagonal / pitch) + 2
        start_offset = -diagonal / 2
        
        # Vertical lines (will be rotated)
        for i in range(-num_lines, num_lines + 1):
            x = cx + i * pitch
            svg_parts.append(
                f'<line x1="{x}" y1="{cy - diagonal/2}" x2="{x}" y2="{cy + diagonal/2}" '
                f'stroke="{stroke_color}" stroke-width="1"/>'
            )
        
        # Horizontal lines (will be rotated)
        for i in range(-num_lines, num_lines + 1):
            y = cy + i * pitch
            svg_parts.append(
                f'<line x1="{cx - diagonal/2}" y1="{y}" x2="{cx + diagonal/2}" y2="{y}" '
                f'stroke="{stroke_color}" stroke-width="1"/>'
            )
        
        svg_parts.append('</g>')
    
    svg_parts.append('</svg>')
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(svg_parts))


def main():
    """CLI for grid analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze halftone grid parameters")
    parser.add_argument("cluster_file", type=Path, help="Path to cluster JSON file")
    parser.add_argument("--sample", type=int, default=5000, help="Sample size for analysis")
    parser.add_argument("--output-svg", type=Path, help="Output SVG overlay file")
    parser.add_argument("--width", type=int, default=6496, help="Image width for SVG")
    parser.add_argument("--height", type=int, default=5984, help="Image height for SVG")
    
    args = parser.parse_args()
    
    print(f"Analyzing grid parameters from: {args.cluster_file}")
    results = analyze_grid(args.cluster_file, sample_size=args.sample)
    
    print(f"\nTotal clusters analyzed: {results['total_clusters']}")
    print("\nGrid Parameters by Color:")
    print("-" * 60)
    
    for color, params in results["colors"].items():
        print(f"\n{color.upper()}:")
        print(f"  Dot count:     {params['count']}")
        print(f"  Grid pitch:    {params['grid_pitch']:.1f} px (±{params['pitch_std_dev']:.1f})")
        print(f"  Screen angle:  {params['angle_degrees']:.1f}° (confidence: {params['angle_confidence']:.1%})")
    
    if args.output_svg:
        print(f"\nGenerating grid overlay SVG: {args.output_svg}")
        generate_grid_overlay_svg(args.width, args.height, results, args.output_svg)
        print("Done!")
    
    return results


if __name__ == "__main__":
    main()
