"""Generate visual samples for jitter prototype validation."""
import subprocess
import sys
from pathlib import Path
import cv2
import numpy as np

# Test configurations: (name, jitter_position, jitter_size, description)
test_configs = [
    ("baseline", 0, 0, "No jitter (baseline)"),
    ("conservative", 15, 0, "15% position jitter only"),
    ("moderate", 25, 20, "25% position, 20% size (recommended)"),
    ("aggressive", 40, 35, "40% position, 35% size"),
    ("reproducible_seed42", 25, 20, "Reproducible with seed=42"),
    ("reproducible_seed42_again", 25, 20, "Same seed=42 (should match previous)"),
]

# Input and output paths
input_img = Path("tests/data/multicolor_test.png")
output_dir = Path("demo_results/jitter_samples")

# Ensure output directory exists
output_dir.mkdir(exist_ok=True, parents=True)

# Generate samples
print(f"Generating jitter samples using: {input_img}")
print(f"Output directory: {output_dir}\n")

for name, pos, size, desc in test_configs:
    output_path = output_dir / f"{name}.png"
    
    # Build command
    cmd = [
        sys.executable, "-m", "dotmatrix",
        "-i", str(input_img),
        "-m", "halftone",
        "--reconstitute",
        "--render-method", "flower",
        "--output-dir", str(output_dir / name),
        f"--jitter-position={pos}",
        f"--jitter-size={size}",
    ]
    
    # Add seed for reproducibility tests
    if "seed" in name:
        cmd.append("--jitter-seed=42")
    
    print(f"[{name}]: {desc}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"   [OK] Success")
        else:
            print(f"   [FAIL] Exit code {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
    except Exception as e:
        print(f"   [ERROR] Exception: {e}")
    print()

print("\nSample generation complete!")

# Create labeled versions for comparison (without modifying originals)
print("\nCreating labeled versions for visual comparison...")
try:
    for name, pos, size, desc in test_configs:
        # Find the reconstituted image
        recon_path = output_dir / name / "reconstituted.png"
        if recon_path.exists():
            img = cv2.imread(str(recon_path))
            if img is not None:
                # Create labeled copy
                labeled = img.copy()
                cv2.putText(labeled, f"{name}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(labeled, f"{desc}", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                cv2.putText(labeled, f"pos={pos}% size={size}%", (10, 85), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
                
                # Save as separate labeled file
                labeled_path = output_dir / f"{name}_labeled.png"
                cv2.imwrite(str(labeled_path), labeled)
                print(f"  Created: {labeled_path.name}")
    
    print(f"\nLabeled samples saved to: {output_dir}")
    print(f"Original reconstituted images: {output_dir}/<name>/reconstituted.png")
    print(f"Labeled versions: {output_dir}/<name>_labeled.png")
    
except Exception as e:
    print(f"Could not create labeled images: {e}")

print(f"\nCheck outputs in: {output_dir}")
