# Fix Radius Underestimation In Convex Edge Detection

**Type:** Bug
**Priority:** P0
**Status:** backlog
**Created:** Generated via MCP
**Confirmed:** 2025-11-28 (Spike `739f3w`)

## Description
HoughCircles consistently underestimates circle radius by ~6 pixels, leaving dark outer rings around detected circles visible in diff images.

## Root Cause Analysis

**Evidence from Investigation:**
- 3,111 black pixels found just outside detected circle edges
- Mean distance from detected edge: 6.1 pixels
- Impact: 37.5% of all uncovered pixels are black (outer ring artifacts)

**Technical Root Cause:**
HoughCircles fits circles to convex edge points which are biased toward the inner edge of the actual circle boundary. The algorithm uses edge points that are detected via Canny which tends to find the inner edge of thick black lines.

**Location:** `src/dotmatrix/convex_detector.py:509-518`

## Proposed Solutions

### Option A: Radius Padding Factor
Add a configurable radius multiplier or fixed padding (e.g., +6px or 1.3x)
- Pros: Simple, predictable
- Cons: May overcorrect in some cases

### Option B: Edge Analysis
Analyze the mask to find actual outer edge and adjust radius
- Pros: More accurate per-circle
- Cons: More complex, slower

### Option C: HoughCircles Param Tuning
Adjust `param1`/`param2` to produce larger radius estimates
- Pros: No post-processing needed
- Cons: May affect detection quality

## Tasks
- [x] Write unit test to measure radius underestimation
- [x] Implement Option A (radius padding)
- [x] Test on corner_test.png and other images
- [x] Verify diff image shows reduced outer ring artifacts
- [x] Update documentation

## Acceptance Criteria
- Black outer ring artifacts reduced by >80%
- No regression in circle detection count
- Diff coverage percentage improved

## Related
- Spike: `739f3w`
- Sprint: DETECTIONQUALITY
