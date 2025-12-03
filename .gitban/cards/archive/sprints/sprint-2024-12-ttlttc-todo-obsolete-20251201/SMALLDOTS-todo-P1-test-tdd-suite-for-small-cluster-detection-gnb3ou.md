# Test: TDD Suite for Small Cluster Detection

## Testing Goal

Small Cluster Detection - Test Coverage Improvement

Ensure the multi-pass detection algorithm correctly identifies small halftone clusters that were previously missed. Tests should be written TDD-style: first create failing tests that define expected behavior, then implement the feature to make them pass.

**Value**: Prevent regression of small cluster detection. Ensure $50k+ print quality by verifying complete halftone coverage. Enable confident refactoring of detection algorithms.

**Current Coverage**: 0% (new feature)

**Target Coverage**: 90% for multi-pass detection code

**Estimated Effort**: 1 day

---

## Test Scope

### Modules to Test

- [ ] **gap_detection module**: Voronoi computation and gap identification
  - `compute_voronoi_regions`: Verify correct region labeling
  - `find_gap_regions`: Verify gaps identified where expected

- [ ] **sensitive_detection module**: Second-pass detection in gap regions
  - `detect_in_region`: Verify detection with lower thresholds
  - `merge_detections`: Verify duplicate removal

- [ ] **integration**: Full multi-pass pipeline
  - `run_multi_pass_detection`: End-to-end test

### Code Paths to Cover

- [x] Happy path scenarios
- [x] Error handling paths
- [x] Edge cases and boundary conditions

### Out of Scope

- GPU acceleration (tested separately)
- Rendering (separate card)

---

## Test Scenarios

### Happy Path Scenarios

1. **Synthetic image with known small dots**:
   - Setup: Create 100x100 image with 3 large dots and 2 small dots between them
   - Action: Run multi-pass detection
   - Expected: All 5 dots detected
   - Test: Assert len(centers) == 5

2. **Real image with orphan region**:
   - Setup: Crop orphan region from `input_large.png` (X:1597-1700, Y:1831-1950)
   - Action: Run detection, count orphan pixels
   - Expected: Orphan count < 100 (was ~2000 in this crop)
   - Test: Assert orphan_count < 100

### Edge Cases

- [x] Empty image (no dots) - should return empty list
- [x] Image with only large dots - should match single-pass
- [x] Image with overlapping Voronoi regions
- [x] Gap region at image edge
- [ ] Very small dots (radius < 3px)

### Error Conditions

- [x] Invalid image input - should raise ValueError
- [x] Empty cluster list - should handle gracefully
- [x] Gap region outside image bounds

---

## Acceptance Criteria

### Coverage Achieved

- [ ] Target coverage percentage met: 90%
- [x] All modules in scope covered
- [x] All critical paths have tests

### Test Quality

- [ ] All tests pass consistently
- [ ] No flaky tests
- [x] Tests are well-named and documented
- [x] Tests follow pytest conventions

---

## Implementation Plan (optional)

### Phase 1: Test Infrastructure

1. **Create test fixtures**:
   - [ ] Synthetic images with known dot positions
   - [ ] Cropped orphan region from real image
   - [ ] Expected detection results for each

2. **Create test utilities**:
   - [ ] `create_synthetic_halftone(dots: List[Tuple[int, int, int]])` - create test image
   - [ ] `count_orphan_pixels(image, centers, threshold)` - count unassigned pixels

### Phase 2: Write Failing Tests (TDD)

3. **Unit Tests** (write before implementation):
   - [ ] `test_voronoi_regions_correct_labels`
   - [ ] `test_gap_detection_finds_empty_regions`
   - [ ] `test_sensitive_detection_finds_small_dots`
   - [ ] `test_merge_removes_duplicates`

4. **Integration Tests**:
   - [ ] `test_multipass_detects_all_dots_synthetic`
   - [ ] `test_multipass_reduces_orphans_real_image`
   - [ ] `test_multipass_performance_acceptable`

### Phase 3: Implementation Support

5. **After feature implementation**:
   - [ ] Run all tests - should pass
   - [ ] Add regression tests for any bugs found
   - [ ] Measure coverage, add tests to reach 90%

---

## Related Cards (optional)

### Features Being Tested

**Tests**: kk5hjj - Multi-Pass Detection for Small Clusters

### Blocks

**Blocks**: Sprint closeout - cannot verify sprint complete until tests pass




## Test Types (optional)

### Unit Tests

- [ ] Test individual functions in isolation
- [ ] Mock external dependencies
- [ ] Cover all code branches
- [ ] Test with valid inputs
- [ ] Test with invalid/edge case inputs
- [ ] Test error conditions




## Test Plan

- [ ] Write failing tests first (TDD)
- [ ] Create synthetic test images with known dot positions
- [ ] Run tests against implementation
- [ ] Measure coverage and reach 90% target
- [ ] Add regression tests for any bugs found
