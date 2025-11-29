#!/usr/bin/env python3
"""Compare source and reconstituted images by color pixel counts.

Usage:
    python scripts/compare_run.py <run_directory>
    python scripts/compare_run.py output/run_20251129_142642

This script:
1. Finds input_*.png (source) and reconstituted.png in the run directory
2. Counts pixels for 8 colors: white, black, cyan, magenta, yellow, red, green, blue
3. Displays a comparison table with difference vector
4. Computes R² (coefficient of determination) as accuracy metric
"""

import sys
from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np

try:
    import cv2
except ImportError:
    print("Error: OpenCV (cv2) is required. Install with: pip install opencv-python")
    sys.exit(1)


# BGR color ranges for pixel classification
# Using tolerance ranges to handle anti-aliasing and compression artifacts
COLOR_RANGES: Dict[str, Tuple[np.ndarray, np.ndarray]] = {
    'white':   (np.array([250, 250, 250]), np.array([255, 255, 255])),
    'black':   (np.array([0, 0, 0]),       np.array([5, 5, 5])),
    'cyan':    (np.array([250, 250, 0]),   np.array([255, 255, 10])),     # BGR: high B, high G, low R
    'magenta': (np.array([250, 0, 250]),   np.array([255, 10, 255])),     # BGR: high B, low G, high R
    'yellow':  (np.array([0, 250, 250]),   np.array([10, 255, 255])),     # BGR: low B, high G, high R
    'red':     (np.array([0, 0, 250]),     np.array([10, 10, 255])),      # BGR: low B, low G, high R
    'green':   (np.array([0, 250, 0]),     np.array([10, 255, 10])),      # BGR: low B, high G, low R
    'blue':    (np.array([250, 0, 0]),     np.array([255, 10, 10])),      # BGR: high B, low G, low R
}

# Display order for consistency
COLOR_ORDER = ['white', 'black', 'cyan', 'magenta', 'yellow', 'red', 'green', 'blue']


def find_images(run_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """Find input and reconstituted images in run directory.

    Args:
        run_dir: Path to the run directory

    Returns:
        Tuple of (input_image_path, reconstituted_image_path)
        Either can be None if not found
    """
    # Find input image (input_*.png pattern)
    input_images = list(run_dir.glob("input_*.png"))
    input_path = input_images[0] if input_images else None

    # Find reconstituted image
    recon_path = run_dir / "reconstituted.png"
    if not recon_path.exists():
        recon_path = None

    return input_path, recon_path


def count_colors(image: np.ndarray) -> Dict[str, int]:
    """Count pixels matching each color range.

    Args:
        image: BGR numpy array from cv2.imread

    Returns:
        Dict mapping color name to pixel count
    """
    counts = {}

    for color_name, (lower, upper) in COLOR_RANGES.items():
        # Create mask for pixels in range
        mask = cv2.inRange(image, lower, upper)
        # Count non-zero pixels
        counts[color_name] = int(np.count_nonzero(mask))

    return counts


def calculate_r_squared(source_counts: Dict[str, int], recon_counts: Dict[str, int]) -> float:
    """Calculate R² (coefficient of determination) between source and reconstituted.

    R² = 1 - (SS_res / SS_tot)
    where SS_res = sum of squared residuals
          SS_tot = total sum of squares

    Args:
        source_counts: Color counts from source image
        recon_counts: Color counts from reconstituted image

    Returns:
        R² value (1.0 = perfect match, lower = worse)
    """
    # Convert to arrays (excluding white for comparison since it's background)
    colors_to_compare = [c for c in COLOR_ORDER if c != 'white']

    source_vals = np.array([source_counts[c] for c in colors_to_compare], dtype=float)
    recon_vals = np.array([recon_counts[c] for c in colors_to_compare], dtype=float)

    # Calculate mean of source values
    mean_source = np.mean(source_vals)

    # Sum of squared residuals
    ss_res = np.sum((source_vals - recon_vals) ** 2)

    # Total sum of squares
    ss_tot = np.sum((source_vals - mean_source) ** 2)

    # Avoid division by zero
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0

    return 1.0 - (ss_res / ss_tot)


def format_number(n: int) -> str:
    """Format number with thousands separators."""
    return f"{n:,}"


def format_diff(diff: int) -> str:
    """Format difference with sign and color hint."""
    if diff > 0:
        return f"+{diff:,}"
    elif diff < 0:
        return f"{diff:,}"
    else:
        return "0"


def print_comparison(
    source_counts: Dict[str, int],
    recon_counts: Dict[str, int],
    source_path: Path,
    recon_path: Path
) -> None:
    """Print formatted comparison table and metrics."""

    print("\n" + "=" * 70)
    print("COLOR PIXEL COMPARISON")
    print("=" * 70)
    print(f"Source:        {source_path.name}")
    print(f"Reconstituted: {recon_path.name}")
    print("-" * 70)

    # Header
    print(f"{'Color':<12} {'Source':>14} {'Recon':>14} {'Diff':>14} {'% Err':>10}")
    print("-" * 70)

    # Calculate differences
    diffs = {}
    for color in COLOR_ORDER:
        source = source_counts[color]
        recon = recon_counts[color]
        diff = recon - source
        diffs[color] = diff

        # Calculate percentage error (avoid div by zero)
        if source > 0:
            pct_err = (diff / source) * 100
            pct_str = f"{pct_err:+.1f}%"
        else:
            pct_str = "N/A" if recon == 0 else "+inf"

        print(f"{color:<12} {format_number(source):>14} {format_number(recon):>14} {format_diff(diff):>14} {pct_str:>10}")

    print("-" * 70)

    # Totals
    total_source = sum(source_counts.values())
    total_recon = sum(recon_counts.values())
    print(f"{'TOTAL':<12} {format_number(total_source):>14} {format_number(total_recon):>14}")

    # R² calculation
    r_squared = calculate_r_squared(source_counts, recon_counts)

    print("\n" + "=" * 70)
    print("METRICS")
    print("=" * 70)
    print(f"R² (excluding white): {r_squared:.6f}")
    print(f"Interpretation: ", end="")
    if r_squared >= 0.99:
        print("Excellent match")
    elif r_squared >= 0.95:
        print("Good match")
    elif r_squared >= 0.90:
        print("Moderate match")
    elif r_squared >= 0.80:
        print("Poor match")
    else:
        print("Very poor match")

    # Sum of absolute differences (excluding white)
    colors_no_white = [c for c in COLOR_ORDER if c != 'white']
    total_abs_diff = sum(abs(diffs[c]) for c in colors_no_white)
    print(f"Sum of |diff| (no white): {format_number(total_abs_diff)}")

    print("=" * 70 + "\n")


def normalize_path(path_str: str) -> Path:
    """Normalize path for cross-platform compatibility (Windows/WSL)."""
    path_str = path_str.strip()

    # Handle Windows paths in WSL
    if path_str.startswith("C:") or path_str.startswith("c:"):
        # Convert C:\path to /mnt/c/path
        drive = path_str[0].lower()
        rest = path_str[2:].replace("\\", "/")
        path_str = f"/mnt/{drive}{rest}"

    return Path(path_str)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare source and reconstituted images by color pixel counts."
    )
    parser.add_argument("run_dir", help="Path to run directory")
    parser.add_argument(
        "--margin", "-m", type=int, default=0,
        help="Exclude border margin (pixels) from comparison. Use to ignore edge clusters."
    )
    args = parser.parse_args()

    run_dir = normalize_path(args.run_dir)
    margin = args.margin

    # Validate run directory
    if not run_dir.exists():
        print(f"Error: Run directory not found: {run_dir}")
        sys.exit(1)

    if not run_dir.is_dir():
        print(f"Error: Not a directory: {run_dir}")
        sys.exit(1)

    # Find images
    input_path, recon_path = find_images(run_dir)

    if input_path is None:
        print(f"Error: No input_*.png found in {run_dir}")
        sys.exit(1)

    if recon_path is None:
        print(f"Error: No reconstituted.png found in {run_dir}")
        sys.exit(1)

    # Load images
    source_img = cv2.imread(str(input_path))
    recon_img = cv2.imread(str(recon_path))

    if source_img is None:
        print(f"Error: Failed to load source image: {input_path}")
        sys.exit(1)

    if recon_img is None:
        print(f"Error: Failed to load reconstituted image: {recon_path}")
        sys.exit(1)

    # Sanity check: same dimensions
    if source_img.shape != recon_img.shape:
        print(f"Warning: Image dimensions differ!")
        print(f"  Source: {source_img.shape}")
        print(f"  Recon:  {recon_img.shape}")

    # Apply margin crop if specified
    if margin > 0:
        h, w = source_img.shape[:2]
        if margin * 2 >= h or margin * 2 >= w:
            print(f"Error: Margin {margin} too large for image size {w}x{h}")
            sys.exit(1)
        source_img = source_img[margin:h-margin, margin:w-margin]
        recon_img = recon_img[margin:h-margin, margin:w-margin]
        print(f"Applied margin={margin}px crop: {w}x{h} -> {w-2*margin}x{h-2*margin}")

    # Count colors
    source_counts = count_colors(source_img)
    recon_counts = count_colors(recon_img)

    # Print comparison
    print_comparison(source_counts, recon_counts, input_path, recon_path)


if __name__ == "__main__":
    main()
