# ADR-004: GPU Acceleration Strategy

## Status

**Accepted**

## Date

2025-12-01

## Context

DotMatrix's flower renderer for CMYK halftone reconstitution became the primary performance bottleneck for large images. The petal radius optimization loop—which tests 7 radius values × 3 colors × N clusters—scales poorly on CPU:

- 15,000 clusters × 21 tests = 315,000+ circle mask operations
- Each operation involves pixel counting against a global black mask
- CPU processing time: 5-10 minutes for large halftone images

Users processing production halftone images (10-38+ megapixels) needed significantly faster turnaround for iterative quality tuning.

### Requirements

1. **10x+ speedup** for the rendering phase
2. **Graceful degradation** - must work without GPU
3. **Minimal dependencies** - avoid complex CUDA toolkit installation
4. **NumPy compatibility** - existing code uses NumPy extensively

## Decision

**We will use CuPy for GPU acceleration with automatic CPU fallback.**

### Selected Approach: CuPy/CUDA

CuPy provides a NumPy-compatible API that runs on NVIDIA GPUs via CUDA:

```python
# Existing NumPy code
import numpy as np
mask = np.zeros((h, w), dtype=bool)

# CuPy equivalent (runs on GPU)
import cupy as cp
mask = cp.zeros((h, w), dtype=bool)
```

### Key Design Decisions

1. **Optional Dependency**: CuPy is an optional extra (`pip install dotmatrix[gpu]`)
2. **Auto-Detection**: GPU availability is checked at startup; CPU fallback is automatic
3. **Explicit Override**: Users can force CPU with `--no-gpu` or force GPU attempt with `--gpu`
4. **Single Transfer Point**: Data is transferred to GPU once, processed, and returned

### Implementation Structure

```
gpu.py                    - GPU detection, utilities, array transfer
gpu_renderer.py           - GPU-accelerated flower renderer
cluster_pixel_counter.py  - GPU-accelerated clustering (NMS, labeling)
```

## Options Considered

### Option 1: Pure CPU (Baseline)

**Approach**: Keep existing NumPy/SciPy implementation

**Pros**:
- No additional dependencies
- Works everywhere
- Simple to maintain

**Cons**:
- 5-10 minute render times for large images
- Not competitive for production workflows

**Verdict**: Rejected as sole approach; kept as fallback

### Option 2: CuPy/CUDA (Selected)

**Approach**: Use CuPy for NumPy-compatible GPU operations

**Pros**:
- NumPy-compatible API (minimal code changes)
- Mature NVIDIA ecosystem
- 10-100x speedup for parallel operations
- Good pip-installable packages (cupy-cuda12x)

**Cons**:
- NVIDIA GPUs only
- CUDA runtime dependency
- GPU memory limits

**Verdict**: Selected as primary GPU backend

### Option 3: OpenCL via PyOpenCL

**Approach**: Use OpenCL for cross-vendor GPU support

**Pros**:
- Works on AMD, Intel, NVIDIA GPUs
- More hardware compatibility

**Cons**:
- Less mature Python ecosystem
- More complex API (not NumPy-compatible)
- Significant code rewrite required
- Fewer users have OpenCL configured

**Verdict**: Rejected due to complexity and ecosystem maturity

### Option 4: Numba CUDA

**Approach**: Use Numba's CUDA JIT compilation

**Pros**:
- Python-native syntax
- Good for custom kernels

**Cons**:
- Less mature than CuPy for array operations
- Kernel compilation overhead
- Debugging complexity

**Verdict**: Considered for future custom kernels; not primary approach

## Implementation Details

### GPU Detection (gpu.py)

```python
def is_gpu_available() -> bool:
    """Check if GPU acceleration is available."""
    return _GPU_AVAILABLE  # Set during module initialization

def get_gpu_info() -> dict:
    """Get GPU information for diagnostics."""
    # Returns device name, memory, CUDA version, etc.

def get_array_module(use_gpu: bool = True):
    """Get numpy or cupy based on availability and preference."""
    if use_gpu and is_gpu_available():
        import cupy as cp
        return cp
    return np
```

### Accelerated Operations

| Operation | Module | GPU Function | Speedup |
|-----------|--------|--------------|---------|
| NMS centers | cluster_pixel_counter.py | `gpu_nms_centers()` | 5-10x |
| Cluster labeling | cluster_pixel_counter.py | `gpu_create_cluster_labels()` | 10-20x |
| Pixel counting | cluster_pixel_counter.py | `gpu_count_cluster_colors()` | 10-50x |
| Distance transform | cluster_pixel_counter.py | `gpu_distance_transform()` | 5-10x |
| Flower rendering | gpu_renderer.py | `render_flower_global_blend_gpu()` | 10-20x |
| Petal optimization | gpu_renderer.py | Custom CUDA kernel | 20-50x |

### Custom CUDA Kernel Example

For the petal radius optimization (the hottest loop), we use a custom CUDA kernel:

```python
count_kernel = cp.RawKernel(r'''
extern "C" __global__
void count_exposed_pixels(
    const bool* black_mask,
    const float* px_arr, const float* py_arr,
    const int* radius_arr,
    int* exposed_counts,
    int n_tests, int width, int height
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= n_tests) return;
    // Count pixels in circle not covered by black mask
    // ... (parallel per-test computation)
}
''', 'count_exposed_pixels')
```

This kernel processes all 315,000+ tests in parallel rather than sequentially.

## Consequences

### Positive

1. **10-50x speedup** for flower rendering on large images
2. **Graceful degradation** - works without GPU, just slower
3. **Minimal code changes** - NumPy API compatibility
4. **User control** - explicit `--gpu`/`--no-gpu` flags
5. **Auto-optimization** - window size adjusted based on VRAM

### Negative

1. **NVIDIA only** - no AMD/Intel GPU support
2. **CUDA dependency** - requires CUDA toolkit or cupy wheel
3. **Memory limits** - large images may exceed GPU VRAM
4. **Installation complexity** - users must match cupy-cudaXXx to their CUDA version

### Neutral

1. **Optional feature** - core functionality works without GPU
2. **Performance varies** - speedup depends on GPU model and image size
3. **Debugging complexity** - GPU code harder to debug than CPU

## Performance Benchmarks

From `benchmarks/gpu_benchmark.py`:

| Image Size | Clusters | CPU Time | GPU Time | Speedup |
|------------|----------|----------|----------|---------|
| 1000×1000 | ~500 | 2.1s | 0.8s | 2.6x |
| 2000×2000 | ~2,000 | 15.3s | 1.2s | 12.8x |
| 4000×4000 | ~8,000 | 89.2s | 4.7s | 19.0x |
| 6000×6000 | ~15,000 | 312.5s | 12.3s | 25.4x |

GPU: NVIDIA RTX 3080 (10GB VRAM)

### Memory Usage

| Image Size | CPU Memory | GPU VRAM |
|------------|------------|----------|
| 2000×2000 | ~500 MB | ~800 MB |
| 4000×4000 | ~1.5 GB | ~2.5 GB |
| 6000×6000 | ~3.0 GB | ~5.0 GB |

## Installation

### Standard (CPU Only)
```bash
pip install dotmatrix
```

### With GPU Support
```bash
# For CUDA 12.x
pip install dotmatrix[gpu]
# or
pip install cupy-cuda12x

# For CUDA 11.x
pip install cupy-cuda11x
```

### Verify GPU
```bash
dotmatrix --input test.png -m halftone --gpu --debug
# Output: "GPU acceleration: ENABLED (8192MB VRAM)"
```

## Future Considerations

1. **AMD GPU support**: Consider ROCm/HIP if user demand exists
2. **Multi-GPU**: Not currently needed; single GPU handles all test cases
3. **Tensor Cores**: Could use FP16 for additional speedup
4. **Custom kernels**: More operations could be kernelized for additional gains

## References

- CuPy Documentation: https://docs.cupy.dev/
- CUDA Toolkit: https://developer.nvidia.com/cuda-toolkit
- Benchmark Results: `benchmarks/gpu_benchmark_results.json`
- Related: ADR-001 (Large File Processing)
- Sprint Cards: GPUINTEGRATE, GPURENDER
