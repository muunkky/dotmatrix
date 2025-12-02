# Add --gpu CLI Flag with Auto-Detection and Fallback

## Overview

Add command-line interface support for GPU acceleration with graceful fallback.

## CLI Changes

```bash
# Explicitly enable GPU
dotmatrix -i input.png --reconstitute --gpu

# Explicitly disable GPU (force CPU)
dotmatrix -i input.png --reconstitute --no-gpu

# Auto-detect (default behavior)
dotmatrix -i input.png --reconstitute
# Uses GPU if available, falls back to CPU with warning
```

## Implementation

### New CLI Arguments

```python
@click.option('--gpu/--no-gpu', default=None,
              help='Enable/disable GPU acceleration. Default: auto-detect')
```

### Auto-Detection Logic

```python
def detect_gpu_available() -> bool:
    """Check if GPU acceleration is available."""
    try:
        import [gpu_framework]
        # Test GPU access
        return True
    except (ImportError, RuntimeError):
        return False
```

### Fallback Behavior

1. If `--gpu` specified but GPU unavailable: Error with helpful message
2. If `--no-gpu` specified: Always use CPU
3. If neither specified (auto): Use GPU if available, else CPU with info message

## User Feedback

- Show GPU status in progress output: "Using GPU acceleration (GTX 1080)"
- Show fallback message: "GPU not available, using CPU (install X for GPU support)"
- Include GPU timing in manifest.json

## Files to Modify

- `src/dotmatrix/cli.py` - Add --gpu flag
- `src/dotmatrix/circle_renderer.py` - Dispatch based on flag

## Testing

- [ ] Test --gpu when GPU available
- [ ] Test --gpu when GPU not available (should error)
- [ ] Test --no-gpu always uses CPU
- [ ] Test auto-detect with GPU available
- [ ] Test auto-detect with GPU not available

## Dependencies

- Feature card (GPU Renderer Implementation)

## Notes

Consider adding --gpu-device flag for multi-GPU systems (future enhancement).
