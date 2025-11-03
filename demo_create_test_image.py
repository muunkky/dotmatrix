#!/usr/bin/env python3
"""Create a test image with multiple colored circles for demo."""

import cv2
import numpy as np
from pathlib import Path

# Create 800x600 white image
image = np.ones((600, 800, 3), dtype=np.uint8) * 255

# Draw circles with different colors and spacing
circles = [
    # (center_x, center_y, radius, color_bgr)
    (150, 150, 60, (255, 0, 0)),    # Blue - large
    (400, 150, 60, (255, 0, 0)),    # Blue - large, far from first
    (150, 400, 60, (0, 255, 0)),    # Green - large
    (400, 400, 60, (0, 0, 255)),    # Red - large
    (600, 300, 45, (255, 255, 0)),  # Cyan - medium
    (250, 250, 25, (128, 128, 128)), # Gray - small (close to first blue)
    (300, 180, 30, (0, 128, 255)),  # Orange - medium
    (650, 150, 50, (255, 0, 255)),  # Magenta - large
]

# Draw filled circles
for cx, cy, radius, color in circles:
    cv2.circle(image, (cx, cy), radius, color, -1)

# Draw border around each circle for visibility
for cx, cy, radius, color in circles:
    cv2.circle(image, (cx, cy), radius, (0, 0, 0), 2)

# Save image
output_path = Path(__file__).parent / "demo_circles.png"
cv2.imwrite(str(output_path), image)
print(f"Created test image: {output_path}")
print(f"Contains {len(circles)} circles with various colors and sizes")
