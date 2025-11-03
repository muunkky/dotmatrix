"""Format detection results as JSON or CSV."""

import json
import csv
from io import StringIO
from typing import List, Tuple
from .circle_detector import Circle


def format_json(circles: List[Tuple[Circle, Tuple[int, int, int]]]) -> str:
    """Format detection results as JSON.

    Args:
        circles: List of (Circle, RGB color) tuples

    Returns:
        JSON string with format:
        [{"center": [x, y], "radius": r, "color": [r, g, b], "confidence": c}, ...]
    """
    results = []
    for circle, color in circles:
        results.append({
            "center": [circle.center_x, circle.center_y],
            "radius": circle.radius,
            "color": list(color),
            "confidence": circle.confidence
        })
    return json.dumps(results, indent=2)


def format_csv(circles: List[Tuple[Circle, Tuple[int, int, int]]]) -> str:
    """Format detection results as CSV.

    Args:
        circles: List of (Circle, RGB color) tuples

    Returns:
        CSV string with headers:
        center_x,center_y,radius,color_r,color_g,color_b,confidence
    """
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['center_x', 'center_y', 'radius', 'color_r', 'color_g', 'color_b', 'confidence'])

    # Write data rows
    for circle, color in circles:
        writer.writerow([
            circle.center_x,
            circle.center_y,
            circle.radius,
            color[0],
            color[1],
            color[2],
            circle.confidence
        ])

    return output.getvalue()
