"""Analyze blank spots in reconstituted image vs cluster data."""
import json
import cv2
import numpy as np
import math

# Load cluster data
data = json.load(open('inputs/input_large_clusters.json'))
clusters = data['clusters']
centers = np.array([c['center'] for c in clusters])

print("Cluster radius analysis:")
for i, c in enumerate(clusters[:10]):
    black = c['pixel_counts'].get('black', 0)
    total = sum(c['pixel_counts'].values())
    black_r = math.sqrt(black / math.pi) if black > 0 else 0
    total_r = math.sqrt(total / math.pi) if total > 0 else 0
    cx, cy = c['center']
    print(f"  Cluster {i}: black_r={black_r:.1f}, total_r={total_r:.1f}, center=({cx},{cy})")

# Load images
orig = cv2.imread('inputs/input_large.png')
recon = cv2.imread('output/run_20251201_201158/reconstituted.png')

# Find blank spots (white in recon but not white in original)
recon_white = np.all(recon > 250, axis=2)
orig_white = np.all(orig > 250, axis=2)
blank_spots = recon_white & ~orig_white

print(f"Total blank spot pixels: {np.sum(blank_spots):,}")

# Sample 20 blank spot locations
ys, xs = np.where(blank_spots)
sample_idx = np.random.choice(len(xs), min(20, len(xs)), replace=False)

print("\nChecking if blank spots have nearby clusters:")
far_blanks = []
for i in sample_idx:
    x, y = xs[i], ys[i]
    # Find nearest cluster center
    dists = np.sqrt((centers[:,0] - x)**2 + (centers[:,1] - y)**2)
    nearest_idx = np.argmin(dists)
    nearest_dist = dists[nearest_idx]
    nearest_cluster = clusters[nearest_idx]
    total_pixels = sum(nearest_cluster['pixel_counts'].values())
    
    if nearest_dist > 50:
        far_blanks.append((x, y, nearest_dist))
    
    print(f"  ({x:4d},{y:4d}): nearest={nearest_dist:5.1f}px, cluster_pixels={total_pixels}")

print(f"\nBlanks far from any cluster (>50px): {len(far_blanks)}")
for x, y, d in far_blanks:
    print(f"  ({x}, {y}) - {d:.1f}px from nearest cluster")
