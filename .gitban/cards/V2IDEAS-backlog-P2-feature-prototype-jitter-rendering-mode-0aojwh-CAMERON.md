

## Description
Implement a prototype for the jitter rendering mode based on research findings to add organic irregularity to the output.

## Acceptance Criteria
- [ ] Jitter rendering mode available in CLI
- [ ] Jitter intensity is configurable
- [ ] Output images show randomized dot displacement
- [ ] No collisions between dots (if collision avoidance is part of selected algo)

## Implementation Plan
- [ ] Create JitterRenderer class inheriting from BaseRenderer
- [ ] Implement randomization logic in render loop
- [ ] Add --jitter and --jitter-intensity CLI arguments
- [ ] Update main pipeline to support new renderer
- [ ] Generate sample outputs for verification

## Test Plan
- [ ] Unit tests for jitter calculation
- [ ] Visual regression tests comparing jittered vs non-jittered output
- [ ] Verify determinism with fixed seed
- [ ] Integration test with CLI params