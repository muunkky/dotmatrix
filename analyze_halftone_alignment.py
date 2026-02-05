"""
Halftone Grid Alignment Tool

Analyzes a halftone image to detect the grid spacing and optimal origin alignment
so that generated grids align perfectly with the dots in the source image.

The approach:
1. Detect actual dot centers in the source image (using existing circle detection)
2. For each color, find the grid parameters that best fit the detected dots
3. Output optimal spacing and origin offsets for each color
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import math
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotmatrix.halftone_grid import (
    HALFTONE_ANGLES,
    generate_rotated_grid,
    separate_cmyk_inks_memory_efficient,
)


@dataclass
class GridAlignment:
    """Optimal grid alignment for one color channel."""
    color: str
    angle: float
    spacing: float
    origin_x: float
    origin_y: float
    fit_error: float  # Average distance from grid to nearest detected dot


def detect_blob_centers(
    ink_mask: np.ndarray,
    min_area: int = 10,
    max_area: int = 10000,
) -> List[Tuple[float, float]]:
    """Detect centers of ink blobs in a binary mask.
    
    Args:
        ink_mask: Binary mask (255=ink, 0=absent)
        min_area: Minimum blob area in pixels
        max_area: Maximum blob area in pixels
        
    Returns:
        List of (x, y) centers for detected blobs
    """
    # Find contours
    contours, _ = cv2.findContours(
        ink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    centers = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if min_area <= area <= max_area:
            # Get centroid
            M = cv2.moments(contour)
            if M["m00"] > 0:
                cx = M["m10"] / M["m00"]
                cy = M["m01"] / M["m00"]
                centers.append((cx, cy))
    
    return centers


def estimate_spacing_from_centers(
    centers: List[Tuple[float, float]],
    min_spacing: float = 5.0,
    max_spacing: float = 50.0,
) -> float:
    """Estimate grid spacing from detected dot centers.
    
    Uses nearest-neighbor distances to estimate the typical spacing.
    
    Args:
        centers: List of (x, y) dot centers
        min_spacing: Minimum expected spacing
        max_spacing: Maximum expected spacing
        
    Returns:
        Estimated grid spacing
    """
    if len(centers) < 2:
        return 20.0  # Default fallback
    
    centers_arr = np.array(centers)
    
    # Find nearest neighbor distances for each point
    nn_distances = []
    for i, c in enumerate(centers_arr):
        # Calculate distances to all other points
        diffs = centers_arr - c
        dists = np.sqrt(np.sum(diffs**2, axis=1))
        dists[i] = np.inf  # Exclude self
        nn_dist = np.min(dists)
        if min_spacing <= nn_dist <= max_spacing:
            nn_distances.append(nn_dist)
    
    if not nn_distances:
        return 20.0
    
    # Use median as robust estimate
    return np.median(nn_distances)


def find_best_origin_offset(
    centers: List[Tuple[float, float]],
    image_size: Tuple[int, int],
    spacing: float,
    angle: float,
    search_range: float = None,
    search_steps: int = 20,
) -> Tuple[float, float, float]:
    """Find the origin offset that best aligns grid to detected centers.
    
    Args:
        centers: List of (x, y) detected dot centers
        image_size: (width, height) of image
        spacing: Grid spacing to use
        angle: Grid rotation angle in degrees
        search_range: Range to search for offset (defaults to spacing)
        search_steps: Number of steps in each dimension
        
    Returns:
        Tuple of (best_ox, best_oy, fit_error)
    """
    if not centers:
        return 0.0, 0.0, float('inf')
    
    if search_range is None:
        search_range = spacing
    
    width, height = image_size
    centers_arr = np.array(centers)
    
    best_ox, best_oy = 0.0, 0.0
    best_error = float('inf')
    
    # Search over origin offsets
    step = search_range / search_steps
    
    for ox_idx in range(search_steps):
        ox = -search_range/2 + ox_idx * step
        for oy_idx in range(search_steps):
            oy = -search_range/2 + oy_idx * step
            
            # Generate grid with this offset
            grid_points = generate_rotated_grid(
                width, height, spacing, angle, ox, oy
            )
            
            if not grid_points:
                continue
            
            grid_arr = np.array(grid_points)
            
            # Calculate average distance from each center to nearest grid point
            total_error = 0.0
            for cx, cy in centers:
                diffs = grid_arr - np.array([cx, cy])
                dists = np.sqrt(np.sum(diffs**2, axis=1))
                total_error += np.min(dists)
            
            avg_error = total_error / len(centers)
            
            if avg_error < best_error:
                best_error = avg_error
                best_ox, best_oy = ox, oy
    
    return best_ox, best_oy, best_error


def analyze_halftone_alignment(
    image: np.ndarray,
    min_spacing: float = 5.0,
    max_spacing: float = 50.0,
    verbose: bool = True,
) -> Dict[str, GridAlignment]:
    """Analyze a halftone image and find optimal grid alignment for each color.
    
    Args:
        image: BGR image as numpy array
        min_spacing: Minimum expected dot spacing
        max_spacing: Maximum expected dot spacing
        verbose: Print progress information
        
    Returns:
        Dict mapping color names to GridAlignment objects
    """
    height, width = image.shape[:2]
    
    if verbose:
        print(f"Image size: {width} x {height}")
        print("Separating CMYK inks...")
    
    ink_masks = separate_cmyk_inks_memory_efficient(image)
    
    alignments = {}
    
    for color, angle in HALFTONE_ANGLES.items():
        if verbose:
            print(f"\n--- Analyzing {color.upper()} (angle={angle}°) ---")
        
        mask = ink_masks[color]
        ink_pixels = np.sum(mask > 0)
        
        if ink_pixels < 100:
            if verbose:
                print(f"  Skipping: too few ink pixels ({ink_pixels})")
            continue
        
        # Detect blob centers
        centers = detect_blob_centers(mask)
        
        if verbose:
            print(f"  Detected {len(centers)} dot centers")
        
        if len(centers) < 10:
            if verbose:
                print(f"  Skipping: too few dots detected")
            continue
        
        # Estimate spacing
        spacing = estimate_spacing_from_centers(centers, min_spacing, max_spacing)
        if verbose:
            print(f"  Estimated spacing: {spacing:.1f} px")
        
        # Find best origin offset
        ox, oy, error = find_best_origin_offset(
            centers, (width, height), spacing, angle
        )
        
        if verbose:
            print(f"  Best origin offset: ({ox:.1f}, {oy:.1f})")
            print(f"  Fit error: {error:.2f} px (avg distance to nearest grid point)")
        
        alignments[color] = GridAlignment(
            color=color,
            angle=angle,
            spacing=spacing,
            origin_x=ox,
            origin_y=oy,
            fit_error=error,
        )
    
    return alignments


def main():
    # Load the halftone image
    input_path = Path("output/centroid_large/flower_svg_jitter_p30_seed1_20260204_203038/input_input_large.png")
    
    if not input_path.exists():
        input_path = Path("inputs/input_large.png")
    
    if not input_path.exists():
        # Use small test image for faster testing
        input_path = Path("tests/data/multicolor_test.png")
    
    print(f"Loading: {input_path}")
    image = cv2.imread(str(input_path))
    
    if image is None:
        print("Failed to load image")
        return
    
    # Analyze halftone alignment
    print("\n=== Analyzing Halftone Grid Alignment ===\n")
    alignments = analyze_halftone_alignment(image, verbose=True)
    
    # Summary
    print("\n=== Optimal Grid Parameters ===")
    print(f"{'Color':<10} {'Angle':>8} {'Spacing':>10} {'Origin X':>10} {'Origin Y':>10} {'Error':>8}")
    print("-" * 60)
    
    for color in ['cyan', 'magenta', 'yellow', 'black']:
        if color in alignments:
            a = alignments[color]
            print(f"{color:<10} {a.angle:>8.1f}° {a.spacing:>10.1f} {a.origin_x:>10.1f} {a.origin_y:>10.1f} {a.fit_error:>8.2f}")
    
    # Generate aligned SVG
    print("\n=== Generating Aligned Halftone SVG ===")
    
    from dotmatrix.halftone_grid import (
        generate_halftone_grids,
        size_dots_from_masks,
        render_halftone_svg,
    )
    
    height, width = image.shape[:2]
    ink_masks = separate_cmyk_inks_memory_efficient(image)
    
    # Use detected parameters
    if alignments:
        # Use average spacing across colors
        spacings = [a.spacing for a in alignments.values()]
        avg_spacing = np.mean(spacings)
        print(f"Using average spacing: {avg_spacing:.1f} px")
        
        # Generate grids with per-color origin offsets
        origin_offsets = {
            color: (a.origin_x, a.origin_y) 
            for color, a in alignments.items()
        }
        
        grid_points = generate_halftone_grids(
            width, height, avg_spacing,
            origin_offsets=origin_offsets
        )
        
        grids = size_dots_from_masks(
            grid_points, ink_masks, avg_spacing / 2,
            sample_radius=avg_spacing / 2
        )
        
        svg = render_halftone_svg(grids, width, height)
        
        output_dir = Path("output/halftone_grid_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "halftone_aligned.svg"
        
        with open(output_path, 'w') as f:
            f.write(svg)
        
        print(f"Saved aligned SVG: {output_path} ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
