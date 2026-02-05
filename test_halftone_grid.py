"""
Test script for halftone grid generation.

Analyzes a PORTION of the source halftone image to detect grid parameters,
then applies them to generate a full reconstruction.
"""

import cv2
import numpy as np
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotmatrix.halftone_grid import (
    create_halftone_from_image_memory_efficient,
    separate_cmyk_inks_memory_efficient,
    estimate_grid_spacing_from_image,
    HALFTONE_ANGLES,
)


def analyze_crop(image: np.ndarray, crop_size: int = 500) -> dict:
    """Analyze a small crop to detect grid parameters."""
    h, w = image.shape[:2]
    
    # Take a crop from the center (more likely to have good ink coverage)
    cx, cy = w // 2, h // 2
    half = crop_size // 2
    crop = image[cy - half:cy + half, cx - half:cx + half]
    
    print(f"Analyzing {crop_size}x{crop_size} crop from center...")
    
    # Get ink masks
    ink_masks = separate_cmyk_inks_memory_efficient(crop)
    
    results = {'crop_size': crop_size}
    
    for color, mask in ink_masks.items():
        ink_pixels = np.sum(mask > 0)
        coverage = ink_pixels / mask.size
        
        spacing = None
        if ink_pixels > 100:
            try:
                spacing = estimate_grid_spacing_from_image(mask)
            except Exception as e:
                print(f"  {color}: spacing detection failed: {e}")
        
        results[color] = {
            'coverage': coverage,
            'estimated_spacing': spacing,
        }
        
        print(f"  {color}: coverage={coverage:.1%}, spacing={spacing:.1f}px" if spacing else f"  {color}: coverage={coverage:.1%}")
    
    # Average spacing across colors that have detectable patterns
    spacings = [r['estimated_spacing'] for r in results.values() if isinstance(r, dict) and r.get('estimated_spacing')]
    if spacings:
        results['avg_spacing'] = np.mean(spacings)
        print(f"\n  Average detected spacing: {results['avg_spacing']:.1f}px")
    
    return results


def main():
    # Load the large halftone image
    input_path = Path("inputs/input_large.png")
    
    if not input_path.exists():
        for alt in [
            "output/centroid_large/flower_svg_jitter_p30_seed1_20260204_203038/input_input_large.png",
            "tests/data/multicolor_test.png",
        ]:
            input_path = Path(alt)
            if input_path.exists():
                break
        else:
            print("Error: No test image found")
            return
    
    print(f"Loading: {input_path}")
    image = cv2.imread(str(input_path))
    
    if image is None:
        print("Failed to load image")
        return
    
    height, width = image.shape[:2]
    print(f"Image size: {width} x {height} ({width * height / 1e6:.1f} MP)")
    
    # Step 1: Analyze a small crop to detect grid parameters
    print("\n=== Step 1: Detect grid parameters from crop ===")
    analysis = analyze_crop(image, crop_size=800)
    
    # Use detected spacing or fallback
    detected_spacing = analysis.get('avg_spacing', 20)
    print(f"\nUsing grid spacing: {detected_spacing:.1f}px")
    
    # Step 2: Generate halftone for the full image with detected parameters
    print(f"\n=== Step 2: Generate halftone for full image ===")
    print(f"Standard angles: C={HALFTONE_ANGLES['cyan']}°, M={HALFTONE_ANGLES['magenta']}°, Y={HALFTONE_ANGLES['yellow']}°, K={HALFTONE_ANGLES['black']}°")
    
    output_dir = Path("output/halftone_grid_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test with detected spacing and a couple nearby values
    test_spacings = [
        int(detected_spacing - 2),
        int(detected_spacing),
        int(detected_spacing + 2),
    ]
    
    for spacing in test_spacings:
        if spacing < 5:
            continue
        print(f"\n--- Generating with spacing = {spacing}px ---")
        
        grids, svg = create_halftone_from_image_memory_efficient(
            image,
            grid_spacing=spacing,
            angles=HALFTONE_ANGLES
        )
        
        output_path = output_dir / f"halftone_spacing_{spacing}.svg"
        with open(output_path, 'w') as f:
            f.write(svg)
        
        total_dots = sum(g.dot_count for g in grids.values())
        print(f"  Total dots: {total_dots:,}")
        print(f"  Saved: {output_path} ({len(svg):,} bytes)")
    
    print(f"\n=== Done! ===")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
