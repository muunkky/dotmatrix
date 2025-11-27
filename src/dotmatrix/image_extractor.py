"""Extract circles to separate PNG images with transparent backgrounds."""

from pathlib import Path
from typing import List, Tuple, Dict
import numpy as np
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
