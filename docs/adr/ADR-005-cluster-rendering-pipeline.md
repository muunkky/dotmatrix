# ADR-005: Cluster-Based Pixel Counting for CMYK Halftone Analysis

## Status

**Accepted**

## Date

2025-12-15

## Context

Dotmatrix processes CMYK halftone images where overlapping ink dots create complex color relationships. The challenge is accurately counting pixels for each color channel while:

1. **Handling Overlaps**: CMYK inks produce secondary colors at overlap points (C∩M=Blue, M∩Y=Red, C∩Y=Green)
2. **Avoiding Double-Counting**: The same pixel cannot be counted twice
3. **Maintaining Spatial Relationships**: Pixel counts must be attributed to specific halftone dots
4. **Supporting Reconstitution**: Counts must be sufficient to recreate the original image

The traditional approach of counting pixels per-circle fails when dots merge in dense halftone patterns. We needed an architecture that could handle overlapping circles while maintaining accurate, non-duplicated counts.

## Decision

**We will implement cluster-based pixel counting that groups all ink pixels around black (K) dot centers using Voronoi tessellation.**

### Algorithm Overview

The cluster pipeline operates in distinct phases:

```
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 1: Complete Midtone Masks                                  │
│ ─────────────────────────────────────────────────────────────────│
│ Problem: RGB overlaps fragment the C/M/Y masks                   │
│ Solution: Temporarily include overlaps for clustering:           │
│   - Cyan    += Green (C∩Y) + Blue (C∩M)                         │
│   - Magenta += Red (M∩Y)  + Blue (C∩M)                          │
│   - Yellow  += Red (M∩Y)  + Green (C∩Y)                         │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 2: Find Black Dot Centers                                  │
│ ─────────────────────────────────────────────────────────────────│
│ Option A (centroid): Connected component analysis → centroids    │
│ Option B (distance transform): For merged dots:                  │
│   1. Distance transform (distance to edge)                       │
│   2. Find local maxima (peaks = centers)                         │
│   3. NMS to enforce min_distance between centers                 │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 3: Voronoi Tessellation (Cluster Labels)                   │
│ ─────────────────────────────────────────────────────────────────│
│ For each pixel → assign to nearest black dot center              │
│ Creates cluster label image where label = cluster ID             │
│ Implementation: KDTree for O(M log N) performance                │
│   (GPU alternative tested but 10x slower for typical sizes)      │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 4: Count Pixels Per Cluster                                │
│ ─────────────────────────────────────────────────────────────────│
│ For each cluster, count:                                         │
│   - Pure midtones: C, M, Y (with overlaps subtracted)            │
│   - Black: K                                                     │
│   - Overlaps: R (M∩Y), G (C∩Y), B (C∩M)                          │
│ Output: ClusterResult with 9 color counts + metadata             │
└──────────────────────────────────────────────────────────────────┘
```

### Output Format

Each cluster produces a `ClusterResult` dataclass:

```python
@dataclass
class ClusterResult:
    x: int           # Black dot center X
    y: int           # Black dot center Y
    cyan: int        # Pure cyan pixels (RGB subtracted)
    magenta: int     # Pure magenta pixels
    yellow: int      # Pure yellow pixels
    black: int       # Black ink pixels
    red: int         # M∩Y overlap pixels
    green: int       # C∩Y overlap pixels
    blue: int        # C∩M overlap pixels
    partial: bool    # True if cluster at image edge
    bbox: Tuple      # (x_min, y_min, x_max, y_max)
```

The serialization format is `[x, y, C, M, Y, K, R, G, B]` for compact JSON/CSV output.

### Cluster Anchor Modes

The `--cluster-anchor` CLI option controls center point selection:

| Mode | Description | Use Case |
|------|-------------|----------|
| `centroid` | Connected component centroid | Default, mathematically accurate |
| `pixel` | Nearest black pixel to centroid | Legacy compatibility, snaps to actual ink |

### Debug Visualization

The `--debug-clusters` flag generates visual cluster diagnostics:

- Each cluster rendered with unique HSV-spaced color
- White crosshair markers at cluster centers  
- Semi-transparent overlay on original image
- Output: `cluster_debug.png`

## Alternatives Considered

### 1. Per-Circle Pixel Counting (Rejected)
- Count pixels within each detected circle's radius
- **Problem**: Circles overlap; same pixel counted multiple times
- **Problem**: Can't handle merged/touching dots

### 2. Voronoi Tessellation with Circle Centers (Rejected)
- Use detected circle centers instead of black dot centers
- **Problem**: Circle detection is less reliable than black mask analysis
- **Problem**: No ground truth for overlapping circles

### 3. Connected Components Only (Rejected for Dense Patterns)
- Use connected component labels directly
- **Problem**: Merged black dots become single component
- **Problem**: Can't separate touching halftone dots
- **Retained**: As fallback when distance transform finds no peaks

## Consequences

### Positive

- **Accurate Deduplication**: Each pixel counted exactly once via Voronoi assignment
- **Handles Overlaps**: RGB overlaps properly attributed without double-counting
- **Separation of Merged Dots**: Distance transform + NMS separates touching dots
- **Reconstitution Quality**: Bullseye and block renderers achieve 91-100% accuracy
- **Bounding Box Support**: Spatial queries enabled via `bbox` field
- **Cache Support**: Results serializable to JSON for incremental processing

### Negative

- **Computational Cost**: O(M log N) KDTree queries for M pixels, N centers
- **Memory Usage**: Full-resolution label image required (~4 bytes/pixel)
- **Edge Effects**: Clusters at image boundaries have incomplete counts (`partial=True`)

### Neutral

- **Black Dot Requirement**: Algorithm assumes black (K) channel anchors all clusters
- **GPU Trade-offs**: GPU cluster labeling tested but CPU KDTree is faster for typical sizes

## Implementation Details

### Key Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `complete_midtone_masks()` | `cluster_pixel_counter.py` | Phase 1: Include RGB overlaps in midtone masks |
| `find_black_dot_centers()` | `cluster_pixel_counter.py` | Phase 2a: Connected component centroids |
| `find_black_dot_centers_distance_transform()` | `cluster_pixel_counter.py` | Phase 2b: Distance transform for merged dots |
| `_nms_centers()` | `cluster_pixel_counter.py` | Non-maximum suppression for center spacing |
| `create_cluster_labels_from_centers()` | `cluster_pixel_counter.py` | Phase 3: KDTree Voronoi assignment |
| `cluster_and_count_pixels()` | `cluster_pixel_counter.py` | Main entry point orchestrating all phases |
| `generate_cluster_debug_image()` | `cluster_pixel_counter.py` | Debug visualization output |

### GPU Acceleration Points

While cluster labeling uses CPU KDTree, GPU acceleration is applied to:

- `gpu_nms_centers()`: Non-maximum suppression for >200 centers
- `gpu_count_cluster_colors()`: Batch bincount for >1M pixels
- `gpu_distance_transform()`: Distance transform for merged dot detection
- `gpu_maximum_filter()`: Local maxima detection for center finding

See ADR-004 for GPU acceleration architecture details.

### Performance Characteristics

| Operation | Complexity | Typical Time |
|-----------|------------|--------------|
| Midtone mask completion | O(N) | ~5ms per megapixel |
| Center finding (centroid) | O(K) | ~2ms for K components |
| Center finding (distance) | O(N) | ~50ms per megapixel |
| Cluster labeling | O(M log N) | ~100ms for 4K image |
| Pixel counting | O(N) | ~10ms per megapixel |

### Rendering Options

Two renderers consume `ClusterResult` data:

1. **Bullseye Renderer** (`cluster_renderer.py`): Concentric circles, ~91% accuracy
   - Visual representation for quality assessment
   - Circle radius proportional to pixel count
   
2. **Block Renderer** (`block_renderer.py`): Horizontal bars, 100% accuracy
   - Integer-exact pixel counts via rectangle areas
   - Required for printer overlay workflows

See ADR-003 for block renderer architecture details.

## References

- ADR-003: Block Renderer for 100% Pixel Accuracy
- ADR-004: GPU Acceleration for Processing Performance
- CLUSTEREXT sprint: `--cluster-anchor` and `--debug-clusters` features
- `cluster_pixel_counter.py`: Core implementation (~1200 lines)
- `cluster_renderer.py`: Bullseye visualization
- `tests/test_cluster_pixel_counter.py`: 50 unit tests
