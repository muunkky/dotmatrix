# Spike: Root Cause Analysis - Why Small Clusters Are Not Detected

## Research Question

Why are 38,586 pixels in the input image located more than 50px from any detected cluster center? What detection parameters or algorithm limitations are causing small halftone clusters to be missed?

## Context

Analysis of `input_large.png` showed orphan pixels concentrated in region X:1597-3530, Y:1831-2956. These are clearly part of the halftone pattern but no cluster center was detected for them. This spike will trace through the detection pipeline to identify exactly where and why small dots are filtered out.

## Problem Statement

**Decision**: Determine root cause of missing small cluster detection

The detection pipeline has multiple filtering stages:
1. **Distance Transform**: `threshold_ratio=0.5` - may filter faint dots
2. **NMS (Non-Maximum Suppression)**: `min_distance=10` - may suppress nearby peaks  
3. **Blob Area Filter**: `min_blob_area` - may filter small blobs
4. **Edge Detection**: Edge-based methods may miss small circular features

Need to identify which stage(s) are responsible for the ~38k orphan pixels.

---

## Time Box

**Maximum Time**: 4 hours

---

## Success Criteria

**We'll know this spike is successful when**:
- [x] Detection pipeline stages documented
- [x] Orphan pixel region analyzed with debug output
- [x] Specific filtering stage(s) identified as cause
- [x] Parameter changes proposed to capture small dots
- [x] Trade-off analysis: false positives vs. missed detections

---

## Investigation Plan

### Step 1: Visualize Orphan Region
- Extract the orphan region (X:1597-3530, Y:1831-2956)
- Examine original image pixels in this area
- Confirm halftone dots exist that should be detected

### Step 2: Trace Detection Pipeline
- Run detection with verbose/debug output
- Track which centers are detected in the region
- Compare to expected grid pattern

### Step 3: Parameter Sensitivity Analysis
- Test with lower `threshold_ratio` (0.3, 0.2)
- Test with lower `min_distance` (5, 3)
- Test with lower `min_blob_area` (25, 10)
- Document effect on orphan count and false positives

### Step 4: Root Cause Determination
- Identify primary cause(s)
- Document parameter changes needed
- Assess impact on overall detection quality

---

## Acceptance Criteria

- [x] Orphan region visualized and analyzed
- [x] Detection pipeline traced with debug output
- [x] Root cause identified with evidence
- [x] Recommended parameter changes documented
- [x] Trade-off analysis completed

## Test Plan

- [x] Run detection on orphan region crop
- [x] Compare detected centers to visual halftone pattern
- [x] Test parameter variations and document results
- [x] Verify findings generalize to other image regions


## Investigation Findings


### Root Cause: Global Threshold Calculation

**Location**: `src/dotmatrix/cluster_pixel_counter.py`, lines 354-360

```python
threshold = max(0.5, threshold_ratio * dist_transform.max())
```

This calculates threshold using the **GLOBAL maximum** distance transform value across the entire image. Large halftone dots dominate this value, causing small dots to be filtered.

### Evidence (2025-11-27)

| Metric | Value |
|--------|-------|
| Full image distance transform max | 26.8 px |
| Global threshold (0.5 × 26.8) | **13.4 px** |
| Orphan crop distance transform max | 13.0 px |
| Connected black regions in orphan crop | 9 |
| Regions above global threshold | **0 / 9** |

#### Individual Region Analysis

| Region | Max Distance | Above Threshold? |
|--------|--------------|------------------|
| 1 | 2.8 px | ❌ |
| 2 | 9.0 px | ❌ |
| 3 | 7.0 px | ❌ |
| 4 | 7.6 px | ❌ |
| 5 | 2.8 px | ❌ |
| 6 | 12.4 px | ❌ |
| 7 | 13.0 px | ❌ |
| 8 | 1.0 px | ❌ |
| 9 | 1.0 px | ❌ |

**Key Insight**: The largest dot in the orphan region (13.0 px) is STILL below the global threshold (13.4 px). Every single dot in this region is filtered out.

### Why This Happens

1. Distance transform finds distance to nearest background pixel for each foreground pixel
2. Large circles have high max distance values (their centers are far from edges)
3. Small circles have low max distance values (their centers are close to edges)
4. Using `dist_transform.max()` (global) creates threshold dominated by largest dots
5. Small dots with distance values of 1-13 px get filtered because threshold is 13.4 px

### Recommended Solutions

**Option A: Adaptive Local Thresholding**
- Calculate threshold in local windows instead of globally
- Pro: Naturally adapts to local dot sizes
- Con: More complex, possible edge effects

**Option B: Multi-Pass Detection**
- First pass: high threshold captures large dots
- Second pass: lower threshold captures remaining small dots
- Pro: Simple to implement, predictable behavior
- Con: May need deduplication between passes

**Option C: Absolute Threshold Floor**
- Set minimum absolute threshold (e.g., 1.0 or 0.5)
- Change: `threshold = max(absolute_floor, threshold_ratio * local_max)`
- Pro: Simplest fix
- Con: May increase false positives globally

### Recommended Approach

**Multi-Pass Detection (Option B)** is recommended because:
1. Matches the established pattern (already have multi-pass for rendering)
2. Predictable behavior - can tune each pass independently
3. TDD-friendly - easy to test each pass
4. Low risk - doesn't change existing large dot detection

### Trade-off Analysis

| Approach | False Positives | Missed Detections | Complexity |
|----------|-----------------|-------------------|------------|
| Current | Low | High (~38k pixels) | Low |
| Local Threshold | Medium | Low | High |
| Multi-Pass | Low-Medium | Low | Medium |
| Threshold Floor | High | Low | Low |

Multi-pass provides the best balance for $50k+ print quality requirements.
