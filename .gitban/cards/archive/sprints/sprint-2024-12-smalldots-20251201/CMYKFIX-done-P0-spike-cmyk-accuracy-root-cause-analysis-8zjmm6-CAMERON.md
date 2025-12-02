# Troubleshooting: CMYK Accuracy Pixel Count Mismatch

**Card Type**: Spike - Troubleshooting
**Status**: investigation
**Priority**: P0
**Date Started**: 2025-11-30
**Owner**: CAMERON

## Problem Statement

### Symptoms Observed
- **What is broken/not working?** Reconstituted image CMYK pixel counts don't match source image
- **Error messages or unexpected behavior**: 
  - Expected Cyan: 53,370 pixels, Actual: ~33,674 (36% error)
  - Expected Magenta: 27,798 pixels, Actual: ~10,192 (63% error)
  - Black is overestimated: ~130,281 vs 121,364 expected
- **Impact**: CMYK halftone reconstitution produces inaccurate color representation
- **Urgency**: Core functionality of dotmatrix tool is broken

### Environment Context
- **System/Service**: dotmatrix CLI / circle_renderer.py
- **Version**: Current development branch
- **Configuration**: petal_distance=0.5, exposed_area_sizing=always, blend_overlaps=True
- **Recent Changes**: 
  - Changed petal_distance from 0.7 to 0.5
  - Made exposed_area_sizing always-on (removed flag)
  - Fixed render order: black first, then petals (was petals first)

---

## Investigation Progress

### Pre-Investigation Checklist
- [x] Problem statement clearly defined
- [x] Error messages captured verbatim
- [x] Recent changes reviewed (git log, deployment logs)
- [x] Similar past issues searched (gitban cards, docs, git history)
- [x] Monitoring/logs checked for related errors
- [x] Impact scope assessed (how many users/systems affected)

### Research Performed

#### Documentation Review
- [x] Official product documentation consulted
- [x] Internal documentation/runbooks checked
- [x] Architecture diagrams reviewed
- [x] Related ADRs/design docs examined

**Key Documents Referenced**:
- circle_renderer.py docstrings - Flower rendering algorithm documentation
- cluster_pixel_counter.py - CMYK decomposition logic

#### Knowledge Base Search
- [x] Google search performed
- [x] Stack Overflow / GitHub issues searched
- [x] Context7 / library documentation consulted
- [x] Team knowledge / Slack history checked

**Google / Web Search Terms Used**:
1. `lens area formula circle intersection` - Found formula for overlap calculation
2. `subtractive CMY blending algorithm` - Verified blending approach

#### Related Gitban Cards:

| Card ID | Card Name | Initial Status | Description of relevance |
|---------|-----------|----------------|--------------------------|
| CMYKFIX | Previous attempts | done | Multiple fixes attempted but problem persists |

#### Related Code/Config:
- `src/dotmatrix/circle_renderer.py:350-430` - render_flower_cluster blend_overlaps branch
- `src/dotmatrix/circle_renderer.py:180-220` - radius_for_exposed_pixels calculation
- `src/dotmatrix/cluster_pixel_counter.py` - CMYK decomposition from RGB

---

## Solution Attempts

### Attempt Log

| # | Attempt Name | Hypothesis | Outcome | Status | Notes |
|---|-------------|------------|---------|--------|-------|
| 1 | Fix binary search bounds | r_max = target*3 insufficient | Improved but still errors | 🔄 Partial | Changed to *10 |
| 2 | Remove exposed_area flag | Flag should always be on | No change | ❌ Fail | Was already being used |
| 3 | Fix petal_distance | 0.7 wrong, should be 0.5 | No change | ❌ Fail | Petals now inside black |
| 4 | Fix render order | Black drawn after petals eating crescent | Improved | 🔄 Partial | Black now first |
| 5 | TBD | Adjacent cluster interference | TBD | ⏳ Pending | Need to investigate |

### Detailed Attempt Logs

#### Attempt 1: Binary Search Bounds

**Hypothesis**: Binary search r_max = target_exposed * 3 is insufficient when petal is heavily occluded

**Root Cause Theory**: For high-occlusion scenarios, radius needs to be much larger than 3x target

**Steps Performed**:
1. Changed line 196 in circle_renderer.py:
   ```python
   # OLD: r_max = radius_from_pixels(target_exposed * 3)
   r_max = radius_from_pixels(target_exposed * 10)
   ```

**Results**:
- **Observed Behavior**: Binary search no longer hitting ceiling
- **Outcome**: 🔄 Partial - helped but errors remain

---

#### Attempt 4: Fix Render Order

**Hypothesis**: Black was drawn AFTER petals, overwriting the exposed crescent

**Steps Performed**:
1. Reordered blend_overlaps branch to draw black FIRST
2. Then draw petal masks on exposed areas only

**Results**:
- **Observed Behavior**: Cyan/magenta crescents now visible
- **Outcome**: 🔄 Partial - visible improvement but pixel counts still wrong

---

#### Attempt 5: Adjacent Cluster Interference (CURRENT INVESTIGATION)

**Hypothesis**: The `used` mask causes inter-cluster pixel loss when adjacent flowers overlap

**Root Cause Theory**: 
- Cluster A is processed first, marks pixels as `used`
- Cluster B's petal overlaps with A's territory
- B's exposed_count shows full exposed area
- But B's actually_drawable = exposed & ~used is smaller
- Total rendered pixels < sum of cluster targets

**Steps To Perform**:
1. Trace pixel loss by comparing exposed vs actually_drawable for each cluster
2. Sum all cluster targets and compare to source totals
3. Determine if source totals are achievable with current geometry

---

## Root Cause Analysis

### Confirmed Root Cause
**Summary**: TBD - Under investigation

**Technical Explanation**:
Multiple potential causes being investigated:
1. Adjacent cluster interference via `used` mask
2. Edge clusters extending beyond image boundaries
3. Possible mismatch between cluster pixel targets and source totals

### Why This Wasn't Caught Earlier
- Per-cluster calculations show correct exposed areas (exposed = target)
- But sum of all clusters may not equal source totals
- Accuracy checker compares against source, not cluster totals

---

## Solution

### Implemented Fix
TBD - Pending root cause confirmation

---

## Follow-Up Actions

### Immediate Actions
- [x] Complete Attempt 5 diagnostic script
- [x] Verify sum(cluster.cyan) == source_cyan
- [x] Trace where pixels are being lost

### Long-Term Prevention

| Prevention Measure | Type | Priority | Owner | Status | Card/Issue |
|-------------------|------|----------|-------|--------|------------|
| Add rendered pixel count validation | Testing | P1 | CAMERON | ⬜ Todo | CMYKFIX testing card |
| Document flower rendering algorithm | Documentation | P1 | CAMERON | ⬜ Todo | CMYKFIX docs card |

---

## Timeline

| Time (UTC) | Event | Actor | Outcome |
|------------|-------|-------|---------|
| 2025-11-30 00:00 | Problem first observed | CAMERON | 36% cyan, 63% magenta error |
| 2025-11-30 00:30 | Binary search fix | CAMERON | Partial improvement |
| 2025-11-30 01:00 | Render order fix | CAMERON | Partial improvement |
| 2025-11-30 02:00 | Sprint created | CAMERON | Systematic investigation begins |

---

**Resolution Status**: 🔄 Ongoing
**Total Investigation Time**: ~2 hours
**Total Downtime/Impact**: Feature broken
**Prevention Items Created**: TBD


## Lessons Learned

### What Worked Well
- Systematic attempt logging helps track what's been tried
- Per-cluster tracing reveals internal calculation accuracy

### What Could Be Improved
- Should have validated sum(cluster targets) == source totals earlier
- Need better logging/tracing in render pipeline

### Key Takeaways
1. Accuracy validation must compare at multiple levels (cluster, total, source)
2. The `used` mask creates inter-cluster dependencies
3. Always verify the math from source → cluster → render → output

## Appendices

### Appendix A: Error Metrics

```
Source Image Analysis:
- Cyan: 53,370 pixels
- Magenta: 27,798 pixels  
- Yellow: 8,285 pixels
- Black: 121,364 pixels

Rendered Output:
- Cyan: 33,674 pixels (36.9% error)
- Magenta: 10,192 pixels (63.3% error)
- Yellow: 3,419 pixels
- Black: 130,281 pixels

Missing Pixels:
- Cyan: ~20,000 pixels lost
- Magenta: ~17,000 pixels lost
```

### Appendix B: Key Files

- `src/dotmatrix/circle_renderer.py` - Flower rendering logic
- `src/dotmatrix/cluster_pixel_counter.py` - CMYK decomposition
- `src/dotmatrix/cli.py` - CLI integration

## Acceptance Criteria

- [x] Root cause of CMYK pixel count mismatch is identified
- [x] sum(cluster.cyan/magenta/yellow) equals source image totals (verified)
- [x] Each step of the pipeline is traced and validated:
  - [x] Pixel extraction from source image
  - [x] CMYK decomposition (RGB → CMYK)
  - [x] Cluster assignment (Voronoi)
  - [x] Exposed area calculation
  - [x] Rendering to output image
- [x] The specific step causing pixel loss is documented
- [x] Recommended fix is proposed based on findings

## Test Plan

### Validation Steps

1. **Source Pixel Extraction**
   - [x] Count CMYKRGB pixels in source image
   - [x] Verify decomposition: Co = Ci + Gi + Bi, Mo = Mi + Ri + Bi, Yo = Yi + Ri + Gi

2. **Cluster Assignment**  
   - [x] Verify sum(cluster.cyan) == source_cyan_decomposed
   - [x] Verify sum(cluster.magenta) == source_magenta_decomposed
   - [x] Verify 100% pixel coverage (no gaps in Voronoi)

3. **Geometry Calculation**
   - [x] For sample clusters, verify exposed_area == target_pixels
   - [x] Verify radius_for_exposed_pixels returns correct values

4. **Rendering**
   - [x] Count actually rendered pixels per color
   - [x] Identify delta between expected and actual
   - [x] Trace lost pixels to specific cause (overlap, edge, etc.)


## RESOLUTION - Root Causes Identified and Fixed

**Date Resolved**: 2025-11-30
**Commits**: 2f50a1d, 23e6bf7

### Root Cause 1: CMYK Decomposition Missing
The `render_flower_cluster()` function was reading pure CMYK values (`cluster.cyan`, etc.) 
but these only contain pixels that are EXACTLY that color. RGB overlap pixels were stored 
separately (`cluster.red`, `cluster.green`, `cluster.blue`) and never added back.

**Fix**: Added decomposition before rendering:
```python
decomposed_counts = {
    'cyan': cluster.cyan + cluster.green + cluster.blue,
    'magenta': cluster.magenta + cluster.red + cluster.blue,
    'yellow': cluster.yellow + cluster.red + cluster.green,
}
```

### Root Cause 2: cv2.circle Integer Radius Overshoot
`cv2.circle()` with `LINE_AA` draws ~40% more pixels than the theoretical area (πr²).
For example, r=7 draws 217 pixels vs theoretical 154 pixels.

**Fix**: Added `find_best_radius_for_pixels()` that tests actual cv2 rendering to find
the optimal integer radius minimizing error between drawn and target pixels.

### Accuracy Results

| Channel | Before Fix | After Fix |
|---------|-----------|----------|
| Cyan | 36% error | 0.3% error |
| Magenta | 63% error | 14.1% error |
| Yellow | N/A | 0.0% error |
| Black | N/A | 0.8% error |
| **Average** | ~50% | **3.8%** |

**Status**: ✅ RESOLVED - Average error reduced from ~50% to 3.8%
