## Refactoring Goal

Consolidate `lens_area()` and `exposed_area()` functions in `circle_renderer.py` into a single, cleaner `calculate_remaining_area()` function with explicit edge case handling.

**Value**: Improved code readability and maintainability - edge cases clearly documented inline

**Complexity**: Low

**Estimated Effort**: 1-2 hours

---

## Current State

Two separate functions that split the logic unnecessarily:

### Code Location

**Path**: `src/dotmatrix/circle_renderer.py`

**Modules Affected**:
- `lens_area()`: Lines 109-141 - calculates circle intersection area
- `exposed_area()`: Lines 144-157 - subtracts lens from total area

### Problems with Current Code

1. **Split Logic**: Two functions where one would suffice
   - **Impact**: Readers must understand both functions to follow the math
   - **Example**: `exposed_area` just calls `lens_area` and subtracts

2. **Implicit Edge Cases**: Edge cases handled in `lens_area` but not clearly documented
   - **Impact**: Hard to verify correctness at a glance
   - **Example**: `d <= abs(r1 - r2)` case not obviously correct

### Current Code

```python
def lens_area(r1: float, r2: float, d: float) -> float:
    if d <= 0:
        return math.pi * min(r1, r2) ** 2
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return math.pi * min(r1, r2) ** 2
    # ... formula ...

def exposed_area(petal_radius, black_radius, distance):
    total_area = math.pi * petal_radius ** 2
    overlap = lens_area(petal_radius, black_radius, distance)
    return max(0.0, total_area - overlap)
```

---

## Desired State

Single function with explicit, commented edge cases:

### Target Architecture

```python
def calculate_remaining_area(r_petal: float, r_black: float, d: float) -> float:
    """Calculate visible petal area after black circle overlap."""
    
    # Edge Case 1: No Overlap - circles too far apart
    if d >= r_petal + r_black:
        return math.pi * r_petal**2

    # Edge Case 2: Petal inside Black - fully hidden
    if r_black >= d + r_petal:
        return 0.0

    # Edge Case 3: Black inside Petal - subtract full black area
    if r_petal >= d + r_black:
        return math.pi * r_petal**2 - math.pi * r_black**2

    # Standard Case: Partial Overlap
    term1 = r_petal**2 * math.acos((d**2 + r_petal**2 - r_black**2) / (2 * d * r_petal))
    term2 = r_black**2 * math.acos((d**2 + r_black**2 - r_petal**2) / (2 * d * r_black))
    term3 = 0.5 * math.sqrt((-d + r_petal + r_black) * (d + r_petal - r_black) * 
                            (d - r_petal + r_black) * (d + r_petal + r_black))
    
    intersection = term1 + term2 - term3
    return math.pi * r_petal**2 - intersection
```

### Design Improvements

1. **Single Function**: All logic in one place
   - **Benefit**: Easier to understand and verify

2. **Explicit Edge Cases**: Each case clearly commented
   - **Benefit**: Self-documenting code

---

## Benefits

### Code Quality Benefits

- **Readability**: One function to understand instead of two
- **Maintainability**: Edge cases clearly visible
- **Testability**: Single function to test all cases

---

## Refactoring Steps

### Phase 1: Preparation

- [ ] Verify existing tests cover all edge cases
- [ ] Add tests for edge cases if missing (no overlap, full containment both ways)

### Phase 2: Refactoring

- [ ] Create new `calculate_remaining_area()` function
- [ ] Update `radius_for_exposed_pixels()` to call new function
- [ ] Deprecate or remove `lens_area()` and `exposed_area()`
- [ ] Run tests after each step

### Phase 3: Validation

- [ ] All existing tests pass
- [ ] Visual output unchanged (golden master comparison)

---

## Testing Strategy

### Behavioral Equivalence

- [ ] Same inputs produce same outputs for all edge cases
- [ ] Test: r1=10, r2=10, d=10 (partial overlap)
- [ ] Test: r1=10, r2=10, d=25 (no overlap)
- [ ] Test: r1=5, r2=10, d=2 (petal inside black)
- [ ] Test: r1=10, r2=5, d=2 (black inside petal)

---

## Related Cards

### Related To
- **FLOWERFIX sprint**: This is a cleanup after fixing the core bugs
- **scv7f9**: Technical design spike documents the math
