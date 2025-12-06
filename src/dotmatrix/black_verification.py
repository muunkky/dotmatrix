"""Black dot verification for CMYK detection calibration.

Uses black (K) channel dots as ground truth for verifying detection settings.
Black dots have unique properties that make them reliable reference points:
- Always printed on top (never occluded by other colors)
- High contrast against white background
- Well-defined edges (no color mixing)
- Complete circles (no partial shapes from overlap)

This module provides functions to:
1. Detect black dots from an image
2. Calculate verification metrics (count, density, radius distribution)
3. Generate warnings when settings may be misconfigured
"""

from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Optional
import numpy as np
import cv2

from .convex_detector import (
    separate_cmyk_inks,
    detect_circles_from_convex_edges,
    CMYK_INK_COLORS,
    DetectedCircle,
)


@dataclass
class VerificationResult:
    """Result of black dot verification.

    Contains metrics about detected black circles and warnings
    about potential configuration issues.
    """
    black_circles_detected: int
    radius_mean: float
    radius_std: float
    radius_min: int
    radius_max: int
    expected_density: float
    actual_density: float
    coverage_percent: float
    warnings: List[str]
    passed: bool
    suggested_radius_range: Optional[Tuple[int, int]] = None
    circles: Optional[List[DetectedCircle]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Exclude circles from serialization (too verbose)
        result.pop('circles', None)
        return result


def verify_black_dot_detection(
    image: np.ndarray,
    min_radius: int,
    max_radius: int,
    ink_threshold: int = 100,
    black_threshold: int = 60,
    dedup_distance: int = 0,
    expected_count_range: Optional[Tuple[int, int]] = None,
) -> VerificationResult:
    """Detect black dots and calculate verification metrics.

    Uses the black channel from CMYK ink separation to detect dots
    and calculate statistics about the detection quality.

    Args:
        image: RGB image as numpy array (H, W, 3)
        min_radius: Minimum circle radius for detection
        max_radius: Maximum circle radius for detection
        ink_threshold: Threshold for ink separation (see separate_cmyk_inks)
        black_threshold: Threshold for black detection (see separate_cmyk_inks)
        dedup_distance: Distance for deduplication (0 = no dedup)
        expected_count_range: Optional (min, max) expected circle count

    Returns:
        VerificationResult with metrics and warnings
    """
    # Extract black channel mask (with quantization for clean separation)
    ink_masks = separate_cmyk_inks(image)
    black_mask = ink_masks['black']

    # Detect black circles
    black_color = CMYK_INK_COLORS['black']
    circles = detect_circles_from_convex_edges(
        black_mask,
        black_color,
        min_radius=min_radius,
        max_radius=max_radius,
        dedup_distance=dedup_distance
    )

    # Calculate metrics
    image_shape = image.shape[:2]
    radii = [c.radius for c in circles]
    metrics = calculate_verification_metrics(
        black_circle_count=len(circles),
        image_shape=image_shape,
        radii=radii
    )

    # Generate warnings
    if expected_count_range is None:
        # Estimate expected count based on image size and typical halftone density
        # Typical halftone: 1 circle per ~100-200 pixels in each dimension
        h, w = image_shape
        expected_min = int((h * w) / (200 * 200))  # Sparse estimate
        expected_max = int((h * w) / (50 * 50))    # Dense estimate
        expected_count_range = (expected_min, expected_max)

    warnings = generate_verification_warnings(
        black_circle_count=len(circles),
        expected_count_range=expected_count_range,
        radius_mean=metrics['radius_mean'],
        radius_std=metrics['radius_std'],
        min_radius=min_radius,
        max_radius=max_radius,
        coverage_percent=metrics['coverage_percent']
    )

    # Suggest radius range if detected distribution warrants it
    suggested_range = suggest_radius_range(
        radius_mean=metrics['radius_mean'],
        radius_std=metrics['radius_std'],
        radius_min=metrics['radius_min'],
        radius_max=metrics['radius_max'],
        current_min=min_radius,
        current_max=max_radius
    )

    # Determine if verification passed
    passed = len(warnings) == 0

    return VerificationResult(
        black_circles_detected=len(circles),
        radius_mean=metrics['radius_mean'],
        radius_std=metrics['radius_std'],
        radius_min=metrics['radius_min'],
        radius_max=metrics['radius_max'],
        expected_density=metrics.get('expected_density', 0.0),
        actual_density=metrics['density'],
        coverage_percent=metrics['coverage_percent'],
        warnings=warnings,
        passed=passed,
        suggested_radius_range=suggested_range,
        circles=circles
    )


def calculate_verification_metrics(
    black_circle_count: int,
    image_shape: Tuple[int, int],
    radii: List[int]
) -> Dict[str, float]:
    """Calculate metrics for black dot verification.

    Args:
        black_circle_count: Number of black circles detected
        image_shape: (height, width) of the image
        radii: List of detected circle radii

    Returns:
        Dictionary with density, coverage, and radius statistics
    """
    h, w = image_shape
    total_pixels = h * w

    # Handle empty case
    if not radii or black_circle_count == 0:
        return {
            'density': 0.0,
            'coverage_percent': 0.0,
            'radius_mean': 0.0,
            'radius_std': 0.0,
            'radius_min': 0,
            'radius_max': 0,
            'count': 0
        }

    # Density: circles per megapixel (for human-readable numbers)
    density = black_circle_count / (total_pixels / 1_000_000)

    # Coverage: total circle area / image area
    total_circle_area = sum(np.pi * r * r for r in radii)
    coverage_percent = (total_circle_area / total_pixels) * 100

    # Radius statistics
    radius_mean = float(np.mean(radii))
    radius_std = float(np.std(radii))
    radius_min = int(np.min(radii))
    radius_max = int(np.max(radii))

    return {
        'density': density,
        'coverage_percent': coverage_percent,
        'radius_mean': radius_mean,
        'radius_std': radius_std,
        'radius_min': radius_min,
        'radius_max': radius_max,
        'count': black_circle_count
    }


def generate_verification_warnings(
    black_circle_count: int,
    expected_count_range: Tuple[int, int],
    radius_mean: float,
    radius_std: float,
    min_radius: int,
    max_radius: int,
    coverage_percent: float
) -> List[str]:
    """Generate warnings about potential configuration issues.

    Analyzes detection results and flags potential problems:
    - Count too low (settings may be filtering valid circles)
    - Mean radius near boundary (min/max may need adjustment)
    - High variance (inconsistent detection)
    - Low coverage (missing circles)

    Args:
        black_circle_count: Number of black circles detected
        expected_count_range: (min, max) expected count based on image
        radius_mean: Mean radius of detected circles
        radius_std: Standard deviation of radii
        min_radius: Configured minimum radius
        max_radius: Configured maximum radius
        coverage_percent: Percentage of image covered by circles

    Returns:
        List of warning messages (empty if no issues)
    """
    warnings = []

    # No circles detected at all
    if black_circle_count == 0:
        warnings.append(
            "No black circles detected. Check min_radius/max_radius settings "
            "or verify image contains CMYK halftone dots."
        )
        return warnings  # No point checking other metrics

    expected_min, expected_max = expected_count_range

    # Count significantly below expected
    if black_circle_count < expected_min * 0.5:
        warnings.append(
            f"Very few black circles detected ({black_circle_count}). "
            f"Expected at least {expected_min}. "
            "Consider lowering min_radius or raising max_radius."
        )

    # Mean radius very close to min_radius (may be cutting off circles)
    if radius_mean > 0:
        radius_range = max_radius - min_radius
        margin = radius_range * 0.15  # 15% margin

        if radius_mean < min_radius + margin:
            warnings.append(
                f"Mean radius ({radius_mean:.1f}) is close to min_radius ({min_radius}). "
                "Some circles may be cut off. Consider lowering min_radius."
            )

        if radius_mean > max_radius - margin:
            warnings.append(
                f"Mean radius ({radius_mean:.1f}) is close to max_radius ({max_radius}). "
                "Some circles may be cut off. Consider raising max_radius."
            )

    # High variance in radius (may indicate detection issues)
    if radius_mean > 0 and radius_std > 0:
        coefficient_of_variation = radius_std / radius_mean
        if coefficient_of_variation > 0.4:  # CV > 40% is high
            warnings.append(
                f"High radius variation (CV={coefficient_of_variation:.1%}). "
                "Detection may be inconsistent. Check image quality or adjust thresholds."
            )

    # Very low coverage (suspicious)
    if coverage_percent < 0.1 and black_circle_count > 0:
        warnings.append(
            f"Very low coverage ({coverage_percent:.2f}%). "
            "This suggests many circles may be missed."
        )

    return warnings


def suggest_radius_range(
    radius_mean: float,
    radius_std: float,
    radius_min: int,
    radius_max: int,
    current_min: int,
    current_max: int
) -> Optional[Tuple[int, int]]:
    """Suggest improved radius range based on detected black dots.

    Uses statistical analysis of detected radii to suggest a better
    min/max radius range that would capture the actual dot sizes.

    Args:
        radius_mean: Mean radius of detected circles
        radius_std: Standard deviation of radii
        radius_min: Minimum detected radius
        radius_max: Maximum detected radius
        current_min: Current min_radius setting
        current_max: Current max_radius setting

    Returns:
        (suggested_min, suggested_max) tuple, or None if current range is good
    """
    if radius_mean == 0:
        return None

    # Calculate bounds using mean ± 2 std (covers ~95% of normal distribution)
    # Add 20% padding to ensure we don't cut off edge cases
    lower_bound = max(1, int((radius_mean - 2 * radius_std) * 0.8))
    upper_bound = int((radius_mean + 2 * radius_std) * 1.2)

    # Check if current range is too narrow
    range_too_narrow = (
        radius_min < current_min + (current_max - current_min) * 0.2 or
        radius_max > current_max - (current_max - current_min) * 0.2
    )

    # Suggest new range if:
    # 1. Current range is too narrow (cutting off circles)
    # 2. Suggested range differs significantly from current (>15% difference)
    min_diff_pct = abs(lower_bound - current_min) / current_min if current_min > 0 else 1.0
    max_diff_pct = abs(upper_bound - current_max) / current_max if current_max > 0 else 1.0

    if range_too_narrow or min_diff_pct > 0.15 or max_diff_pct > 0.15:
        return (lower_bound, upper_bound)

    return None


def generate_coverage_map(
    circles: List[DetectedCircle],
    image_shape: Tuple[int, int],
    grid_size: int = 10
) -> np.ndarray:
    """Generate a visual heatmap of black dot detection coverage.

    Divides image into a grid and colors each cell based on detection density.
    Useful for identifying regions with sparse detection.

    Args:
        circles: List of detected circles
        image_shape: (height, width) of original image
        grid_size: Number of grid cells per dimension (default: 10)

    Returns:
        RGB heatmap image as numpy array
    """
    h, w = image_shape
    
    # Create grid to count circles per cell
    cell_height = h // grid_size
    cell_width = w // grid_size
    grid_counts = np.zeros((grid_size, grid_size), dtype=np.float32)

    # Count circles in each grid cell
    for circle in circles:
        cell_y = min(int(circle.y / cell_height), grid_size - 1)
        cell_x = min(int(circle.x / cell_width), grid_size - 1)
        grid_counts[cell_y, cell_x] += 1

    # Normalize to 0-255 range
    if grid_counts.max() > 0:
        grid_normalized = (grid_counts / grid_counts.max() * 255).astype(np.uint8)
    else:
        grid_normalized = grid_counts.astype(np.uint8)

    # Resize to full image dimensions for visualization
    coverage_map = cv2.resize(
        grid_normalized,
        (w, h),
        interpolation=cv2.INTER_NEAREST
    )

    # Apply colormap (COLORMAP_JET: blue=low, red=high)
    coverage_map_color = cv2.applyColorMap(coverage_map, cv2.COLORMAP_JET)

    # Convert BGR to RGB for consistency
    coverage_map_rgb = cv2.cvtColor(coverage_map_color, cv2.COLOR_BGR2RGB)

    return coverage_map_rgb


def format_verification_output(result: VerificationResult) -> str:
    """Format verification result for console output.

    Args:
        result: VerificationResult to format

    Returns:
        Formatted string for console display
    """
    lines = [
        "Black Dot Verification:",
        f"  Circles detected: {result.black_circles_detected}",
    ]

    if result.black_circles_detected > 0:
        lines.extend([
            f"  Radius: mean={result.radius_mean:.1f}, "
            f"std={result.radius_std:.1f}, "
            f"range=[{result.radius_min}, {result.radius_max}]",
            f"  Coverage: {result.coverage_percent:.2f}%",
            f"  Density: {result.actual_density:.1f} circles/MP",
        ])

    if result.warnings:
        lines.append("  Warnings:")
        for warning in result.warnings:
            lines.append(f"    ⚠ {warning}")
    else:
        lines.append("  Status: ✓ Verification passed")

    # Add suggested radius range if available
    if result.suggested_radius_range:
        suggested_min, suggested_max = result.suggested_radius_range
        lines.append(f"  Suggested radius range: --min-radius {suggested_min} --max-radius {suggested_max}")

    return "\n".join(lines)
