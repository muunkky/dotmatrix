#!/usr/bin/env python3
"""
Orphan Pixel Diagnostic Tool

Analyzes the INPUT image to find pixels that belong to halftone dots
but were not captured by any detected cluster center.

IMPORTANT CONCEPTUAL MODEL:
- INPUT image: Contains original halftone dots (what we're trying to detect)
- Cluster centers: The detected positions of halftone dots
- Orphan pixels: INPUT pixels that are part of dots we MISSED detecting

This is NOT about comparing input to output pixel counts (they differ by design).
This is about finding regions in the INPUT where detection failed.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def load_cluster_centers(json_path: Path) -> np.ndarray:
    """Load cluster centers from detection JSON output.
    
    Handles multiple JSON formats:
    - List of dicts with 'center_x', 'center_y' keys
    - Dict with 'clusters' key containing list
    """
    with open(json_path) as f:
        data = json.load(f)
    
    # Handle different formats
    if isinstance(data, list):
        clusters = data
    elif isinstance(data, dict) and 'clusters' in data:
        clusters = data['clusters']
    else:
        raise ValueError(f"Unknown JSON format: {type(data)}")
    
    if not clusters:
        return np.array([]).reshape(0, 2)
    
    # Extract centers - handle different key names
    centers = []
    for c in clusters:
        if 'center_x' in c and 'center_y' in c:
            centers.append([c['center_x'], c['center_y']])
        elif 'center' in c:
            # center is [x, y] tuple/list
            centers.append([c['center'][0], c['center'][1]])
        elif 'x' in c and 'y' in c:
            centers.append([c['x'], c['y']])
        else:
            raise ValueError(f"Cannot find center coordinates in: {c.keys()}")
    
    return np.array(centers)


def find_input_foreground_pixels(image_path: Path, color: str = 'black') -> np.ndarray:
    """Find foreground (non-background) pixels in the INPUT image.
    
    For halftone detection, we care about the dots themselves.
    Default is black pixels (K channel in CMYK).
    
    Returns:
        Boolean mask where True = foreground pixel
    """
    img = np.array(Image.open(image_path).convert('RGB'))
    
    if color == 'black':
        # Black pixels: all channels are 0
        mask = np.all(img == [0, 0, 0], axis=2)
    elif color == 'non-white':
        # Any non-white pixel
        mask = ~np.all(img == [255, 255, 255], axis=2)
    else:
        raise ValueError(f"Unknown color mode: {color}")
    
    return mask


def compute_orphan_pixels(
    foreground_mask: np.ndarray,
    centers: np.ndarray,
    distance_threshold: float = 50.0
) -> tuple[np.ndarray, dict]:
    """Find foreground pixels that are far from any detected cluster center.
    
    Args:
        foreground_mask: Boolean mask of input foreground pixels
        centers: Array of (x, y) cluster center coordinates
        distance_threshold: Max distance (px) to be considered "covered"
    
    Returns:
        orphan_mask: Boolean mask of orphan pixels
        stats: Dictionary with statistics
    """
    if len(centers) == 0:
        # No clusters detected - all foreground is orphan
        return foreground_mask.copy(), {
            'total_foreground': int(foreground_mask.sum()),
            'orphan_count': int(foreground_mask.sum()),
            'orphan_percent': 100.0,
            'cluster_count': 0
        }
    
    # Get coordinates of all foreground pixels
    fg_coords = np.argwhere(foreground_mask)  # (row, col) = (y, x)
    
    if len(fg_coords) == 0:
        return np.zeros_like(foreground_mask, dtype=bool), {
            'total_foreground': 0,
            'orphan_count': 0,
            'orphan_percent': 0.0,
            'cluster_count': len(centers)
        }
    
    # Create distance map from cluster centers
    # Use scipy.ndimage for efficiency with large images
    center_mask = np.zeros(foreground_mask.shape, dtype=bool)
    for cx, cy in centers:
        # Bounds check
        ix, iy = int(round(cx)), int(round(cy))
        if 0 <= iy < foreground_mask.shape[0] and 0 <= ix < foreground_mask.shape[1]:
            center_mask[iy, ix] = True
    
    # Distance transform from center points
    distance_map = ndimage.distance_transform_edt(~center_mask)
    
    # Orphan = foreground AND far from any center
    orphan_mask = foreground_mask & (distance_map > distance_threshold)
    
    orphan_count = int(orphan_mask.sum())
    total_fg = int(foreground_mask.sum())
    
    # Find bounding box of orphans
    if orphan_count > 0:
        orphan_coords = np.argwhere(orphan_mask)
        y_min, x_min = orphan_coords.min(axis=0)
        y_max, x_max = orphan_coords.max(axis=0)
        bbox = {'x_min': int(x_min), 'x_max': int(x_max), 
                'y_min': int(y_min), 'y_max': int(y_max)}
    else:
        bbox = None
    
    return orphan_mask, {
        'total_foreground': total_fg,
        'orphan_count': orphan_count,
        'orphan_percent': 100.0 * orphan_count / total_fg if total_fg > 0 else 0.0,
        'cluster_count': len(centers),
        'distance_threshold': distance_threshold,
        'orphan_bbox': bbox
    }


def find_orphan_clusters(orphan_mask: np.ndarray, min_size: int = 5) -> list[dict]:
    """Find connected regions of orphan pixels (missed halftone dots).
    
    These represent individual dots that should have been detected.
    """
    labeled, num_features = ndimage.label(orphan_mask)
    
    clusters = []
    for i in range(1, num_features + 1):
        region = labeled == i
        size = int(region.sum())
        
        if size >= min_size:
            coords = np.argwhere(region)
            y_coords, x_coords = coords[:, 0], coords[:, 1]
            
            clusters.append({
                'id': i,
                'size': size,
                'centroid': (float(x_coords.mean()), float(y_coords.mean())),
                'bbox': {
                    'x_min': int(x_coords.min()),
                    'x_max': int(x_coords.max()),
                    'y_min': int(y_coords.min()),
                    'y_max': int(y_coords.max())
                }
            })
    
    # Sort by size descending
    clusters.sort(key=lambda c: c['size'], reverse=True)
    return clusters


def main():
    parser = argparse.ArgumentParser(
        description='Find orphan pixels in INPUT image not covered by detected clusters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CONCEPTUAL MODEL:
  This tool analyzes the INPUT image to find halftone dots that were
  NOT detected by the clustering algorithm. These are "orphan" pixels -
  part of the original artwork that will be missing from the output.

EXAMPLE:
  python diagnose_orphans.py inputs/input_large.png results/clusters.json
  
  This checks which black pixels in input_large.png are more than 50px
  away from any detected cluster center in clusters.json.
"""
    )
    parser.add_argument('input_image', type=Path, help='INPUT image to analyze')
    parser.add_argument('clusters_json', type=Path, help='Detection results JSON')
    parser.add_argument('--threshold', type=float, default=50.0,
                        help='Distance threshold for orphan detection (default: 50px)')
    parser.add_argument('--color', choices=['black', 'non-white'], default='black',
                        help='Which pixels to consider foreground (default: black)')
    parser.add_argument('--output', type=Path, help='Save orphan mask as image')
    parser.add_argument('--json', type=Path, help='Save full results as JSON')
    parser.add_argument('--top-orphans', type=int, default=10,
                        help='Show top N orphan clusters (default: 10)')
    
    args = parser.parse_args()
    
    print(f"=== Orphan Pixel Diagnostic ===")
    print(f"Input image: {args.input_image}")
    print(f"Clusters JSON: {args.clusters_json}")
    print(f"Distance threshold: {args.threshold}px")
    print(f"Foreground color: {args.color}")
    print()
    
    # Load data
    print("Loading cluster centers...")
    centers = load_cluster_centers(args.clusters_json)
    print(f"  Loaded {len(centers)} cluster centers")
    
    print("Loading input image...")
    foreground = find_input_foreground_pixels(args.input_image, args.color)
    print(f"  Found {foreground.sum():,} {args.color} pixels")
    print()
    
    # Compute orphans
    print("Computing orphan pixels...")
    orphan_mask, stats = compute_orphan_pixels(foreground, centers, args.threshold)
    
    print()
    print("=== RESULTS ===")
    print(f"Total {args.color} pixels in INPUT: {stats['total_foreground']:,}")
    print(f"Detected clusters: {stats['cluster_count']:,}")
    print(f"Orphan pixels: {stats['orphan_count']:,} ({stats['orphan_percent']:.2f}%)")
    
    if stats.get('orphan_bbox'):
        bbox = stats['orphan_bbox']
        print(f"Orphan region: X={bbox['x_min']}-{bbox['x_max']}, Y={bbox['y_min']}-{bbox['y_max']}")
    
    # Find orphan clusters (missed dots)
    if stats['orphan_count'] > 0:
        print()
        print(f"Finding missed halftone dots (orphan clusters)...")
        orphan_clusters = find_orphan_clusters(orphan_mask)
        print(f"Found {len(orphan_clusters)} orphan clusters (missed dots)")
        
        if orphan_clusters and args.top_orphans > 0:
            print()
            print(f"Top {min(args.top_orphans, len(orphan_clusters))} largest missed dots:")
            for c in orphan_clusters[:args.top_orphans]:
                bbox = c['bbox']
                print(f"  #{c['id']}: {c['size']} pixels at ({c['centroid'][0]:.0f}, {c['centroid'][1]:.0f})")
    else:
        orphan_clusters = []
    
    # Save outputs
    if args.output:
        print()
        print(f"Saving orphan mask to {args.output}...")
        Image.fromarray((orphan_mask * 255).astype(np.uint8)).save(args.output)
    
    if args.json:
        print(f"Saving results to {args.json}...")
        results = {
            'input_image': str(args.input_image),
            'clusters_json': str(args.clusters_json),
            'stats': stats,
            'orphan_clusters': orphan_clusters[:100]  # Limit size
        }
        with open(args.json, 'w') as f:
            json.dump(results, f, indent=2)
    
    # Return exit code based on orphan threshold
    if stats['orphan_percent'] > 5.0:
        print()
        print(f"⚠️  WARNING: {stats['orphan_percent']:.1f}% orphan rate exceeds 5% threshold")
        return 1
    else:
        print()
        print(f"✅ Orphan rate {stats['orphan_percent']:.1f}% is acceptable")
        return 0


if __name__ == '__main__':
    sys.exit(main())
