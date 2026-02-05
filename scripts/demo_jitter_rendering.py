"""Jitter rendering demo with synthetic circle data."""
import sys
from pathlib import Path
import cv2
import numpy as np
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotmatrix.circle_renderer import render_flower
from dotmatrix.cluster_pixel_counter import ClusterResult

def create_grid_clusters(width=800, height=600, grid_size=5, circle_radius=40):
    """Create a grid of CMYK clusters for testing."""
    clusters = []
    
    # Calculate spacing
    x_spacing = width // (grid_size + 1)
    y_spacing = height // (grid_size + 1)
    
    # Use larger pixel counts for more visible circles
    # Each value represents actual pixel count in the cluster
    base_pixels = 2000  # ~25px radius circles
    
    # CMYK patterns - mix of different ink combinations
    cmyk_patterns = [
        (base_pixels, 0, 0, base_pixels),           # Cyan + Black
        (0, base_pixels, 0, base_pixels),           # Magenta + Black
        (0, 0, base_pixels, base_pixels),           # Yellow + Black
        (base_pixels, base_pixels, 0, base_pixels), # Cyan + Magenta + Black
    ]
    
    for row in range(grid_size):
        for col in range(grid_size):
            x = (col + 1) * x_spacing
            y = (row + 1) * y_spacing
            
            # Vary colors across grid
            pattern = cmyk_patterns[(row + col) % len(cmyk_patterns)]
            
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

def render_jitter_demo(output_dir):
    """Generate jitter comparison images."""
    output_dir = Path(output_dir)
    
    # Clear existing outputs
    if output_dir.exists():
        print(f"Clearing existing outputs in {output_dir}...")
        shutil.rmtree(output_dir)
    
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Image dimensions
    width, height = 800, 600
    
    # Create synthetic cluster grid
    print("Creating synthetic cluster grid (5x5)...")
    clusters = create_grid_clusters(width, height, grid_size=5, circle_radius=30)
    print(f"  Created {len(clusters)} clusters")
    
    # Test configurations - using stronger jitter for visibility
    configs = [
        ("baseline", 0, 0, 1, "No jitter - perfect grid"),
        ("light", 30, 15, 2, "Light jitter (30% pos, 15% size)"),
        ("medium", 50, 30, 3, "Medium jitter (50% pos, 30% size)"),
        ("heavy", 80, 50, 4, "Heavy jitter (80% pos, 50% size)"),
        ("seed42_a", 50, 30, 42, "Reproducible (seed=42)"),
        ("seed42_b", 50, 30, 42, "Reproducible (seed=42) - should match"),
    ]
    
    print("\nRendering with different jitter settings...")
    for name, pos, size, seed, desc in configs:
        print(f"\n[{name}] {desc}")
        print(f"  Position: {pos}%, Size: {size}%, Seed: {seed}")
        
        # Render with jitter
        img = render_flower(
            clusters,
            (height, width),
            petal_distance=0.5,  # More visible petal separation
            scale=1.0,  # Use scale=1.0 to avoid float dimension issues
            skip_partial=False,
            rotation_mode='fixed',  # Fixed rotation so jitter differences are visible
            base_rotation=0.0,
            rotation_seed=seed,  # Use same seed for rotation
            blend_overlaps=True,  # Enable blending for overlapping petals
            jitter_position=pos,
            jitter_size=size,
            jitter_seed=seed,
            jitter_algorithm='gaussian'
        )
        
        # Add label
        labeled = img.copy()
        cv2.putText(labeled, name, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(labeled, desc, (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.putText(labeled, f"pos={pos}% size={size}%", (10, 85), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        
        # Save
        output_path = output_dir / f"{name}.png"
        cv2.imwrite(str(output_path), labeled)
        print(f"  Saved: {output_path}")
    
    print(f"\n✓ Demo complete! Check: {output_dir}")
    print("\nCompare baseline vs moderate to see jitter effect")
    print("Compare seed42_a vs seed42_b to verify reproducibility")

if __name__ == "__main__":
    render_jitter_demo("demo_results/jitter_demo")
