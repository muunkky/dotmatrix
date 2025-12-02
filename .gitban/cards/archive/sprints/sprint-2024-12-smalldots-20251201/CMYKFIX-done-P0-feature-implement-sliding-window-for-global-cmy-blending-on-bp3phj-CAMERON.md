## Description

Implement sliding window (tiled) processing for global CMY blending to handle large images without exceeding memory limits.

**Value**: Enables the global CMY blending algorithm to work on production-scale images (like `input_large.png`) that would otherwise consume too much memory when processing all clusters at once.

**Target Users**: Users processing high-resolution halftone images

**Estimated Effort**: 2-4 hours

---

## Acceptance Criteria

- [x] Process `inputs/input_large.png` successfully with global blending
- [x] Memory usage stays bounded (doesn't grow with image size)
- [x] Cross-tile cluster blending produces correct results (no seams)
- [x] CMYK pixel accuracy matches single-pass approach (within 1% per channel)
- [x] Add `--tile-size` CLI option for configurable tile dimensions

---

## Implementation Plan

### Overview

Extend `render_flower_global_blend()` to process images in overlapping tiles. Each tile includes clusters that could affect its pixels (including clusters centered outside but with petals extending into the tile). Tiles are processed independently and composited together.

### Implementation Steps

1. **Add tile iteration logic**: Divide image into tiles with configurable overlap margin (e.g., 2x max petal radius)

2. **Cluster-to-tile mapping**: For each tile, identify all clusters whose flowers could affect pixels within that tile (center + max petal reach)

3. **Per-tile global blending**: Apply existing `render_flower_global_blend()` logic to just the clusters affecting each tile

4. **Tile compositing**: Merge tile outputs into final image, handling overlap regions

5. **CLI integration**: Add `--tile-size` option, auto-detect when tiling is needed based on image dimensions

### Technical Considerations

- **Overlap margin**: Must be at least `max_black_radius + max_petal_radius` to ensure cross-cluster blending at tile boundaries is correct
- **Memory**: Each tile should process independently, releasing memory before next tile
- **Edge handling**: Partial clusters at image edges already handled by existing code

---

## Testing Strategy

### Manual Testing Scenarios

1. **Large image**: Process `inputs/input_large.png` with global blending
   - Verify no memory issues
   - Compare CMYK pixel counts to expected

2. **Boundary check**: Verify clusters spanning tile boundaries blend correctly
   - No visible seams in output
   - Pixel counts match single-pass (on smaller test image)

---

## Related Cards

**Depends on**: Global CMY blending implementation (just completed this session)

---

## Notes

### Context from current session

- Global CMY blending now achieves ~0.3% cyan, ~2.9% magenta, ~1.5% black error
- Boundary/edge clusters likely cause remaining errors
- Large image test will validate the approach at scale


## Investigation Findings

Tested on `chunk_center.png` (1000x1000, 436 clusters, dense black circles):
- Magenta: -12.5% error
- Yellow: -10.0% error  
- Black: -0.0% ✓

**Root cause**: Petal radius optimization only considers own cluster's black circle, but global blend masks petals with ALL neighboring black circles too.

**Potential fixes to try:**

A. **90° petal orientation (N/S/E/W)** - reduces contact with neighboring black circles which are diagonally positioned

B. **Iterative correction** - calculate cluster, measure error, adjust radius, repeat until CMYK matches

C. **Global black mask optimization** - when finding optimal petal radius, test against global black mask (all clusters) not just own cluster's black

D. **Pre-compensation factor** - estimate average neighbor black overlap and scale petals up proportionally

E. **Two-pass rendering** - first pass renders and measures error, second pass adjusts radii based on measured shortfall
