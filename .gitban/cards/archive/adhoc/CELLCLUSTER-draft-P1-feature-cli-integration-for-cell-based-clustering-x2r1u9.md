## Summary

**SPIKE FINDING: Cell-based clustering already exists via `--reconstitute`.**

The technical design spike (23pts3) discovered that:
1. `cluster_pixel_counter.py` already implements cell-based clustering via KDTree nearest-neighbor
2. `--reconstitute` already bypasses circle detection and uses `cluster_and_count_pixels()`
3. No new `--cell-clustering` flag is needed

**Decision: Archive this card - the feature already exists.**

## Original Motivation

User requested: "keep an eye on the crazy cli architecture, keep it neat."

## What Already Exists

```bash
# This command ALREADY uses cell-based clustering:
dotmatrix -i image.png -m halftone --reconstitute --render-method flower --blend-overlaps
```

Output shows: "Running cluster pixel counting... Found N cluster(s)"

The existing flow in `cli.py:843-873`:
1. Detects CMYK palette
2. Calls `cluster_and_count_pixels()` which:
   - Finds black dot centers via connected components
   - Creates Voronoi-like cells via KDTree nearest-neighbor assignment
   - Counts CMYK pixels per cell
3. Passes `ClusterResult` objects to flower renderer

## Acceptance Criteria

- [x] Cell-based clustering works with `--reconstitute`
- [x] Works with `--render-method flower` and `--blend-overlaps`
- [x] Existing commands unchanged (backward compatible)
- [x] No additional flag needed - feature is automatic

## Recommendation

Archive this card. The feature is complete. If a documentation update is needed to clarify that `--reconstitute` uses cell-based clustering, that can be a separate chore card.
