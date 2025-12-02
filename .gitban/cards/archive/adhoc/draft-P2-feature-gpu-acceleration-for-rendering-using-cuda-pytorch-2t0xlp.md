# GPU Acceleration for Rendering

## Problem
The global render pass for large images (38+ megapixels with 15k+ clusters) takes significant time on CPU - potentially 20+ minutes for a single render. This is a bottleneck for iterative workflows.

## Proposed Solution
Leverage GPU acceleration via CUDA/PyTorch for compute-intensive operations:

### Candidates for GPU acceleration:
1. **Flower rendering** - The render_flower_global_blend function iterates through 15k+ clusters, creating alpha masks and blending. This is embarrassingly parallel.
2. **Circle detection** - Hough transform and convex edge detection could benefit from GPU
3. **Alpha blending** - The core compositing operation

### Available tools:
- CUDA (available on system)
- PyTorch with CUDA support
- CuPy (numpy-like GPU arrays)
- OpenCV CUDA modules

## Expected Speedup
- 10-100x speedup for rendering operations
- Could reduce 20 minute renders to 1-2 minutes

## Implementation Notes
- Start with rendering (biggest bottleneck)
- Use PyTorch tensors for GPU memory management
- Batch flower operations for maximum parallelism
- Keep CPU fallback for systems without GPU
