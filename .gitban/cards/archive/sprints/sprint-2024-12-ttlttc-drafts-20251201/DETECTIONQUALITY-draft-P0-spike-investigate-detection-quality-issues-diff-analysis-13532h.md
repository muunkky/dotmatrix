# Troubleshooting: Circle Detection Quality Issues from Diff Analysis

**Card Type**: Spike - Troubleshooting
**Status**: investigation
**Priority**: P0
**Date Started**: 2025-11-28
**Owner**: CAMERON

## Problem Statement

### Symptoms Observed
- **What is broken/not working?**
  1. **Black dot outer rings left behind** - Detected radii appear too small, leaving dark rings around detected circles
  2. **Disproportionate cyan artifacts** - Significantly more cyan remaining than other colors
  3. **Gray semi-circles visible** - Overlapping region handling may be incorrect
  4. **Missing blue circles** - Blue (cyan+magenta overlap) areas seem misattributed

- **Error messages or unexpected behavior**: The diff.png image shows significant uncovered regions that should have been detected as circles

- **Impact**: Detection quality is visibly degraded, reducing accuracy of circle extraction for halftone images

- **Urgency**: Core functionality - accurate circle detection is the primary purpose of dotmatrix

### Environment Context
- **System/Service**: dotmatrix circle detection (convex-edge mode)
- **Version**: Current main branch
- **Configuration**: CMYK palette, convex-edge detection
- **Recent Changes**: Diff image feature added, calibration algorithm updated to count-based error metric

---

## Investigation Progress

### Pre-Investigation Checklist
- [ ] Problem statement clearly defined
- [ ] Error messages captured verbatim
- [ ] Recent changes reviewed (git log, deployment logs)
- [ ] Similar past issues searched (gitban cards, docs, git history)
- [ ] Monitoring/logs checked for related errors
- [ ] Impact scope assessed (how many users/systems affected)

### Research Performed

#### Documentation Review
- [ ] Official product documentation consulted
- [ ] Internal documentation/runbooks checked
- [ ] Architecture diagrams reviewed
- [ ] Related ADRs/design docs examined

**Key Documents Referenced**:
- `src/dotmatrix/convex_edge_detector.py` - Convex edge detection implementation
- `src/dotmatrix/image_extractor.py` - Circle extraction and color sampling logic
- Card `nj0ev7` - Previous work on occluded circle detection

#### Knowledge Base Search
- [ ] Google search performed
- [ ] Stack Overflow / GitHub issues searched
- [ ] Context7 / library documentation consulted
- [ ] Team knowledge / Slack history checked

**Google / Web Search Terms Used**:
1. `opencv hough circle radius accuracy` - [Pending]
2. `cmyk halftone circle overlap detection` - [Pending]
3. `convex edge detection radius estimation` - [Pending]

#### Related Gitban Cards:

| Card ID | Card Name | Initial Status | Description of relevance |
|---------|-----------|----------------|--------------------------|
| nj0ev7 | improve-detection-of-occluded-circles | done | Previous overlapping circle handling |
| z5hn8w | edge-based-color-sampling-for-overlapping-circles | done | Color sampling at edges |
| clsczj | auto-calibrate-radius-parameters | done | Radius calibration - may be related |
| fa5nnx | fix-calibration-to-use-count-based-error | done | Recent calibration change |

#### Related Code/Config:
- `src/dotmatrix/convex_edge_detector.py` - Circle detection algorithm
- `src/dotmatrix/image_extractor.py:extract_color_from_circle()` - Color attribution
- `src/dotmatrix/circle_detector.py` - Hough-based detection

---

## Solution Attempts

### Attempt Log

| # | Attempt Name | Hypothesis | Outcome | Status | Notes |
|---|-------------|------------|---------|--------|-------|
| 1 | Radius padding | Detected radius is consistently too small | [Pending] | ⬜ Todo | Add radius buffer |
| 2 | Cyan threshold tuning | Cyan detection threshold too strict | [Pending] | ⬜ Todo | Review color matching |
| 3 | Overlap attribution | Blue regions misattributed to single color | [Pending] | ⬜ Todo | Review color assignment |
| 4 | Edge detection sensitivity | Convex edges not capturing full circle | [Pending] | ⬜ Todo | Review edge params |

### Detailed Attempt Logs

#### Attempt 1: Radius Padding Investigation

**Hypothesis**: The convex edge detection algorithm estimates a radius that is slightly too small, leaving outer ring artifacts. This could be a systematic bias in the edge-to-radius conversion.

**Root Cause Theory**: When converting convex edge contours to circle radius, the algorithm may be using inner edge rather than outer edge, resulting in ~2-5px radius underestimation.

**Steps Performed**:
1. [ ] Examine radius calculation in `convex_edge_detector.py`
2. [ ] Compare detected vs actual radius on known test circles
3. [ ] Test adding radius padding factor (e.g., 1.05x or +2px)

**Results**: [Pending]

---

#### Attempt 2: Cyan Color Threshold Analysis

**Hypothesis**: The color matching for cyan has stricter thresholds than other colors, causing cyan circles to be missed or misattributed more frequently.

**Root Cause Theory**: User observation that cyan is disproportionately left behind suggests either:
- Cyan detection threshold is too narrow
- Cyan is being consumed by blue detection but not credited

**Steps Performed**:
1. [ ] Review color tolerance settings for CMYK palette
2. [ ] Compare cyan vs magenta detection rates
3. [ ] Check if blue (C+M overlap) regions are correctly handled

**Results**: [Pending]

---

#### Attempt 3: Overlapping Circle Color Attribution

**Hypothesis**: When circles overlap, the color attribution logic assigns the overlap region to only one color (e.g., magenta), leaving the other color (cyan) as "missed".

**Root Cause Theory**: The edge-based color sampling may sample from the wrong region when circles overlap, causing:
- Blue areas → detected as magenta only
- Cyan component → left behind in diff

**Steps Performed**:
1. [ ] Review `extract_color_from_circle()` logic
2. [ ] Check how overlapping regions are handled
3. [ ] Verify if both overlapping circles get proper attribution

**Results**: [Pending]

---

## Root Cause Analysis

### Confirmed Root Cause
**Summary**: [To be determined after investigation]

### Why This Wasn't Caught Earlier
- Diff image feature is new - provides first clear visibility into missed regions
- Previous validation focused on detection count, not spatial coverage
- Overlapping regions are complex edge cases

---

## Solution

### Implemented Fix
[To be determined after root cause confirmed]

### Verification

**Success Criteria**:
- [ ] Black dot outer rings no longer visible in diff
- [ ] Cyan and magenta remainder rates are proportionally similar
- [ ] Overlapping regions (blue) properly attributed to both colors
- [ ] Overall diff coverage reduced by >50%

---

## Follow-Up Actions

### Immediate Actions
- [ ] Complete investigation of all three hypotheses
- [ ] Create specific bug cards for each confirmed root cause
- [ ] Prioritize fixes based on impact

### Long-Term Prevention

| Prevention Measure | Type | Priority | Owner | Status | Card/Issue |
|-------------------|------|----------|-------|--------|------------|
| Add automated diff coverage metric | Testing | P1 | CAMERON | ⬜ Todo | [Pending] |
| Visual regression tests for detection quality | Testing | P2 | CAMERON | ⬜ Todo | [Pending] |
| Per-color detection rate metrics | Monitoring | P2 | CAMERON | ⬜ Todo | [Pending] |

---

## Lessons Learned

### Key Takeaways
1. Diff image feature revealed previously invisible quality issues
2. Multiple overlapping root causes require systematic investigation
3. Color-specific metrics needed for balanced detection

---

## Timeline

| Time (UTC) | Event | Actor | Outcome |
|------------|-------|-------|---------|
| 2025-11-28 | Problem discovered via diff image | USER | Investigation started |
| 2025-11-28 | Troubleshooting spike created | CAMERON | - |

---

**Resolution Status**: 🔄 Ongoing
**Total Investigation Time**: [In progress]
**Prevention Items Created**: 0 cards (pending investigation)
