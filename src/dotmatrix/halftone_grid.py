"""
Halftone Grid Generator

Creates authentic halftone screen patterns using standard industry angles.
Instead of detecting existing dots, this generates a regular grid for each
CMYK color and sizes each dot based on ink coverage at that position.

Standard Screen Angles:
    Cyan:    15° (30° from black, minimizes moiré)
    Magenta: 75° (30° from black, opposite side)
    Yellow:   0° (or 90°, least visible ink at most visible angle)
    Black:   45° (most visible angle goes to least visible ink)

The 30° separation between colors minimizes rosette patterns and moiré.

Usage:
    >>> from dotmatrix.halftone_grid import generate_halftone_grids, render_halftone_svg
    >>> grids = generate_halftone_grids(width, height, grid_spacing=10)
    >>> svg = render_halftone_svg(grids, ink_masks, max_dot_radius=5)
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np

# Standard halftone screen angles (in degrees)
HALFTONE_ANGLES = {
    'cyan': 15.0,
    'magenta': 75.0,
    'yellow': 0.0,
    'black': 45.0,
}

# CMYK RGB colors for rendering (pure subtractive primaries)
CMYK_RGB_COLORS = {
    'cyan': '#00FFFF',
    'magenta': '#FF00FF',
    'yellow': '#FFFF00',
    'black': '#000000',
}


@dataclass
class GridPoint:
    """A single point in a halftone grid."""
    x: float
    y: float
    radius: float  # Dot radius based on ink coverage (0 = no dot)


@dataclass
class HalftoneGrid:
    """A complete halftone grid for one color channel."""
    color: str  # 'cyan', 'magenta', 'yellow', or 'black'
    angle: float  # Screen angle in degrees
    spacing: float  # Distance between grid points
    points: List[GridPoint]  # All grid points with their radii
    
    @property
    def dot_count(self) -> int:
        """Number of dots with non-zero radius."""
        return sum(1 for p in self.points if p.radius > 0)


def generate_rotated_grid(
    width: int,
    height: int,
    spacing: float,
    angle_degrees: float,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> List[Tuple[float, float]]:
    """Generate a grid of points rotated at a specific angle.
    
    The grid is generated large enough to cover the entire image after rotation.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        spacing: Distance between grid points
        angle_degrees: Rotation angle in degrees (0 = horizontal lines)
        origin_x: X offset for grid origin (for alignment)
        origin_y: Y offset for grid origin (for alignment)
        
    Returns:
        List of (x, y) tuples for each grid point within image bounds
    """
    angle_rad = math.radians(angle_degrees)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Calculate how large the unrotated grid needs to be to cover the image
    # after rotation. Use diagonal of the image as a safe bound.
    diagonal = math.sqrt(width**2 + height**2)
    
    # Grid extends from -diagonal/2 to +diagonal/2 in both directions
    # centered on the image center
    center_x = width / 2
    center_y = height / 2
    
    half_extent = diagonal / 2 + spacing
    
    # Generate grid points in unrotated space, then rotate
    points = []
    
    # Number of grid lines in each direction
    n_lines = int(2 * half_extent / spacing) + 1
    
    for i in range(-n_lines, n_lines + 1):
        for j in range(-n_lines, n_lines + 1):
            # Unrotated grid position (relative to center)
            gx = i * spacing + origin_x
            gy = j * spacing + origin_y
            
            # Rotate around origin
            rx = gx * cos_a - gy * sin_a
            ry = gx * sin_a + gy * cos_a
            
            # Translate to image coordinates
            px = center_x + rx
            py = center_y + ry
            
            # Check if point is within image bounds (with margin for dots)
            margin = spacing / 2
            if -margin <= px < width + margin and -margin <= py < height + margin:
                points.append((px, py))
    
    return points


def sample_ink_coverage(
    ink_mask: np.ndarray,
    x: float,
    y: float,
    sample_radius: float,
) -> float:
    """Sample the ink coverage at a grid point.
    
    Uses area sampling around the point to determine what percentage
    of the sampling area contains ink. This determines dot size.
    
    Args:
        ink_mask: Binary mask (255=ink, 0=no ink) for one color
        x: X coordinate of sample point
        y: Y coordinate of sample point  
        sample_radius: Radius of area to sample (typically half grid spacing)
        
    Returns:
        Coverage fraction from 0.0 (no ink) to 1.0 (full ink coverage)
    """
    height, width = ink_mask.shape
    
    # Calculate sampling bounds
    x0 = max(0, int(x - sample_radius))
    y0 = max(0, int(y - sample_radius))
    x1 = min(width, int(x + sample_radius) + 1)
    y1 = min(height, int(y + sample_radius) + 1)
    
    if x0 >= x1 or y0 >= y1:
        return 0.0
    
    # Extract sampling region
    region = ink_mask[y0:y1, x0:x1]
    
    if region.size == 0:
        return 0.0
    
    # Calculate coverage (255 = ink present)
    coverage = np.mean(region) / 255.0
    
    return coverage


def generate_halftone_grids(
    width: int,
    height: int,
    grid_spacing: float,
    angles: Optional[Dict[str, float]] = None,
    origin_offsets: Optional[Dict[str, Tuple[float, float]]] = None,
) -> Dict[str, List[Tuple[float, float]]]:
    """Generate halftone grid points for all four CMYK colors.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        grid_spacing: Distance between grid points (determines LPI)
        angles: Optional custom angles dict, defaults to standard halftone angles
        origin_offsets: Optional per-color origin offsets for grid alignment
        
    Returns:
        Dict mapping color names to lists of (x, y) grid points
    """
    if angles is None:
        angles = HALFTONE_ANGLES.copy()
    
    if origin_offsets is None:
        origin_offsets = {color: (0.0, 0.0) for color in angles}
    
    grids = {}
    for color, angle in angles.items():
        ox, oy = origin_offsets.get(color, (0.0, 0.0))
        grids[color] = generate_rotated_grid(
            width, height, grid_spacing, angle, ox, oy
        )
    
    return grids


def size_dots_from_masks(
    grid_points: Dict[str, List[Tuple[float, float]]],
    ink_masks: Dict[str, np.ndarray],
    max_radius: float,
    sample_radius: Optional[float] = None,
    min_coverage: float = 0.01,
) -> Dict[str, HalftoneGrid]:
    """Size dots at each grid point based on ink coverage from masks.
    
    Args:
        grid_points: Dict mapping color names to lists of (x, y) grid points
        ink_masks: Dict mapping color names to binary masks (255=ink, 0=no ink)
        max_radius: Maximum dot radius at 100% coverage
        sample_radius: Radius of sampling area (defaults to max_radius)
        min_coverage: Minimum coverage to create a dot (default 1%)
        
    Returns:
        Dict mapping color names to HalftoneGrid objects with sized dots
    """
    if sample_radius is None:
        sample_radius = max_radius
    
    grids = {}
    
    for color, points in grid_points.items():
        if color not in ink_masks:
            print(f"Warning: No ink mask for {color}, skipping")
            continue
            
        mask = ink_masks[color]
        sized_points = []
        
        for x, y in points:
            coverage = sample_ink_coverage(mask, x, y, sample_radius)
            
            if coverage >= min_coverage:
                # Dot radius proportional to sqrt of coverage
                # (area proportional to coverage)
                radius = max_radius * math.sqrt(coverage)
                sized_points.append(GridPoint(x, y, radius))
            else:
                # Still add point with zero radius for grid visualization if needed
                sized_points.append(GridPoint(x, y, 0.0))
        
        grids[color] = HalftoneGrid(
            color=color,
            angle=HALFTONE_ANGLES.get(color, 0.0),
            spacing=max_radius * 2,  # Approximate
            points=sized_points,
        )
    
    return grids


def render_halftone_svg(
    grids: Dict[str, HalftoneGrid],
    width: int,
    height: int,
    background_color: str = '#FFFFFF',
    include_zero_dots: bool = False,
) -> str:
    """Render halftone grids as an SVG document.
    
    Args:
        grids: Dict mapping color names to HalftoneGrid objects
        width: SVG width in pixels
        height: SVG height in pixels
        background_color: Background fill color
        include_zero_dots: If True, render zero-radius dots as tiny markers
        
    Returns:
        SVG document as a string
    """
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'  <rect width="100%" height="100%" fill="{background_color}"/>',
    ]
    
    # Render in order: yellow, cyan, magenta, black (lightest to darkest)
    render_order = ['yellow', 'cyan', 'magenta', 'black']
    
    for color in render_order:
        if color not in grids:
            continue
            
        grid = grids[color]
        fill_color = CMYK_RGB_COLORS.get(color, '#000000')
        
        lines.append(f'  <!-- {color.upper()} layer (angle={grid.angle}°, dots={grid.dot_count}) -->')
        lines.append(f'  <g id="{color}" fill="{fill_color}">')
        
        for point in grid.points:
            if point.radius > 0:
                lines.append(
                    f'    <circle cx="{point.x:.2f}" cy="{point.y:.2f}" r="{point.radius:.2f}"/>'
                )
            elif include_zero_dots:
                # Render as tiny dot for visualization
                lines.append(
                    f'    <circle cx="{point.x:.2f}" cy="{point.y:.2f}" r="0.5" opacity="0.1"/>'
                )
        
        lines.append('  </g>')
    
    lines.append('</svg>')
    
    return '\n'.join(lines)


def estimate_grid_spacing_from_image(
    ink_mask: np.ndarray,
    method: str = 'fft',
) -> float:
    """Estimate the halftone grid spacing from an image.
    
    Attempts to detect the screen frequency (LPI equivalent) from
    the periodic pattern in the image.
    
    Args:
        ink_mask: Binary mask of one ink color
        method: Detection method ('fft' or 'autocorr')
        
    Returns:
        Estimated grid spacing in pixels
    """
    if method == 'fft':
        return _estimate_spacing_fft(ink_mask)
    elif method == 'autocorr':
        return _estimate_spacing_autocorr(ink_mask)
    else:
        raise ValueError(f"Unknown method: {method}")


def _estimate_spacing_fft(ink_mask: np.ndarray) -> float:
    """Estimate grid spacing using FFT analysis."""
    # Normalize mask to 0-1
    mask_float = ink_mask.astype(np.float32) / 255.0
    
    # Compute 2D FFT
    fft = np.fft.fft2(mask_float)
    fft_shifted = np.fft.fftshift(fft)
    magnitude = np.abs(fft_shifted)
    
    # Find peaks in magnitude spectrum (excluding DC component)
    height, width = magnitude.shape
    center_y, center_x = height // 2, width // 2
    
    # Mask out DC component and nearby low frequencies
    dc_mask_radius = 5
    y_coords, x_coords = np.ogrid[:height, :width]
    dc_mask = ((y_coords - center_y)**2 + (x_coords - center_x)**2) <= dc_mask_radius**2
    magnitude[dc_mask] = 0
    
    # Find the strongest peak
    peak_idx = np.argmax(magnitude)
    peak_y, peak_x = np.unravel_index(peak_idx, magnitude.shape)
    
    # Distance from center to peak gives frequency
    freq_dist = math.sqrt((peak_x - center_x)**2 + (peak_y - center_y)**2)
    
    if freq_dist < 1:
        # No clear periodicity detected, return reasonable default
        return 10.0
    
    # Convert frequency to spacing (wavelength)
    # freq_dist is in cycles per image dimension
    avg_dim = (width + height) / 2
    spacing = avg_dim / freq_dist
    
    return spacing


def _estimate_spacing_autocorr(ink_mask: np.ndarray) -> float:
    """Estimate grid spacing using autocorrelation."""
    # Normalize mask
    mask_float = ink_mask.astype(np.float32) / 255.0
    mask_float = mask_float - np.mean(mask_float)
    
    # Use FFT for fast autocorrelation
    fft = np.fft.fft2(mask_float)
    autocorr = np.fft.ifft2(fft * np.conj(fft)).real
    autocorr = np.fft.fftshift(autocorr)
    
    # Normalize
    autocorr = autocorr / autocorr.max()
    
    height, width = autocorr.shape
    center_y, center_x = height // 2, width // 2
    
    # Find first significant peak away from center
    # Search in a horizontal slice from center
    slice_1d = autocorr[center_y, center_x + 5:]  # Skip near-center
    
    # Find first local maximum above threshold
    threshold = 0.3
    for i in range(1, len(slice_1d) - 1):
        if slice_1d[i] > threshold and slice_1d[i] > slice_1d[i-1] and slice_1d[i] > slice_1d[i+1]:
            return i + 5  # Add back the offset
    
    # Fallback: use half the distance to the edge
    return min(width, height) / 20


def create_halftone_from_image(
    image: np.ndarray,
    grid_spacing: Optional[float] = None,
    max_dot_radius: Optional[float] = None,
    angles: Optional[Dict[str, float]] = None,
    auto_detect_spacing: bool = True,
) -> Tuple[Dict[str, HalftoneGrid], str]:
    """Complete pipeline: image → ink masks → halftone grids → SVG.
    
    Args:
        image: BGR image as numpy array
        grid_spacing: Grid spacing in pixels (auto-detected if None)
        max_dot_radius: Maximum dot radius (defaults to spacing/2)
        angles: Custom screen angles (defaults to standard CMYK angles)
        auto_detect_spacing: If True and grid_spacing is None, detect from image
        
    Returns:
        Tuple of (halftone grids dict, SVG string)
    """
    from .convex_detector import separate_cmyk_inks
    
    height, width = image.shape[:2]
    
    # Get ink masks
    ink_masks = separate_cmyk_inks(image)
    
    # Auto-detect grid spacing if needed
    if grid_spacing is None:
        if auto_detect_spacing:
            # Use black mask for spacing detection (usually clearest pattern)
            if np.any(ink_masks['black']):
                grid_spacing = estimate_grid_spacing_from_image(ink_masks['black'])
            else:
                # Fall back to cyan or magenta
                for color in ['cyan', 'magenta', 'yellow']:
                    if np.any(ink_masks[color]):
                        grid_spacing = estimate_grid_spacing_from_image(ink_masks[color])
                        break
                else:
                    grid_spacing = 10.0  # Default fallback
            print(f"Auto-detected grid spacing: {grid_spacing:.1f} pixels")
        else:
            grid_spacing = 10.0
    
    if max_dot_radius is None:
        max_dot_radius = grid_spacing / 2
    
    # Generate grid points
    grid_points = generate_halftone_grids(width, height, grid_spacing, angles)
    
    # Size dots based on ink coverage
    grids = size_dots_from_masks(
        grid_points, ink_masks, max_dot_radius, 
        sample_radius=grid_spacing / 2
    )
    
    # Render SVG
    svg = render_halftone_svg(grids, width, height)
    
    return grids, svg


# Convenience functions for interactive use

def separate_cmyk_inks_memory_efficient(
    image: np.ndarray,
    threshold: int = 128,
) -> Dict[str, np.ndarray]:
    """Memory-efficient CMYK ink separation using thresholds.
    
    Unlike quantize_to_cmyk_rgb which creates large intermediate arrays,
    this works directly with channel comparisons. Good for large images.
    
    Args:
        image: BGR image as numpy array (H, W, 3)
        threshold: Value threshold for ink detection (0-255)
        
    Returns:
        Dictionary mapping ink names to binary masks (255=ink, 0=absent)
    """
    # Extract channels (BGR format)
    b = image[:, :, 0].astype(np.int16)
    g = image[:, :, 1].astype(np.int16)
    r = image[:, :, 2].astype(np.int16)
    
    # Background detection (near white)
    white_threshold = 250
    is_white = (r > white_threshold) & (g > white_threshold) & (b > white_threshold)
    
    # Black detection (near black)
    black_threshold = 50
    is_black = (r < black_threshold) & (g < black_threshold) & (b < black_threshold)
    
    # Colored pixels (not white, not black)
    colored = ~is_white & ~is_black
    
    # Cyan ink present: red channel is absorbed (low R relative to G,B)
    # In pure cyan, R=0, G=255, B=255
    cyan_mask = colored & (r < threshold) & (g > threshold) & (b > threshold)
    
    # Magenta ink present: green channel is absorbed (low G relative to R,B)  
    # In pure magenta, R=255, G=0, B=255
    magenta_mask = colored & (r > threshold) & (g < threshold) & (b > threshold)
    
    # Yellow ink present: blue channel is absorbed (low B relative to R,G)
    # In pure yellow, R=255, G=255, B=0
    yellow_mask = colored & (r > threshold) & (g > threshold) & (b < threshold)
    
    # Secondary colors (overlaps)
    # Red = Magenta + Yellow (low G and B)
    red_mask = colored & (r > threshold) & (g < threshold) & (b < threshold)
    
    # Green = Cyan + Yellow (low R and B)
    green_mask = colored & (r < threshold) & (g > threshold) & (b < threshold)
    
    # Blue = Cyan + Magenta (low R and G)
    blue_mask = colored & (r < threshold) & (g < threshold) & (b > threshold)
    
    # Final masks include both primary and secondary contributions
    # Using OR logic: any pixel where this ink contributes
    final_cyan = cyan_mask | green_mask | blue_mask
    final_magenta = magenta_mask | red_mask | blue_mask
    final_yellow = yellow_mask | red_mask | green_mask
    
    return {
        'cyan': (final_cyan * 255).astype(np.uint8),
        'magenta': (final_magenta * 255).astype(np.uint8),
        'yellow': (final_yellow * 255).astype(np.uint8),
        'black': (is_black * 255).astype(np.uint8),
    }


def analyze_halftone_image(image: np.ndarray, memory_efficient: bool = False) -> Dict:
    """Analyze a halftone image and report detected parameters.
    
    Args:
        image: BGR image as numpy array
        memory_efficient: If True, use threshold-based separation (less memory)
        
    Returns:
        Dict with detected spacing, angles, and ink coverage stats
    """
    if memory_efficient:
        ink_masks = separate_cmyk_inks_memory_efficient(image)
    else:
        from .convex_detector import separate_cmyk_inks
        ink_masks = separate_cmyk_inks(image)
    
    results = {}
    
    for color, mask in ink_masks.items():
        ink_pixels = np.sum(mask > 0)
        total_pixels = mask.size
        coverage = ink_pixels / total_pixels
        
        spacing = None
        if ink_pixels > 100:  # Need enough ink to detect pattern
            try:
                spacing = estimate_grid_spacing_from_image(mask)
            except Exception:
                pass
        
        results[color] = {
            'coverage': coverage,
            'ink_pixels': int(ink_pixels),
            'estimated_spacing': spacing,
        }
    
    return results


def create_halftone_from_image_memory_efficient(
    image: np.ndarray,
    grid_spacing: float,
    max_dot_radius: Optional[float] = None,
    angles: Optional[Dict[str, float]] = None,
) -> Tuple[Dict[str, HalftoneGrid], str]:
    """Memory-efficient version for large images.
    
    Uses threshold-based ink separation instead of quantization.
    
    Args:
        image: BGR image as numpy array
        grid_spacing: Grid spacing in pixels (required, no auto-detection)
        max_dot_radius: Maximum dot radius (defaults to spacing/2)
        angles: Custom screen angles (defaults to standard CMYK angles)
        
    Returns:
        Tuple of (halftone grids dict, SVG string)
    """
    height, width = image.shape[:2]
    print(f"Image size: {width} x {height}")
    
    # Get ink masks using memory-efficient method
    print("Separating CMYK inks (memory-efficient mode)...")
    ink_masks = separate_cmyk_inks_memory_efficient(image)
    
    if max_dot_radius is None:
        max_dot_radius = grid_spacing / 2
    
    # Generate grid points
    print(f"Generating grid points (spacing={grid_spacing}, radius={max_dot_radius})...")
    grid_points = generate_halftone_grids(width, height, grid_spacing, angles)
    
    total_points = sum(len(pts) for pts in grid_points.values())
    print(f"  Generated {total_points:,} grid points total")
    
    # Size dots based on ink coverage
    print("Sizing dots based on ink coverage...")
    grids = size_dots_from_masks(
        grid_points, ink_masks, max_dot_radius, 
        sample_radius=grid_spacing / 2
    )
    
    for color, grid in grids.items():
        print(f"  {color}: {grid.dot_count:,} dots with non-zero radius")
    
    # Render SVG
    print("Rendering SVG...")
    svg = render_halftone_svg(grids, width, height)
    
    return grids, svg
