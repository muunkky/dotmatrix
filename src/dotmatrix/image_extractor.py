"""Extract circles to separate PNG images with transparent backgrounds."""

from pathlib import Path
from typing import List, Tuple, Dict
import numpy as np
import cv2
from PIL import Image, ImageDraw
from collections import defaultdict

from .circle_detector import Circle
from .color_clustering import cluster_colors


# CMYK color name mappings for layer file naming
CMYK_COLOR_NAMES = {
    'cyan': [(0, 255, 255), (0, 200, 200), (0, 180, 180)],
    'magenta': [(255, 0, 255), (200, 0, 200), (180, 0, 180)],
    'yellow': [(255, 255, 0), (200, 200, 0), (180, 180, 0)],
    'black': [(0, 0, 0), (30, 30, 30), (50, 50, 50), (20, 20, 20)],
}


def get_cmyk_layer_name(color: Tuple[int, int, int], tolerance: int = 60) -> str:
    """Map an RGB color to its CMYK layer name.

    Args:
        color: RGB tuple
        tolerance: Maximum color distance to match

    Returns:
        Layer name ('cyan', 'magenta', 'yellow', 'black') or None if no match
    """
    for layer_name, reference_colors in CMYK_COLOR_NAMES.items():
        for ref_color in reference_colors:
            distance = sum(abs(a - b) for a, b in zip(color, ref_color))
            if distance <= tolerance * 3:
                return layer_name
    return None


def generate_cmyk_layer_files(
    circles_with_colors: List[Tuple[Circle, Tuple[int, int, int]]],
    image_shape: Tuple[int, int],
    output_dir: Path,
    tolerance: int = 60
) -> Dict[str, Path]:
    """Generate CMYK layer files (cyan.png, magenta.png, yellow.png, black.png).

    Creates composite images for each CMYK channel showing all circles
    of that color at their detected positions and sizes.

    Args:
        circles_with_colors: List of (Circle, RGB color) tuples
        image_shape: Original image shape (height, width)
        output_dir: Directory to save layer files
        tolerance: Color matching tolerance for CMYK classification

    Returns:
        Dictionary mapping layer name to file path

    Example:
        >>> circles = [(Circle(100, 100, 50), (0, 255, 255))]  # Cyan circle
        >>> layers = generate_cmyk_layer_files(circles, (300, 300), Path("output"))
        >>> print(layers)
        {'cyan': Path('output/cyan.png')}
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    height, width = image_shape

    # Group circles by CMYK layer
    layer_circles: Dict[str, List[Tuple[Circle, Tuple[int, int, int]]]] = {
        'cyan': [],
        'magenta': [],
        'yellow': [],
        'black': [],
    }

    for circle, color in circles_with_colors:
        layer_name = get_cmyk_layer_name(color, tolerance)
        if layer_name:
            layer_circles[layer_name].append((circle, color))

    created_files = {}

    # Create layer images for each CMYK channel
    for layer_name, circles in layer_circles.items():
        if not circles:
            continue

        # Create transparent image (RGBA)
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw all circles for this layer
        for circle, color in circles:
            left = int(circle.center_x - circle.radius)
            top = int(circle.center_y - circle.radius)
            right = int(circle.center_x + circle.radius)
            bottom = int(circle.center_y + circle.radius)

            # Use the original detected color with full opacity
            rgba_color = color + (255,)
            draw.ellipse([left, top, right, bottom], fill=rgba_color, outline=rgba_color)

        # Save with layer name
        filepath = output_dir / f"{layer_name}.png"
        img.save(filepath, 'PNG')
        created_files[layer_name] = filepath

    return created_files


def group_circles_by_color(
    circles_with_colors: List[Tuple[Circle, Tuple[int, int, int]]],
    tolerance: int = 20
) -> Dict[Tuple[int, int, int], List[Circle]]:
    """Group circles by similar colors.

    Groups circles with similar RGB values together using a tolerance threshold.

    Args:
        circles_with_colors: List of (Circle, RGB color) tuples
        tolerance: Maximum RGB difference to consider colors similar (default: 20)

    Returns:
        Dictionary mapping representative color to list of circles

    Example:
        >>> circles = [(Circle(100, 100, 50), (255, 0, 0)),
        ...            (Circle(200, 200, 50), (250, 5, 5))]
        >>> groups = group_circles_by_color(circles, tolerance=20)
        >>> len(groups)  # Both reds grouped together
        1
    """
    color_groups = {}

    for circle, color in circles_with_colors:
        # Find if this color matches any existing group
        matched = False
        for group_color in color_groups.keys():
            # Calculate color distance
            distance = sum(abs(a - b) for a, b in zip(color, group_color))
            if distance <= tolerance * 3:  # tolerance per channel
                color_groups[group_color].append(circle)
                matched = True
                break

        if not matched:
            # Create new color group
            color_groups[color] = [circle]

    return color_groups


def extract_circles_to_images(
    circles_with_colors: List[Tuple[Circle, Tuple[int, int, int]]],
    image_shape: Tuple[int, int],
    output_dir: Path,
    prefix: str = "circles",
    tolerance: int = 20,
    max_colors: int = None
) -> List[Path]:
    """Extract circles to separate PNG images grouped by color.

    Creates one PNG per color group with transparent background.
    Each PNG contains all circles of that color as filled circles.

    Args:
        circles_with_colors: List of (Circle, RGB color) tuples
        image_shape: Original image shape (height, width)
        output_dir: Directory to save extracted images
        prefix: Filename prefix (default: "circles")
        tolerance: Color grouping tolerance (default: 20)
        max_colors: If specified, use k-means clustering to reduce to N colors
                   (overrides tolerance-based grouping)

    Returns:
        List of paths to created PNG files

    Example:
        >>> circles = [(Circle(100, 100, 50), (255, 0, 0))]
        >>> paths = extract_circles_to_images(circles, (300, 300), Path("output"))

        >>> # Use k-means to reduce to 4 color groups
        >>> paths = extract_circles_to_images(circles, (300, 300), Path("output"), max_colors=4)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # If max_colors specified, use k-means clustering
    if max_colors is not None:
        # Extract all unique colors
        unique_colors = list(set(color for _, color in circles_with_colors))

        # Cluster colors using k-means
        color_mapping = cluster_colors(unique_colors, n_clusters=max_colors)

        # Remap circles to cluster colors
        clustered_circles = defaultdict(list)
        for circle, original_color in circles_with_colors:
            cluster_color = color_mapping[original_color]
            clustered_circles[cluster_color].append(circle)

        color_groups = dict(clustered_circles)
    else:
        # Use tolerance-based grouping
        color_groups = group_circles_by_color(circles_with_colors, tolerance)

    created_files = []
    height, width = image_shape

    # Create one image per color group
    for idx, (color, circles) in enumerate(sorted(color_groups.items())):
        # Create transparent image (RGBA)
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw all circles of this color
        for circle in circles:
            # Calculate bounding box for ellipse
            left = int(circle.center_x - circle.radius)
            top = int(circle.center_y - circle.radius)
            right = int(circle.center_x + circle.radius)
            bottom = int(circle.center_y + circle.radius)

            # Draw filled circle with the color (fully opaque)
            rgba_color = color + (255,)  # Add alpha channel
            draw.ellipse([left, top, right, bottom], fill=rgba_color, outline=rgba_color)

        # Generate filename with color info
        r, g, b = color
        filename = f"{prefix}_color_{r:03d}_{g:03d}_{b:03d}.png"
        filepath = output_dir / filename

        # Save image
        img.save(filepath, 'PNG')
        created_files.append(filepath)

    return created_files


def generate_composite_image(
    circles_with_colors: List[Tuple[Circle, Tuple[int, int, int]]],
    image_shape: Tuple[int, int],
    output_dir: Path
) -> Path:
    """Generate a composite image showing all detected circles for visual QA.

    Creates a single image with all detected circles rendered at their
    positions with their detected colors on a white background.

    Args:
        circles_with_colors: List of (Circle, RGB color) tuples
        image_shape: Original image shape (height, width)
        output_dir: Directory to save the composite image

    Returns:
        Path to the created composite.png file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    height, width = image_shape

    # Create white background image
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw all circles
    for circle, color in circles_with_colors:
        left = int(circle.center_x - circle.radius)
        top = int(circle.center_y - circle.radius)
        right = int(circle.center_x + circle.radius)
        bottom = int(circle.center_y + circle.radius)

        draw.ellipse([left, top, right, bottom], fill=color, outline=color)

    filepath = output_dir / "composite.png"
    img.save(filepath, 'PNG')
    return filepath


def generate_diff_image(
    source_image: np.ndarray,
    circles_with_colors: List[Tuple[Circle, Tuple[int, int, int]]],
    output_dir: Path,
    mode: str = "highlight"
) -> Path:
    """Generate a diff image showing regions missed by detection.

    Compares the source image with the detected circles to highlight
    regions that weren't captured by the detection algorithm.

    Args:
        source_image: Original source image (numpy array, RGB)
        circles_with_colors: List of (Circle, RGB color) tuples
        output_dir: Directory to save the diff image
        mode: Diff visualization mode:
            - "highlight": Show missed regions with bright highlight
            - "mask": Show original colors of missed regions

    Returns:
        Path to the created diff.png file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    height, width = source_image.shape[:2]

    # Create mask of detected circles
    detected_mask = np.zeros((height, width), dtype=np.uint8)

    for circle, color in circles_with_colors:
        # Draw filled circle on mask
        y, x = np.ogrid[:height, :width]
        dist_sq = (x - circle.center_x)**2 + (y - circle.center_y)**2
        circle_mask = dist_sq <= circle.radius**2
        detected_mask[circle_mask] = 255

    # Find missed regions (non-white pixels not covered by detection)
    # Assume white background (255, 255, 255)
    is_white = np.all(source_image >= 250, axis=2)
    is_detected = detected_mask > 0
    is_missed = ~is_white & ~is_detected

    if mode == "mask":
        # Show original colors of missed regions, black elsewhere
        diff_img = np.zeros_like(source_image)
        diff_img[is_missed] = source_image[is_missed]
    else:
        # Highlight mode: show missed regions in bright magenta
        diff_img = np.full_like(source_image, 255)  # White background
        diff_img[is_missed] = [255, 0, 255]  # Magenta highlight

    # Save as PIL image
    img = Image.fromarray(diff_img)
    filepath = output_dir / "diff.png"
    img.save(filepath, 'PNG')
    return filepath


def generate_composite_from_images(
    source_image: np.ndarray,
    rendered_image: np.ndarray,
    output_dir: Path,
    alpha: float = 0.5
) -> Path:
    """Generate a composite overlay blending source and rendered images.

    Creates a 50/50 blend of the source and rendered images for visual
    comparison of detection and rendering quality.

    Args:
        source_image: Original source image (numpy array, BGR)
        rendered_image: Rendered/reconstituted image (numpy array, BGR)
        output_dir: Directory to save the composite image
        alpha: Blend factor (0=source only, 1=rendered only, 0.5=equal blend)

    Returns:
        Path to the created composite.png file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle size mismatch (e.g., if render_scale != 1)
    if source_image.shape[:2] != rendered_image.shape[:2]:
        # Resize source to match rendered
        rendered_h, rendered_w = rendered_image.shape[:2]
        source_resized = cv2.resize(source_image, (rendered_w, rendered_h))
    else:
        source_resized = source_image

    # Blend images
    composite = cv2.addWeighted(source_resized, 1 - alpha, rendered_image, alpha, 0)

    filepath = output_dir / "composite.png"
    cv2.imwrite(str(filepath), composite)
    return filepath


def generate_diff_from_images(
    source_image: np.ndarray,
    rendered_image: np.ndarray,
    output_dir: Path,
    amplify: int = 3
) -> Path:
    """Generate a diff image showing pixel differences between source and rendered.

    Creates an image showing |source - rendered| per pixel, optionally amplified
    for visibility. Useful for identifying rendering errors and coverage gaps.

    Args:
        source_image: Original source image (numpy array, BGR)
        rendered_image: Rendered/reconstituted image (numpy array, BGR)
        output_dir: Directory to save the diff image
        amplify: Multiplier for diff values to make small errors visible

    Returns:
        Path to the created diff.png file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle size mismatch
    if source_image.shape[:2] != rendered_image.shape[:2]:
        rendered_h, rendered_w = rendered_image.shape[:2]
        source_resized = cv2.resize(source_image, (rendered_w, rendered_h))
    else:
        source_resized = source_image

    # Calculate absolute difference
    diff = cv2.absdiff(source_resized, rendered_image)

    # Amplify for visibility
    if amplify > 1:
        diff = np.clip(diff.astype(np.int32) * amplify, 0, 255).astype(np.uint8)

    filepath = output_dir / "diff.png"
    cv2.imwrite(str(filepath), diff)
    return filepath
