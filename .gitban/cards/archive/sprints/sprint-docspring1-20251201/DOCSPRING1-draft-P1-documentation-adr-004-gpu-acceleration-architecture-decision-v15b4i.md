# ADR-004: GPU Acceleration Architecture

## Status

**Current Status**: Proposed

**Date**: 2025-12-01

**Supersedes**: None

---

## Decision Context

**Problem Statement**: The dotmatrix pipeline needs to handle large images efficiently. As image sizes grow and cluster counts increase, CPU-based processing becomes a bottleneck, particularly for non-maximum suppression, Voronoi tessellation, and color counting operations.

**Background**: The GPUINTEGRATE and GPURENDER sprints added GPU acceleration using CuPy for CUDA-enabled systems. Key decisions were made about when to use GPU vs CPU, how to handle fallback, and which operations benefit most from GPU acceleration.

---

## Options Considered

### Option 1: Pure CPU Processing

**Description**: Continue with existing CPU-based NumPy and SciPy operations.

**Pros**:
- No additional dependencies (CuPy, CUDA)
- Works on all systems
- Simpler codebase

**Cons**:
- Slower for large images
- O(n²) operations become bottlenecks
- Cannot leverage modern GPU hardware

### Option 2: CuPy GPU Acceleration with Automatic Fallback

**Description**: Use CuPy for CUDA operations with automatic CPU fallback when GPU unavailable.

**Pros**:
- Significant speedup for large operations
- Graceful degradation on non-GPU systems
- Minimal API changes (CuPy mirrors NumPy)

**Cons**:
- Requires CUDA-compatible GPU for acceleration
- Additional dependency (cupy-cuda12x)
- GPU memory constraints for very large images

### Option 3: OpenCL for Cross-Platform GPU

**Description**: Use PyOpenCL for cross-platform GPU acceleration.

**Pros**:
- Works on AMD and NVIDIA GPUs
- More portable

**Cons**:
- Less mature Python ecosystem
- More complex kernel development
- Fewer optimized operations

---

## Decision

**Selected Option**: Option 2 - CuPy GPU Acceleration with Automatic Fallback

**Rationale**: CuPy provides the best balance of performance gains and development simplicity. Its NumPy-compatible API minimizes code changes, and automatic fallback ensures the tool works everywhere while taking advantage of NVIDIA GPUs when available.

**Decision Makers**: Engineering team

---

## Consequences

### Positive Consequences

- GPU NMS: O(n²) distance matrix computed in parallel on GPU
- GPU labeling: Parallel pixel-center distance computation vs sequential KDTree query
- GPU color counting: Batch bincount across all colors vs per-cluster loop
- 10-100x speedup for operations on >1000 clusters

### Negative Consequences

- Requires CUDA 12.x for GPU acceleration
- Additional ~500MB dependency size for cupy-cuda12x
- GPU memory limits maximum processable image size

### Neutral Consequences

- No change to public API - existing code works unchanged
- CLI flag --gpu/--no-gpu for explicit control

---

## Implementation Notes

**Affected Components**:
- `gpu.py`: GPU detection, info, array transfer utilities
- `gpu_renderer.py`: GPU-accelerated flower renderer
- `cluster_pixel_counter.py`: GPU-accelerated NMS, labeling, counting

**Migration Steps**:
1. Install cupy-cuda12x for GPU support
2. No code changes required - GPU auto-detected
3. Use --no-gpu flag to force CPU if needed

---

## References

- GPUINTEGRATE sprint cards
- GPURENDER sprint cards
- CuPy documentation: https://cupy.dev/
- CUDA compatibility matrix

---

## Review History

- 2025-12-01: Created as part of DOCSPRING1 documentation sprint



## ADR Template Tips

**Status lifecycle**:
- **Proposed**: Decision under discussion
- **Accepted**: Decision approved and active
- **Deprecated**: No longer recommended (but code may still use it)
- **Superseded**: Replaced by newer ADR

**Best practices**:
- Keep ADRs immutable - don't edit decisions, create new ADRs that supersede
- Number ADRs sequentially (ADR-001, ADR-002, etc.)
- Store in `docs/adr/` directory
- Link from code comments where decision is implemented