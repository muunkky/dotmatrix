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

**Decision:** _________________

---

## Q2: Handling Missing Black Dots

**Question:** Some clusters may have CMY dots without a black dot (light areas). How should we handle these?

**Options:**
1. **Require black** - Discard clusters without K channel
2. **Virtual anchor** - Create synthetic cluster center from CMY centroid
3. **Separate output** - Report CMY-only clusters separately

**Trade-offs:**
- Option 1: Loses data in light image regions
- Option 2: Maintains unified structure
- Option 3: More complete but complicates downstream processing

**Recommendation:** Option 2 or 3 depending on use case

**Decision:** _________________

---

## Q3: Overlap Color Calculation

**Question:** How do we count RGB overlap pixels?

**Options:**
1. **AND logic** - Pixel counts in both C AND Y mask = Green
2. **Subtractive model** - Use color theory to detect overlaps from RGB values
3. **Exclusive counting** - Red = M∩Y - (M∩Y∩C) (exclude triple overlaps)

**Trade-offs:**
- Option 1: Simple, may double-count
- Option 2: More accurate, handles gradients
- Option 3: Most precise, avoids double-counting

**Recommendation:** Option 3 for accuracy

**Decision:** _________________

---

## Q4: What Constitutes a Valid Cluster?

**Question:** What error tolerance is acceptable for cluster validation?

**Current proposal:** "Error is acceptable as long as clusters have only one of each midtone when calculated to include RGB counterparts"

**Clarifications needed:**
- Does "one of each" mean exactly 1, or at most 1?
- What if a cluster has 2 cyan dots? Merge? Split? Error?
- What about 0 of a color (e.g., no yellow in a cluster)?

**Options:**
1. **Strict** - Exactly 0-1 of each CMY, error if more
2. **Lenient** - Allow multiples, report warning
3. **Merge** - If 2 cyans detected, treat as single larger cyan region

**Decision:** _________________

---

## Q5: Output Granularity

**Question:** What level of detail in the output?

**Options:**
1. **Pixel counts only** - Just the 7 numbers per cluster
2. **With geometry** - Include bounding box, centroid, area
3. **With masks** - Include binary mask for each color per cluster
4. **Full debug** - All above plus visualization

**Trade-offs:**
- More data = more storage, slower processing
- Less data = harder to debug/validate

**Decision:** _________________

---

## Q6: Edge Clusters

**Question:** How to handle clusters at image boundaries (partial dots)?

**Options:**
1. **Include as-is** - May have artificially low counts
2. **Exclude** - Cleaner data, loses edge information
3. **Flag** - Include but mark as "partial"

**Decision:** _________________

---

## ADR Topics to Document

Based on decisions above, we'll need ADRs for:
- [ ] ADR: Cluster membership algorithm
- [ ] ADR: Overlap pixel counting methodology  
- [ ] ADR: Cluster validation rules
- [ ] ADR: Output format specification

---

## Next Steps

1. Review and answer questions above
2. Create ADRs for major decisions
3. Proceed with implementation sprint
