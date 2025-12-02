## Stakeholder Review & Signoff

**Stakeholder Notes:**
<!-- Space for notes, concerns, feedback -->

**Approval Checklist:**
- [x] CAMERON personally approves this feature for implementation

---

## Description

Add centroid-based cluster anchor as an alternative to nearest-pixel assignment in cluster_pixel_counter.py.

Currently, `cluster_and_count_pixels()` assigns non-black pixels to their nearest black *pixel*. This feature adds an option to use the nearest black dot *centroid* instead, which may provide more stable clustering for irregular or fragmented black regions.

**Value**: Improves clustering accuracy for images where black dots are not perfectly circular or have irregular boundaries. Centroid-based assignment is less sensitive to pixel-level noise at dot edges.

**Target Users**: Users processing low-quality halftone scans or images with compression artifacts.

**Estimated Effort**: 4 hours

---

## Acceptance Criteria

- [x] Add `anchor_method` parameter to `cluster_and_count_pixels()` with values `'centroid'` (default) and `'nearest_pixel'`
- [x] When `anchor_method='centroid'`, compute cluster assignment based on distance to black dot centroid
- [x] Legacy behavior available via `'nearest_pixel'` mode for backwards compatibility testing
- [x] Unit tests cover both anchor methods
- [x] CLI flag `--cluster-anchor` added with choices `pixel` and `centroid`

---

## Implementation Plan

### Overview

Modify `cluster_and_count_pixels()` to accept an `anchor_method` parameter. When set to `'centroid'`, use the existing `find_black_dot_centers()` output directly as anchor points instead of building a KDTree from all black pixels.

### Implementation Steps

1. **Add parameter to cluster_and_count_pixels()**: Add `anchor_method: str = 'centroid'` parameter with validation.

2. **Modify cluster label creation**: When `anchor_method='centroid'`, use `create_cluster_labels_from_centers()` (already exists) instead of `create_cluster_labels()`.

3. **Add CLI flag**: Add `--cluster-anchor` option to reconstitute command with choices `['pixel', 'centroid']`.

4. **Write unit tests**: Test both methods produce valid ClusterResult output. Test edge cases (single dot, no dots, overlapping dots).

### Technical Considerations

- **Architecture**: Minimal change - reuse existing `create_cluster_labels_from_centers()` function
- **Performance**: Centroid method may be slightly faster (fewer KDTree points)
- **Backwards Compatibility**: Default behavior unchanged

---

## Testing Strategy (optional)

### Unit Tests

- [x] Test `anchor_method='nearest_pixel'` produces expected output (regression)
- [x] Test `anchor_method='centroid'` produces valid ClusterResult
- [x] Test invalid `anchor_method` raises ValueError
- [x] Test both methods on sample halftone image

---

## Related Cards (optional)

**Related**: krzyj6 - ADR: CMYK Cluster Pixel Counting Architecture (parent ADR with "Future TODOs")
