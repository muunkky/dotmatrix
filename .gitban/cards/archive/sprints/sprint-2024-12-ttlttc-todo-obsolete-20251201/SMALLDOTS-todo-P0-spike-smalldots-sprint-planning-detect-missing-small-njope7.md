# SMALLDOTS Sprint Planning - Detect Missing Small Halftone Clusters

## Research Question

How do we detect small halftone clusters that are currently being missed, causing blank spots in reconstituted output for $50k+ fine art prints?

## Context

Analysis of `input_large.png` revealed:
- **38,586 orphan pixels** located in region X:1597-3530, Y:1831-2956
- These pixels are more than 50px from any detected cluster center
- Given cluster spacing of ~49px, these represent **missing clusters**
- These images are destined for **$50k+ fine art prints** where accuracy is paramount

## Problem Statement

**Decision**: Design and implement detection for small halftone clusters that are currently being missed, causing blank spots in reconstituted output for $50k+ fine art prints.

**Evidence**: Analysis of `input_large.png` revealed:
- **38,586 orphan pixels** located in region X:1597-3530, Y:1831-2956
- These pixels are more than 50px from any detected cluster center
- Given cluster spacing of ~49px, these represent **missing clusters**

---

## Time Box

**Maximum Time**: 1 sprint (planning session: 2 hours)

---

## Success Criteria

**We'll know this spike is successful when**:
- [x] Root cause of missing clusters identified
- [x] Solution options evaluated and recommendation made
- [x] Sprint cards created with detailed implementation plans
- [ ] All sprint cards executed and verified

---

## Analysis Summary

### Root Cause Investigation

The detection pipeline uses:
1. **Distance Transform**: `threshold_ratio=0.5` filters based on distance from edges
2. **NMS (Non-Maximum Suppression)**: `min_distance=10` suppresses nearby peaks
3. **Blob Area Filter**: `min_blob_area` may filter out small blobs

**Findings**:
- Coverage ratio is 97.2% on average (good)
- But 38,586 pixels are orphans (>50px from any cluster)
- These are in a specific region, suggesting systematic detection failure

### Issue Triage

| Issue # | Summary | Type | Complexity | Priority |
| :---: | :--- | :--- | :--- | :--- |
| **1** | Root cause spike - why small clusters missed | spike | medium | P0 |
| **2** | Orphan pixel diagnostic visualization | feature | small | P0 |
| **3** | Multi-pass detection for gap regions | feature | large | P0 |
| **4** | TDD test suite for small cluster detection | test | medium | P1 |
| **5** | Small cluster rendering adjustments | feature | medium | P1 |
| **6** | Sprint closeout with quality metrics | chore | small | P1 |

---

## Recommendation

**Decision**: Implement multi-pass detection with gap analysis

**Rationale**: 
1. First pass: Run standard detection (current algorithm)
2. Compute Voronoi regions from detected centers
3. Identify gaps: regions with high pixel density but no cluster
4. Second pass: Run sensitive detection only in gap regions
5. Merge results, avoiding duplicates

This approach:
- Preserves existing detection quality for standard dots
- Only applies sensitive detection where needed
- Minimizes false positive risk
- Provides complete coverage for $50k+ print quality

**Confidence Level**: High

---

## Sprint Cards to Create

1. **Spike: Root cause analysis** - Trace detection pipeline for orphan region
2. **Feature: Orphan diagnostic tool** - Visualize orphan pixels for debugging
3. **Feature: Gap detection algorithm** - Find areas missing clusters
4. **Feature: Multi-pass detection** - Run sensitive detection in gaps
5. **Test: TDD suite for small clusters** - Regression tests
6. **Chore: Sprint closeout** - Verify quality metrics

---

## Next Steps

- [x] Create all sprint cards with detailed acceptance criteria
- [x] Add sprint to roadmap under cmyk-accuracy-optimization
- [ ] Execute sprint cards in dependency order
- [ ] Verify orphan pixel count drops to near-zero



## Acceptance Criteria

- [x] Orphan pixel count and locations documented
- [x] Root cause hypotheses formed
- [x] Solution options identified and evaluated
- [x] Sprint cards defined with dependencies
- [ ] All sprint cards created in gitban
- [ ] Sprint added to roadmap

## Test Plan

- [x] Run orphan pixel analysis on `input_large.png`
- [x] Verify orphan pixels are in region X:1597-3530, Y:1831-2956
- [x] Confirm 38,586 pixels are >50px from any cluster
- [ ] After sprint completion: verify orphan count drops to <1000
