# Fix radius overestimation causing white halos in diff

## Problem Statement

**Observed Behavior**: Detected circles have white "halo" rings in the diff image, showing that drawn circles extend beyond the original dot boundaries.

**Expected Behavior**: Circles should closely match original dot boundaries with minimal overshoot or undershoot.

**Root Cause Hypothesis**: 
1. `HOUGH_RADIUS_PADDING = 3` is too aggressive
2. Fallback detection uses `sqrt(area/pi)` which overestimates for partial arcs
3. HoughCircles param2 may be too permissive

---

## Investigation

### Current Radius Sources

| Source | Formula | Issue |
|--------|---------|-------|
| HoughCircles | OpenCV internal | May overestimate with padding |
| Fallback | `sqrt(area/pi) + 3` | Overestimates for partial coverage |
| HOUGH_RADIUS_PADDING | +3 constant | Blanket addition |

### Options to Fix

**Option A: Reduce/Remove HOUGH_RADIUS_PADDING**
- Pros: Simple, direct fix
- Cons: May reintroduce underestimation from earlier bug

**Option B: Adaptive padding based on edge point density**
- Pros: Context-aware, handles both full and partial circles
- Cons: More complex implementation

**Option C: Post-detection radius refinement using edge fitting**
- Pros: Most accurate, uses actual boundary data
- Cons: Additional computation

**Option D: Use diff metric to optimize padding value**
- Pros: Data-driven, objective
- Cons: Requires metric implementation first (card audjl2)

---

## Tasks

- [ ] Measure current overfit ratio using fit metric
- [ ] Test with HOUGH_RADIUS_PADDING = 0, 1, 2 
- [ ] Implement adaptive or refined radius calculation
- [ ] Verify diff shows reduced white halos
- [ ] Verify no regression in detection count

---

## Acceptance Criteria

- [ ] White halo area reduced by >50% vs baseline
- [ ] Detection count maintained (no circles lost)
- [ ] Fit score improved vs baseline
- [ ] All existing tests pass

---

## Technical Details

**Affected Files**:
- `src/dotmatrix/convex_detector.py` - HOUGH_RADIUS_PADDING constant
- `src/dotmatrix/convex_detector.py:526-535` - Fallback radius calculation

**Current Code** (lines 526-535):
```python
if circles is None:
    # Fallback: use connected component centroid and area-derived radius
    centroid = centroids[label_id]
    fallback_radius = int(np.sqrt(area / np.pi)) + HOUGH_RADIUS_PADDING
    
    if min_radius <= fallback_radius <= max_radius:
        candidate_circles.append((int(centroid[0]), int(centroid[1]), fallback_radius))
    continue
```

**Proposed Fix**: Remove padding from fallback, or use edge-distance based radius.

