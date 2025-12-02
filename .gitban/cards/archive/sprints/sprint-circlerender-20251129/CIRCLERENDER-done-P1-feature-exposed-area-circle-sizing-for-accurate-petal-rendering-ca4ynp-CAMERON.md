## Description

**Exposed Area Circle Sizing for Accurate Petal Rendering**

Calculate petal circle radii based on the VISIBLE/EXPOSED area after accounting for overlap with the black circle. Currently, circles are sized based on total area (πr²), but petals partially hide behind the black center, so the visible portion is less than the pixel count suggests.

**Value**: More accurate visual representation where the exposed color area matches the detected pixel counts. Users see correctly-proportioned petals that truly represent the color distribution in the source image.

**Target Users**: Users needing accurate visual reconstruction of halftone images

**Estimated Effort**: 4-6 hours (includes circle-circle intersection math)

---

## Acceptance Criteria

- [x] Implement lens area formula for two overlapping circles
- [x] Calculate exposed area = total_area - intersection_with_black
- [x] Solve for radius that gives target exposed area given black radius and distance
- [x] Add `--exposed-area-sizing` CLI flag to enable this mode
- [x] Default to current behavior (total area sizing) for backwards compatibility
- [x] Verify visually that petals appear correctly proportioned when exposed-area mode is enabled

---

## Implementation Plan

### Overview

When sizing a petal circle, account for the portion that will be hidden by the black center circle. The visible (exposed) area should equal the target pixel count, requiring a larger total radius.

### Implementation Steps

1. **Implement circle-circle intersection (lens) area formula**:
   ```python
   def lens_area(r1: float, r2: float, d: float) -> float:
       """Calculate intersection area of two circles.
       
       r1, r2: radii of the two circles
       d: distance between centers
       
       Returns area of the lens (intersection region).
       """
       if d >= r1 + r2:
           return 0.0  # No overlap
       if d <= abs(r1 - r2):
           # One circle inside the other
           return math.pi * min(r1, r2) ** 2
       
       # Lens area formula
       part1 = r1**2 * math.acos((d**2 + r1**2 - r2**2) / (2*d*r1))
       part2 = r2**2 * math.acos((d**2 + r2**2 - r1**2) / (2*d*r2))
       part3 = 0.5 * math.sqrt((r1+r2-d)*(d+r1-r2)*(d-r1+r2)*(d+r1+r2))
       return part1 + part2 - part3
   ```

2. **Implement exposed radius solver**:
   ```python
   def radius_for_exposed_pixels(
       target_exposed: int,
       black_radius: float,
       distance: float
   ) -> float:
       """Find radius such that visible area equals target.
       
       Uses numerical solver since analytical solution is complex.
       """
       # Binary search or scipy.optimize.brentq
   ```

3. **Update render_flower_cluster() to use exposed sizing**:
   - Add `use_exposed_area: bool = False` parameter
   - When enabled, use `radius_for_exposed_pixels()` instead of `radius_from_pixels()`

4. **Add CLI option**:
   - Add `--exposed-area-sizing` flag
   - Pass to render_flower()

### Technical Considerations

- **Numerical stability**: Lens area formula has edge cases at d=0, d=r1+r2
- **Solver convergence**: Binary search is robust; analytical solution exists but complex
- **Performance**: One solve per petal per cluster (~360 solves for 120 clusters × 3 colors)

---

## Testing Strategy (optional)

### Unit Tests

- [x] Test lens_area returns 0 for non-overlapping circles
- [x] Test lens_area returns smaller circle area when fully contained
- [x] Test lens_area formula against known values
- [x] Test radius_for_exposed_pixels finds correct radius
- [x] Test edge cases: zero black radius, zero distance

---

## Notes (optional)

### Design Decisions

- **Decision**: Use numerical solver (binary search) over analytical solution
- **Rationale**: Analytical solution for r given exposed area is complex inverse; numerical is robust and fast enough
- **Trade-offs**: Slightly slower but more maintainable code

### Research Findings

The lens area formula is well-documented:
- https://mathworld.wolfram.com/Circle-CircleIntersection.html
- Two overlapping circles form a "lens" or "vesica piscis" shaped intersection
