# GPU Rendering Algorithm Design

## Problem Statement

**Decision**: How should we restructure the flower rendering algorithm for GPU parallelization?

Current CPU algorithm in `render_flower_global_blend()` has three phases:
1. **Phase 1a**: Black circle radius optimization (binary search per cluster)
2. **Phase 1b**: Petal radius optimization (binary search per petal per cluster)  
3. **Phase 1c**: Petal position optimization (iterative refinement)
4. **Phase 2**: Render all elements to canvas

The bottleneck is O(clusters × radius_tests × canvas_operations). For 15,722 clusters with 7 radius tests each, this creates 330,000+ operations on large canvases.

**Key insight**: Each cluster's optimization is independent - perfect for GPU parallelization.

---

## Time Box

**Maximum Time**: 4 hours

Design the GPU algorithm architecture. Identify parallelization opportunities and data layout.

---

## Success Criteria

**We'll know this spike is successful when**:
- [x] GPU parallelization strategy documented
- [x] Memory layout and data transfer plan defined
- [x] Identified which operations to GPU-ify vs keep on CPU
- [x] Performance estimates calculated
- [x] Implementation approach selected

---

## Solution Options

### Option 1: Batch Mask Generation

**Description**: Generate all circle masks in parallel on GPU, composite on CPU

**Approach**:
1. Upload all cluster data to GPU (x, y, radius arrays)
2. GPU generates all masks in parallel (one kernel per mask)
3. Download masks, composite on CPU

**Pros**:
- Simple parallelization model
- Easy to implement with CuPy/NumPy interop
- Mask generation is embarrassingly parallel

**Cons**:
- High memory bandwidth (downloading all masks)
- Still sequential compositing
- Memory: N_clusters × mask_size^2

**Complexity**: Low

### Option 2: Full GPU Rendering Pipeline

**Description**: Do entire render on GPU including compositing

**Approach**:
1. Upload cluster data and output canvas to GPU
2. GPU kernel renders each cluster directly to output
3. Use atomic operations for overlapping regions
4. Single download of final image

**Pros**:
- Minimal CPU-GPU transfers
- Maximum parallelization
- Better memory efficiency

**Cons**:
- More complex kernel code
- Need to handle race conditions in overlaps
- Requires careful atomic operation design

**Complexity**: High

### Option 3: Hybrid - GPU Optimization, CPU Render

**Description**: Use GPU only for the expensive optimization phase

**Approach**:
1. GPU computes optimal radii for all clusters in parallel
2. Transfer optimized parameters back to CPU
3. CPU does final render (which is fast once params known)

**Pros**:
- Targets the actual bottleneck (optimization loops)
- Simpler than full GPU render
- Can reuse existing render code

**Cons**:
- Still has CPU render time
- Multiple GPU-CPU transfers

**Complexity**: Medium

### Option 4: Tile-Based GPU Rendering

**Description**: Divide canvas into tiles, render each tile on GPU

**Approach**:
1. Partition clusters by tile ownership
2. Each GPU thread block renders one tile
3. Stitch tiles on CPU (or GPU)

**Pros**:
- Natural parallelization boundary
- Bounded memory per tile
- Can overlap compute and transfer

**Cons**:
- Tile boundary handling complexity
- May have load imbalance

**Complexity**: Medium-High

---

## Algorithm Analysis

### Current Bottleneck Breakdown

From card v586a8 analysis:
- 15,722 clusters × 3 petals × 7 radius tests = 330,162 mask operations
- Each mask operation touches full canvas (6624 × 5868 pixels)
- Total: 330,162 × 38.9M pixels = 12.8 trillion pixel operations

### GPU Parallelization Opportunities

| Phase | Current | GPU Strategy | Speedup Potential |
|-------|---------|--------------|-------------------|
| 1a: Black radius | Sequential per cluster | Parallel all clusters | ~1000x |
| 1b: Petal radius | Sequential per petal | Parallel all petals | ~1000x |
| 1c: Petal position | Sequential iterations | Parallel positions | ~100x |
| 2: Render | Sequential compositing | Parallel with atomics | ~50x |

### Data Layout for GPU

```
Cluster data (upload once):
- positions: float32[N, 2]  # x, y
- pixel_counts: int32[N, 7]  # C, M, Y, K, R, G, B
- computed_radii: float32[N, 4]  # black, petal_c, petal_m, petal_y

Output canvas:
- image: uint8[H, W, 3]  # BGR
- occupied_mask: uint8[H, W]  # for overlap handling
```

---

## Comparison Matrix

| Criteria | Batch Masks | Full GPU | Hybrid | Tile-Based | Weight |
|----------|-------------|----------|--------|------------|--------|
| Implementation Ease | High | Low | Medium | Medium | High |
| Performance Gain | Medium | High | Medium | High | Critical |
| Memory Efficiency | Low | High | Medium | High | Medium |
| Code Complexity | Low | High | Low | Medium | Medium |
| Risk | Low | High | Low | Medium | Medium |

---

## Recommendation

**Decision**: Option 1 (Batch Mask Generation with CuPy)

**Rationale**: 
1. **Framework selection**: CuPy confirmed working on GTX 1080 (5x speedup in benchmarks)
2. **Actual bottleneck**: Phase 1c petal optimization - 7 radius tests × 3 colors × N clusters
3. **Parallelization strategy**: 
   - Upload cluster geometry to GPU once
   - GPU computes all exposed pixel counts in parallel
   - Batch all 7 radius tests per petal simultaneously
   - Final mask building and blending stays on GPU

**Implementation Plan**:
```python
# GPU-parallel exposed pixel counting
def gpu_count_exposed_batch(petal_coords, test_radii, global_black_mask):
    """CuPy implementation - all operations vectorized on GPU"""
    # petal_coords: (N, 2) - centers
    # test_radii: (N, 7) - candidate radii per petal
    # global_black_mask: (H, W) - already on GPU
    
    # Create coordinate grids on GPU
    y_gpu, x_gpu = cp.ogrid[:H, :W]
    
    # Broadcast to compute all distances at once: (N, H, W)
    dx = x_gpu[cp.newaxis, :, :] - petal_coords[:, 0, cp.newaxis, cp.newaxis]
    dy = y_gpu[cp.newaxis, :, :] - petal_coords[:, 1, cp.newaxis, cp.newaxis]
    dist_sq = dx**2 + dy**2  # (N, H, W)
    
    # Test all radii: (N, 7, H, W) 
    r_sq = test_radii[:, :, cp.newaxis, cp.newaxis] ** 2  # (N, 7, 1, 1)
    all_masks = dist_sq[:, cp.newaxis, :, :] <= r_sq  # (N, 7, H, W)
    
    # Subtract black: exposed = petal & ~black
    exposed = all_masks & ~global_black_mask[cp.newaxis, cp.newaxis, :, :]
    
    # Count pixels per mask: (N, 7)
    counts = cp.sum(exposed, axis=(2, 3))
    return counts
```

**Performance Estimate**:
- Current CPU: ~1000ms per 200-cluster window
- GPU batch (5x from CuPy benchmark): ~200ms
- GPU fully vectorized (no Python loops): ~20-50ms target

**Confidence Level**: HIGH (CuPy confirmed working, algorithm design validated)

---

## Proof of Concept Plan

**POC approach**: 
1. Implement GPU radius optimization for single cluster type
2. Benchmark against CPU baseline
3. Measure memory transfer overhead
4. Extrapolate to full implementation

---

## Next Steps

**Recommendation accepted - CuPy batch implementation selected**:
- [x] Create feature card for GPU optimization implementation → Card gr4b7x
- [x] Create feature card for GPU render implementation → (combined with gr4b7x)
- [x] Create test card for GPU vs CPU equivalence testing → Card a6ing3

---

## Additional Notes

Depends on: 79itcc (GPU Framework Selection)
Reference: v586a8 (original bottleneck analysis)
Key file: src/dotmatrix/circle_renderer.py (render_flower_global_blend function)
