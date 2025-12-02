# Planning Session Spike

## Planning Session Overview

* **Session Date:** 2025-12-01
* **Meeting Context:** Technical Investigation - Missing Small Cluster Detection for High-Value Print Production
* **Attendees:** Cameron (Engineering)

**Required Checks:**
* [x] **Session Date** is recorded above.
* [x] **Meeting Context** is identified.
* [x] **Attendees** are listed.

## Time Box

**Maximum Duration:** 4 hours

**Success Criteria:**
* [x] All issues from the meeting are triaged and categorized
* [x] Each issue has a complexity estimate (small/medium/large)
* [x] Each issue has a proposed card type (feature/bug/spike/chore/docs/refactor)
* [ ] Follow-up cards are created for all high-priority items
* [ ] Backlog cards are created for deferred items

## Context & Background

**Why This Planning Session:**
During visual inspection of reconstituted output from `input_large.png`, blank spots were observed in areas where the original image contained small halftone dots. Analysis revealed **38,586 orphan pixels** (located in region X:1597-3530, Y:1831-2956) that are more than 50px from any detected cluster center, indicating missing small cluster detection.

**What's Blocking:**
These images are destined for **$50k+ fine art prints** where accuracy is paramount. Missing small dots create visible artifacts that diminish print quality and value. Current detection parameters may be filtering out legitimate small halftone clusters.

**Cost of Not Planning:**
- Visual artifacts in high-value prints
- Incomplete representation of original halftone pattern
- Customer dissatisfaction and potential rework costs
- Reputation impact on print quality

---

### Initial Issue Brainstorm

* NMS (Non-Maximum Suppression) min_distance=10 may be suppressing small dots too aggressively
* threshold_ratio=0.5 in distance transform may miss faint/small dots
* Small clusters may have different characteristics than standard halftone dots
* Need diagnostic tooling to visualize orphan pixel regions
* Need TDD approach - tests should fail first, then pass after fix
* Need validation methodology to verify complete coverage
* Consider multi-pass detection: large dots first, then small dots in gaps
* May need Voronoi-based gap analysis to find missing cluster locations
* Rendering may need adjustment if cluster characteristics differ

---

### Issue Triage & Analysis

| Issue # | Issue Summary | Type (feature/bug/spike/chore/docs/refactor) | Complexity (small/medium/large) | Priority (P0/P1/P2) | Notes & Dependencies |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | Investigate why small clusters are not detected | spike | medium | P0 | Root cause analysis - must understand before fixing |
| **2** | Create diagnostic visualization for orphan pixels | feature | small | P0 | Needed to validate fixes and debug |
| **3** | Implement multi-pass detection for small clusters | feature | large | P0 | Core fix - detect small dots in gap regions |
| **4** | Add TDD test suite for small cluster detection | test | medium | P1 | Regression prevention, verify fix works |
| **5** | Update rendering to handle small clusters correctly | feature | medium | P1 | May need different rendering for small dots |
| **6** | Validate complete coverage with metrics | chore | small | P1 | Final verification - orphan count should be near zero |
| **7** | Sprint closeout and quality verification | chore | small | P1 | Ensure $50k+ print quality standards met |

---

#### Issue 1: Investigate why small clusters are not detected

**Type:** spike

**Complexity Assessment:** medium

**Reasoning:** Requires deep analysis of detection pipeline: distance transform thresholds, NMS parameters, blob area filters. May need to trace through code paths to understand filtering behavior.

**Proposed Card Type & Template:** `spike-technical-design.md`

**Dependencies:** None - can start immediately

**Recommended Action:** Create P0 spike card, timebox to 2-4 hours, document findings

---

#### Issue 2: Create diagnostic visualization for orphan pixels

**Type:** feature

**Complexity Assessment:** small

**Reasoning:** Straightforward visualization task - overlay orphan pixels on original image, show distance heatmap to nearest cluster. Uses existing cluster data and image processing tools.

**Proposed Card Type & Template:** `feature.md`

**Dependencies:** Requires understanding from Issue #1 spike

**Recommended Action:** Create P0 feature card after spike completes, use TDD approach

---

#### Issue 3: Implement multi-pass detection for small clusters

**Type:** feature

**Complexity Assessment:** large

**Reasoning:** Core algorithmic work. Options include:
1. Lower detection thresholds globally (may cause false positives)
2. Multi-pass detection: run normal detection, identify gaps, run sensitive detection in gaps only
3. Voronoi-based approach: compute expected cluster grid, find missing locations
4. Adaptive thresholding based on local region characteristics

Requires careful design to avoid introducing artifacts while capturing all legitimate dots.

**Proposed Card Type & Template:** `feature.md`

**Dependencies:** Requires spike findings (Issue #1) and diagnostic tooling (Issue #2)

**Recommended Action:** Create P0 feature card with detailed implementation plan, TDD approach

---

#### Issue 4: Add TDD test suite for small cluster detection

**Type:** test

**Complexity Assessment:** medium

**Reasoning:** Need to create test images with known small clusters, verify detection captures them. Should include:
- Synthetic test images with various dot sizes
- Edge case tests (smallest detectable dot, closely-spaced dots)
- Regression tests using `input_large.png` orphan region

**Proposed Card Type & Template:** `test.md`

**Dependencies:** Should be created alongside Issue #3, tests written first (TDD)

**Recommended Action:** Create P1 test card, integrate with feature development

---

#### Issue 5: Update rendering to handle small clusters correctly

**Type:** feature

**Complexity Assessment:** medium

**Reasoning:** Small clusters may need different rendering treatment:
- Very small circles may not render well with bullseye pattern
- May need minimum radius floor for visual consistency
- May need to verify cumulative radii calculations work for small pixel counts

**Proposed Card Type & Template:** `feature.md`

**Dependencies:** Depends on Issue #3 (detection must work first)

**Recommended Action:** Create P1 feature card, may be merged with Issue #3 if scope is small

---

#### Issue 6: Validate complete coverage with metrics

**Type:** chore

**Complexity Assessment:** small

**Reasoning:** Final validation step - run orphan pixel analysis after fix, verify count drops from 38,586 to near-zero. Document before/after metrics for quality assurance.

**Proposed Card Type & Template:** `chore.md`

**Dependencies:** All other issues must be complete

**Recommended Action:** Create P1 chore card for sprint closeout verification

---

#### Issue 7: Sprint closeout and quality verification

**Type:** chore

**Complexity Assessment:** small

**Reasoning:** Given $50k+ print value, need formal verification that fix meets quality standards. Visual inspection of output, metric documentation, stakeholder sign-off.

**Proposed Card Type & Template:** `chore-cleanup.md`

**Dependencies:** All other issues complete

**Recommended Action:** Create P1 closeout card

---

### Card Generation Plan

| Card to Create | Type | Priority | Template to Use | Status / Link to Card | Universal Check |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Root cause investigation spike** | spike | P0 | spike-technical-design.md | Status: TODO | - [ ] Card created |
| **Orphan pixel diagnostic visualization** | feature | P0 | feature.md | Status: TODO | - [ ] Card created |
| **Multi-pass small cluster detection** | feature | P0 | feature.md | Status: TODO | - [ ] Card created |
| **TDD test suite for small clusters** | test | P1 | test.md | Status: TODO | - [ ] Card created |
| **Small cluster rendering adjustments** | feature | P1 | feature.md | Status: TODO | - [ ] Card created |
| **Coverage validation metrics** | chore | P1 | chore.md | Status: TODO | - [ ] Card created |
| **Sprint closeout verification** | chore | P1 | chore-cleanup.md | Status: TODO | - [ ] Card created |

---

## Session Closeout & Follow-up

| Task | Detail/Link |
| :--- | :--- |
| **Total Issues Triaged** | 7 issues |
| **Cards Created** | 0 cards (pending creation) |
| **Issues Deferred** | 0 issues |
| **Meeting Notes** | Analysis showed 38,586 orphan pixels in region X:1597-3530, Y:1831-2956 |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Sprint Capacity Impact** | Full sprint dedicated to this issue - critical for print quality |
| **Dependencies Identified?** | Spike → Diagnostic → Detection → Tests → Rendering → Validation → Closeout |
| **Architecture Review Needed?** | May need if multi-pass detection requires significant pipeline changes |
| **Further Planning Required?** | Create cards per plan above, then execute sequentially |

### Completion Checklist

* [x] All issues from the meeting are documented in the triage table.
* [x] Each issue has complexity estimate and proposed card type.
* [ ] High-priority cards (P0/P1) are created and assigned.
* [ ] Backlog cards (P2) are created for deferred work.
* [x] Dependencies between cards are documented.
* [x] Sprint capacity impact is assessed.
* [ ] Follow-up actions (architecture review, design meetings, etc.) are scheduled.
* [x] Planning session notes are linked or attached.
