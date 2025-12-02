# Adapt Global CMY Blending to Sliding Window for Large Files

## Context
The global CMY blending approach (phased rendering) requires collecting all circle geometry before compositing. For very large images, this could consume significant memory.

## Problem
- Global blending requires holding all cluster geometry in memory
- Large images with many clusters could exceed available memory
- Need a way to process in chunks while maintaining correct cross-cluster blending

## Proposed Approach
Consider a sliding window / tiled approach:
1. Process image in overlapping tiles
2. For each tile, identify clusters whose bounding boxes intersect the tile
3. Render CMY globally within tile, accounting for edge clusters
4. Blend tiles together with proper overlap handling

## Acceptance Criteria
- [ ] Define memory threshold for switching to windowed mode
- [ ] Implement tile-based processing with overlap
- [ ] Ensure correct blending at tile boundaries
- [ ] Benchmark memory usage vs quality tradeoff
