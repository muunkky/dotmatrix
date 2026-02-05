"""Centroid-guided position drift for improved color coverage.

This module implements centroid-based position movement that replaces random
position jitter with intelligent movement toward the center of mass of color
pixels in the source image.

The goal is to improve color coverage accuracy by moving petals toward
where their color pixels actually are, rather than random displacement.

Pipeline integration:
1. Compute circles (existing)
2. For each cluster:
   a. Compute color centroids from pre-separated CMYK masks
   b. Apply centroid-guided position movement (replaces random jitter)
   c. Apply random size jitter (preserved for organic feel)
3. Drift loop (existing):
   a. Measure actual vs target pixels
   b. Adjust radius to compensate
   c. Repeat until converged

Based on ADR-002 (jitter strategy) and the jitter.py module architecture.
Uses pre-separated CMYK masks from separate_cmyk_inks() for accurate color detection.
"""

import numpy as np
from typing import Tuple, Optional, Dict


def compute_color_centroid_from_mask(
    color_mask: np.ndarray,
    cluster_cx: float,
    cluster_cy: float,
    search_radius: float,
    min_pixels: int = 10,
) -> Optional[Tuple[float, float]]:
    """Find the centroid (center of mass) of color pixels from a pre-separated mask.
    
    Uses the already-separated CMYK mask (from separate_cmyk_inks) rather than
    trying to detect colors from the RGB image. This is more accurate because
    the pipeline has already done clean CMYK separation with quantization.
    
    Args:
        color_mask: Binary mask for this color (H, W), 255=ink present, 0=absent
        cluster_cx: X coordinate of cluster center (in image pixels)
        cluster_cy: Y coordinate of cluster center (in image pixels)  
        search_radius: Radius to search around cluster center (in pixels)
        min_pixels: Minimum pixels required to compute valid centroid
        
    Returns:
        (centroid_x, centroid_y) if sufficient color pixels found, else None
        
    Notes:
        - Handles image boundaries by clamping search region
        - Returns None if fewer than min_pixels color pixels found
        - Uses binary mask (no weighting needed - already clean separation)
    """
    h, w = color_mask.shape[:2]
    
    # Clamp search region to image bounds
    x1 = max(0, int(cluster_cx - search_radius))
    x2 = min(w, int(cluster_cx + search_radius))
    y1 = max(0, int(cluster_cy - search_radius))
    y2 = min(h, int(cluster_cy + search_radius))
    
    # Extract local region from mask
    region = color_mask[y1:y2, x1:x2]
    
    if region.size == 0:
        return None
    
    # Binary mask - pixels where this color ink is present
    mask = region > 0
    
    # Check if enough pixels found
    pixel_count = np.sum(mask)
    if pixel_count < min_pixels:
        return None
    
    # Calculate centroid using binary mask
    region_h, region_w = region.shape[:2]
    y_coords, x_coords = np.mgrid[0:region_h, 0:region_w]
    
    # Simple centroid (all pixels weighted equally - they're already clean)
    centroid_x_local = np.sum(x_coords[mask]) / pixel_count
    centroid_y_local = np.sum(y_coords[mask]) / pixel_count
    
    # Convert back to image coordinates
    centroid_x = x1 + centroid_x_local
    centroid_y = y1 + centroid_y_local
    
    return (centroid_x, centroid_y)


def compute_color_centroid(
    source_image: np.ndarray,
    cluster_cx: float,
    cluster_cy: float,
    search_radius: float,
    color: str,
    min_pixels: int = 10,
) -> Optional[Tuple[float, float]]:
    """Find the centroid (center of mass) of color pixels within a local region.
    
    DEPRECATED: Use compute_color_centroid_from_mask() with pre-separated masks.
    
    This fallback function tries to detect colors from the RGB image directly,
    which is less accurate than using the pre-separated CMYK masks.
    
    Args:
        source_image: RGB image array (H, W, 3), uint8
        cluster_cx: X coordinate of cluster center (in image pixels)
        cluster_cy: Y coordinate of cluster center (in image pixels)  
        search_radius: Radius to search around cluster center (in pixels)
        color: Target color channel - 'cyan', 'magenta', or 'yellow'
        min_pixels: Minimum pixels required to compute valid centroid
        
    Returns:
        (centroid_x, centroid_y) if sufficient color pixels found, else None
    """
    h, w = source_image.shape[:2]
    
    # Clamp search region to image bounds
    x1 = max(0, int(cluster_cx - search_radius))
    x2 = min(w, int(cluster_cx + search_radius))
    y1 = max(0, int(cluster_cy - search_radius))
    y2 = min(h, int(cluster_cy + search_radius))
    
    # Extract local region
    region = source_image[y1:y2, x1:x2]
    
    if region.size == 0:
        return None
    
    # Convert to float for calculations
    region_float = region.astype(np.float32) / 255.0
    
    # Extract RGB channels
    r, g, b = region_float[:, :, 0], region_float[:, :, 1], region_float[:, :, 2]
    
    # Calculate CMY from RGB (subtractive color model)
    # Cyan = 1 - Red, Magenta = 1 - Green, Yellow = 1 - Blue
    if color == 'cyan':
        color_intensity = (1.0 - r) * ((g + b) / 2)
    elif color == 'magenta':
        color_intensity = (1.0 - g) * ((r + b) / 2)
    elif color == 'yellow':
        color_intensity = (1.0 - b) * ((r + g) / 2)
    else:
        raise ValueError(f"color must be 'cyan', 'magenta', or 'yellow', got '{color}'")
    
    # Apply threshold to get significant pixels only
    threshold = 0.3
    mask = color_intensity > threshold
    weights = color_intensity * mask
    
    # Check if enough pixels found
    pixel_count = np.sum(mask)
    if pixel_count < min_pixels:
        return None
    
    # Calculate weighted centroid
    total_weight = np.sum(weights)
    if total_weight == 0:
        return None
    
    # Create coordinate grids for the region
    region_h, region_w = region.shape[:2]
    y_coords, x_coords = np.mgrid[0:region_h, 0:region_w]
    
    # Weighted centroid in region coordinates
    centroid_x_local = np.sum(x_coords * weights) / total_weight
    centroid_y_local = np.sum(y_coords * weights) / total_weight
    
    # Convert back to image coordinates
    centroid_x = x1 + centroid_x_local
    centroid_y = y1 + centroid_y_local
    
    return (centroid_x, centroid_y)


def apply_centroid_position(
    petal_x: float,
    petal_y: float,
    centroid_x: float,
    centroid_y: float,
    step_size: float,
) -> Tuple[float, float]:
    """Move petal position toward the color centroid by a step fraction.
    
    This is a deterministic movement (not random) that guides the petal
    toward where its color pixels are actually located.
    
    Args:
        petal_x: Current petal X position
        petal_y: Current petal Y position
        centroid_x: Target centroid X position
        centroid_y: Target centroid Y position
        step_size: Fraction of distance to move (0.0 = stay, 1.0 = reach centroid)
        
    Returns:
        (new_x, new_y) - updated petal position
        
    Examples:
        # Move halfway to centroid
        >>> apply_centroid_position(100, 100, 120, 110, 0.5)
        (110.0, 105.0)
        
        # Full step reaches centroid
        >>> apply_centroid_position(50, 50, 150, 200, 1.0)
        (150.0, 200.0)
    """
    # Calculate displacement vector
    dx = centroid_x - petal_x
    dy = centroid_y - petal_y
    
    # Apply step fraction
    new_x = petal_x + dx * step_size
    new_y = petal_y + dy * step_size
    
    return (new_x, new_y)


def apply_centroid_jitter_from_mask(
    x: float,
    y: float,
    color_mask: np.ndarray,
    cluster_cx: float,
    cluster_cy: float,
    search_radius: float,
    step_size: float = 0.5,
    fallback_jitter: float = 0.0,
    fallback_seed: int = 0,
    fallback_algorithm: str = 'gaussian',
) -> Tuple[float, float]:
    """Apply centroid-guided position movement using pre-separated CMYK mask.
    
    PREFERRED: Uses pre-separated ink masks from separate_cmyk_inks() for
    accurate color detection. This is much more reliable than trying to
    detect colors from the RGB image.
    
    Args:
        x: Original petal X position
        y: Original petal Y position
        color_mask: Binary mask for this color (H, W), 255=ink, 0=absent
        cluster_cx: Cluster center X (for centroid search region)
        cluster_cy: Cluster center Y
        search_radius: Radius to search for color pixels
        step_size: Fraction of distance to move toward centroid (0.0-1.0)
        fallback_jitter: Jitter percentage if no centroid found (0 = no fallback)
        fallback_seed: Random seed for fallback jitter
        fallback_algorithm: 'gaussian' or 'uniform' for fallback
        
    Returns:
        (new_x, new_y) - moved petal position
    """
    # Find color centroid from pre-separated mask
    centroid = compute_color_centroid_from_mask(
        color_mask=color_mask,
        cluster_cx=cluster_cx,
        cluster_cy=cluster_cy,
        search_radius=search_radius,
    )
    
    if centroid is not None:
        # Move toward centroid
        return apply_centroid_position(
            petal_x=x,
            petal_y=y,
            centroid_x=centroid[0],
            centroid_y=centroid[1],
            step_size=step_size,
        )
    else:
        # Fallback to random jitter if configured
        if fallback_jitter > 0:
            from dotmatrix.jitter import apply_position_jitter
            return apply_position_jitter(
                x=x,
                y=y,
                position_pct=fallback_jitter,
                base_radius=search_radius,
                seed=fallback_seed,
                algorithm=fallback_algorithm,
            )
        else:
            return (x, y)


def apply_centroid_jitter(
    x: float,
    y: float,
    source_image: np.ndarray,
    cluster_cx: float,
    cluster_cy: float,
    search_radius: float,
    color: str,
    step_size: float = 0.5,
    fallback_jitter: float = 0.0,
    fallback_seed: int = 0,
    fallback_algorithm: str = 'gaussian',
) -> Tuple[float, float]:
    """Apply centroid-guided position movement with fallback to random jitter.
    
    DEPRECATED: Use apply_centroid_jitter_from_mask() with pre-separated masks.
    
    This fallback uses RGB image and tries to detect colors, which is less
    accurate than using the pre-separated CMYK masks.
    
    Args:
        x: Original petal X position
        y: Original petal Y position
        source_image: RGB source image for centroid calculation
        cluster_cx: Cluster center X (for centroid search region)
        cluster_cy: Cluster center Y
        search_radius: Radius to search for color pixels
        color: Target color ('cyan', 'magenta', 'yellow')
        step_size: Fraction of distance to move toward centroid (0.0-1.0)
        fallback_jitter: Jitter percentage if no centroid found (0 = no fallback)
        fallback_seed: Random seed for fallback jitter
        fallback_algorithm: 'gaussian' or 'uniform' for fallback
        
    Returns:
        (new_x, new_y) - moved petal position
    """
    # Try to find color centroid
    centroid = compute_color_centroid(
        source_image=source_image,
        cluster_cx=cluster_cx,
        cluster_cy=cluster_cy,
        search_radius=search_radius,
        color=color,
    )
    
    if centroid is not None:
        # Move toward centroid
        return apply_centroid_position(
            petal_x=x,
            petal_y=y,
            centroid_x=centroid[0],
            centroid_y=centroid[1],
            step_size=step_size,
        )
    else:
        # Fallback to random jitter if configured
        if fallback_jitter > 0:
            from dotmatrix.jitter import apply_position_jitter
            return apply_position_jitter(
                x=x,
                y=y,
                position_pct=fallback_jitter,
                base_radius=search_radius,  # Use search radius as reference
                seed=fallback_seed,
                algorithm=fallback_algorithm,
            )
        else:
            # No fallback, return original position
            return (x, y)
