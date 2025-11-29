# ADR-003: Block Renderer for 100% Pixel Accuracy

## Status

**Accepted**

## Date

2025-11-29

## Context

The dotmatrix reconstitute pipeline currently uses a "bullseye" renderer (`cluster_renderer.py`) that draws concentric circles for each detected cluster. Each circle's radius is calculated so that area = pixel_count:

```
radius = sqrt(pixel_count / π)
```

However, this achieves only ~91% pixel accuracy because:
1. Circle areas are continuous (π*r²), but pixel counts are discrete integers
2. `int(round(radius))` introduces rounding error
3. Each color segment loses precision independently

For CMYK halftone analysis, we need exact pixel count preservation to validate the detection pipeline.

## Decision

**We will implement a second renderer option (`block_renderer.py`) that uses horizontal stacked rectangles to achieve 100% pixel accuracy.**

### Design

Each cluster is rendered as vertically stacked color rows:

```
┌─────────────────────────────────────┐  ← yellow (width = yellow_pixels / segment_height)
├───────────────────────────┐         │  ← red
├─────────────────────┐     │         │  ← green
├───────────────────────────────┐     │  ← magenta
├─────────────────┐   │     │   │     │  ← blue
├─────────────────────────┐ │   │     │  ← cyan
├───────────────────────────────────┐ │  ← black
└───────────────────────────────────┘
```

**Key properties:**
- Each color gets a fixed-height row (e.g., 10px)
- Row width = pixel_count / segment_height (integer math)
- Total bar height = 7 × segment_height
- Rectangle area = width × height exactly represents pixel count

### Height Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `fixed-segment` | All color rows same height, widths vary | Primary mode for midtone printer overlap |
| `fixed-bar` | All bars same total height | Uniform visual appearance |
| `variable` | Bar height scales with pixel count | Proportional representation |
| `min-height` | Minimum height enforced | Prevents thin bars |

**Primary implementation**: `fixed-segment` mode (required for printer overlap use case).

### CLI Integration

```bash
# Default bullseye (backward compatible)
dotmatrix reconstitute image.png

# Block renderer (100% accuracy)
dotmatrix reconstitute --render-method block image.png

# With custom segment height
dotmatrix reconstitute --render-method block --segment-height 20 image.png
```

## Alternatives Considered

### 1. Improve bullseye accuracy with sub-pixel rendering
- Render at 2-4x resolution, then downsample
- Adds complexity and memory overhead
- Still can't achieve exact integer pixel counts
- **Rejected**: Complex, still imperfect

### 2. Vertical stacked bars
- Same accuracy as horizontal
- Less natural visual flow
- **Deferred**: Could add as option later

### 3. Grid/tile approach
- Divide image into cells, fill each with exact pixel counts
- Loses cluster position information
- More complex boundary calculations
- **Rejected**: Misaligns with cluster-based detection

## Consequences

### Positive
- 100% pixel accuracy for reconstituted images
- Enables validation of detection pipeline
- Supports midtone printer overlay workflow
- Simple implementation (cv2.rectangle)
- Fast rendering (faster than circles)

### Negative
- Visual output differs significantly from bullseye
- Two rendering methods to maintain
- Bars may overlap for dense clusters

### Neutral
- Bullseye remains default for visual appeal
- Block mode is opt-in via CLI flag

## References

- Spike card: hgcp2f (BLOCKRENDER sprint)
- Feature card: gsqq6k (block_renderer.py implementation)
- Related: color-pipeline.md architecture doc
