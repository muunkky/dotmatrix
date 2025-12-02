# Implement GPU-Accelerated Flower Renderer

## Overview

Implement a GPU-accelerated version of `render_flower_global_blend()` based on the algorithm design from spike qt2qer.

## Target Performance

- Small image (100x100): < 1 second
- Medium image (500x500): < 5 seconds
- Large image (6624x5868): < 2 minutes

Current CPU times (estimated):
- Large image: 73+ minutes

## Implementation Approach

Based on spike qt2qer recommendation (TBD - likely hybrid approach):

### Phase 1: GPU Radius Optimization
- [ ] Upload cluster data to GPU memory
- [ ] Implement parallel radius computation kernel
- [ ] Download optimized radii to CPU

### Phase 2: GPU or CPU Render
- [ ] If full GPU: Implement GPU compositing with atomics
- [ ] If hybrid: Use optimized CPU render with pre-computed radii

## Key Functions to Implement

```python
def render_flower_gpu(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    petal_distance: float = 0.35,
    scale: int = 1,
    ...
) -> np.ndarray:
    """GPU-accelerated flower rendering."""
    pass
```

## Files to Modify/Create

- `src/dotmatrix/gpu_renderer.py` (new file)
- `src/dotmatrix/circle_renderer.py` (add GPU dispatch)

## Testing Strategy

1. Test on small synthetic image first
2. Compare output to CPU baseline (pixel-perfect or within tolerance)
3. Benchmark timing at each image size
4. Test with different cluster counts

## Dependencies

- Spike qt2qer (Algorithm Design) - for approach selection
- Chore card (Environment Setup) - for working GPU environment
- Feature card (CPU Baseline) - for comparison ground truth

## Notes

Start simple, optimize iteratively. Profile to find actual bottlenecks.
