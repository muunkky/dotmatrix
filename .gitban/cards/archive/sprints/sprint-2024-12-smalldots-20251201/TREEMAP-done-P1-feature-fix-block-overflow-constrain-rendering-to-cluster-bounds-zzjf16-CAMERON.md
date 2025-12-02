# Fix Block Overflow - Constrain Rendering To Cluster Bounds

**Type:** Bug Fix
**Priority:** P1
**Status:** backlog
**Sprint:** TREEMAP
**Card ID:** zzjf16

## Description
The current block renderer creates bars that overflow beyond cluster boundaries. Black bars especially can extend off the edge of the image. This must be fixed before treemap layout can work correctly.

## Problem Analysis
- Current block renderer stacks bars vertically without height constraint
- Bars can overflow image bounds when pixel counts are large
- No bounds checking on calculated dimensions
- cluster.x/y is treated as starting position, not center

## Acceptance Criteria
- [x] Blocks are constrained to stay within cluster bounds
- [x] Blocks do not overflow image boundaries
- [x] Total rendered area matches cluster bounding box
- [x] Test verifies no pixels rendered outside bounds

## Implementation Tasks (Resolved via Treemap Renderer)
- [x] Define cluster bounding box calculation - implemented in treemap_renderer.get_cluster_bounds()
- [x] Add bounds constraint - treemap renderer inherently constrains to bounds
- [x] Add clipping when content exceeds bounds - render_single_treemap clips to image bounds
- [x] Add test for boundary constraint verification - TestRenderSingleTreemap::test_stays_within_cluster_bounds
- [x] N/A - block renderer unchanged, treemap is new approach

## Test Plan (Implemented)
- [x] Unit test: verify no pixels outside cluster bounds (test_stays_within_cluster_bounds)
- [x] Unit test: verify rendering scales to fit (slice_and_dice proportional allocation)
- [x] Integration test: test_no_overflow_with_large_counts

## Dependencies
- None (first in sprint order)

## Resolution Notes
Instead of modifying the block renderer, we created a new treemap renderer (src/dotmatrix/treemap_renderer.py)
that inherently solves the overflow problem by:
1. Defining fixed cluster bounds via get_cluster_bounds(cluster, cluster_size)
2. Using slice-and-dice algorithm to subdivide proportionally within those bounds
3. Clipping to image boundaries in render_single_treemap()

The block renderer remains unchanged for users who prefer that style.
