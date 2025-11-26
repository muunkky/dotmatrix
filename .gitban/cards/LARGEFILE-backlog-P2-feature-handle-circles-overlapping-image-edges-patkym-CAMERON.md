# Handle Circles Overlapping Image Edges

## Description
Detect and handle circles that are partially cut off at image edges. Currently, HoughCircles may miss circles that extend beyond image boundaries. This is a nice-to-have enhancement for better detection coverage.

## Priority
P2 - Lower priority enhancement. Can be deferred if time-constrained.

## Acceptance Criteria
- [ ] Detect circles with centers inside image but radius extending beyond
- [ ] Correctly estimate radius for partial circles at edges
- [ ] Optional flag to enable/disable edge circle detection
- [ ] Mark edge circles in output (e.g., `"partial": true`)

## Implementation Approach
*Research needed - potential approaches:*
1. **Image padding**: Pad image edges with background color, then detect
2. **Arc detection**: Detect circular arcs at edges and estimate full circles
3. **Reduced radius search**: Search for smaller circles near edges
4. **Mask-aware detection**: Use edge mask to guide detection

## Test Plan
- [ ] Create test images with circles at all 4 edges
- [ ] Test corner cases (circles in corners)
- [ ] Verify center and radius accuracy for partial circles

## Notes
- Lower priority than large file handling
- May be complex to implement accurately
- Consider as future enhancement if time permits
