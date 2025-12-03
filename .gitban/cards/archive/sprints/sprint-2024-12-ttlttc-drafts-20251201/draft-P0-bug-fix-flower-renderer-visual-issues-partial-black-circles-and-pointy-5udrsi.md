# Bug: Flower Renderer Visual Issues

## Problem Statement
The flower renderer has multiple visual defects that make the reconstituted output look incorrect:

1. **Black circles are partial/cut off**: Many black circles appear to be truncated, as if the rendering "ran out of pixels" partway through drawing
2. **CMY petals visible behind black**: The cyan, magenta, and yellow petals are not properly hidden behind the black circle - they show through where they should be occluded
3. **Petals too pointy**: The petal circle centers are positioned on the edge of the black circle, creating sharp/pointy petal shapes that intrude into neighboring clusters

## Reproduction
```bash
python -m dotmatrix -i inputs/corner_test.png -m halftone --reconstitute --render-method flower --blend-overlaps --petal-rotation cluster-hash
```

View `output/run_*/reconstituted.png` - black circles are partial and petals are too pointy.

## Root Cause Analysis
Looking at `circle_renderer.py`, the petal positioning uses:
```python
# Distance from center: black radius + petal radius * distance factor
dist = black_radius + preliminary_radius * petal_distance
```

With `petal_distance=1.0` (default), petal centers sit exactly on the black circle edge. This creates:
- Maximum protrusion into white space (pointy appearance)
- Complex overlap geometry at the black boundary

## Proposed Fix
1. **Move petal centers inward**: Change default `petal_distance` to ~0.5 or make it configurable
   - Centers at `r/2` from black center = shallower arcs
   - Less intrusion into neighboring clusters
   - More rounded petal appearance

2. **Fix black circle clipping**: Investigate why black circles are being drawn partially - likely a bounds/canvas issue

3. **Fix petal occlusion**: Ensure petals are properly masked by black circle or drawn in correct z-order

## Acceptance Criteria
- [ ] Black circles render fully without clipping
- [ ] CMY petals are hidden behind black circle where they overlap
- [ ] Petal geometry uses shallower arcs (centers moved toward black center)
- [ ] Visual output matches expected halftone flower pattern
- [ ] No regression in existing tests

## Technical Notes
- May need to adjust canvas size calculation
- Z-order: black should always render on top of CMY
- Consider making petal_distance configurable via CLI
