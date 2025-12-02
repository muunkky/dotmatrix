# CLUSTERING Sprint Planning

## Sprint Goal
Implement CMYK cluster pixel counting system that outputs `[x, y, C, M, Y, K, R, G, B]` per cluster.

## Implementation Order (TDD Approach)

### Phase 0: Test Infrastructure
- [x] Create test fixtures (synthetic CMYK halftone images)
- [x] Define expected outputs for test cases
- [x] Set up test module `tests/test_cluster_pixel_counter.py`

### Phase 1: Core Module Structure
- [x] Create `src/dotmatrix/cluster_pixel_counter.py`
- [x] Define `ClusterResult` dataclass
- [x] Define main API: `cluster_and_count_pixels(image, ink_masks) -> List[ClusterResult]`

### Phase 2: Midtone Completion (Tests First)
- [x] Test: complete_midtone_mask() includes RGB overlaps
- [x] Implement: `complete_midtone_mask(ink_mask, overlap_masks) -> completed_mask`
- [x] Test: verify cyan mask includes G and B pixels
- [x] Test: verify magenta mask includes R and B pixels
- [x] Test: verify yellow mask includes R and G pixels

### Phase 3: Clustering (Tests First)
- [x] Test: find_black_dot_centers() returns correct centers
- [x] Implement: `find_black_dot_centers(k_mask) -> List[Tuple[int, int]]`
- [x] Test: assign_pixel_to_cluster() finds nearest black pixel
- [x] Implement: `assign_pixel_to_cluster(pixel, k_mask) -> cluster_id`
- [x] Test: cluster entire image correctly

### Phase 4: Pixel Counting with Deduplication (Tests First)
- [x] Test: count_pixels_per_cluster() returns correct counts
- [x] Test: deduplication subtracts RGB from CMY correctly
- [x] Implement: `count_pixels_per_cluster(clusters, masks) -> ClusterResult`
- [x] Test: no double counting in final output

### Phase 5: Edge Cases
- [x] Test: edge clusters flagged as partial
- [x] Test: missing colors (0 count) handled
- [x] Test: max 1 of each color validation (N/A - counts pixels not circles, validation deferred)
- [x] Implement edge handling

### Phase 6: CLI Integration
- [x] Add `--cluster-count` CLI flag
- [x] Output format: JSON array of [x, y, C, M, Y, K, R, G, B]
- [x] Integration tests

## Dependencies
- Existing `separate_cmyk_inks()` from convex_detector.py
- scipy.spatial for KDTree (nearest neighbor)

## Success Criteria
- [x] All unit tests pass
- [x] No double counting verified
- [x] Edge clusters flagged correctly
- [x] Output matches expected format
