# Implement Spatial Indexing for O(n log n) Deduplication

## Problem Statement
Current circle deduplication in `convex_detector.py` (lines 304-318) uses nested loops with O(n²) complexity. For dense halftone images with tens of thousands of circles, this creates a performance bottleneck that makes processing impractical.

## Solution
Replace the O(n²) nested loop deduplication with spatial indexing using scipy's KD-tree or a custom grid-based approach.

## Acceptance Criteria
- [x] Implement KD-tree based spatial indexing using `scipy.spatial.KDTree`
- [x] Replace nested loop deduplication with `query_ball_point()` for O(n log n) neighbor searches
- [x] Maintain identical deduplication behavior (same distance threshold, same merge logic)
- [x] Add unit tests comparing results of old vs new deduplication
- [x] Benchmark: 10,000 circles should deduplicate in <1 second
- [x] Benchmark: 50,000 circles should deduplicate in <10 seconds

## Technical Approach

### Current Implementation (O(n²))
```python
for i in range(len(candidate_circles)):
    if used[i]:
        continue
    x1, y1, r1 = candidate_circles[i]
    for j in range(i + 1, len(candidate_circles)):
        if used[j]:
            continue
        x2, y2, r2 = candidate_circles[j]
        dist = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        if dist < dedup_distance:
            used[j] = True
```

### New Implementation (O(n log n))
```python
from scipy.spatial import KDTree

# Build KD-tree from circle centers
centers = np.array([(c[0], c[1]) for c in candidate_circles])
tree = KDTree(centers)

# For each circle, find neighbors within dedup_distance
used = set()
final_circles = []
for i, (x, y, r) in enumerate(candidate_circles):
    if i in used:
        continue
    final_circles.append(DetectedCircle(x, y, r, color))
    # Mark nearby circles as used
    nearby = tree.query_ball_point([x, y], dedup_distance)
    used.update(nearby)
```

## Dependencies
- `scipy>=1.7.0` (already available in scientific Python environments)

## Testing Strategy
1. Create synthetic test with known duplicate circles
2. Verify identical output between old and new implementations
3. Performance benchmarks with 1k, 10k, 50k, 100k circles
4. Edge cases: empty input, single circle, all duplicates

## Notes
- KD-tree build is O(n log n), queries are O(log n) average
- Alternative: grid-based indexing for very dense images (O(1) lookup within cell)
- Consider making indexing method configurable if different approaches work better for different densities
