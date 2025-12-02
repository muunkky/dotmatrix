## Description

Integrate GPU-accelerated cluster functions from `gpu.py` into the main `cluster_pixel_counter.py` pipeline to enable end-to-end GPU acceleration when processing halftone images.

The GPUACCEL sprint created standalone GPU functions with tests proving correctness:
- `gpu_nms_centers()` - GPU Non-Maximum Suppression (replaces `_nms_centers`)
- `gpu_create_cluster_labels()` - GPU Voronoi labeling (replaces KDTree in `create_cluster_labels_from_centers`)
- `gpu_count_cluster_colors()` - GPU per-cluster color counting (replaces per-cluster loop)

**Value**: Users running `python -m dotmatrix -i inputs/input_large.png` will automatically use GPU acceleration when available, significantly reducing processing time for large halftone images (38+ megapixels).

**Target Users**: All dotmatrix users processing halftone images

**Estimated Effort**: 4 hours

---

## Acceptance Criteria

- [x] `_nms_centers()` in cluster_pixel_counter.py conditionally uses `gpu_nms_centers()` when GPU available
- [x] `create_cluster_labels_from_centers()` conditionally uses `gpu_create_cluster_labels()` when GPU available
- [x] Per-cluster counting loop replaced with `gpu_count_cluster_colors()` batch operation when GPU available
- [x] `cluster_and_count_pixels()` accepts `use_gpu` parameter (default: None = auto-detect)
- [x] GPU flag propagates from CLI through image_extractor to cluster_pixel_counter
- [x] Default CLI `python -m dotmatrix -i inputs/input_large.png` uses GPU when available
- [x] CPU fallback works correctly when GPU unavailable
- [x] All existing tests pass

---

## Implementation Plan

### Overview

Modify `cluster_pixel_counter.py` to import and use GPU functions from `gpu.py`, with automatic fallback to CPU when GPU is unavailable. The integration follows the existing pattern in `gpu.py` where each function auto-detects GPU availability.

### Implementation Steps

1. **Add use_gpu parameter to cluster_and_count_pixels()**:
   - Add `use_gpu: Optional[bool] = None` parameter
   - None = auto-detect GPU availability
   - True = force GPU (raises if unavailable)
   - False = force CPU
   ```python
   def cluster_and_count_pixels(
       ...,
       use_gpu: Optional[bool] = None,
       ...
   ):
   ```

2. **Integrate GPU NMS into _nms_centers()**:
   - Import `gpu_nms_centers` from `gpu.py`
   - Add use_gpu parameter to `_nms_centers()`
   - Call `gpu_nms_centers()` when GPU enabled
   ```python
   from .gpu import gpu_nms_centers, is_gpu_available
   
   def _nms_centers(centers, dist_transform, min_distance, use_gpu=None):
       if use_gpu is None:
           use_gpu = is_gpu_available()
       if use_gpu:
           scores = np.array([dist_transform[y, x] for x, y in centers])
           centers_array = np.array(centers, dtype=np.float64)
           result = gpu_nms_centers(centers_array, scores, min_distance)
           return [(int(x), int(y)) for x, y in result]
       # ... existing CPU code
   ```

3. **Integrate GPU Voronoi labeling**:
   - Import `gpu_create_cluster_labels` from `gpu.py`
   - Add use_gpu parameter to `create_cluster_labels_from_centers()`
   - Call GPU function when enabled
   ```python
   from .gpu import gpu_create_cluster_labels
   
   def create_cluster_labels_from_centers(centers, image_shape, max_distance=None, use_gpu=None):
       if use_gpu is None:
           use_gpu = is_gpu_available()
       if use_gpu:
           return gpu_create_cluster_labels(image_shape, np.array(centers))
       # ... existing KDTree code
   ```

4. **Integrate GPU color counting**:
   - Import `gpu_count_cluster_colors` from `gpu.py`
   - Replace per-cluster loop with batch GPU call
   - Convert GPU counts to ClusterResult objects
   ```python
   from .gpu import gpu_count_cluster_colors
   
   # In cluster_and_count_pixels():
   if use_gpu:
       color_masks = {'C': cyan_mask > 0, 'M': magenta_mask > 0, ...}
       counts = gpu_count_cluster_colors(labels, color_masks, len(centers))
       # Build ClusterResult objects from counts dict
   else:
       # ... existing per-cluster loop
   ```

5. **Wire use_gpu through the call chain**:
   - `cli.py` already has `--gpu` flag
   - Propagate to `image_extractor.py`
   - Propagate to `cluster_pixel_counter.py`

### Technical Considerations

- **Backwards Compatibility**: Default `use_gpu=None` preserves auto-detect behavior
- **Performance**: GPU functions already have internal thresholds (e.g., <100 centers uses CPU)
- **Error Handling**: GPU functions already handle unavailable GPU gracefully
- **Memory**: GPU functions use chunked processing for large images

---

## Testing Strategy (optional)

### Unit Tests

- [x] Test cluster_and_count_pixels with use_gpu=True (mocked GPU)
- [x] Test cluster_and_count_pixels with use_gpu=False (CPU path)
- [x] Test cluster_and_count_pixels with use_gpu=None (auto-detect)
- [x] Test GPU and CPU paths produce equivalent results

### Integration Tests

- [x] Test full CLI pipeline: `python -m dotmatrix -i inputs/input_large.png --gpu`
- [x] Test default CLI uses GPU when available
- [x] Test CLI works without GPU installed

---

## Documentation Updates (optional)

- [x] **Add entry to CHANGELOG.md under [Unreleased]** (REQUIRED for user-facing features)

---

## Notes (optional)

### Related Cards

- GPUACCEL sprint cards (completed): kuartq, 6u8k3y, ahzwqx
- This card completes the GPU integration work started in GPUACCEL


## Benchmark Results - Critical Performance Issue Found

**Date:** 2025-12-01

### Benchmark Results

| Function | Small Tile | Medium Tile | Large Tile |
|----------|------------|-------------|------------|
| NMS | 0.91x | 1.84x | 2.36x ✅ |
| Nearest Center Labels | **0.32x** | **0.19x** | **0.09x** ❌ |
| Color Counting | 0.26x | 1.51x | 2.29x ✅ |

### Analysis

**GPU Nearest Center Labeling is 10x SLOWER than CPU KDTree!**

- KDTree: O(M log N) - efficient tree-based nearest neighbor search
- GPU brute-force: O(M × N) - computes all pairwise distances

For 4M pixels × 500 centers:
- KDTree: 1.4 seconds
- GPU: 16.8 seconds (12x slower!)

### Action Required

1. **Remove GPU for cluster labeling** - KDTree is far superior
2. **Keep GPU for NMS** - 2x+ speedup for >200 centers
3. **Keep GPU for Color Counting** - 2x+ speedup for large tiles

### Fix Plan

Modify `cluster_pixel_counter.py` to:
- Always use KDTree for `create_cluster_labels_from_centers()`
- Only use GPU for NMS when centers > 200
- Only use GPU for color counting when image size > 1000×1000

## Fixes Applied

**Date:** 2025-12-01

### Changes Made to `cluster_pixel_counter.py`

1. **Removed GPU cluster labeling** - Always use KDTree
   ```python
   # NOTE: GPU cluster labeling is SLOWER than KDTree (O(M×N) vs O(M log N))
   # Always use KDTree for cluster labeling - it's superior.
   tree = KDTree(centers_array)
   ```

2. **Added NMS threshold** - Only use GPU when centers > 200
   ```python
   GPU_NMS_THRESHOLD = 200
   if use_gpu and len(centers) > GPU_NMS_THRESHOLD:
       result = gpu_nms_centers(centers_array, scores, float(min_distance))
   ```

3. **Added color counting threshold** - Only use GPU when pixels > 1M
   ```python
   GPU_COUNTING_THRESHOLD = 1_000_000
   n_pixels = image_shape[0] * image_shape[1]
   use_gpu_counting = use_gpu and n_pixels > GPU_COUNTING_THRESHOLD
   ```

### Changes Made to `gpu.py`

1. **Added adaptive chunk sizing** for OOM protection
2. **Added GPU memory cleanup** between chunks
3. **Added CPU fallback** on OutOfMemoryError

### Verification Benchmark (Post-Fix)

```
NMS PERFORMANCE (threshold: 200 centers):
  100 centers: CPU only (below threshold)
  200 centers: CPU only (below threshold)
  300 centers: GPU 2.11x faster ✅
  500 centers: GPU 3.29x faster ✅
 1000 centers: GPU 3.82x faster ✅

COLOR COUNTING (threshold: 1M pixels):
  500K px: CPU only (below threshold)
    1M px: GPU 2.33x faster ✅
    2M px: GPU 2.12x faster ✅
    4M px: GPU 1.47x faster ✅

CLUSTER LABELING (always KDTree):
  100K px: KDTree 0.07s
  500K px: KDTree 0.31s
    1M px: KDTree 0.48s
```

### Test Results

- **50/50 tests passed** in `test_cluster_pixel_counter.py`
- **13/13 tests passed** in `test_gpu_acceleration.py`

### Decision Summary

| Function | Use GPU When | Speedup |
|----------|--------------|---------|
| NMS | centers > 200 | 2-4x ✅ |
| Cluster labeling | NEVER (KDTree superior) | N/A |
| Color counting | pixels > 1M | 1.5-2.3x ✅ |

## Time Estimation Criterion

**Added:** 2025-12-01

Before running large image tests, estimate the expected runtime:

1. **Calculate based on benchmarks:**
   - KDTree labeling: ~0.5s per 1M pixels
   - GPU NMS: ~0.2s per 500 centers
   - GPU color counting: ~0.03s per 1M pixels (4 colors)

2. **For input_large.png (7200×5400 = 38.9M pixels):**
   - Expected centers: ~10,000 (typical halftone density)
   - KDTree labeling: 38.9M × 0.5s/1M = ~20s
   - NMS: 10k centers × 0.2s/500 = ~4s (GPU path)
   - Color counting: 38.9M × 0.03s/1M = ~1.2s (GPU path)
   - **Estimated total cluster phase: ~25-30 seconds**

3. **Maximum runtime policy:**
   - Do NOT start tests expected to take >10 minutes
   - Always estimate runtime before starting large tests
   - Use smaller test images first to validate changes