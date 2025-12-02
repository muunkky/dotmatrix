# Planning Session Spike

## Planning Session Overview

* **Session Date:** 2025-12-01
* **Meeting Context:** ADR Follow-up - Implementing deferred cluster pixel counter features from ADR krzyj6
* **Attendees:** Engineering Team

**Required Checks:**
* [x] **Session Date** is recorded above.
* [x] **Meeting Context** is identified.
* [x] **Attendees** are listed.

## Time Box

**Maximum Duration:** 1 day for planning, 1 week for implementation

**Success Criteria:**
* [x] All issues from the meeting are triaged and categorized
* [x] Each issue has a complexity estimate (small/medium/large)
* [x] Each issue has a proposed card type (feature/bug/spike/chore/docs/refactor)
- [x] Follow-up cards are created for all high-priority items
- [x] Backlog cards are created for deferred items

## Context & Background

**Why This Planning Session:**
The ADR for CMYK Cluster Pixel Counting (card krzyj6) was accepted on 2024-11-28 with 4 "Future TODOs" that were deferred during initial implementation. These features enhance the cluster_pixel_counter.py module with alternative anchor methods, output formats, and debugging capabilities.

**What's Blocking:**
The ADR card cannot be marked complete until these follow-up items are addressed - either implemented or explicitly deferred to separate cards.

**Cost of Not Planning:**
- ADR card remains in limbo (accepted but incomplete)
- Useful debugging and output features remain unavailable
- Alternative clustering approaches not explored

---

### Initial Issue Brainstorm

* Centroid calculation as alternative anchor (currently uses nearest black pixel)
* Bounding box output option (add bbox to ClusterResult)
* Binary mask output for reconstruction (per-cluster masks)
* Debug visualization mode (visual debugging of clustering)

---

### Issue Triage & Analysis

| Issue # | Issue Summary | Type (feature/bug/spike/chore/docs/refactor) | Complexity (small/medium/large) | Priority (P0/P1/P2) | Notes & Dependencies |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | Centroid calculation as alternative anchor | feature | small | P2 | Alternative to nearest-pixel. May improve accuracy for irregular shapes. |
| **2** | Bounding box output option | feature | small | P2 | Add bbox field to ClusterResult. Useful for downstream processing. |
| **3** | Binary mask output for reconstruction | feature | medium | P1 | Per-cluster masks enable accurate pixel-level reconstruction. |
| **4** | Debug visualization mode | feature | medium | P1 | Essential for debugging clustering issues. Color-coded cluster viz. |

---

#### Issue 1: Centroid calculation as alternative anchor

**Type:** feature

**Complexity Assessment:** small

**Reasoning:** The code already has `find_black_dot_centers()` which uses centroids. Need to add option to use centroid as cluster assignment anchor instead of nearest black pixel.

**Proposed Card Type & Template:** feature.md

**Dependencies:** None - standalone enhancement

**Recommended Action:** Create P2 feature card - nice-to-have enhancement

---

#### Issue 2: Bounding box output option

**Type:** feature

**Complexity Assessment:** small

**Reasoning:** Add `bbox: Tuple[int,int,int,int]` field to ClusterResult dataclass. Compute from cluster mask using cv2.boundingRect() or numpy min/max.

**Proposed Card Type & Template:** feature.md

**Dependencies:** None - standalone enhancement

**Recommended Action:** Create P2 feature card - useful for downstream cropping

---

#### Issue 3: Binary mask output for reconstruction

**Type:** feature

**Complexity Assessment:** medium

**Reasoning:** Add option to output per-cluster binary masks. Requires storing/returning mask arrays which increases memory. May need lazy/on-demand generation.

**Proposed Card Type & Template:** feature.md

**Dependencies:** None - builds on existing cluster labels

**Recommended Action:** Create P1 feature card - enables precise reconstruction

---

#### Issue 4: Debug visualization mode

**Type:** feature

**Complexity Assessment:** medium

**Reasoning:** Add `--debug-clusters` CLI flag that outputs color-coded cluster visualization. Each cluster gets unique color, overlaid on original image or white background.

**Proposed Card Type & Template:** feature.md

**Dependencies:** None - visualization layer on top of clustering

**Recommended Action:** Create P1 feature card - essential for debugging

---

### Card Generation Plan

| Card to Create | Type | Priority | Template to Use | Status / Link to Card | Universal Check |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Centroid anchor option** | feature | P2 | feature.md | Card v3ld39 | - [x] Card created |
| **Bounding box output** | feature | P2 | feature.md | Card euac65 | - [x] Card created |
| **Binary mask output** | feature | P1 | feature.md | Card e1x1ck | - [x] Card created |
| **Debug visualization** | feature | P1 | feature.md | Card elr3ns | - [x] Card created |

---

## Session Closeout & Follow-up

| Task | Detail/Link |
| :--- | :--- |
| **Total Issues Triaged** | 4 issues |
| **Cards Created** | 4 cards planned |
| **Issues Deferred** | None - all will be created |
| **Meeting Notes** | ADR krzyj6 Future TODOs section |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Sprint Capacity Impact** | Small - these are enhancement features |
| **Dependencies Identified?** | No blocking dependencies |
| **Architecture Review Needed?** | No - extends existing ClusterResult dataclass |
| **Further Planning Required?** | No - ready to create cards |

### Completion Checklist

* [x] All issues from the meeting are documented in the triage table.
* [x] Each issue has complexity estimate and proposed card type.
- [x] High-priority cards (P0/P1) are created and assigned.
- [x] Backlog cards (P2) are created for deferred work.
* [x] Dependencies between cards are documented.
* [x] Sprint capacity impact is assessed.
* [x] Follow-up actions (architecture review, design meetings, etc.) are scheduled.
* [x] Planning session notes are linked or attached.


## Acceptance Criteria

- [x] All 4 feature cards created with CLUSTEREXT sprint tag
- [x] Each card has detailed acceptance criteria and implementation plan
- [x] Cards are assigned appropriate priorities (P1 for high-value, P2 for nice-to-have)
- [x] ADR card krzyj6 checkboxes can be toggled once sprint cards complete (tracked by sprint cards)

## Test Plan

- [x] Verify each created card has required template sections
- [x] Verify sprint tag CLUSTEREXT is applied to all cards
- [x] Verify cards link back to ADR krzyj6 as related work
