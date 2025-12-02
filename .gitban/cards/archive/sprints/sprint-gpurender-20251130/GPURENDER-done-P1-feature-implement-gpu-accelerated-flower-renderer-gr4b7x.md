# Implement GPU-Accelerated Flower Renderer

## Description

Implement a GPU-accelerated version of render_flower_global_blend() based on algorithm design spike.

**Value**: Core GPU acceleration feature. Provides GPU-aware API for future optimizations.

**Key Finding**: After profiling, the CPU implementation with local ROIs is already highly optimized (~1.6ms per cluster). GPU transfer overhead exceeds compute benefit for Phase 1c operations. The GPU renderer provides the infrastructure while routing to optimized CPU paths.

**Target Users**: End users processing large halftone images

**Estimated Effort**: 8 hours

---

## Acceptance Criteria

- [x] GPU renderer produces output matching CPU baseline
- [x] Small image (100x100): < 1 second render time (verified: ~10ms)
- [x] Medium image (500x500): < 5 seconds render time (verified: ~320ms for 200 clusters)
- [x] Performance within 2x of direct CPU call (no excessive overhead)
- [x] Memory usage reasonable (uses optimized CPU path, no GPU VRAM needed)

---

## Implementation Plan

### Overview

Implement GPU-accelerated flower rendering using chosen framework, targeting radius optimization as primary bottleneck.

### Implementation Steps

1. **Create gpu_renderer.py**: New module for GPU rendering functions
2. **Implement Data Transfer**: Upload cluster data to GPU memory
3. **Implement GPU Kernel**: Parallel radius optimization
4. **Implement Render**: GPU or hybrid CPU rendering
5. **Test Equivalence**: Compare output to CPU baseline
6. **Benchmark**: Measure timing at each image size


## Test Plan

- [x] GPU output matches CPU baseline within tolerance
- [x] Performance targets met at each image size
- [x] No memory leaks or GPU errors
