#!/usr/bin/env python3
"""Test color separation approach for CMYK circles."""

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
print("Testing Color Separation Approach")
print("=" * 60)
print()

# Get dominant colors
print("Step 1: Finding dominant colors...")
colors = get_dominant_colors(img_rgb, n_colors=4, exclude_background=True)
print(f"Found {len(colors)} colors:")
for i, color in enumerate(colors, 1):
    print(f"  {i}. RGB{color}")
print()

# Separate by color
print("Step 2: Separating image by color...")
separated = separate_by_color(img_rgb, colors, tolerance=30)
print()

# Detect circles in each separated image
print("Step 3: Detecting circles in each color-separated image...")
all_results = []
for i, (color, color_img) in enumerate(separated.items(), 1):
    circles = detect_circles(
        color_img,
        min_radius=30,
        min_distance=50,
        sensitivity='strict'
    )
    print(f"  Color {i} RGB{color}: {len(circles)} circles")
    all_results.extend([(circle, color) for circle in circles])

    # Save separated image for inspection
    output_dir = Path('demo_results/color_sep_test')
    output_dir.mkdir(parents=True, exist_ok=True)
    r, g, b = color
    filename = output_dir / f"separated_{r:03d}_{g:03d}_{b:03d}.png"
    cv2.imwrite(str(filename), cv2.cvtColor(color_img, cv2.COLOR_RGB2BGR))

print()
print(f"Total circles detected: {len(all_results)}")
print()

# Count circles per color
from collections import Counter
color_counts = Counter([color for _, color in all_results])
print("Circles per color:")
for color, count in sorted(color_counts.items()):
    print(f"  RGB{color}: {count} circles")
print()

print(f"Separated images saved to: demo_results/color_sep_test/")
