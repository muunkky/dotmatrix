"""Auto-detect color palette from image using histogram analysis.

This module provides automatic color palette detection for halftone images,
eliminating the need to manually specify colors. Uses histogram analysis
with optional k-means clustering to identify the N most dominant colors.

Key features:
- Subsample large images for performance
- Quantize colors to reduce noise from anti-aliasing
- Filter out white background
- Ensure black is always included when present
- Support minimum presence threshold
"""

from typing import List, Tuple, Optional
from collections import Counter
import numpy as np


def color_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    """Calculate Euclidean distance between two RGB colors.

    Args:
        c1: First RGB tuple
        c2: Second RGB tuple

    Returns:
        Distance as float (0.0 for identical colors, ~441.7 for black/white)
    """
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def is_white_like(color: Tuple[int, int, int], threshold: int = 240) -> bool:
    """Check if a color is white or near-white (background).

    Args:
        color: RGB tuple
        threshold: Minimum value for all channels to be considered white

    Returns:
        True if color is white-like
    """
    return all(c >= threshold for c in color)


def is_black_like(color: Tuple[int, int, int], threshold: int = 30) -> bool:
    """Check if a color is black or near-black.

    Args:
        color: RGB tuple
        threshold: Maximum value for all channels to be considered black

    Returns:
        True if color is black-like
    """
    return all(c <= threshold for c in color)


def quantize_color(
    color: Tuple[int, int, int],
    bucket_size: int = 20
) -> Tuple[int, int, int]:
    """Quantize a color to the nearest bucket.

    Reduces color precision to eliminate noise from anti-aliasing and
    minor variations. Each channel is rounded to the nearest multiple
    of bucket_size.

    Args:
        color: RGB tuple (0-255 per channel)
        bucket_size: Quantization bucket size (default: 20)

    Returns:
        Quantized RGB tuple
    """
    def round_channel(c: int) -> int:
        # Round to nearest bucket, clamped to 0-255
        rounded = round(c / bucket_size) * bucket_size
        return min(255, max(0, rounded))

    return tuple(round_channel(c) for c in color)


def subsample_image(
    image: np.ndarray,
    sample_step: int = 10
) -> List[Tuple[int, int, int]]:
    """Subsample image pixels for faster processing.

    Extracts every Nth pixel in both dimensions to reduce the number
    of pixels to process while preserving color distribution.

    Args:
        image: RGB image as numpy array (H, W, 3)
        sample_step: Sample every Nth pixel (default: 10)

    Returns:
        List of RGB tuples
    """
    h, w = image.shape[:2]
    pixels = []

    for y in range(0, h, sample_step):
        for x in range(0, w, sample_step):
            r, g, b = image[y, x]
            pixels.append((int(r), int(g), int(b)))

    return pixels


def is_auto_palette(palette_spec: str) -> bool:
    """Check if palette specification is 'auto'.

    Args:
        palette_spec: Palette specification string

    Returns:
        True if palette_spec indicates auto-detection
    """
    return palette_spec.lower() == 'auto'


def detect_dominant_colors(
    image: np.ndarray,
    n_colors: int = 6,
    exclude_white: bool = True,
    ensure_black: bool = True,
    min_presence: float = 0.005,
    sample_step: int = 10,
    bucket_size: int = 20
) -> List[Tuple[int, int, int]]:
    """Detect the N most dominant colors in an image.

    Uses histogram analysis with quantization to identify the most
    common colors. Designed for halftone images where colors are
    distinct but may have anti-aliasing noise.

    Args:
        image: RGB image as numpy array (H, W, 3)
        n_colors: Maximum number of colors to return (default: 6)
        exclude_white: If True, filter out white/near-white (default: True)
        ensure_black: If True, always include black if present (default: True)
        min_presence: Minimum fraction of pixels for a color to be included
        sample_step: Subsample every Nth pixel for performance
        bucket_size: Quantization bucket size to reduce noise

    Returns:
        List of RGB tuples representing detected colors, sorted by frequency
    """
    # Subsample image for performance
    pixels = subsample_image(image, sample_step)
    total_pixels = len(pixels)

    if total_pixels == 0:
        return []

    # Quantize colors to reduce noise
    quantized = [quantize_color(p, bucket_size) for p in pixels]

    # Count occurrences
    color_counts = Counter(quantized)

    # Check if black is present (before filtering)
    has_black = any(is_black_like(c) for c in color_counts.keys())

    # Filter colors
    filtered_colors = []
    black_color = None

    for color, count in color_counts.items():
        presence = count / total_pixels

        # Skip colors below minimum presence
        if presence < min_presence:
            continue

        # Track black separately if ensure_black
        if ensure_black and is_black_like(color):
            if black_color is None or count > color_counts.get(black_color, 0):
                black_color = color
            continue

        # Skip white if excluding
        if exclude_white and is_white_like(color):
            continue

        filtered_colors.append((color, count))

    # Sort by count (descending)
    filtered_colors.sort(key=lambda x: x[1], reverse=True)

    # Build result list
    result = []

    # Add black first if ensuring black and present
    if ensure_black and black_color is not None:
        result.append(black_color)

    # Add remaining colors up to n_colors
    for color, _ in filtered_colors:
        if len(result) >= n_colors:
            break
        if color not in result:  # Avoid duplicates
            result.append(color)

    return result


def detect_palette_for_convex(
    image: np.ndarray,
    n_colors: int = 6,
    include_white_background: bool = True
) -> List[Tuple[int, int, int]]:
    """Detect palette suitable for convex edge detection.

    This is a wrapper around detect_dominant_colors that formats
    the output for use with the convex detector. White is always
    included as the first color (background) for quantization.

    Args:
        image: RGB image as numpy array (H, W, 3)
        n_colors: Number of non-white colors to detect (default: 6)
        include_white_background: If True, prepend white to palette

    Returns:
        List of RGB tuples with white first (if included)
    """
    # Detect colors excluding white
    colors = detect_dominant_colors(
        image,
        n_colors=n_colors,
        exclude_white=True,
        ensure_black=True
    )

    # Prepend white as background
    if include_white_background:
        palette = [(255, 255, 255)] + colors
    else:
        palette = colors

    return palette


def format_detected_palette(colors: List[Tuple[int, int, int]]) -> str:
    """Format detected palette for display.

    Args:
        colors: List of RGB tuples

    Returns:
        Human-readable string describing the palette
    """
    # Color name mapping for common colors
    color_names = {
        (0, 0, 0): 'black',
        (255, 0, 0): 'red',
        (0, 255, 0): 'green',
        (0, 0, 255): 'blue',
        (255, 255, 0): 'yellow',
        (255, 0, 255): 'magenta',
        (0, 255, 255): 'cyan',
        (255, 255, 255): 'white',
    }

    def name_color(c: Tuple[int, int, int]) -> str:
        # Check for exact match
        if c in color_names:
            return color_names[c]

        # Check for approximate match (within 30 distance)
        for known, name in color_names.items():
            if color_distance(c, known) < 30:
                return f"~{name}"

        # Fall back to RGB
        return f"RGB({c[0]},{c[1]},{c[2]})"

    names = [name_color(c) for c in colors]
    return ", ".join(names)
