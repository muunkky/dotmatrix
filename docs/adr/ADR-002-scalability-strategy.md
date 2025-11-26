# ADR-002: Scalability Strategy for Large/Dense Images

## Status

**Accepted**

## Date

2025-11-26

## Context

ADR-001 concluded that chunking/tiling wasn't needed for target file sizes (10MB / 4-9 MP). However, real-world testing with a 38.88 MP CMYK halftone image revealed a critical performance bottleneck: the O(n²) deduplication algorithm in `convex_detector.py` (lines 300-322).

For dense halftone images containing tens of thousands of circles, the nested loop deduplication becomes the dominant performance factor:
- 10,000 circles: 67 seconds with O(n²), 0.13s with KD-tree (527x speedup)
- The 38 MP halftone image processing hung for 25+ minutes

## Decision

### 1. Implement Spatial Indexing with KD-tree (Primary Fix)

Replace the O(n²) nested loop deduplication with scipy's KDTree for O(n log n) performance.

**Benchmark Results:**
| N Circles | Nested Loop | KD-tree | Speedup |
|-----------|-------------|---------|---------|
| 100 | 0.009s | 0.002s | 4x |
| 1,000 | 0.79s | 0.014s | 57x |
| 10,000 | 67s | 0.13s | 527x |
| 50,000 | est. 28min | 0.48s | ~3500x |
| 100,000 | est. 2hrs | 0.56s | ~12000x |

**Implementation:**
```python
from scipy.spatial import KDTree

def deduplicate_circles_fast(circles, dedup_distance=20):
    if not circles:
        return []

    centers = np.array([(c[0], c[1]) for c in circles])
    tree = KDTree(centers)

    used = set()
    final_circles = []

    for i, (x, y, r) in enumerate(circles):
        if i in used:
            continue
        final_circles.append(DetectedCircle(x, y, r, color))
        nearby = tree.query_ball_point([x, y], dedup_distance)
        used.update(nearby)

    return final_circles
```

### 2. Add Chunked Processing (Secondary - For Very Large Images)

For images exceeding 25+ MP with convex detection, implement tiled processing:

**Adaptive Chunk Sizing Strategy:**
After evaluating the approaches in the spike card, we recommend **Approach 1: Fixed Size Based on Max Radius** as the primary strategy, with optional density-based adjustment:

```python
def calculate_chunk_size(image_shape, max_radius, target_circles_per_chunk=2000):
    """Calculate optimal chunk size.

    Primary: Use max_radius-based formula
    Secondary: Adjust based on estimated density if available
    """
    # Base chunk size: enough to contain several circles
    base_size = max(2000, max_radius * 50)

    # Cap at image dimensions
    h, w = image_shape[:2]
    chunk_size = min(base_size, h, w)

    return chunk_size
```

**Rationale:**
- Simple, predictable, no extra processing overhead
- max_radius correlation ensures tiles can contain full circles
- Spatial indexing handles any circle count per chunk efficiently
- Density-based and backoff approaches add complexity without proportional benefit

### 3. Combined Architecture

```
Large Image
    │
    ▼
┌─────────────────────────────┐
│  Tile Generator             │
│  (if image > threshold)     │
│  overlap = 2 * max_radius   │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Per-Tile Processing        │
│  └── KD-tree deduplication  │ ← O(n log n) per tile
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Global Merge               │
│  └── KD-tree deduplication  │ ← O(n log n) for boundaries
└─────────────────────────────┘
```

## Performance Targets

| Image Size | Circle Count | Target Time | Memory |
|------------|--------------|-------------|--------|
| 10 MP | 1,000 | <5s | <100MB |
| 25 MP | 10,000 | <30s | <200MB |
| 38 MP | 50,000 | <3min | <500MB |

## Consequences

### Positive
- 500x+ speedup for dense images
- Scales to 100k+ circles
- Minimal code change (dedup function replacement)
- scipy dependency already common in scientific Python

### Negative
- Adds scipy as required dependency
- Minor memory overhead for KD-tree structure
- Processing order may differ (shouldn't affect results)

### Neutral
- Chunking only needed for extreme cases (>25 MP with convex)
- ADR-001's conclusions remain valid for most use cases

## Implementation Priority

1. **Spatial Indexing (P0)**: Replace nested loop with KD-tree
2. **Chunked Processing (P0)**: Add tiled processing for >25 MP
3. **Integration (P1)**: Combine both for optimal performance

## References

- Spike Card: 9dsqox (Adaptive Chunk Sizing Research)
- Benchmark: `benchmarks/dedup_benchmark.py`
- scipy.spatial.KDTree documentation
