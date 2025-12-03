# CLUSTERING Sprint Planning

## Sprint Goal
Implement CMYK cluster pixel counting system that outputs `[x, y, C, M, Y, K, R, G, B]` per cluster.

## Implementation Order (TDD Approach)

### Phase 0: Test Infrastructure
- [ ] Create test fixtures (synthetic CMYK halftone images)
- [ ] Define expected outputs for test cases
- [ ] Set up test module `tests/test_cluster_pixel_counter.py`

### Phase 1: Core Module Structure
- [ ] Create `src/dotmatrix/cluster_pixel_counter.py`
- [ ] Define `ClusterResult` dataclass
- [ ] Define main API: `cluster_and_count_pixels(image, ink_masks) -> List[ClusterResult]`

### Phase 2: Midtone Completion (Tests First)
- [ ] Test: complete_midtone_mask() includes RGB overlaps
- [ ] Implement: `complete_midtone_mask(ink_mask, overlap_masks) -> completed_mask`
- [ ] Test: verify cyan mask includes G and B pixels
- [ ] Test: verify magenta mask includes R and B pixels
- [ ] Test: verify yellow mask includes R and G pixels

### Phase 3: Clustering (Tests First)
- [ ] Test: find_black_dot_centers() returns correct centers
- [ ] Implement: `find_black_dot_centers(k_mask) -> List[Tuple[int, int]]`
- [ ] Test: assign_pixel_to_cluster() finds nearest black pixel
- [ ] Implement: `assign_pixel_to_cluster(pixel, k_mask) -> cluster_id`
- [ ] Test: cluster entire image correctly

### Phase 4: Pixel Counting with Deduplication (Tests First)
- [ ] Test: count_pixels_per_cluster() returns correct counts
- [ ] Test: deduplication subtracts RGB from CMY correctly
- [ ] Implement: `count_pixels_per_cluster(clusters, masks) -> ClusterResult`
- [ ] Test: no double counting in final output

### Phase 5: Edge Cases
- [ ] Test: edge clusters flagged as partial
- [ ] Test: missing colors (0 count) handled
- [ ] Test: max 1 of each color validation
- [ ] Implement edge handling

### Phase 6: CLI Integration
- [ ] Add `--cluster-count` CLI flag
- [ ] Output format: JSON array of [x, y, C, M, Y, K, R, G, B]
- [ ] Integration tests

## Dependencies
- Existing `separate_cmyk_inks()` from convex_detector.py
- scipy.spatial for KDTree (nearest neighbor)

## Success Criteria
- [ ] All unit tests pass
- [ ] No double counting verified
- [ ] Edge clusters flagged correctly
- [ ] Output matches expected format
