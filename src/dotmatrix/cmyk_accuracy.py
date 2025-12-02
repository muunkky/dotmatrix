"""
CMYK Accuracy Measurement Module

Provides functions to decompose images to CMYK pixel counts and compare
source vs reconstituted images for accuracy validation.

Subtractive Color Model:
    In subtractive color mixing (like print/ink), combining primary colors
    creates secondary colors:
    - Magenta + Yellow = Red (absorbs G and B, reflects R)
    - Cyan + Yellow = Green (absorbs R and B, reflects G)
    - Cyan + Magenta = Blue (absorbs R and G, reflects B)

    When we see a secondary color, we attribute it back to its primaries:
    - Red pixel -> contributes to BOTH Magenta AND Yellow
    - Green pixel -> contributes to BOTH Cyan AND Yellow
    - Blue pixel -> contributes to BOTH Cyan AND Magenta

Usage:
    >>> source_cmyk = decompose_to_cmyk("source.png")
    >>> recon_cmyk = decompose_to_cmyk("reconstituted.png")
    >>> result = compare_cmyk_vectors(source_cmyk, recon_cmyk)
    >>> print(f"Total error: {result['total_error']:.1%}")
    >>> print(f"Passed: {result['passed']}")
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Union

import cv2
import numpy as np


# Color definitions in BGR format (OpenCV's native format)
COLORS_BGR = {
    'black':   (0, 0, 0),
    'white':   (255, 255, 255),
    'cyan':    (255, 255, 0),      # BGR: high B, high G, low R
    'magenta': (255, 0, 255),      # BGR: high B, low G, high R
    'yellow':  (0, 255, 255),      # BGR: low B, high G, high R
    'red':     (0, 0, 255),        # BGR: low B, low G, high R (secondary: M+Y)
    'green':   (0, 255, 0),        # BGR: low B, high G, low R (secondary: C+Y)
    'blue':    (255, 0, 0),        # BGR: high B, low G, low R (secondary: C+M)
}


@dataclass
class CMYKDecomposition:
    """Result of decomposing an image to CMYK counts."""
    cyan: int
    magenta: int
    yellow: int
    black: int

    # Diagnostic information
    primary_pixels: int      # C + M + Y + K pixels
    secondary_pixels: int    # R + G + B pixels
    white_pixels: int        # Background pixels
    total_pixels: int        # Total image pixels

    # Raw color counts before decomposition
    raw_counts: Dict[str, int]

    def to_dict(self) -> dict:
        """Convert to dictionary for comparison."""
        return {
            'cyan': self.cyan,
            'magenta': self.magenta,
            'yellow': self.yellow,
            'black': self.black,
            'primary_pixels': self.primary_pixels,
            'secondary_pixels': self.secondary_pixels,
            'white_pixels': self.white_pixels,
            'total_pixels': self.total_pixels,
            'raw_counts': self.raw_counts
        }

    def cmyk_vector(self) -> Tuple[int, int, int, int]:
        """Return CMYK as a tuple for easy comparison."""
        return (self.cyan, self.magenta, self.yellow, self.black)


@dataclass
class ComparisonResult:
    """Result of comparing two CMYK decompositions."""
    per_channel: Dict[str, Dict[str, float]]  # {color: {diff, pct_error}}
    total_error: float                         # Weighted average error
    passed: bool                               # Under threshold?
    threshold: float                           # Threshold used
    source: CMYKDecomposition
    reconstituted: CMYKDecomposition

    def to_dict(self) -> dict:
        return {
            'per_channel': self.per_channel,
            'total_error': self.total_error,
            'passed': self.passed,
            'threshold': self.threshold
        }

    def format_report(self) -> str:
        """Generate human-readable accuracy report."""
        lines = [
            "=== CMYK Accuracy Report ===",
            "",
            "--- Decomposition ---",
            f"{'':12} {'Source':>10} {'Recon':>10} {'Diff':>10} {'Error':>10}",
        ]

        for color in ['cyan', 'magenta', 'yellow', 'black']:
            src = getattr(self.source, color)
            rec = getattr(self.reconstituted, color)
            ch = self.per_channel[color]
            diff = ch['diff']
            pct = ch['pct_error']
            sign = '+' if diff > 0 else ''
            lines.append(f"{color.capitalize():12} {src:>10,} {rec:>10,} {sign}{diff:>9,} {pct:>9.1%}")

        lines.extend([
            "",
            "Secondary colors detected:",
            f"  Source:  Red={self.source.raw_counts.get('red', 0):,}, "
            f"Green={self.source.raw_counts.get('green', 0):,}, "
            f"Blue={self.source.raw_counts.get('blue', 0):,}",
            f"  Recon:   Red={self.reconstituted.raw_counts.get('red', 0):,}, "
            f"Green={self.reconstituted.raw_counts.get('green', 0):,}, "
            f"Blue={self.reconstituted.raw_counts.get('blue', 0):,}",
            "",
            "--- Summary ---",
            f"Total Error: {self.total_error:.1%} (weighted average)",
            f"Threshold:   {self.threshold:.1%}",
            f"Result:      {'PASS' if self.passed else 'FAIL'}",
        ])

        return '\n'.join(lines)


def count_color(img: np.ndarray, target_bgr: Tuple[int, int, int], tolerance: int) -> int:
    """
    Count pixels matching target color within tolerance.

    Uses vectorized numpy operations for performance.

    Args:
        img: Image array in BGR format (H, W, 3)
        target_bgr: Target color as (B, G, R) tuple
        tolerance: Maximum difference per channel to consider a match

    Returns:
        Number of pixels matching the target color
    """
    # Calculate absolute difference from target
    diff = np.abs(img.astype(np.int16) - np.array(target_bgr, dtype=np.int16))

    # Pixel matches if ALL channels are within tolerance
    matches = np.all(diff <= tolerance, axis=2)

    return int(np.sum(matches))


def decompose_to_cmyk(
    image_path: Union[str, Path],
    tolerance: int = 20,
    white_threshold: int = 250
) -> CMYKDecomposition:
    """
    Decompose image to CMYK pixel counts using subtractive color model.

    Secondary colors are attributed back to their primary components:
    - Red pixels contribute to BOTH Magenta AND Yellow
    - Green pixels contribute to BOTH Cyan AND Yellow
    - Blue pixels contribute to BOTH Cyan AND Magenta

    Args:
        image_path: Path to image file
        tolerance: Maximum per-channel difference for color matching (0-255)
        white_threshold: Minimum value for all channels to be considered white

    Returns:
        CMYKDecomposition with counts and diagnostic info

    Note:
        Total CMYK contributions may exceed actual colored pixel count because
        secondary colors contribute to two channels each.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    total_pixels = img.shape[0] * img.shape[1]

    # Count white/background pixels
    white_mask = np.all(img >= white_threshold, axis=2)
    white_pixels = int(np.sum(white_mask))

    # Count each color
    raw_counts = {}
    for name, bgr in COLORS_BGR.items():
        if name == 'white':
            raw_counts[name] = white_pixels
        else:
            raw_counts[name] = count_color(img, bgr, tolerance)

    # Calculate primary and secondary pixel counts
    primary_pixels = (
        raw_counts['cyan'] +
        raw_counts['magenta'] +
        raw_counts['yellow'] +
        raw_counts['black']
    )
    secondary_pixels = (
        raw_counts['red'] +
        raw_counts['green'] +
        raw_counts['blue']
    )

    # Decompose to CMYK ink contributions using subtractive color model
    # Secondary colors are mixtures of primary inks:
    #   Blue = C + M (cyan + magenta ink produces blue)
    #   Green = C + Y (cyan + yellow ink produces green)
    #   Red = M + Y (magenta + yellow ink produces red)
    cyan_total = raw_counts['cyan'] + raw_counts['green'] + raw_counts['blue']
    magenta_total = raw_counts['magenta'] + raw_counts['red'] + raw_counts['blue']
    yellow_total = raw_counts['yellow'] + raw_counts['red'] + raw_counts['green']
    black_total = raw_counts['black']

    return CMYKDecomposition(
        cyan=cyan_total,
        magenta=magenta_total,
        yellow=yellow_total,
        black=black_total,
        primary_pixels=primary_pixels,
        secondary_pixels=secondary_pixels,
        white_pixels=white_pixels,
        total_pixels=total_pixels,
        raw_counts=raw_counts
    )


def compare_cmyk_vectors(
    source: CMYKDecomposition,
    reconstituted: CMYKDecomposition,
    threshold: float = 0.10
) -> ComparisonResult:
    """
    Compare two CMYK decompositions and calculate accuracy metrics.

    Args:
        source: Decomposition of source/reference image
        reconstituted: Decomposition of reconstituted/output image
        threshold: Maximum acceptable total error (0.0 to 1.0)

    Returns:
        ComparisonResult with per-channel and total error metrics
    """
    per_channel = {}
    total_weighted_error = 0.0
    total_weight = 0

    for color in ['cyan', 'magenta', 'yellow', 'black']:
        src_val = getattr(source, color)
        rec_val = getattr(reconstituted, color)

        diff = rec_val - src_val

        # Calculate percentage error (handle zero case)
        if src_val > 0:
            pct_error = abs(diff) / src_val
        elif rec_val > 0:
            pct_error = 1.0  # 100% error if source is 0 but recon is not
        else:
            pct_error = 0.0  # Both are 0, no error

        per_channel[color] = {
            'source': src_val,
            'reconstituted': rec_val,
            'diff': diff,
            'pct_error': pct_error
        }

        # Weight by source count for total error calculation
        total_weighted_error += abs(diff)
        total_weight += src_val

    # Calculate total error as weighted average
    if total_weight > 0:
        total_error = total_weighted_error / total_weight
    else:
        total_error = 0.0 if total_weighted_error == 0 else 1.0

    passed = total_error <= threshold

    return ComparisonResult(
        per_channel=per_channel,
        total_error=total_error,
        passed=passed,
        threshold=threshold,
        source=source,
        reconstituted=reconstituted
    )


def measure_accuracy(
    source_path: Union[str, Path],
    reconstituted_path: Union[str, Path],
    tolerance: int = 20,
    threshold: float = 0.10,
    verbose: bool = False
) -> ComparisonResult:
    """
    Convenience function to measure accuracy between two images.

    Args:
        source_path: Path to source/reference image
        reconstituted_path: Path to reconstituted/output image
        tolerance: Color matching tolerance (0-255)
        threshold: Maximum acceptable total error (0.0-1.0)
        verbose: If True, print detailed report

    Returns:
        ComparisonResult with accuracy metrics
    """
    source = decompose_to_cmyk(source_path, tolerance)
    recon = decompose_to_cmyk(reconstituted_path, tolerance)
    result = compare_cmyk_vectors(source, recon, threshold)

    if verbose:
        print(result.format_report())

    return result
