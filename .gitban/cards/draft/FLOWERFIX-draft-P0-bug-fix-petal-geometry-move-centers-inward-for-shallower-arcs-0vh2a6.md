## Bug Description

**Summary**: Petal circles in flower renderer are positioned with centers at the black circle edge, creating "pointy" petals that intrude excessively into neighboring cluster space. Moving petal centers inward (toward black center) will create shallower, more rounded arcs.

**Severity**: P0/Critical - Petals intrude on neighboring clusters, making output look wrong

**Value of Fix**: Flower petals will have pleasing rounded shapes that don't interfere with adjacent clusters.

**Discovered**: User testing after CIRCLERENDER sprint

**Reporter**: User (suggested moving centers to "r/2 or something")

---

## Steps to Reproduce

### Prerequisites
- Input image with CMYK halftone pattern
- DotMatrix CLI installed

### Reproduction Steps

1. **Run flower renderer**:
   ```bash
   python -m dotmatrix -i inputs/corner_test.png -m halftone --reconstitute --render-method flower --blend-overlaps
   ```

2. **View output**:
   - Open `output/run_*/reconstituted.png`

3. **Observe**: Petals appear "pointy" with sharp intrusions into white space between clusters

### Expected Behavior
- Petal visible arcs should be shallow curves
- Petals should not intrude far into neighboring cluster space
- Flower pattern should look balanced

### Actual Behavior
- Petal arcs are sharp/pointy
- Petals extend far beyond black circle boundary
- Creates crowded appearance between clusters

### Reproduction Rate
- **Consistency**: Always
- **Success rate**: 10 out of 10 attempts

---

## Root Cause Analysis

### Investigation Findings

**Code Location**: `src/dotmatrix/circle_renderer.py:333-334`

**Logic Error**: Petal distance formula positions centers too far from black center:

```python
# Current formula (line 334):
dist = black_radius + preliminary_radius * petal_distance
```

With `petal_distance=0.7` (default), this puts petal center at:
- `dist = black_radius + 0.7 * petal_radius`
- This is OUTSIDE the black circle edge!

### Technical Details

**Current Geometry**:
```
                    petal center
                         |
     black center -------|----> (black_radius + 0.7*petal_radius)
         |               |
         |<- black_r ->| |<-- petal protrusion
```

**Proposed Geometry** (per technical design spike scv7f9):
```
              petal center
                   |
     black center -|----> (black_radius * 0.5)
         |         |
         |<- r/2 ->|
         |<--- black_radius --->|
```

**Why Current Is Wrong**: Petal centers should be INSIDE the black circle to create shallow arcs, not outside creating pointy protrusions.

---

## Solution

### Fix Strategy

**Approach**: Change petal distance formula per technical design spike recommendation.

**Complexity**: Simple - single line change + default value change
**Risk**: Low - formula change is well-understood from design spike

### Code Changes

```python
# Before (line 334):
dist = black_radius + preliminary_radius * petal_distance

# After:
dist = black_radius * petal_distance
```

And change default `petal_distance` from `0.7` to `0.5`:

```python
# Before (line 275):
petal_distance: float = 0.7,

# After:
petal_distance: float = 0.5,
```

**Explanation**: 
- With `petal_distance=0.5`, petal center is at r/2 from black center
- This means petal center is INSIDE black circle
- More of petal is hidden behind black
- Visible arc is shallower and rounder
- `exposed_area_sizing` will automatically compensate by increasing petal radius

### Implementation Steps

1. Change formula at line 334
2. Change default at lines 275 and 429
3. Verify exposed_area calculation still works correctly
4. Test with various petal_distance values (0.3, 0.5, 0.7) to confirm 0.5 is good default

### Rollback Plan

1. Revert single commit
2. Old geometry restored

---

## Testing & Verification

### Bug Reproduction Verification

- [ ] Confirm pointy petal appearance in current version
- [ ] Capture screenshot showing intrusion into neighbors

### Fix Verification

- [ ] Petals have shallower, rounder arcs
- [ ] Petals don't intrude far into neighboring cluster space
- [ ] Visual appearance matches expected halftone flower pattern
- [ ] exposed_area_sizing still produces correct pixel counts

### Regression Testing

- [ ] All existing unit tests pass
- [ ] Blend mode still works correctly (after ffii9o fix)
- [ ] Non-blend mode still works
- [ ] Various rotation modes still work

### Visual Comparison

- [ ] Generate output with old formula (petal_distance=0.7, old formula)
- [ ] Generate output with new formula (petal_distance=0.5, new formula)
- [ ] Side-by-side comparison shows improvement

---

## Regression Prevention

### Automated Tests Added

- [ ] **Unit Test**: `test_circle_renderer.py::test_petal_center_inside_black_radius`
  - Tests: With petal_distance=0.5, petal center distance < black_radius
  - Coverage: Petal positioning formula

- [ ] **Unit Test**: `test_circle_renderer.py::test_petal_arc_shallower_than_before`
  - Tests: Visible petal arc doesn't extend as far as before
  - Coverage: Geometry validation

---

## Related Issues

### Depends On
- **ffii9o**: Black circle clipping fix must be done first
- **scv7f9**: Technical design spike (provides rationale)

### Validates Assumptions From
- scv7f9 Assumption 2: "Moving petal centers inward creates shallower arcs"
- scv7f9 Assumption 3: "Optimal petal distance is between 0 and black_radius"

---

## Notes

### Mathematical Background

The visible portion of a petal is the part outside the black circle. By moving the petal center inward:
- Overlap with black increases
- Exposed area decreases (compensated by larger radius via exposed_area_sizing)
- Visible arc has larger radius of curvature (shallower)
- Protrusion distance from black edge decreases

### CLI Parameter

The `petal_distance` parameter will still be available for tuning, but the new default (0.5) should work well for most cases. Advanced users can adjust via `--petal-distance` CLI flag.
