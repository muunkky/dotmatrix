#!/usr/bin/env python3
"""Test hybrid approach: detect on full image, assign colors from separated images."""

import sys
import cv2
import numpy as np
from pathlib import Path

sys.path.insert(0, 'src')

from dotmatrix.circle_detector import detect_circles
from dotmatrix.color_separation import get_dominant_colors, separate_by_color

# Load image
img = cv2.imread('test_dotmatrix.png')
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

print("=" * 60)
print("Testing Hybrid Approach")
print("=" * 60)
print()

# Step 1: Detect circles on FULL image (complete circles)
print("Step 1: Detecting circles on full image...")
circles = detect_circles(
    img_rgb,
    min_radius=30,
    min_distance=50,
    sensitivity='strict'
)
print(f"Detected {len(circles)} complete circles")
print()

# Step 2: Get dominant colors
print("Step 2: Finding dominant colors...")
colors = get_dominant_colors(img_rgb, n_colors=4, exclude_background=True)
print(f"Found {len(colors)} dominant colors:")
for i, color in enumerate(colors, 1):
    print(f"  {i}. RGB{color}")
print()

# Step 3: Separate by color
print("Step 3: Separating image by color...")
separated = separate_by_color(img_rgb, colors, tolerance=30)
print()

# Step 4: Assign each circle to a color by checking separated images
print("Step 4: Assigning colors to detected circles...")
print()

results = []
for i, circle in enumerate(circles, 1):
    cx, cy, r = int(circle.center_x), int(circle.center_y), int(circle.radius)

    # For each color, count how many non-white pixels are in the circle area
    color_scores = {}
    for color, color_img in separated.items():
        # Create circular mask
        mask = np.zeros(color_img.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (cx, cy), r, 255, -1)

        # Count non-white pixels in this circle area
        gray = cv2.cvtColor(color_img, cv2.COLOR_RGB2GRAY)
        non_white = np.sum((gray < 250) & (mask > 0))

        color_scores[color] = non_white

    # Assign to color with most pixels
    best_color = max(color_scores.items(), key=lambda x: x[1])
    assigned_color, pixel_count = best_color

    results.append((circle, assigned_color))

    print(f"Circle {i} at ({cx}, {cy}) r={r}:")
    for color, count in sorted(color_scores.items(), key=lambda x: -x[1]):
        marker = " <-- ASSIGNED" if color == assigned_color else ""
        print(f"  RGB{color}: {count:,} pixels{marker}")

print()
print("=" * 60)
print("Summary")
print("=" * 60)

from collections import Counter
color_counts = Counter([color for _, color in results])
print(f"\nTotal circles: {len(results)}")
print("Circles per color:")
for color, count in sorted(color_counts.items()):
    print(f"  RGB{color}: {count} circles")
