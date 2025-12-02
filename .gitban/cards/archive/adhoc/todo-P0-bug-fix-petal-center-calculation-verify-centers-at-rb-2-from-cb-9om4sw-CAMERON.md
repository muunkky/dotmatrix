## Problem

Flower renderer petals are not consistently positioned inside the black dot. Some petals (especially large cyan ones) appear to have their centers outside the black circle, creating full circles instead of crescents.

**Expected behavior**: All petal centers should be at `Rb/2` from `Cb` (half the black radius from the center of the black dot), producing consistent crescent shapes.

**Actual behavior**: Some petals appear correctly as crescents, but others (particularly large cyan) look like full circles barely touching the black.

## Root Cause Investigation

Check `circle_renderer.py` around line 334 where petal distance is calculated:

```python
# Current formula (after FLOWERFIX):
dist = black_radius * petal_distance
```

Where `petal_distance` defaults to 0.5.

**Questions to verify:**
1. Is `dist` being used correctly as distance from black center to petal center?
2. Is the petal center being placed at `(cx + dist * cos(angle), cy + dist * sin(angle))`?
3. Is this calculation consistent for all petal colors regardless of petal size?
4. Are larger petals getting different treatment that moves their centers?

## Additional Issue: No RGB from petal overlap

Petals within the same cluster are NOT overlapping each other (they have room around them), so no RGB secondary colors are being produced via `--blend-overlaps`.

However, petals ARE overlapping with OTHER clusters. We should NOT blend across clusters because:
- Cross-cluster overlap is unintended
- Creates unwanted RGB colors
- Increases total ink coverage (we want to reduce it)

**Possible fix**: Only apply subtractive blending within the same cluster, not across clusters.

## Acceptance Criteria

- [ ] Verify petal center formula: center should be at `black_center + (black_radius * 0.5) * direction`
- [ ] All petal colors should use the same center calculation
- [ ] Large petals should still have centers inside black, producing crescents
- [ ] Document the expected geometry with a diagram if needed
- [ ] Consider whether blend-overlaps should be cluster-local only

## Test Case

Use the corner_test.png image and visually inspect:
1. All petals should be crescents, not full circles
2. The amount of black visible should be consistent
3. Larger petals = larger crescents, but still crescents
