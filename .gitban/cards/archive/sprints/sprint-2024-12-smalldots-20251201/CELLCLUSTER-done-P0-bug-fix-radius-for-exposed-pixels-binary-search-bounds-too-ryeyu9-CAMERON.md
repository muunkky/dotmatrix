## Bug Description

`radius_for_exposed_pixels()` in `circle_renderer.py:195` uses a binary search upper bound that is too tight:

```python
r_max = radius_from_pixels(target_exposed * 3)  # Assumes max 2/3 hidden
```

This assumes at most 2/3 of the petal is hidden behind black. But with `petal_distance=0.5`, the petal center is **inside** the black circle, hiding almost ALL of the petal.

## Steps to Reproduce

```python
from src.dotmatrix.circle_renderer import radius_from_pixels, exposed_area, radius_for_exposed_pixels

target = 261  # magenta pixels
black_r = 19.56
dist = 9.78  # = 0.5 * black_r (petal center inside black)

r = radius_for_exposed_pixels(target, black_r, dist)
actual = exposed_area(r, black_r, dist)

print(f"Target: {target}, Got: {actual}")  
# Output: Target: 261, Got: 158.8  ← WRONG!
```

## Expected Behavior

`radius_for_exposed_pixels(261, 19.56, 9.78)` should return a radius such that `exposed_area(r, 19.56, 9.78) == 261`.

## Actual Behavior

Returns r=15.79 which gives exposed_area=158.8 (only 61% of target).

## Root Cause

Binary search upper bound `r_max = target * 3` is not enough. Testing shows:
- 3x multiplier: exposed=158.8 (not enough)
- 4x multiplier: exposed=290 (overshoots, can binary search down)

## Impact

- **23% loss of magenta pixels** across all clusters
- **3% loss of cyan pixels**
- Causes visible accuracy degradation in reconstituted images

## Solution

Change line 195 from:
```python
r_max = radius_from_pixels(target_exposed * 3)
```

To:
```python
r_max = radius_from_pixels(target_exposed * 10)  # Safe upper bound for high occlusion
```

Or compute dynamically based on overlap ratio.

## Environment

- File: `src/dotmatrix/circle_renderer.py`
- Line: 195
- Function: `radius_for_exposed_pixels()`

## Acceptance Criteria

- [x] Fix binary search upper bound
- [x] Add unit test for high-occlusion case (petal center inside black)
- [x] Verify magenta loss drops from 23% to <1%
- [x] Run cmyk_accuracy comparison to confirm improvement
