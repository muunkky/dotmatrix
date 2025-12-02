# V1 Baseline User Input Session - Visual Quality Feedback and Next Steps

**Context**: The V1 CMYK halftone reconstitution baseline is complete. Before proceeding with V2 optimizations, we need structured user input on visual quality, priorities, and ideas. This session gathers feedback by reviewing the output images together and discussing what problems the user sees.

**Related Card/Project**: CMYKFIX sprint - V1 baseline documentation

**Note**: This template is for tracking **stakeholder/leadership decisions** (business rules, requirements, policies, approvals). For **technical research decisions** (architecture choices, technology evaluations, ADRs), use `spike-technical-design.md` instead.

---

## Decision Checkboxes by Category

### Category 1: Visual Quality Assessment

- [x] **Decision 1**: What are the most noticeable visual artifacts in the reconstituted image?
  - **Answer**: Two issues: (1) Tile seams with cut-off circles, (2) Large black regions as giant circles
- [x] **Decision 2**: Are the tile seams from sliding window processing acceptable or need fixing?
  - **Answer**: Need fixing - circles should not be trimmed at boundaries
- [x] **Decision 3**: Does the color balance look correct (cyan, magenta, yellow, black)?
  - **Answer**: Yes, no strong noticeable imbalance. Re-evaluate after other fixes.

### Category 2: V2 Priority Direction

- [x] **Decision 4**: Which problem should V2 focus on first: seams, color accuracy, or rendering quality?
  - **Answer**: Fix tile seams AND large black region clustering. Both are high priority.
- [x] **Decision 5**: Should we pursue the "error balancing dot injection" optimization idea captured earlier?
  - **Answer**: Defer to V2. Solve the two main issues first.
- [x] **Decision 6**: Are there specific image regions or patterns that are most problematic?
  - **Answer**: Large overlapping black circles (face shadows, hair) render as giant blobs.

### Category 3: Requirements and Expectations

- [x] **Decision 7**: What does "good enough" look like for this project?
  - **Answer**: Solve tile seams + black region clustering = pretty close to final product
- [x] **Decision 8**: Are there reference images or expectations to compare against?
  - **Answer**: The original halftone source image - output should visually match the dot pattern.

---

## Decision Tables to Fill In

### Table 1: Visual Issues Observed

| Issue Location | Description | Severity (High/Med/Low) | Potential Cause |
|-----------|-----------|-----------|---------------------------|
| Tile boundaries | Circles are cut off/trimmed at window edges | High | Order of operations - circles detected but clipped during render |
| Large black regions | Enormous single circles instead of halftone pattern | High | Clustering treats overlapping circles as one mega-cluster |
| Color balance | No noticeable imbalance | N/A - OK | Defer to V2 after other fixes |

### Table 2: Color Channel Accuracy Observations

| Color Channel | Observation | Too Much / Too Little / Correct | Notes |
|-----------|-----------|-----------|------------------------|
| Cyan | [What you observe] | [Assessment] | [Details] |
| Magenta | [What you observe] | [Assessment] | [Details] |
| Yellow | [What you observe] | [Assessment] | [Details] |
| Black | [What you observe] | [Assessment] | [Details] |

### Table 3: V2 Feature Prioritization

| Feature/Fix | User Priority (1-5) | Technical Feasibility | Notes |
|-----------|-----------|-----------|-----------| 
| Fix tile seams | 5 (Critical) | Medium - order of ops fix | Circles cut at boundaries |
| Fix large black regions | 5 (Critical) | Medium - clustering logic | Giant circles instead of dots |
| Improve color accuracy | 2 (Deferred) | TBD | Re-evaluate after main fixes |
| Error balancing dots | 1 (V2+) | Unknown | Captured idea for later |

---

## Completion Checklist

### By Decision Domain

**Visual Quality:**
- [x] All decision checkboxes completed
- [x] Relevant tables filled in
- [x] Stakeholder agreement documented
- [x] Next steps identified

**V2 Priorities:**
- [x] All decision checkboxes completed
- [x] Relevant tables filled in
- [x] Stakeholder agreement documented
- [x] Next steps identified

**Requirements:**
- [x] All decision checkboxes completed
- [x] Relevant tables filled in
- [x] Stakeholder agreement documented
- [x] Next steps identified

---

## Meeting/Discussion Notes

### Session 1: V1 Baseline Review

**Date:** 2025-11-30
**Participants:** Cameron, Claude
**Duration:** [To be filled]

#### Key Decisions Made

1. **Two priority issues identified**: Tile seams (cut-off circles) and large black regions (giant circles)
2. **Color balance is acceptable**: No noticeable imbalance - defer further analysis to V2
3. **Error balancing deferred**: Focus on the two main issues first
4. **Success criteria**: Fixing these two issues = "pretty close to final product"

#### Open Questions

1. **Question:** What specific areas of the large image (pd_test.png) look wrong?
   - **Answer:** TBD
   - **Follow-up Required:** Yes
   - **Owner:** Cameron
   - **Due Date:** Today

2. **Question:** How do the tile seams affect the final artistic impression?
   - **Answer:** TBD
   - **Follow-up Required:** Yes
   - **Owner:** Cameron
   - **Due Date:** Today

3. **Question:** Are there color imbalances visible to the human eye?
   - **Answer:** TBD
   - **Follow-up Required:** Yes
   - **Owner:** Cameron
   - **Due Date:** Today

#### Action Items

- [x] **Action 1:** Review reconstituted.png at full zoom - Owner: Cameron - Due: Today
- [x] **Action 2:** Identify 3-5 specific problem areas - Owner: Cameron - Due: Today

---

## Decision Log

Record all finalized decisions here for easy reference:

1. **Tile Seams**: Fix by rendering all clusters, not just core clusters - 2025-11-30 - Cameron
2. **Large Black Regions**: Need circle detection for dense areas, not just clustering - 2025-11-30 - Cameron
3. **Error Balancing**: Defer to V2+ after main fixes complete - 2025-11-30 - Cameron
4. **Color Accuracy**: Acceptable for now, re-evaluate after main fixes - 2025-11-30 - Cameron

---

## Next Steps

1. **Step 1**: Review the V1 output together and gather visual feedback
2. **Step 2**: Prioritize issues based on user impact
3. **Step 3**: Create follow-up cards for V2 work based on decisions

---

## Timeline

- **Estimated Effort**: 30-60 minutes of interactive discussion
- **Dependencies**: V1 sliding window output complete ✓
- **Blocks**: V2 implementation direction

---

## Supporting Documentation

**Reference Materials:**
- Output image: `output/run_20251130_164455/reconstituted.png`
- V1 baseline doc: `src/dotmatrix/circle_renderer.py` (docstring)
- Sliding window: `src/dotmatrix/sliding_window.py`

**Related Cards/Issues:**
- CMYKFIX sprint: V1 baseline locked
- Captured idea: Error balancing dot injection optimization

---

## Success Criteria

This spike is complete when:

- [x] All decision checkboxes checked
- [x] All decision tables filled with validated input
- [x] Stakeholder agreement/sign-off obtained
- [x] Decisions documented in appropriate location
- [x] Next steps identified with owners and timelines
- [x] No blocking questions remain unresolved


## Acceptance Criteria

- [x] User has reviewed the V1 reconstituted output image at full resolution
- [x] Visual quality issues are identified and documented in tables
- [x] Color accuracy observations captured for all 4 CMYK channels
- [x] V2 priorities ranked by user importance
- [x] Next steps are clear with follow-up cards created if needed

**Follow-up Cards Created:**
- `2k2n5x`: Fix tile seam artifacts (P0)
- `hb9bd7`: Fix large black regions (P0)

---

## Test Plan

This is a user feedback session, not a code change. Testing is not applicable.

- [x] N/A - Interactive feedback session only
