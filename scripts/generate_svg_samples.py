"""Generate SVG samples from test images for validation.

Generates SVG outputs with varying cluster counts to validate file sizes,
structure, and editor compatibility.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotmatrix.svg_renderer import render_svg
from dotmatrix.cluster_pixel_counter import ClusterResult


def create_test_clusters(count=100, width=800, height=600):
    """Create grid of test clusters."""
    import math
    
    clusters = []
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)
    
    x_spacing = width // (cols + 1)
    y_spacing = height // (rows + 1)
    
    # CMYK color patterns - varied sizes for visual interest
    # Using different pixel counts so colors are visible
    cmyk_patterns = [
        (3000, 0, 0, 500),           # Large Cyan, small Black center
        (0, 3000, 0, 500),           # Large Magenta, small Black center
        (0, 0, 3000, 500),           # Large Yellow, small Black center
        (2000, 2000, 0, 500),        # Cyan + Magenta, small Black center
        (2000, 0, 2000, 500),        # Cyan + Yellow, small Black center
        (0, 2000, 2000, 500),        # Magenta + Yellow, small Black center
    ]
    
    for idx in range(count):
        row = idx // cols
        col = idx % cols
        
        x = (col + 1) * x_spacing
        y = (row + 1) * y_spacing
        
        pattern = cmyk_patterns[idx % len(cmyk_patterns)]
        
        cluster = ClusterResult(
            x=x,
            y=y,
            cyan=pattern[0],
            magenta=pattern[1],
            yellow=pattern[2],
            black=pattern[3],
            red=0,
            green=0,
            blue=0,
            partial=False
        )
        clusters.append(cluster)
    
    return clusters


def generate_svg_samples():
    """Generate SVG samples with varying cluster counts."""
    output_dir = Path("demo_results/svg_samples")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Test cases: (count, width, height, description)
    test_cases = [
        (25, 500, 400, "Small - 25 clusters"),
        (100, 800, 600, "Medium - 100 clusters"),
        (400, 1600, 1200, "Large - 400 clusters"),
        (1000, 2000, 1600, "Very Large - 1000 clusters"),
    ]
    
    print("Generating SVG samples...")
    print(f"Output directory: {output_dir}\n")
    
    results = []
    
    for count, width, height, desc in test_cases:
        print(f"[{desc}]")
        print(f"  Dimensions: {width}x{height}")
        
        # Create clusters
        clusters = create_test_clusters(count, width, height)
        print(f"  Created {len(clusters)} clusters")
        
        # Render SVG
        svg_output = render_svg(clusters, (height, width), scale=1.0)
        
        # Save to file
        filename = f"sample_{count}_clusters.svg"
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg_output)
        
        file_size = len(svg_output)
        file_size_kb = file_size / 1024
        
        print(f"  File size: {file_size:,} bytes ({file_size_kb:.1f} KB)")
        print(f"  Saved: {filename}\n")
        
        results.append({
            "filename": filename,
            "clusters": count,
            "size_bytes": file_size,
            "size_kb": file_size_kb,
            "avg_bytes_per_cluster": file_size / count if count > 0 else 0
        })
    
    # Print summary
    print("\n=== Summary ===")
    print(f"{'Filename':<30} {'Clusters':>10} {'Size (KB)':>12} {'Bytes/Cluster':>15}")
    print("-" * 70)
    for r in results:
        print(f"{r['filename']:<30} {r['clusters']:>10} {r['size_kb']:>12.1f} {r['avg_bytes_per_cluster']:>15.1f}")
    
    print(f"\n✅ Generated {len(results)} SVG samples in {output_dir}")
    print("\nNext steps:")
    print("  1. Open SVGs in Inkscape or Illustrator")
    print("  2. Verify color grouping (layers)")
    print("  3. Test editability")
    print("  4. Validate rendering performance")


if __name__ == "__main__":
    generate_svg_samples()
