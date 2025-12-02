# Fix Cyan Circle Detection Failure (HoughCircles Partial Arcs)

**Type:** Bug  
**Priority:** P0
**Status:** backlog
**Created:** Generated via MCP
**Confirmed:** 2025-11-28 (Spike `739f3w`)

## Description
HoughCircles fails to detect many cyan circles, leaving 57.5% of cyan pixels uncovered. The original hypothesis (threshold imbalance) was DISPROVEN - all colors use the same `ink_threshold=100`. The actual issue is HoughCircles failing on partial arcs created by overlapping circles.

## Root Cause Analysis

**Evidence from Investigation:**
- 102 large cyan blobs detected in cyan mask via connected component analysis
- Only 56 cyan circles detected by HoughCircles (45% miss rate)
- Each missed blob has ~13 convexity defects on average (partial arcs due to overlaps)
- 92.9% of uncovered cyan pixels are TRULY MISSED (not overlap attribution)
- Impact: 41.2% of all uncovered pixels are cyan

**Technical Root Cause:**
HoughCircles uses gradient-based circle detection which fails on partial arcs. When circles overlap, the convex edge detection creates arc fragments with multiple defects. HoughCircles can't reliably fit circles to these fragmented edges.

**Note:** Original hypothesis about cyan threshold imbalance was DISPROVEN:
- `separate_cmyk_inks()` uses same `ink_threshold=100` for all CMY colors
- Color detection is symmetric; detection failure is in HoughCircles

**Location:** `src/dotmatrix/convex_detector.py:377-550` (detect_circles_from_convex_edges)

## Proposed Solutions

### Option A: Lower HoughCircles param2
Lower the accumulator threshold to accept weaker circle evidence
- Pros: May catch more partial arcs
- Cons: May increase false positives

### Option B: Fallback Connected Component Fitting
For large blobs not detected by HoughCircles, fit circles using:
- Center: centroid of connected component
- Radius: derived from area (r = sqrt(area/pi))
- Pros: Catches all large missed blobs
- Cons: Less accurate for irregular shapes

### Option C: Morphological Enhancement
Before HoughCircles, use morphological operations to close gaps:
- Dilation to connect arc fragments
- Then detection
- Pros: May complete partial arcs
- Cons: May merge adjacent circles incorrectly

## Tasks
- [x] Write test to measure cyan detection rate vs expected blobs
- [x] Implement Option B (fallback connected component fitting)
- [x] Test on corner_test.png and other images
- [x] Verify diff shows balanced color detection rates
- [x] Update documentation

## Acceptance Criteria
- Cyan detection rate increased to >90% of detected blobs
- Cyan/Magenta detection ratio within 20% of each other
- No increase in false positive detections
- Diff coverage percentage improved

## Related
- Spike: `739f3w`
- Sprint: DETECTIONQUALITY
