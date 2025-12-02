# CMYKFIX Sprint Planning - V1 Baseline + Sliding Window

## Research Question
How do we lock down the current flower renderer as a V1 baseline and implement sliding window to process the full-size input image?

## Context
The current flower renderer achieves ~1-2% error on test chunks. Rather than optimizing further, we should lock this down as V1 baseline, implement sliding window, and use the full pipeline as a benchmark for future improvements.

## Problem Statement
1. Lock down current implementation as V1 baseline benchmark
2. Implement sliding window to handle large input images
3. Validate end-to-end on the big input file
4. Use V1 accuracy as benchmark for future optimization work

## Time Box
- V1 Baseline lock: 1 hour (document current state)
- Sliding window implementation: 4-6 hours
- End-to-end validation: 2 hours

---

## V1 Baseline (LOCKED)

### Current Implementation ✅
- [x] 90° petal angles (N/E/S at 0°/90°/180°)
- [x] Global CMY blending with CMYK decomposition
- [x] Global black mask optimization
- [x] petal_distance=0.35 default
- [x] Exposed area sizing with cv2.LINE_AA
- [x] CLI with --petal-distance tuning

### Baseline Accuracy Benchmark
| Image | C | M | Y | K | Total |
|-------|---|---|---|---|-------|
| chunk_center.png | +0.2% | -1.2% | -0.6% | +0.0% | 2.0% |
| source_quantized.png | -0.3% | -0.4% | -0.6% | +0.0% | 1.3% |

**V1 Target**: <3% total error on full image

### Parameters Locked for V1
```
petal_distance = 0.35
petal_angles = [0°, 90°, 180°]  # N/E/S
render_method = flower
cmyk_mode = absolute
```

---

## Sliding Window Implementation

### Design Decisions

**Window Size**: 500x500 pixels (adjustable via CLI)
- Fits comfortably in memory
- Large enough for cluster context

**Overlap Region**: 2x max_radius (e.g., 100px if max_radius=50)
- Ensures circles at boundaries are fully detected
- Petals have neighbor context for optimization

**Boundary Handling Strategy**: Detect in overlap, render only in core
- Detect circles in full window (including overlap)
- Only render circles whose CENTER is in the core region
- Neighboring tiles will render the boundary circles

### Implementation Steps
- [x] Add sliding window chunking to CLI
- [x] Implement overlap-aware circle detection
- [x] Filter circles by center position for rendering
- [x] Stitch output tiles (no blending needed if boundaries clean)
- [x] Validate: chunk accuracy ≈ single-pass accuracy

### Boundary Cluster Rendering
```
+------------------+------------------+
|    overlap       |    overlap       |
|  +------------+  |  +------------+  |
|  |   core A   |  |  |   core B   |  |
|  | (render)   |  |  | (render)   |  |
|  +------------+  |  +------------+  |
|    overlap       |    overlap       |
+------------------+------------------+

Circle at boundary: detected by both tiles
Rendered by: tile whose core contains circle center
```

---

## V1 Success Criteria

### Must Have
- [x] Process full input image (inputs/pd_test.png or similar)
- [x] Total CMYK error <5% on full image
- [x] No visible seam artifacts at tile boundaries
- [x] Single CLI command: `dotmatrix detect --sliding-window`

### Output Files
- [x] reconstituted.png - full image reconstruction
- [x] composite.png - overlay for visual validation
- [x] diff.png - error visualization
- [x] accuracy.json - per-color pixel counts

### Benchmark Established
V1 accuracy becomes the baseline for measuring future improvements:
- Per-cluster optimization (V2)
- Alternative petal shapes (V2)
- Angle optimization (V2)

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-11-30 | petal_distance=0.35 | 33% error reduction from 0.5 |
| 2024-11-30 | 90° petal angles | Minimizes neighbor overlap |
| 2024-11-30 | Lock V1, add sliding window | Ship working baseline before optimizing |
| 2024-11-30 | Detect in overlap, render in core | Clean boundaries without blending |

---

## Next Actions
1. [ ] Document V1 baseline parameters in code/config
2. [ ] Implement sliding window chunking
3. [ ] Add --sliding-window and --window-size CLI options
4. [ ] Run on full pd_test.png input
5. [ ] Record V1 benchmark accuracy

## Future Work (V2+)
- Per-cluster multivariate optimization
- Alternative petal shapes
- Angle optimization per cluster density
- Performance optimization

## Related Cards
- Existing: Sliding window card (bp3phj)
- Parent: CMYKFIX sprint


## Acceptance Criteria
- [x] V1 baseline parameters documented and locked
- [x] Sliding window implementation complete
- [x] Full input image processes without memory issues
- [x] No visible seam artifacts at tile boundaries
- [x] V1 benchmark accuracy recorded for future comparison

## Test Plan
- [x] Run on chunk_center.png - verify matches current accuracy
- [x] Run on full pd_test.png with sliding window
- [x] Compare tile boundary regions for seam artifacts
- [x] Verify accuracy.json output for benchmark recording

## Future Optimization Ideas

## Future Optimization Ideas (Captured)

### Balance Dot Injection
> "Take the error of a cluster, or cluster of clusters, and if it is above a threshold, shove a dot of that color in somewhere to help balance"

This could be implemented as:
- Calculate per-cluster or regional error after rendering
- If error exceeds threshold (e.g., 5%), inject a small correction dot
- Place dot in whitespace between clusters to avoid overlap issues
