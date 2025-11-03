"""Extract colors from detected circles."""

from typing import Tuple, List, Optional
import numpy as np
import cv2
from .circle_detector import Circle


def extract_color(
    image: np.ndarray,
    circle: Circle,
    use_edge_sampling: bool = False,
    num_samples: int = 36,
    edge_method: str = "circumference",
    all_circles: Optional[List[Circle]] = None
) -> Tuple[int, int, int]:
    """Extract the RGB color of a circle using area or edge sampling.

    Creates a circular mask and samples pixels within the circle boundary,
    or samples points along the circle's edge/perimeter.
    Converts BGR (OpenCV format) to RGB for output.

    Args:
        image: Input image as BGR numpy array (height, width, 3)
        circle: Detected circle with center coordinates and radius
        use_edge_sampling: If True, sample colors from circle edge instead of area.
                          Edge sampling is better for overlapping circles (default: False)
        num_samples: Number of evenly-spaced points to sample around edge (default: 36)
        edge_method: Method for edge sampling (default: "circumference"):
                    - "circumference": Sample evenly around full circle
                    - "canny": Sample from actual Canny edge pixels
                    - "exposed": Sample only from exposed arcs (not occluded)
                    - "band": Sample from edge pixel band
        all_circles: List of all detected circles (required for "exposed" method)

    Returns:
        RGB tuple (r, g, b) with integer values in range 0-255

    Raises:
        ValueError: If image is invalid or circle has invalid parameters

    Example:
        >>> image = load_image("photo.png")
        >>> circle = Circle(center_x=100, center_y=100, radius=50)
        >>> color = extract_color(image, circle)
        >>> print(f"RGB: {color}")
        RGB: (255, 100, 50)

        >>> # For overlapping circles, use edge sampling
        >>> edge_color = extract_color(image, circle, use_edge_sampling=True)

        >>> # Use Canny edges for most accurate color
        >>> canny_color = extract_color(image, circle, use_edge_sampling=True, edge_method="canny")
    """
    # Validate inputs
    if image.size == 0:
        raise ValueError("Image is empty")

    if len(image.shape) != 3 or image.shape[2] != 3:
        raise ValueError(f"Image must be 3-channel BGR, got shape {image.shape}")

    if circle.radius <= 0:
        raise ValueError(f"Circle radius must be positive, got {circle.radius}")

    height, width = image.shape[:2]

    if use_edge_sampling:
        center_x = circle.center_x
        center_y = circle.center_y
        radius = circle.radius

        if edge_method == "canny":
            # Method 1: Sample from actual Canny edge pixels
            return _extract_color_from_canny_edges(image, circle, width, height)

        elif edge_method == "exposed":
            # Method 2: Sample only from exposed (non-occluded) arcs
            if all_circles is None:
                raise ValueError("all_circles parameter required for 'exposed' method")
            return _extract_color_from_exposed_arcs(image, circle, all_circles, num_samples, width, height)

        elif edge_method == "band":
            # Method 3: Sample from edge pixel band
            return _extract_color_from_edge_band(image, circle, width, height)

        else:  # "circumference" (default)
            # Original method: Edge-based sampling around full circumference
            # Generate evenly-spaced angles around the circle (0 to 2π)
            angles = np.linspace(0, 2 * np.pi, num_samples, endpoint=False)

            # Calculate (x, y) coordinates for each sample point
            sample_x = center_x + radius * np.cos(angles)
            sample_y = center_y + radius * np.sin(angles)

            # Clip coordinates to image bounds
            sample_x = np.clip(sample_x, 0, width - 1)
            sample_y = np.clip(sample_y, 0, height - 1)

            # Convert to integer coordinates
            sample_x = sample_x.astype(int)
            sample_y = sample_y.astype(int)

            # Extract colors at sample points
            sampled_colors = image[sample_y, sample_x]  # Shape: (num_samples, 3) in BGR

            # Calculate median color (more robust than mean for edge sampling)
            median_bgr = np.median(sampled_colors, axis=0)

            # Convert BGR to RGB and round to integers
            b, g, r = median_bgr
            rgb = (int(round(r)), int(round(g)), int(round(b)))

            # Ensure values are in valid range
            rgb = tuple(max(0, min(255, v)) for v in rgb)

            return rgb

    else:
        # Area-based sampling: average all pixels within the circle
        # Create a mask for the circle
        mask = np.zeros((height, width), dtype=np.uint8)

        # Draw filled circle on mask
        center = (int(circle.center_x), int(circle.center_y))
        radius = int(circle.radius)

        cv2.circle(mask, center, radius, 255, -1)  # -1 fills the circle

        # Extract pixels within the circle using the mask
        masked_pixels = cv2.bitwise_and(image, image, mask=mask)

        # Get only non-zero pixels (pixels inside the circle)
        pixels_in_circle = masked_pixels[mask > 0]

        # Check if we have any pixels
        if len(pixels_in_circle) == 0:
            # Circle is completely outside image bounds
            return (0, 0, 0)

        # Calculate mean color in BGR
        mean_bgr = np.mean(pixels_in_circle, axis=0)

        # Convert BGR to RGB and round to integers
        b, g, r = mean_bgr
        rgb = (int(round(r)), int(round(g)), int(round(b)))

        # Ensure values are in valid range
        rgb = tuple(max(0, min(255, v)) for v in rgb)

        return rgb


def _extract_color_from_canny_edges(
    image: np.ndarray,
    circle: Circle,
    width: int,
    height: int
) -> Tuple[int, int, int]:
    """Extract color by sampling from actual Canny edge pixels.

    This method runs Canny edge detection and samples colors from detected
    edge pixels that fall within a band around the circle's radius.
    Most aligned with how HoughCircles detects circles.

    Args:
        image: BGR image array
        circle: Circle to extract color from
        width: Image width
        height: Image height

    Returns:
        RGB color tuple
    """
    # Convert to grayscale for Canny edge detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise (same as circle_detector)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    # Run Canny edge detection with same params as HoughCircles default
    edges = cv2.Canny(blurred, 50, 150)

    # Find all edge pixel coordinates
    edge_y, edge_x = np.where(edges > 0)

    if len(edge_x) == 0:
        # No edges detected, fall back to area sampling
        return _fallback_area_sampling(image, circle, width, height)

    # Calculate distance of each edge pixel from circle center
    center_x = circle.center_x
    center_y = circle.center_y
    radius = circle.radius

    distances = np.sqrt((edge_x - center_x)**2 + (edge_y - center_y)**2)

    # Find edge pixels within a band around the circle radius (±3 pixels)
    band_width = 3
    mask = np.abs(distances - radius) <= band_width

    if not np.any(mask):
        # No edge pixels near this circle, fall back to area sampling
        return _fallback_area_sampling(image, circle, width, height)

    # Get edge pixels within the band
    edge_x_filtered = edge_x[mask]
    edge_y_filtered = edge_y[mask]

    # Sample colors from these edge pixels
    sampled_colors = image[edge_y_filtered, edge_x_filtered]

    # Calculate median color
    median_bgr = np.median(sampled_colors, axis=0)

    # Convert BGR to RGB
    b, g, r = median_bgr
    rgb = (int(round(r)), int(round(g)), int(round(b)))

    # Ensure values are in valid range
    rgb = tuple(max(0, min(255, v)) for v in rgb)

    return rgb


def _extract_color_from_exposed_arcs(
    image: np.ndarray,
    circle: Circle,
    all_circles: List[Circle],
    num_samples: int,
    width: int,
    height: int
) -> Tuple[int, int, int]:
    """Extract color by sampling only from exposed (non-occluded) arcs.

    Detects which portions of the circle's circumference are visible
    (not covered by other circles) and samples only from those exposed arcs.

    Args:
        image: BGR image array
        circle: Circle to extract color from
        all_circles: All detected circles (for occlusion detection)
        num_samples: Number of sample points to check around circumference
        width: Image width
        height: Image height

    Returns:
        RGB color tuple
    """
    center_x = circle.center_x
    center_y = circle.center_y
    radius = circle.radius

    # Generate sample points around full circumference
    angles = np.linspace(0, 2 * np.pi, num_samples, endpoint=False)
    sample_x = center_x + radius * np.cos(angles)
    sample_y = center_y + radius * np.sin(angles)

    # Clip to image bounds
    sample_x = np.clip(sample_x, 0, width - 1)
    sample_y = np.clip(sample_y, 0, height - 1)

    # Convert to integer coordinates
    sample_x = sample_x.astype(int)
    sample_y = sample_y.astype(int)

    # Determine which sample points are NOT occluded by other circles
    exposed_mask = np.ones(num_samples, dtype=bool)

    for other_circle in all_circles:
        # Skip the circle itself
        if (other_circle.center_x == circle.center_x and
            other_circle.center_y == circle.center_y and
            other_circle.radius == circle.radius):
            continue

        # Check if this circle is in front (larger radius = drawn later = in front)
        # If other circle is smaller, it's behind us, so skip
        if other_circle.radius <= circle.radius:
            continue

        # Calculate distance from sample points to other circle's center
        dist_to_other = np.sqrt(
            (sample_x - other_circle.center_x)**2 +
            (sample_y - other_circle.center_y)**2
        )

        # Sample point is occluded if it's inside the other circle
        occluded = dist_to_other < other_circle.radius
        exposed_mask &= ~occluded

    # If no exposed points, fall back to all points
    if not np.any(exposed_mask):
        exposed_mask = np.ones(num_samples, dtype=bool)

    # Sample colors only from exposed points
    exposed_x = sample_x[exposed_mask]
    exposed_y = sample_y[exposed_mask]
    sampled_colors = image[exposed_y, exposed_x]

    # Calculate median color
    median_bgr = np.median(sampled_colors, axis=0)

    # Convert BGR to RGB
    b, g, r = median_bgr
    rgb = (int(round(r)), int(round(g)), int(round(b)))

    # Ensure values are in valid range
    rgb = tuple(max(0, min(255, v)) for v in rgb)

    return rgb


def _extract_color_from_edge_band(
    image: np.ndarray,
    circle: Circle,
    width: int,
    height: int
) -> Tuple[int, int, int]:
    """Extract color by sampling from edge pixel band.

    Samples all pixels within a thin annular band around the circle's
    radius (radius ± 3 pixels), without restricting to specific angles.

    Args:
        image: BGR image array
        circle: Circle to extract color from
        width: Image width
        height: Image height

    Returns:
        RGB color tuple
    """
    center_x = circle.center_x
    center_y = circle.center_y
    radius = circle.radius

    # Define band width
    band_width = 3
    inner_radius = max(0, radius - band_width)
    outer_radius = radius + band_width

    # Create coordinate grids
    y_coords, x_coords = np.ogrid[:height, :width]

    # Calculate distance from each pixel to circle center
    distances = np.sqrt((x_coords - center_x)**2 + (y_coords - center_y)**2)

    # Create mask for pixels in the band
    band_mask = (distances >= inner_radius) & (distances <= outer_radius)

    # Get pixels within the band
    pixels_in_band = image[band_mask]

    if len(pixels_in_band) == 0:
        # No pixels in band, fall back to area sampling
        return _fallback_area_sampling(image, circle, width, height)

    # Calculate median color
    median_bgr = np.median(pixels_in_band, axis=0)

    # Convert BGR to RGB
    b, g, r = median_bgr
    rgb = (int(round(r)), int(round(g)), int(round(b)))

    # Ensure values are in valid range
    rgb = tuple(max(0, min(255, v)) for v in rgb)

    return rgb


def _fallback_area_sampling(
    image: np.ndarray,
    circle: Circle,
    width: int,
    height: int
) -> Tuple[int, int, int]:
    """Fallback to area-based sampling when edge methods fail.

    Args:
        image: BGR image array
        circle: Circle to extract color from
        width: Image width
        height: Image height

    Returns:
        RGB color tuple
    """
    # Create a mask for the circle
    mask = np.zeros((height, width), dtype=np.uint8)

    # Draw filled circle on mask
    center = (int(circle.center_x), int(circle.center_y))
    radius = int(circle.radius)

    cv2.circle(mask, center, radius, 255, -1)

    # Extract pixels within the circle
    masked_pixels = cv2.bitwise_and(image, image, mask=mask)
    pixels_in_circle = masked_pixels[mask > 0]

    if len(pixels_in_circle) == 0:
        return (0, 0, 0)

    # Instead of averaging, find the most common exact color
    # This avoids anti-aliasing issues with overlapping circles
    from collections import Counter

    # Convert BGR pixels to RGB tuples
    rgb_pixels = [(int(p[2]), int(p[1]), int(p[0])) for p in pixels_in_circle]

    # Find most common color
    color_counts = Counter(rgb_pixels)
    most_common_color = color_counts.most_common(1)[0][0]

    return most_common_color


def extract_color_with_palette(
    image: np.ndarray,
    circle,
    palette: List[Tuple[int, int, int]],
    use_edge_sampling: bool = False,
    num_samples: int = 32,
    edge_method: str = 'circumference',
    all_circles: List = None,
    max_distance: float = 30.0
) -> Tuple[int, int, int]:
    """Extract color by finding which palette color appears most frequently.

    Instead of sampling and averaging, this counts how many pixels along the
    edge match each palette color (within max_distance threshold).

    Args:
        image: Input image (BGR format from OpenCV)
        circle: Circle object with center_x, center_y, radius
        palette: List of exact RGB colors to look for
        use_edge_sampling: Whether to sample edge or full circle area
        num_samples: Number of points to sample around edge
        edge_method: 'circumference', 'canny', 'exposed', or 'band'
        all_circles: List of all circles (needed for 'exposed' method)
        max_distance: Maximum RGB distance to consider a pixel as matching a palette color

    Returns:
        The palette color that appears most frequently, or (0,0,0) if no matches
    """
    from collections import Counter

    cx, cy, radius = int(circle.center_x), int(circle.center_y), int(circle.radius)

    # Sample points around circumference
    angles = np.linspace(0, 2 * np.pi, num_samples, endpoint=False)

    sampled_pixels = []
    for angle in angles:
        x = int(cx + radius * np.cos(angle))
        y = int(cy + radius * np.sin(angle))

        if 0 <= y < image.shape[0] and 0 <= x < image.shape[1]:
            pixel_bgr = image[y, x]
            pixel_rgb = (int(pixel_bgr[2]), int(pixel_bgr[1]), int(pixel_bgr[0]))
            sampled_pixels.append(pixel_rgb)

    if not sampled_pixels:
        return (0, 0, 0)

    # Count how many pixels match each palette color
    palette_counts = [0] * len(palette)
    for pixel in sampled_pixels:
        for i, pal_color in enumerate(palette):
            dist = np.linalg.norm(np.array(pixel) - np.array(pal_color))
            if dist <= max_distance:
                palette_counts[i] += 1
                break  # Only count first match

    # Return the palette color with most matches
    # Apply bias: prefer non-black colors if they're within 80% of black's count
    # This handles overlapping where black circles cover colored circles
    if max(palette_counts) > 0:
        # Find darkest color (likely black/gray) - sum of RGB values < 50
        darkest_idx = None
        for i, pal_color in enumerate(palette):
            if sum(pal_color) < 50:  # Very dark color
                darkest_idx = i
                break

        # If darkest color wins, check if any other color is close
        raw_best_idx = np.argmax(palette_counts)
        if darkest_idx is not None and raw_best_idx == darkest_idx and palette_counts[darkest_idx] > 0:
            # Find highest-scoring non-dark color
            max_non_dark = 0
            max_non_dark_idx = None
            for i, count in enumerate(palette_counts):
                if i != darkest_idx and count > max_non_dark:
                    max_non_dark = count
                    max_non_dark_idx = i

            # If non-dark color is within 75% of dark color's score, prefer it
            if max_non_dark_idx is not None and max_non_dark >= 0.75 * palette_counts[darkest_idx]:
                best_idx = max_non_dark_idx
                return palette[best_idx]

        best_idx = raw_best_idx
        return palette[best_idx]
    else:
        # No palette colors found, return most common sampled color
        color_counter = Counter(sampled_pixels)
        return color_counter.most_common(1)[0][0]
