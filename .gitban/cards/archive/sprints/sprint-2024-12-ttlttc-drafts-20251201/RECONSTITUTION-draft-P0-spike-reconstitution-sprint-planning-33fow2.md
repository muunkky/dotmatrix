# RECONSTITUTION Sprint Planning

## Planning Session Overview

* **Session Date:** 2025-11-28
* **Meeting Context:** Feature Sprint Planning - Cluster Reconstitution Rendering
* **Attendees:** Engineering (Claude Code Assistant)

**Required Checks:**
* [x] **Session Date** is recorded above.
* [x] **Meeting Context** is identified.
* [x] **Attendees** are listed.

## Time Box

**Maximum Duration:** 2-3 days for full implementation

**Success Criteria:**
* [x] All issues from the meeting are triaged and categorized
* [x] Each issue has a complexity estimate (small/medium/large)
* [x] Each issue has a proposed card type (feature/bug/spike/chore/docs/refactor)
* [ ] Follow-up cards are created for all high-priority items
* [ ] Backlog cards are created for deferred items

## Context & Background

**Why This Planning Session:**
After implementing cluster pixel counting (CLUSTERING sprint), the next logical step is to visualize the detected clusters by reconstituting them into a rendered image. This allows visual comparison between the original halftone and a simplified representation using the detected ink ratios.

**What's Blocking:**
Need to define rendering modes and output format before implementation. The "bullseye" pattern is a starting point, but architecture should support future modes.

**Cost of Not Planning:**
- Rendering code may not be extensible for future visualization modes
- Poor visual quality feedback loop for detection improvements
- Missing integration with existing CLI and output workflow

---

### Initial Issue Brainstorm

* Render bullseye pattern (concentric circles: K inside C inside M inside Y)
* Calculate circle radii from pixel count ratios (area-proportional)
* Integrate with `--cluster-count` output data
* Add CLI flag `--reconstitute` or similar
* Save reconstituted image to run directory
* Support multiple rendering modes (bullseye is MVP, others later)
* Handle edge clusters (partial) - draw at edge or skip?
* Ensure RGB overlaps show correctly (intersecting regions)
* Add to manifest.json output_files
* Performance: should work on images with 1000+ clusters

---

### Issue Triage & Analysis

| Issue # | Issue Summary | Type | Complexity | Priority | Notes & Dependencies |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | Core bullseye renderer function | feature | medium | P0 | Core functionality. Takes ClusterResult, returns image. |
| **2** | Calculate radii from pixel ratios | feature | small | P0 | Math: radius = sqrt(area/pi), preserve ratios |
| **3** | CLI integration `--reconstitute` | feature | small | P1 | Add flag, integrate with existing CMYK flow |
| **4** | Handle edge/partial clusters | feature | small | P1 | Skip or clip at boundary |
| **5** | Add to manifest and output workflow | chore | small | P1 | Include in run directory outputs |
| **6** | Multiple rendering modes (extensible) | refactor | medium | P2 | Architecture to support future modes |
| **7** | Performance optimization | chore | small | P2 | Only if needed after testing |

---

#### Issue 1: Core bullseye renderer function

**Type:** feature

**Complexity Assessment:** medium

**Reasoning:** Medium: Requires understanding of cluster data structure, drawing filled circles with proper layering (K on top, then C, M, Y in order), and handling color overlaps. ~4-8 hours.

**Proposed Card Type & Template:** feature.md

**Dependencies:** ClusterResult from cluster_pixel_counter.py

**Recommended Action:** Create P0 feature card as core sprint deliverable

---

#### Issue 2: Calculate radii from pixel ratios

**Type:** feature

**Complexity Assessment:** small

**Reasoning:** Small: Pure math - convert pixel counts to circle areas, then to radii. Can be integrated into Issue 1. ~1-2 hours.

**Proposed Card Type & Template:** Part of Issue 1 (not separate card)

**Dependencies:** None

**Recommended Action:** Include in core renderer implementation

---

#### Issue 3: CLI integration

**Type:** feature

**Complexity Assessment:** small

**Reasoning:** Small: Add CLI flag, call renderer, save output. Pattern established by composite.png. ~2-4 hours.

**Proposed Card Type & Template:** feature.md

**Dependencies:** Issue 1 must complete first

**Recommended Action:** Create P1 feature card

---

#### Issue 4: Handle edge/partial clusters

**Type:** feature

**Complexity Assessment:** small

**Reasoning:** Small: ClusterResult already has `partial` flag. Decision: render at position (may clip) or skip entirely. ~1 hour.

**Proposed Card Type & Template:** Part of Issue 1

**Dependencies:** None

**Recommended Action:** Include in core renderer with configurable behavior

---

### Card Generation Plan

| Card to Create | Type | Priority | Template | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Bullseye cluster renderer** | feature | P0 | feature.md | - [ ] Card created |
| **CLI --reconstitute flag** | feature | P1 | feature.md | - [ ] Card created |
| **Sprint close-out verification** | chore | P2 | chore.md | - [ ] Card created |

---

## Session Closeout & Follow-up

| Task | Detail/Link |
| :--- | :--- |
| **Total Issues Triaged** | 7 issues |
| **Cards Created** | 3 cards planned |
| **Issues Deferred** | 2 (rendering modes, performance optimization) |
| **Meeting Notes** | This document |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Sprint Capacity Impact** | Small sprint - 1-2 days estimated |
| **Dependencies Identified?** | Depends on cluster_pixel_counter.py (already complete) |
| **Architecture Review Needed?** | No - straightforward image rendering |
| **Further Planning Required?** | No - ready to start work |

### Completion Checklist

* [x] All issues from the meeting are documented in the triage table.
* [x] Each issue has complexity estimate and proposed card type.
* [ ] High-priority cards (P0/P1) are created and assigned.
* [ ] Backlog cards (P2) are created for deferred work.
* [x] Dependencies between cards are documented.
* [x] Sprint capacity impact is assessed.
* [ ] Follow-up actions (architecture review, design meetings, etc.) are scheduled.
* [x] Planning session notes are linked or attached.
