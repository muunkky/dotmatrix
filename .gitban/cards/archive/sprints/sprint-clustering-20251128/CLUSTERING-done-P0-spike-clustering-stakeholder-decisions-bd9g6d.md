# Clustering System - Stakeholder Decisions Required

## Context

Before implementing the CMYK cluster pixel counting system, we need decisions on several architectural and behavioral questions.

---

## Q1: Cluster Membership Definition

**Question:** How do we determine which CMY dots belong to a black dot's cluster?

**Options:**
1. **Spatial proximity** - CMY dots within N pixels of black center
2. **Overlap detection** - CMY dots that physically overlap the black dot
3. **Grid-based** - Assume regular halftone grid, assign by position
4. **Hybrid** - Overlap first, then proximity for non-overlapping

**Trade-offs:**
- Option 1: Simple but may mis-cluster in dense areas
- Option 2: Accurate but misses non-overlapping midtones
- Option 3: Assumes regularity that may not exist
- Option 4: Most robust but more complex

**Recommendation:** Option 4 (Hybrid) - prioritize overlap, fall back to proximity

**Decision:** ✅ SPATIAL PROXIMITY with color completion algorithm:
1. For each midtone (C/M/Y), convert matching RGB pixels to complete broken circles
2. Use nearest neighbors to cluster each midtone to black dots
3. Repeat for all three midtones
4. Then nearest neighbors on RGB overlaps (won't be fragmented)
5. **IMPORTANT:** After clustering, subtract RGB counts from parent midtones (no double counting)
6. Capture black dot center point (x, y) - no radius needed

---

## Q2: Handling Missing Black Dots

**Question:** Some clusters may have CMY dots without a black dot (light areas). How should we handle these?

**Decision:** ✅ LEAVE WHITE AS WHITE
- White is the background color
- No virtual clusters for K-less regions
- Remaining pixel count after all 7 channels = white (implicit)

---

## Q3: Overlap Color Calculation

**Question:** How do we count RGB overlap pixels?

**Decision:** ✅ NO DOUBLE COUNTING at end of process
- Use RGB values to capture overlap information
- For clustering: complete midtones first (makes nearest neighbors easier)
- After clustering: identify RGB overlaps and subtract from parent midtones
- Final counts: C, M, Y each exclude their RGB children

Algorithm:
```
1. Complete midtones for clustering (include RGB temporarily)
2. Cluster using nearest neighbors
3. Identify RGB overlaps: R=M∩Y, G=C∩Y, B=C∩M
4. Subtract: C -= (G + B), M -= (R + B), Y -= (R + G)
5. Output: [x, y, C, M, Y, K, R, G, B] with no double counting
```

---

## Q4: What Constitutes a Valid Cluster?

**Question:** What error tolerance is acceptable for cluster validation?

**Decision:** ✅ MAX 1 OF EACH COLOR per black dot
- 0 is valid (not all dots have all colors)
- 1 is valid (normal case)
- 2+ is invalid (treat as error/noise, acceptable error rate)
- Assumes color bits aren't separated into two pieces (if they are, accept as noise)

---

## Q5: Output Granularity

**Question:** What level of detail in the output?

**Decision:** ✅ BLACK DOT CENTER + 7 CHANNEL COUNTS

Output format per cluster:
```python
[x, y, cyan, magenta, yellow, black, red, green, blue]
```

Where:
- `x, y` = center point of the black circle
- Pixel counts for each channel (no double counting)

**TODOs for future consideration (deferred to backlog):**
- [x] TODO: Add centroid calculation as alternative to black center - DEFERRED
- [x] TODO: Add bounding box option - DEFERRED
- [x] TODO: Add mask output option for full reconstruction - DEFERRED
- [x] TODO: Add visualization/debug mode - DEFERRED

---

## Q6: Edge Clusters

**Question:** How to handle clusters at image boundaries (partial dots)?

**Decision:** ✅ INCLUDE AND FLAG
- Process edge clusters (even if center is off the map)
- Do these last in processing order
- Flag as `partial: true` in output
- Whatever is easiest implementation-wise

---

## ADR Topics to Document

Based on decisions above, we'll need ADRs for (implementation documents existing decisions):
- [x] ADR: Cluster membership algorithm - documented in cluster_pixel_counter.py
- [x] ADR: Overlap pixel counting methodology - documented in cluster_pixel_counter.py
- [x] ADR: Cluster validation rules - documented in cluster_pixel_counter.py
- [x] ADR: Output format specification - documented in ClusterResult dataclass

---

## Next Steps

1. Review and answer questions above
2. Create ADRs for major decisions
3. Proceed with implementation sprint
