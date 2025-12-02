## Description

GPU-accelerated per-cluster color pixel counting using CuPy bincount operations instead of sequential Python loops.

Replace the loop over N clusters in `count_cluster_pixels()` with a single GPU pass that counts all colors for all clusters simultaneously.

**Value**: 5-20× speedup for color counting phase. Eliminates O(N) sequential loop where N = number of clusters.

**Target Users**: All dotmatrix users processing halftone images with CMYK separation

**Estimated Effort**: 1.5 days

---

## Acceptance Criteria

- [x] `gpu_count_cluster_colors()` function implemented in `gpu.py`
- [x] Function accepts label array and color mask arrays (C, M, Y, K)
- [x] Returns per-cluster color counts (same format as CPU version)
- [x] Falls back gracefully to CPU when GPU unavailable
- [x] Unit tests verify identical results to CPU implementation
- [x] Performance benchmark shows >5× speedup for 1000+ clusters

---

## Implementation Plan

### Overview

Use `cupy.bincount()` with color masks as weights to count pixels of each color per cluster in a single GPU pass, rather than iterating over clusters.

### Implementation Steps

1. **Add `gpu_count_cluster_colors()` to `gpu.py`**:
   ```python
   def gpu_count_cluster_colors(
       labels: np.ndarray,      # (H, W) cluster labels
       color_masks: dict,       # {'C': mask, 'M': mask, 'Y': mask, 'K': mask}
       n_clusters: int
   ) -> dict:
       """GPU-accelerated per-cluster color counting.
       
       Args:
           labels: (H, W) array of cluster indices
           color_masks: Dict mapping color names to (H, W) boolean masks
           n_clusters: Total number of clusters
           
       Returns:
           Dict mapping color names to (n_clusters,) count arrays
       """
       if not _GPU_AVAILABLE:
           return _cpu_count_cluster_colors(labels, color_masks, n_clusters)
       
       import cupy as cp
       
       labels_gpu = cp.asarray(labels.ravel())
       counts = {}
       
       for color, mask in color_masks.items():
           mask_gpu = cp.asarray(mask.ravel().astype(np.int32))
           
           # bincount with mask as weights: count color pixels per cluster
           color_counts = cp.bincount(
               labels_gpu,
               weights=mask_gpu,
               minlength=n_clusters
           )
           counts[color] = cp.asnumpy(color_counts)
       
       return counts
   ```

2. **Add total pixel counting**:
   ```python
   def gpu_count_cluster_totals(
       labels: np.ndarray,
       n_clusters: int
   ) -> np.ndarray:
       """Count total pixels per cluster using GPU bincount."""
       if not _GPU_AVAILABLE:
           return np.bincount(labels.ravel(), minlength=n_clusters)
       
       import cupy as cp
       labels_gpu = cp.asarray(labels.ravel())
       return cp.asnumpy(cp.bincount(labels_gpu, minlength=n_clusters))
   ```

3. **Integrate into `cluster_pixel_counter.py`**:
   - Import GPU functions from `gpu` module
   - Replace manual loop in `count_cluster_pixels()` with GPU version

4. **Handle overlap counting**:
   ```python
   def gpu_count_color_overlaps(
       labels: np.ndarray,
       mask_a: np.ndarray,
       mask_b: np.ndarray,
       n_clusters: int
   ) -> np.ndarray:
       """Count pixels where both colors overlap per cluster."""
       overlap_mask = mask_a & mask_b
       return gpu_count_cluster_colors(
           labels, {'overlap': overlap_mask}, n_clusters
       )['overlap']
   ```

### Technical Considerations

- **Memory**: Labels + 4 color masks on GPU = 5 × H × W bytes. Manageable for most images.
- **Data types**: Use int32 for bincount weights (boolean masks → 0/1 integers)
- **Sparse optimization**: For images with many small clusters, consider sparse matrix approach
