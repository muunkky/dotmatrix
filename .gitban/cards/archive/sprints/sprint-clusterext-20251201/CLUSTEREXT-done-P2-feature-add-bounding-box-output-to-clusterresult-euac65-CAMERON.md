## Stakeholder Review & Signoff

**Stakeholder Notes:**
<!-- Space for notes, concerns, feedback -->

**Approval Checklist:**
- [x] CAMERON personally approves this feature for implementation

---

## Description

Add bounding box field to the ClusterResult dataclass in cluster_pixel_counter.py.

Each cluster should report its bounding box (x_min, y_min, x_max, y_max) in addition to center coordinates. This enables downstream processing like cropping individual clusters for analysis or export.

**Value**: Enables efficient cluster extraction and spatial analysis. Useful for debugging (crop to specific cluster), export workflows (save individual cluster regions), and performance optimization (process only cluster bounds instead of full image).

**Target Users**: Users building pipelines that process individual halftone dots, or need to export per-cluster data.

**Estimated Effort**: 2 hours

---

## Acceptance Criteria

- [x] Add `bbox: Optional[Tuple[int, int, int, int]]` field to ClusterResult dataclass
- [x] Bbox format is `(x_min, y_min, x_max, y_max)` following OpenCV convention
- [x] Bbox computed from cluster label mask during counting phase
- [x] `to_dict()` method includes bbox in output
- [x] Unit tests verify bbox accuracy for known cluster shapes

---

## Implementation Plan

### Overview

Extend ClusterResult dataclass with a `bbox` field. During `count_cluster_pixels()`, compute the bounding box from the cluster mask using numpy argwhere or cv2.boundingRect.

### Implementation Steps

1. **Add bbox field to ClusterResult**: Add `bbox: Optional[Tuple[int, int, int, int]] = None` with docstring.

2. **Update to_dict() method**: Include bbox in dictionary output.

3. **Compute bbox in count_cluster_pixels()**: After creating cluster_mask, compute bounds:
   ```python
   coords = np.argwhere(cluster_mask)
   if len(coords) > 0:
       y_min, x_min = coords.min(axis=0)
       y_max, x_max = coords.max(axis=0)
       bbox = (x_min, y_min, x_max, y_max)
   ```

4. **Write unit tests**: Verify bbox for synthetic cluster shapes.

### Technical Considerations

- **Architecture**: Non-breaking addition to existing dataclass
- **Performance**: Minimal overhead - argwhere already computed implicitly
- **Data Model**: Standard OpenCV bbox convention (x, y, width implied by x_max - x_min)

---

## Testing Strategy (optional)

### Unit Tests

- [x] Test bbox computation for single rectangular cluster
- [x] Test bbox for cluster at image edge (partial cluster)
- [x] Test bbox is None when cluster has no pixels
- [x] Test to_dict() includes bbox field

---

## Related Cards (optional)

**Related**: krzyj6 - ADR: CMYK Cluster Pixel Counting Architecture (parent ADR with "Future TODOs")
