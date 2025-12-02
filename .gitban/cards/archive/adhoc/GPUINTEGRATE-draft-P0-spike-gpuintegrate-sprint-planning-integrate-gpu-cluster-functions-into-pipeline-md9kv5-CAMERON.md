# Planning Session Spike

## Planning Session Overview

* **Session Date:** 2025-12-01
* **Meeting Context:** Sprint Planning - GPU Integration
* **Attendees:** Cameron, Claude

**Required Checks:**
* [x] **Session Date** is recorded above.
* [x] **Meeting Context** is identified.
* [x] **Attendees** are listed.

## Time Box

**Maximum Duration:** 2 hours

**Success Criteria:**
* [x] All issues from the meeting are triaged and categorized
* [x] Each issue has a complexity estimate (small/medium/large)
* [x] Each issue has a proposed card type (feature/bug/spike/chore/docs/refactor)
* [ ] Follow-up cards are created for all high-priority items
* [ ] Backlog cards are created for deferred items

## Context & Background

**Why This Planning Session:**
The GPUACCEL sprint created standalone GPU acceleration functions in `gpu.py`:
- `gpu_nms_centers()` - GPU Non-Maximum Suppression
- `gpu_nearest_center_labels()` / `gpu_create_cluster_labels()` - GPU KDTree replacement
- `gpu_count_cluster_colors()` - GPU per-cluster color counting

These functions have tests proving correctness but are not integrated into the main pipeline.

**What's Blocking:**
The `cluster_pixel_counter.py` module still uses CPU implementations:
- `_nms_centers()` at line 365
- `create_cluster_labels_from_centers()` at line 404 (uses scipy KDTree)
- Per-cluster counting loop at line 794

**Cost of Not Planning:**
- GPU acceleration benefits not realized
- Default CLI command `python -m dotmatrix -i inputs/input_large.png` doesn't use GPU cluster ops
- Large image processing remains slower than necessary

---

### Initial Issue Brainstorm

* Integrate gpu_nms_centers into _nms_centers (or replace)
* Integrate gpu_create_cluster_labels into create_cluster_labels_from_centers
* Replace per-cluster counting loop with gpu_count_cluster_colors
* Add use_gpu parameter to cluster_and_count_pixels function
* Propagate GPU flag from CLI through the pipeline
* Integration tests for GPU cluster pipeline
* Verify default behavior works: `python -m dotmatrix -i inputs/input_large.png`

---

### Issue Triage & Analysis

| Issue # | Issue Summary | Type | Complexity | Priority | Notes & Dependencies |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | Integrate GPU NMS into cluster_pixel_counter | refactor | small | P1 | Replace _nms_centers with conditional gpu_nms_centers call |
| **2** | Integrate GPU Voronoi labeling | refactor | small | P1 | Replace KDTree with gpu_create_cluster_labels |
| **3** | Integrate GPU color counting | refactor | medium | P0 | Requires restructuring the per-cluster loop |
| **4** | Add use_gpu parameter to API | feature | small | P1 | Thread through cluster_and_count_pixels |
| **5** | Propagate GPU flag from CLI | feature | small | P1 | Already have --gpu flag, just wire it through |
| **6** | Integration tests | test | medium | P1 | Test default CLI path uses GPU when available |

---

#### Issue 3: Integrate GPU color counting

**Type:** refactor

**Complexity Assessment:** medium

**Reasoning:** Medium: Requires restructuring from per-cluster loop to batch operation. The current loop (lines 794-812) iterates over centers and calls count_func per cluster. GPU version processes all clusters in one pass.

**Proposed Card Type & Template:** feature.md (adds new capability)

**Dependencies:** Issues 1, 2, 4

**Recommended Action:** Create P0 feature card - this is the main value driver

---

### Card Generation Plan

| Card to Create | Type | Priority | Template to Use | Status / Link |
| :--- | :--- | :--- | :--- | :--- |
| **Integrate GPU cluster counting into pipeline** | feature | P0 | feature.md | TODO |
| **Add use_gpu parameter and wire CLI flag** | feature | P1 | feature.md | TODO |
| **GPU cluster pipeline integration tests** | test | P1 | test.md | TODO |
| **Sprint close-out verification** | chore | P2 | chore.md | TODO |

---

## Session Closeout & Follow-up

| Task | Detail/Link |
| :--- | :--- |
| **Total Issues Triaged** | 6 issues |
| **Cards to Create** | 4 cards |
| **Issues Deferred** | None |

### Completion Checklist

* [x] All issues from the meeting are documented in the triage table.
* [x] Each issue has complexity estimate and proposed card type.
* [ ] High-priority cards (P0/P1) are created and assigned.
* [ ] Backlog cards (P2) are created for deferred work.
* [x] Dependencies between cards are documented.
* [x] Sprint capacity impact is assessed.
* [ ] Follow-up actions are scheduled.
* [x] Planning session notes are linked or attached.
