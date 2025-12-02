

# Fix Tile Seam Artifacts - Render Overlap Clusters for Complete Flowers

## Bug Description

Circles are visibly cut off at tile boundaries in the sliding window output. The flower petals that extend beyond the core region are clipped, creating visible seam artifacts where tiles meet.

**Root Cause**: In `sliding_window.py`, we only render clusters whose CENTER is in the core region. But flower petals extend beyond the center, and when those petals cross into the overlap region, they are not copied to the output (we only copy core pixels).

**Current behavior**:
1. Filter to `core_clusters` (centers in core region)
2. Render only those clusters
3. Copy core region to output
4. Result: Petals extending into overlap are cut off

## Steps to Reproduce

1. Run: `python -m dotmatrix process input.png --sliding-window --window-size 500`
2. View `output/run_*/reconstituted.png`
3. Look at tile boundaries - circles are cut off at edges

## Environment

- Module: `src/dotmatrix/sliding_window.py`
- Function: `process_sliding_window()`
- Lines: ~150-175

## Solution

Change rendering strategy from "render only core clusters" to "render all clusters, copy only core pixels":

```python
# BEFORE: Only render core clusters
tile_output = render_flower_global_blend(core_clusters, ...)

# AFTER: Render ALL clusters in tile
tile_output = render_flower_global_blend(tile_clusters, ...)
# (still copy only core region to output)
```

This ensures:
- Cluster in core → fully rendered, fully visible
- Cluster in overlap near core → rendered, petals extending into core are visible
- Cluster deep in overlap → rendered but not copied (handled by adjacent tile)

## Acceptance Criteria

- [x] Flowers are not cut off at tile boundaries
- [x] No visible seams in the output image
- [x] No duplicate circles rendered at boundaries

## Test Plan

- [x] Run on pd_test.png with --sliding-window
- [x] Visually inspect tile boundaries for cut-off circles
- [x] Compare before/after at same zoom level
