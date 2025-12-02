## Stakeholder Review & Signoff

**Stakeholder Notes:**
<!-- Space for notes, concerns, feedback -->

**Approval Checklist:**
- [ ] CAMERON personally approves this feature for implementation

---

## Description

Add option to output per-cluster binary masks from cluster_pixel_counter.py for pixel-perfect reconstruction.

Currently, clusters are summarized as pixel counts per channel. This feature adds the ability to export the actual binary mask for each cluster, enabling exact reconstruction of the original pixels rather than approximated circle rendering.

**Value**: Enables pixel-perfect halftone reconstruction without geometric approximation. Essential for quality validation (compare reconstructed vs original at pixel level) and advanced processing pipelines that need exact pixel data.

**Target Users**: Users requiring lossless halftone analysis, QA engineers validating detection accuracy, researchers studying halftone patterns.

**Estimated Effort**: 1 day

---

## Acceptance Criteria

- [ ] Add `include_masks: bool = False` parameter to `cluster_and_count_pixels()`
- [ ] When enabled, each ClusterResult includes per-channel binary masks
- [ ] Masks stored as numpy arrays in ClusterResult (lazy-loaded or on-demand generation option)
- [ ] Memory usage documented for typical image sizes
- [ ] CLI flag `--output-cluster-masks` saves masks to output directory
- [ ] Unit tests verify mask accuracy matches original ink separation

---

## Implementation Plan

### Overview

Extend ClusterResult with optional mask fields. Add `include_masks` parameter that, when True, stores the cluster's per-channel masks. Consider memory implications and provide lazy generation option.

### Implementation Steps

1. **Extend ClusterResult dataclass**: Add optional mask fields:
   ```python
   @dataclass
   class ClusterResult:
       # ... existing fields ...
       masks: Optional[Dict[str, np.ndarray]] = None  # {'cyan': mask, 'magenta': mask, ...}
   ```

2. **Modify count_cluster_pixels()**: When include_masks=True, store the per-channel masks:
   ```python
   if include_masks:
       result.masks = {
           'cyan': (cluster_mask & (cyan_mask > 0)).astype(np.uint8) * 255,
           'magenta': ...,
           # etc
       }
   ```

3. **Add memory management**: Document memory usage (~8 bytes per pixel per mask). Consider lazy generation via callback.

4. **Add CLI flag**: `--output-cluster-masks` that saves masks as PNG files per cluster.

5. **Write tests**: Verify masks match original separation when summed.

### Technical Considerations

- **Architecture**: Optional feature, no impact when disabled
- **Performance**: Memory-intensive for large images - ~7 masks × image_size per cluster
- **Data Model**: Consider alternative: store only combined mask, regenerate per-channel on demand

### Memory Estimation

For 1000x1000 image with 100 clusters:
- Per cluster: 7 channels × 1M pixels × 1 byte = 7MB
- Total: 100 × 7MB = 700MB (significant!)

**Recommendation**: Implement lazy generation - store cluster label image only, generate masks on-demand.

---

## Testing Strategy (optional)

### Unit Tests

- [ ] Test masks are None when include_masks=False
- [ ] Test masks contain correct per-channel data when enabled
- [ ] Test sum of all cluster masks equals original separation mask
- [ ] Test memory usage stays within bounds for typical images

---

## Related Cards (optional)

**Related**: krzyj6 - ADR: CMYK Cluster Pixel Counting Architecture (parent ADR with "Future TODOs")
