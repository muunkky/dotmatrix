## Description

GPU-accelerated Non-Maximum Suppression (NMS) for centroid discovery in distance transform peak detection.

Replace the O(n²) Python loop in `_nms_centers()` with a GPU broadcast distance matrix calculation using CuPy.

**Value**: 10-50× speedup for NMS phase. For images with 10,000+ detected peaks, this reduces NMS time from seconds to milliseconds.

**Target Users**: All dotmatrix users processing halftone images

**Estimated Effort**: 1 day

---

## Acceptance Criteria

- [x] `gpu_nms_centers()` function implemented in `gpu.py`
- [x] Function accepts centers array and min_distance parameter
- [x] Returns filtered centers array (same format as CPU version)
- [x] Falls back gracefully to CPU when GPU unavailable
- [x] Unit tests verify identical results to CPU implementation
- [x] Performance benchmark shows >5× speedup for 5,000+ centers

---

## Implementation Plan

### Overview

Use GPU broadcast operations to compute the full N×N distance matrix in parallel, then apply vectorized NMS logic to filter peaks.

### Implementation Steps

1. **Add `gpu_nms_centers()` to `gpu.py`**:
   ```python
   def gpu_nms_centers(centers: np.ndarray, min_distance: float) -> np.ndarray:
       """GPU-accelerated Non-Maximum Suppression.
       
       Args:
           centers: (N, 2) array of (x, y) coordinates
           min_distance: Minimum distance between retained centers
           
       Returns:
           Filtered centers array
       """
       if not _GPU_AVAILABLE or len(centers) < 100:
           return _cpu_nms_centers(centers, min_distance)
       
       import cupy as cp
       
       coords = cp.asarray(centers)
       n = len(coords)
       
       # Broadcast distance matrix: (N, 1, 2) - (1, N, 2) → (N, N)
       diff = coords[:, None, :] - coords[None, :, :]
       dist_matrix = cp.sqrt((diff ** 2).sum(axis=2))
       
       # NMS: keep if no higher-indexed point within min_distance
       # (assuming centers are sorted by response strength)
       keep_mask = cp.ones(n, dtype=bool)
       
       for i in range(n):
           if keep_mask[i]:
               # Suppress all points within min_distance (except self)
               suppress = (dist_matrix[i] < min_distance) & (cp.arange(n) > i)
               keep_mask[suppress] = False
       
       return cp.asnumpy(coords[keep_mask])
   ```

2. **Integrate into `cluster_pixel_counter.py`**:
   - Import `gpu_nms_centers` from `gpu` module
   - Replace `_nms_centers()` call with GPU version when `--gpu` flag enabled

3. **Add benchmark test**:
   - Compare CPU vs GPU timing for 1K, 5K, 10K centers
   - Verify result equivalence

### Technical Considerations

- **Memory**: N×N distance matrix for 10K points = 800MB (float64). May need chunking for very large N.
- **Alternative**: Use cupy's `cupyx.scipy.spatial.distance.cdist` if available for even faster computation.
