# Spike: Investigate 100% Pixel Accuracy for Bullseye Reconstitution

## Problem Statement

Currently achieving ~91% pixel accuracy when reconstituting images using the bullseye (concentric ring) method. Since we have exact pixel counts from ClusterResult for all 7 colors (cyan, magenta, yellow, black, red, green, blue), we should theoretically achieve 100% accuracy.

**Current results:**
| Color | Source | Reconstituted | Ratio |
|-------|--------|---------------|-------|
| Black | 121,364 | 120,539 | 99.3% |
| Cyan | 36,134 | 33,202 | 91.9% |
| Blue | 17,236 | 15,696 | 91.1% |
| Magenta | 10,562 | 9,687 | 91.7% |

## Root Cause Analysis

The fundamental challenge: **Circle areas are continuous (π*r²), but pixel counts are discrete integers.**

When we calculate `radius = sqrt(area / π)`, we get a float. When we round to an integer radius for `cv2.circle()`, we lose precision:
- `int(round(outer_r))` introduces rounding error
- Each color ring's actual rendered area differs from target

Additionally:
- Circles overlap at boundaries, causing pixel counting artifacts
- Anti-aliasing effects (though cv2.circle with thickness=-1 should be aliased)
- Edge effects where circles extend past image boundaries

## Time Box

4 hours investigation + prototype

## Success Criteria

- [ ] Understand the mathematical constraints of circle-based rendering
- [ ] Quantify the theoretical maximum accuracy achievable with circles
- [ ] Identify 2-3 alternative approaches that could improve accuracy
- [ ] Prototype at least one improved approach
- [ ] Document findings and recommendation

## Investigation Areas

### 1. Sub-pixel Radius Precision
Can we use floating-point radii somehow? Options:
- Render at higher resolution, then downsample
- Use anti-aliased circles and count partial coverage
- Custom circle rasterization with sub-pixel precision

### 2. Error Correction Strategies
- Accumulate rounding errors and compensate in subsequent rings
- Adjust radii to minimize total pixel count error rather than per-ring error
- Use optimization to find radii that minimize overall discrepancy

### 3. Alternative Rendering Approaches
- **Dithered boundaries**: Instead of hard circle edges, dither between colors
- **Pixel-exact masks**: Generate exact pixel masks rather than using cv2.circle
- **Scanline rendering**: Draw ring by ring using scanline with exact pixel counts

### 4. Hybrid Approaches
- Use circles for bulk area, then pixel-adjust boundaries
- Render core as circle, add/remove individual pixels to match count

## Technical Notes

Current rendering code (`cluster_renderer.py`):
```python
radius = int(round(outer_r))
if radius > 0:
    cv2.circle(output, (cx, cy), radius, COLORS[color], thickness=-1)
```

The `int(round())` is where precision is lost. For a target of 1000 pixels:
- Area = 1000, r = sqrt(1000/π) ≈ 17.84
- Rounded radius = 18, actual area = π*18² ≈ 1018 pixels (+1.8% error)

## Related

- ClusterResult stores exact pixel counts for all 7 colors
- Current renderer draws from outermost (yellow) to innermost (black)
- Each layer overwrites previous, so only outermost ring of each color is visible
