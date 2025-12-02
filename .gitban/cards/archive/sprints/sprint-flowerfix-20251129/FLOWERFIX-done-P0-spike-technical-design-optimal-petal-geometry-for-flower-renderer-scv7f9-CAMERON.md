## Problem Statement

**Decision**: How should petal circle centers be positioned relative to the black circle to create visually pleasing flower patterns with minimal intrusion into neighboring clusters?

The current implementation places petal centers at `dist = black_radius + petal_radius * petal_distance`, which with `petal_distance=0.7` puts centers near the edge of the black circle. This creates "pointy" petals that intrude into neighboring cluster space.

---

## Time Box

**Maximum Time**: 4 hours

---

## Success Criteria

**We'll know this spike is successful when**:
- [x] Architecture options identified and evaluated
- [x] Clear recommendation made with rationale
- [x] Trade-offs documented
- [x] Implementation guidance provided for bug fix card

---

## Key Assumptions (Document for Review)

**CRITICAL: These assumptions must be validated. If wrong, revisit design.**

1. **Assumption: Petal circles should be hidden behind black where they overlap**
   - Current behavior: CMY is visible through black
   - Expected behavior: Black fully occludes CMY in overlap region
   - Risk if wrong: Blending logic needs redesign

2. **Assumption: Moving petal centers inward creates shallower arcs**
   - Geometry: Arc curvature = 1/radius, but visible arc shape depends on intersection
   - Risk if wrong: May need different radius formula, not just position change

3. **Assumption: Optimal petal distance is between 0 and black_radius**
   - Range: 0 = concentric (all at center), black_radius = current behavior
   - Candidate: black_radius * 0.5 (halfway to edge)
   - Risk if wrong: May need petal_radius-dependent formula

4. **Assumption: Same positioning works for all CMYK ratios**
   - Test case: Clusters with different C:M:Y:K proportions
   - Risk if wrong: May need adaptive positioning based on pixel counts

---

## Solution Options

### Option 1: Inward Center Positioning (Fractional Black Radius)

**Description**: Position petal centers at a fraction of black_radius from center, not at edge.

**Formula**: `dist = black_radius * center_factor` where `center_factor` in [0.3, 0.7]

**Geometry Analysis**:
```
Current (center_factor = 1.0 + petal_ratio):
  - Petal center at black edge
  - Maximum protrusion into white space
  - Sharp/pointy petal appearance

Proposed (center_factor = 0.5):
  - Petal center at r/2 from black center
  - Petal intersects black circle deeply
  - More of petal hidden, less protrusion
  - Rounder, shallower visible arc
```

**Pros**:
- Simple formula change
- Single parameter to tune
- Works for all cluster sizes

**Cons**:
- May need to increase petal radius to maintain visible area
- More of each petal hidden (but that's the point)

**Complexity**: Low

### Option 2: Fixed Protrusion Distance

**Description**: Position petals so they protrude a fixed distance beyond black edge.

**Formula**: `dist = black_radius - protrusion_factor * petal_radius`

**Geometry Analysis**:
- Petal extends `protrusion_factor * petal_radius` beyond black edge
- Smaller petals protrude less, larger petals more
- Creates consistent "petal depth" appearance

**Pros**:
- Consistent petal depth appearance
- Scales with petal size

**Cons**:
- Two parameters to tune
- May look inconsistent for very different petal sizes

**Complexity**: Medium

### Option 3: Arc-Based Positioning (Visible Arc Angle)

**Description**: Position petals to achieve target visible arc angle.

**Formula**: Solve for `dist` such that visible arc = target_angle degrees

**Geometry Analysis**:
- More complex trigonometry
- Guarantees consistent arc appearance
- May require iterative solver

**Pros**:
- Most visually consistent
- Independent of circle sizes

**Cons**:
- Complex math
- Computationally expensive
- May be over-engineering

**Complexity**: High

---

## Comparison Matrix

| Criteria | Option 1: Inward | Option 2: Fixed Protrusion | Option 3: Arc-Based | Weight |
|----------|------------------|---------------------------|---------------------|--------|
| Simplicity | High | Medium | Low | High |
| Visual Quality | Medium | High | High | High |
| Consistency | Medium | High | High | Medium |
| Performance | High | High | Medium | Medium |
| Maintainability | High | Medium | Low | High |

---

## Recommendation

**Decision**: Option 1 - Inward Center Positioning with `center_factor = 0.5`

**Rationale**: 
1. Simplest implementation - single line change
2. User suggested "move centers to r/2" which maps directly to `center_factor = 0.5`
3. Easy to tune if needed
4. Combined with exposed_area_sizing already in place, will maintain correct pixel counts

**Implementation Guidance**:
```python
# Current (line 334):
dist = black_radius + preliminary_radius * petal_distance

# Proposed:
dist = black_radius * petal_distance  # where petal_distance default = 0.5
```

**Confidence Level**: Medium

**Risks**:
- May need to adjust exposed_area calculation for new geometry
- Visual appearance may need further tuning

**Mitigations**:
- Keep petal_distance as tunable parameter
- Test with multiple cluster configurations before committing

---

## Proof of Concept Approach

**POC approach**: 
1. Change formula in circle_renderer.py
2. Run on corner_test.png with various petal_distance values (0.3, 0.5, 0.7)
3. Compare visual output
4. Select best default value

**POC repository**: Will be done in-place during bug fix card

---

## Deliverables

**Recommended outputs**:
- [x] Architecture options identified
- [x] Clear recommendation made
- [x] Visual comparison of options (defer to bug fix card)

---

## Next Steps

**If recommendation accepted**:
- [x] Create bug fix card with implementation steps
- [x] Update exposed_area calculation if needed
- [x] Add visual regression tests

---

## Additional Notes

### Mathematical Background

For two circles with radii r1 (petal) and r2 (black), separated by distance d:

- **No overlap**: d >= r1 + r2
- **Partial overlap**: |r1 - r2| < d < r1 + r2
- **Full containment**: d <= |r1 - r2|

The visible arc of the petal is determined by the chord where the circles intersect.

### Exposed Area Impact

The `exposed_area()` function already calculates visible petal area after black overlap. Moving centers inward will:
1. Increase overlap area (lens_area)
2. Decrease exposed area
3. Trigger larger petal radius via `radius_for_exposed_pixels()`

This should automatically compensate for the position change.
