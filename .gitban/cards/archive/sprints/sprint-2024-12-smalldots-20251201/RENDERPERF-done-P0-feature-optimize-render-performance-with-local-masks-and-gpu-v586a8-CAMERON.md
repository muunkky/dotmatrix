## Description

**Optimize render_flower_global_blend performance** - Critical performance fix for large image rendering.

The current `render_flower_global_blend` function in `circle_renderer.py` has O(clusters × canvas_size) complexity due to creating full-canvas masks for each petal radius test. For a 38.9 MP image with 15,722 clusters, this results in ~73 minutes of render time.

**Value**: Reduce render time from 73 minutes to under 5 minutes for large images. This enables iterative workflows and makes the tool practical for production use.

**Target Users**: Anyone processing large halftone images (10+ megapixels)

**Estimated Effort**: 2-4 hours

---

## Acceptance Criteria

- [x] Local mask optimization: Replace full-canvas masks with local ROI masks
- [x] Render time for 38.9 MP image reduced from 73 min to under 10 min (CPU-only)
- [x] GPU acceleration option available via --gpu flag (if CUDA available)
- [x] GPU render time under 2 minutes for 38.9 MP image
- [x] Output quality identical to original (pixel-perfect or within tolerance)
- [x] Fallback to CPU if GPU not available

---

## Implementation Plan

### Overview

Two-phase optimization: First, fix the algorithmic issue (local masks instead of full-canvas). Second, add optional GPU acceleration using PyTorch/CuPy for embarrassingly parallel operations.

### Implementation Steps

1. **Fix make_test_mask to use local ROI** (lines 743-748 in circle_renderer.py)
   - Current: Creates full (out_h, out_w) mask for each test
   - Fix: Create small local mask around petal center, compare against ROI of global_black_mask
   - Expected speedup: ~40x (canvas_size / flower_size ratio)
   ```python
   def make_test_mask_local(center_x, center_y, radius, global_black_mask):
       # Extract local ROI around petal
       margin = radius + 5
       x1 = max(0, int(center_x - margin))
       y1 = max(0, int(center_y - margin))
       x2 = min(out_w, int(center_x + margin))
       y2 = min(out_h, int(center_y + margin))
       
       local_mask = np.zeros((y2-y1, x2-x1), dtype=np.uint8)
       local_cx, local_cy = center_x - x1, center_y - y1
       cv2.circle(local_mask, (int(local_cx), int(local_cy)), int(radius), 255, -1)
       
       local_black = global_black_mask[y1:y2, x1:x2]
       exposed = np.sum((local_mask > 0) & ~local_black)
       return exposed
   ```

2. **Add GPU acceleration option**
   - Use PyTorch tensors for global mask operations
   - Batch process clusters instead of sequential loop
   - Add --gpu CLI flag

3. **Write unit tests for render performance**
   - Test output equivalence between old and optimized versions
   - Benchmark tests with timing assertions

### Technical Considerations

- **Architecture**: Drop-in replacement for existing render function
- **Performance**: O(clusters × flower_size) instead of O(clusters × canvas_size)
- **Backwards Compatibility**: Default behavior unchanged, optimization transparent

### Dependencies

- **Optional**: PyTorch with CUDA support for GPU acceleration
- **Optional**: CuPy as alternative GPU backend

---

## Testing Strategy (optional)

### Unit Tests

- [x] Test local mask produces same exposed pixel count as full mask
- [x] Test output image is identical between old and optimized render
- [x] Test GPU output matches CPU output (if GPU available)
- [x] Test fallback works when GPU unavailable

### Performance Tests

- [x] Benchmark small image (1 MP): should be <1 second
- [x] Benchmark large image (38.9 MP): should be <10 min CPU, <2 min GPU

---

## Notes (optional)

### Root Cause Analysis

Lines 791-793 in circle_renderer.py:
```python
for test_r in range(max(1, int(theoretical_r) - 3), int(theoretical_r) + 4):
    test_mask = make_test_mask(petal_x, petal_y, test_r)  # FULL CANVAS!
    exposed_count = int(np.sum(test_mask & ~global_black_mask))
```

For each cluster (15,722) × 3 petals × 7 radius tests = 330,162 full-canvas operations.
Each operation allocates 38.9 MB and performs ~77.8M pixel operations.
Total: 12.8 trillion pixel operations → 73 minutes.

### Performance Calculation

With local masks (radius=25, margin=30, so ~60x60 = 3,600 pixels per mask):
- 330,162 ops × 3,600 pixels = 1.19 billion pixel ops
- Speedup: 12.8T / 1.19B = ~10,700x theoretical
- Realistic: ~40-100x due to overhead
