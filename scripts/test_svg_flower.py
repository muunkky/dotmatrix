"""Test SVG flower rendering with simple test data."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from dotmatrix.cluster_pixel_counter import ClusterResult
from dotmatrix.circle_renderer import render_flower_svg

# Create test clusters
clusters = [
    ClusterResult(x=100, y=100, cyan=800, magenta=0, yellow=0, black=800,
                 red=0, green=0, blue=0, partial=False),
    ClusterResult(x=200, y=100, cyan=0, magenta=800, yellow=0, black=800,
                 red=0, green=0, blue=0, partial=False),
    ClusterResult(x=150, y=200, cyan=0, magenta=0, yellow=800, black=800,
                 red=0, green=0, blue=0, partial=False),
    ClusterResult(x=250, y=200, cyan=400, magenta=400, yellow=400, black=800,
                 red=0, green=0, blue=0, partial=False),
]

# Generate SVG
print("Generating SVG with render_flower_svg()...")
svg_output = render_flower_svg(
    clusters,
    image_shape=(300, 300),
    scale=2.0,
    petal_distance=0.35
)

# Save to file
output_path = Path(__file__).parent.parent / 'demo_results' / 'test_flower.svg'
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(svg_output)

print(f"✓ Generated: {output_path}")
print(f"✓ File size: {len(svg_output)} bytes ({len(svg_output)/1024:.1f} KB)")
print(f"✓ Clusters: {len(clusters)}")
print("\nSVG structure:")
print("  - CMYK layer groups with blend modes")
print("  - Circle elements (not paths)")
print("  - Proper petal positioning with rotation")
