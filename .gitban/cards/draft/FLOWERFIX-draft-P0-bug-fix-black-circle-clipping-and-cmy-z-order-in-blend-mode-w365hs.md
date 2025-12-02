## Bug Description

**Summary**: Black circles are partially clipped/truncated in flower renderer blend mode because the `used` mask is set for CMY pixels before black is drawn, causing `draw_circle_exact` to skip pixels that should be black.

**Severity**: P0/Critical - Makes flower renderer output visually broken

**Value of Fix**: Reconstituted halftone images will have properly rendered black circles that fully occlude underlying CMY petals.

**Discovered**: User testing after CIRCLERENDER sprint

**Reporter**: User

---

## Steps to Reproduce

### Prerequisites
- Input image with CMYK halftone pattern (e.g., `inputs/corner_test.png`)
- DotMatrix CLI installed

### Reproduction Steps

1. **Run flower renderer with blend mode**:
   ```bash
   python -m dotmatrix -i inputs/corner_test.png -m halftone --reconstitute --render-method flower --blend-overlaps --petal-rotation cluster-hash
   ```

2. **View output**:
   - Open `output/run_*/reconstituted.png`

3. **Observe**: Black circles appear as partial circles, many cut off

### Expected Behavior
- Black circles should render fully as complete circles
- Black should fully occlude CMY where they overlap

### Actual Behavior
- Black circles appear partial/truncated
- CMY colors visible through/behind black

### Reproduction Rate
- **Consistency**: Always
- **Success rate**: 10 out of 10 attempts

---

## Root Cause Analysis

### Investigation Findings

**Code Location**: `src/dotmatrix/circle_renderer.py:380-394`

**Logic Error**: The blend mode code sets `used[any_cmy] = True` BEFORE drawing the black circle. When `draw_circle_exact` is called for black, it checks `if used[py, px]: continue` and skips pixels already marked as used.

### Technical Details

```python
# Current problematic code (lines 380-394):
# Copy blended result to image where any CMY ink was applied
# Only update pixels not already used
update_mask = any_cmy & ~used
image[update_mask] = blend_result[update_mask]
used[any_cmy] = True  # <-- BUG: Marks CMY pixels as used

# Count drawn pixels per color (approximate from masks)
drawn['cyan'] = int(np.sum(mask_c & ~used)) if radii['cyan'] > 0 else 0
drawn['magenta'] = int(np.sum(mask_m & ~used)) if radii['magenta'] > 0 else 0
drawn['yellow'] = int(np.sum(mask_y & ~used)) if radii['yellow'] > 0 else 0

# Draw black center last (on top)
if cluster.black > 0:
    drawn['black'] = draw_circle_exact(  # <-- Skips "used" pixels!
        image, cx, cy,
        cluster.black, COLORS_BGR['black'], used
    )
```

**Problem**: `draw_circle_exact` at line 258-260:
```python
for py, px in zip(circle_pixels[0], circle_pixels[1]):
    if used is not None and used[py, px]:
        continue  # <-- Skips pixels marked by CMY
```

**Why This Happens**: The blend mode correctly draws CMY first, then wants black on top. But by marking CMY pixels as "used", it prevents black from overwriting them.

---

## Solution

### Fix Strategy

**Approach**: Don't use `draw_circle_exact` for black in blend mode. Instead, draw black directly onto the image AFTER CMY blending, overwriting the CMY pixels.

**Complexity**: Simple - change a few lines
**Risk**: Low - only affects blend mode path

### Code Changes

```python
# Fixed code:
# Draw black center last (on top) - directly, not via draw_circle_exact
if cluster.black > 0:
    black_mask = make_circle_mask(cx, cy, radii['black'])
    # Overwrite CMY with black where black circle is
    image[black_mask] = COLORS_BGR['black']
    used[black_mask] = True
    drawn['black'] = int(np.sum(black_mask))
```

**Explanation**: Draw black by directly setting pixels, bypassing the `used` check. This ensures black always renders on top of CMY.

### Implementation Steps

1. In `render_flower_cluster()` blend mode section:
2. Replace `draw_circle_exact` call for black with direct mask-based drawing
3. Update `used` mask after drawing black
4. Update drawn count from mask

### Alternative Solutions

- **Alternative 1**: Pass `used=None` to `draw_circle_exact` for black
  - **Pros**: Minimal change
  - **Cons**: Black wouldn't update `used` mask properly
  - **Why Not Chosen**: Would break isolation between clusters

### Rollback Plan

1. Revert single commit
2. Flower renderer reverts to current behavior

---

## Testing & Verification

### Bug Reproduction Verification

- [ ] Confirm bug is reproducible in current version
- [ ] Document reproduction rate before fix
- [ ] Capture screenshots of bug manifestation

### Fix Verification

- [ ] Apply fix to test environment
- [ ] Verify black circles render fully
- [ ] Verify CMY petals are hidden behind black where they overlap
- [ ] Test with multiple input images

### Regression Testing

- [ ] All existing unit tests pass
- [ ] All existing integration tests pass
- [ ] Non-blend mode still works correctly
- [ ] No new bugs introduced by fix

### Edge Case Testing

- [ ] Test cluster with no black (all CMY)
- [ ] Test cluster with only black (no CMY)
- [ ] Test cluster at image edge
- [ ] Test overlapping clusters

---

## Regression Prevention

### Automated Tests Added

- [ ] **Unit Test**: `test_circle_renderer.py::test_black_renders_over_cmy_in_blend_mode`
  - Tests: Black pixels fully overwrite CMY in overlap region
  - Coverage: Blend mode black rendering

- [ ] **Unit Test**: `test_circle_renderer.py::test_black_not_clipped_by_cmy_mask`
  - Tests: Black circle has expected pixel count after rendering
  - Coverage: `used` mask handling

---

## Related Issues

### Depends On
- Technical design spike scv7f9 should be reviewed first to understand geometry

### Blocks
- Petal geometry fix depends on this being fixed first (z-order must work before adjusting positions)

---

## Notes

### Code Reference
- `src/dotmatrix/circle_renderer.py:348-394` - blend mode section
- `src/dotmatrix/circle_renderer.py:225-268` - draw_circle_exact function
