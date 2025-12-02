## Description

GPU-accelerated nearest-neighbor labeling to replace scipy KDTree for Voronoi tessellation in cluster pixel assignment.

Replace `create_cluster_labels_from_centers()` KDTree approach with a GPU distance matrix calculation that finds the nearest center for each pixel in parallel.

**Value**: 10-50× speedup for the most expensive operation in the pipeline. For a 4000×4000 image (16M pixels) with 5000 centers, this operation dominates processing time.

**Target Users**: All dotmatrix users processing large halftone images

**Estimated Effort**: 2 days

---

## Acceptance Criteria

- [x] `gpu_nearest_center_labels()` function implemented in `gpu.py`
- [x] Function accepts pixel coordinates and center coordinates
- [x] Returns label array (same format as KDTree query)
- [x] Handles memory efficiently with chunked processing for large images
- [x] Falls back gracefully to CPU when GPU unavailable
- [x] Unit tests verify identical results to KDTree implementation
- [x] Performance benchmark shows >10× speedup for 1M+ pixels

---

## Implementation Plan

### Overview

Compute distance from each pixel to all centers using GPU broadcast, then use `argmin` to find the nearest center. Process in chunks to manage GPU memory.

### Implementation Steps

1. **Add `gpu_nearest_center_labels()` to `gpu.py`**:
   ```python
   def gpu_nearest_center_labels(
       pixel_coords: np.ndarray,  # (M, 2) all pixel coordinates
       centers: np.ndarray,       # (N, 2) center coordinates
       chunk_size: int = 500_000  # Process pixels in chunks
   ) -> np.ndarray:
       """GPU-accelerated nearest center labeling.
       
       For each pixel, find the index of the nearest center.
       
       Args:
           pixel_coords: (M, 2) array of (x, y) pixel coordinates
           centers: (N, 2) array of center coordinates
           chunk_size: Number of pixels to process per GPU batch
           
       Returns:
           (M,) array of center indices for each pixel
       """
       if not _GPU_AVAILABLE:
           from scipy.spatial import KDTree
           tree = KDTree(centers)
           _, labels = tree.query(pixel_coords)
           return labels
       
       import cupy as cp
       
       centers_gpu = cp.asarray(centers)  # (N, 2)
       n_pixels = len(pixel_coords)
       labels = np.empty(n_pixels, dtype=np.int32)
       
       # Process in chunks to manage GPU memory
       for start in range(0, n_pixels, chunk_size):
           end = min(start + chunk_size, n_pixels)
           chunk = cp.asarray(pixel_coords[start:end])  # (chunk, 2)
           
           # Distance matrix: (chunk, N)
           diff = chunk[:, None, :] - centers_gpu[None, :, :]
           dist_sq = (diff ** 2).sum(axis=2)  # Skip sqrt for argmin
           
           # Find nearest center for each pixel
           labels[start:end] = cp.asnumpy(cp.argmin(dist_sq, axis=1))
       
       return labels
   ```

2. **Add `gpu_create_cluster_labels()` for full image**:
   ```python
   def gpu_create_cluster_labels(
       image_shape: tuple,  # (H, W)
       centers: np.ndarray  # (N, 2) in (x, y) format
   ) -> np.ndarray:
       """Create cluster label image using GPU.
       
       Returns:
           (H, W) label array where each pixel contains its nearest center index
       """
       h, w = image_shape
       
       # Generate all pixel coordinates
       yy, xx = np.mgrid[0:h, 0:w]
       pixel_coords = np.column_stack([xx.ravel(), yy.ravel()])  # (H*W, 2)
       
       # Get labels and reshape
       labels = gpu_nearest_center_labels(pixel_coords, centers)
       return labels.reshape(h, w)
   ```

3. **Integrate into `cluster_pixel_counter.py`**:
   - Import `gpu_create_cluster_labels` from `gpu` module
   - Replace `create_cluster_labels_from_centers()` when `--gpu` flag enabled

4. **Memory optimization**:
   - Auto-tune chunk_size based on available GPU memory
   - Add memory estimation: `n_pixels * n_centers * 4 bytes` per chunk

### Technical Considerations

- **Memory**: For 16M pixels and 5K centers, full matrix = 320GB. Chunking is essential.
- **Chunk size**: 500K pixels × 5K centers × 4 bytes = 10GB per chunk. Adjust dynamically.
- **Skip sqrt**: Using squared distances for argmin is faster and produces identical results.
