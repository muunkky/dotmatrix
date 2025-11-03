# Feature: Partial Circle Detection at Image Edges

## Description
Detect circles that extend beyond image boundaries using arc detection. Flag as partial in output.

## Acceptance Criteria
- [ ] Detects circles cut by edges
- [ ] Extrapolates full circle from arc
- [ ] Adds "partial": true flag to output
- [ ] `--detect-partial` CLI flag (default: true)
- [ ] >70% accuracy on test images
- [ ] Tests written (TDD)
- [ ] Docs updated

## Implementation
- [ ] Research arc detection approaches
- [ ] Create synthetic test images (edge circles)
- [ ] Add "partial" field to Circle dataclass
- [ ] Implement arc extrapolation logic
- [ ] Update formatters for partial flag
- [ ] Add CLI flag
- [ ] Write tests
- [ ] Update docs

## Technical Notes
- Complex feature - stretch goal for v0.2.0
- May require edge padding or multi-pass
- HoughCircles may miss partial arcs