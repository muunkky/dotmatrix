# CMYK Pipeline User Validation Checkpoints

**Context**: User needs to validate each step of the CMYK pipeline before fixes are implemented to ensure correct understanding of requirements.

**Related Card/Project**: CMYKFIX Sprint - Root Cause Analysis (8zjmm6)

**Note**: This card tracks user validation checkpoints for the CMYK accuracy fix. Each decision requires user confirmation before proceeding.

---

## Decision Checkboxes by Category

### Category 1: Source Image Processing

- [ ] **Decision 1**: Confirm pixel color clamping approach - are we clamping RGB values to pure CMYKRGB?
- [ ] **Decision 2**: Confirm CMYK decomposition formula: Co = Ci + Gi + Bi, Mo = Mi + Ri + Bi, Yo = Yi + Ri + Gi
- [ ] **Decision 3**: Confirm black handling - Ki passes through unchanged as Ko

### Category 2: Flower Geometry

- [ ] **Decision 4**: Confirm petal_distance = 0.5 (center at half black radius, inside the black circle)
- [ ] **Decision 5**: Confirm exposed area calculation - petal radius sized so visible crescent = target pixels
- [ ] **Decision 6**: Confirm petals CAN overlap with each other (subtractive blending handles it)

### Category 3: Rendering & Blending

- [ ] **Decision 7**: Confirm render order: black first, then CMY petals
- [ ] **Decision 8**: Confirm subtractive blending: C removes R, M removes G, Y removes B

---

## Decision Tables to Fill In

### Table 1: Pipeline Step Validation

| Step | Current Behavior | Expected Behavior | User Confirms? |
|------|------------------|-------------------|----------------|
| Pixel extraction | Count pure CMYKRGB pixels | [Confirm or correct] | TBD |
| CMYK decomposition | Co = Ci + Gi + Bi | [Confirm or correct] | TBD |
| Black circle area | π * Rb² = Ko | [Confirm or correct] | TBD |
| Petal distance | Rb * 0.5 | [Confirm or correct] | TBD |
| Petal radius | Sized for exposed area = target | [Confirm or correct] | TBD |
| Render order | Black first, then petals | [Confirm or correct] | TBD |
| Blending | Subtractive CMY | [Confirm or correct] | TBD |

### Table 2: Error Tolerance Decisions

| Metric | Current Threshold | Acceptable Threshold | Rationale |
|--------|-------------------|----------------------|-----------|
| Cyan accuracy | 36% error | [User decides] | [Why this tolerance?] |
| Magenta accuracy | 63% error | [User decides] | [Why this tolerance?] |
| Yellow accuracy | TBD | [User decides] | [Why this tolerance?] |
| Black accuracy | ~7% error | [User decides] | [Why this tolerance?] |

---

## Completion Checklist

### By Decision Domain

**Source Image Processing:**
- [ ] All decision checkboxes completed
- [ ] Relevant tables filled in
- [ ] Stakeholder agreement documented
- [ ] Next steps identified

**Flower Geometry:**
- [ ] All decision checkboxes completed
- [ ] Relevant tables filled in
- [ ] Stakeholder agreement documented
- [ ] Next steps identified

**Rendering & Blending:**
- [ ] All decision checkboxes completed
- [ ] Relevant tables filled in
- [ ] Stakeholder agreement documented
- [ ] Next steps identified

---

## Meeting/Discussion Notes

### Meeting 1: Initial Requirements Clarification

**Date:** 2025-11-30
**Participants:** CAMERON, Claude
**Duration:** Ongoing

#### Key Decisions Made

User has clarified:
1. Exposed area sizing is NOT optional - always use it
2. Petal distance should be 0.5 (not 0.7)
3. CMYK decomposition converts RGB overlaps to CMYK primaries
4. Accuracy checker should compare CMYK only, not RGB

#### Open Questions

1. **Question:** Is sum(cluster.cyan) expected to equal source_cyan_decomposed?
   - **Answer:** TBD
   - **Follow-up Required:** Yes
   - **Owner:** Claude
   - **Due Date:** 2025-11-30

2. **Question:** What is acceptable error threshold for CMYK accuracy?
   - **Answer:** TBD
   - **Follow-up Required:** Yes
   - **Owner:** CAMERON
   - **Due Date:** 2025-11-30

#### Action Items

- [ ] **Action 1:** Trace sum of cluster targets vs source totals - Owner: Claude - Due: 2025-11-30
- [ ] **Action 2:** User to confirm or correct each pipeline step - Owner: CAMERON - Due: 2025-11-30

---

## Decision Log

Record all finalized decisions here for easy reference:

1. **Exposed area sizing**: Always use (not optional) - 2025-11-30 - CAMERON
2. **Petal distance**: 0.5 (inside black circle) - 2025-11-30 - CAMERON
3. **CMYK decomposition**: Blue → C+M, Green → C+Y, Red → M+Y - 2025-11-30 - CAMERON

---

## Next Steps

1. **Step 1**: Complete root cause analysis (card 8zjmm6)
2. **Step 2**: Present findings to user for validation
3. **Step 3**: Get user confirmation on each decision before implementing fix

---

## Success Criteria

This spike is complete when:

- [ ] All decision checkboxes checked
- [ ] All decision tables filled with validated input
- [ ] Stakeholder agreement/sign-off obtained
- [ ] Decisions documented in appropriate location
- [ ] Next steps identified with owners and timelines
- [ ] No blocking questions remain unresolved


## Timeline

- **Estimated Effort**: 1-2 hours (user validation sessions)
- **Dependencies**: Root cause analysis (8zjmm6) must be complete first
- **Blocks**: Bug fix implementation blocked until user confirms pipeline understanding

## Supporting Documentation

**Reference Materials:**
- src/dotmatrix/circle_renderer.py - Flower rendering algorithm
- src/dotmatrix/cluster_pixel_counter.py - CMYK decomposition logic
- Previous conversation history documenting user requirements

**Related Cards/Issues:**
- 8zjmm6: CMYK Accuracy Root Cause Analysis
- CMYKFIX sprint: All cards in this sprint

## Acceptance Criteria

- [ ] User confirms CMYK decomposition formula is correct
- [ ] User confirms flower geometry parameters (petal_distance, exposed area)
- [ ] User confirms rendering order and blending approach
- [ ] User provides acceptable error thresholds for accuracy
- [ ] All open questions have user-provided answers
- [ ] Decision log is complete with all confirmed decisions

## Test Plan

### Validation Approach

1. **Present current understanding** to user via decision checkboxes
2. **Get explicit confirmation** or correction for each step
3. **Document all corrections** in decision tables
4. **Update implementation** based on user feedback

### Success Verification
- [ ] All 8 decision checkboxes marked (confirmed or corrected)
- [ ] Pipeline validation table has user confirmations
- [ ] Error threshold table has user-defined values
- [ ] No ambiguity remains about expected behavior