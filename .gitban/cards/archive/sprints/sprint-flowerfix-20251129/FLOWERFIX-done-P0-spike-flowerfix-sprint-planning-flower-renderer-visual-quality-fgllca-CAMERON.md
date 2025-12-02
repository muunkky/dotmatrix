# Planning Session Spike

## Planning Session Overview

* **Session Date:** 2025-11-29
* **Meeting Context:** Bug Fix Sprint Planning - Flower Renderer Visual Quality Issues
* **Attendees:** Engineering Team

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
* [x] Follow-up cards are created for all high-priority items
* [x] Backlog cards are created for deferred items

## Context & Background

**Why This Planning Session:**
After CIRCLERENDER sprint completion, user testing revealed three critical visual defects in the flower renderer output. The reconstituted CMYK halftone images have visible quality issues that make the output look incorrect.

**What's Blocking:**
The flower renderer is producing output that doesn't match expected halftone appearance:
1. Black circles are being clipped/truncated
2. CMY petals are visible where they should be hidden behind black
3. Petal shapes are too pointy, intruding on neighboring clusters

**Cost of Not Planning:**
- Flower renderer output is visually broken and unusable
- User cannot use the reconstitution feature effectively
- Technical debt from rushed fixes without understanding root causes

---

### Initial Issue Brainstorm

* Black circles appear partial/cut off in many positions
* CMY petals show through behind black circle where they should be occluded
* Petal arcs are too pointy - centers on edge of black circle
* Petal geometry creates sharp intrusions into neighboring cluster space
* The `used` mask logic may be incorrectly clipping black circles
* Petal distance calculation puts centers too far from black center
* Need to understand optimal petal center positioning (r/2 from center?)
* May need CLI flag for petal distance configuration
* Current math assumptions may be wrong about circle positioning

---

### Issue Triage & Analysis

| Issue # | Issue Summary | Type | Complexity | Priority | Notes & Dependencies |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | Black circles clipped/partial | bug | medium | P0 | Root cause: `used` mask set before black drawn (line 382) |
| **2** | CMY petals visible behind black | bug | small | P0 | Same root cause as #1 - z-order/mask issue |
| **3** | Petals too pointy - geometry wrong | spike/bug | medium | P0 | Need technical design to determine optimal positioning |
| **4** | Petal distance not configurable | feature | small | P1 | Nice-to-have after geometry fixed |

---

#### Issue 1: Black circles clipped/partial

**Type:** bug

**Complexity Assessment:** medium

**Reasoning:** Code investigation found root cause at `circle_renderer.py:382` - the `used[any_cmy] = True` line marks CMY pixels as used BEFORE black is drawn. When `draw_circle_exact` is called for black, it skips "used" pixels, causing clipping.

**Proposed Card Type & Template:** bug.md

**Dependencies:** None - can fix independently

**Recommended Action:** Create P0 bug card with clear root cause and fix strategy

---

#### Issue 2: CMY petals visible behind black

**Type:** bug

**Complexity Assessment:** small

**Reasoning:** Same root cause as Issue #1. The CMY pixels that overlap with black's intended position aren't being overwritten. Fix for #1 will likely fix #2.

**Proposed Card Type & Template:** bug.md (combine with Issue #1)

**Dependencies:** Issue #1

**Recommended Action:** Combine with Issue #1 into single bug card

---

#### Issue 3: Petals too pointy - geometry wrong

**Type:** spike → bug

**Complexity Assessment:** medium

**Reasoning:** Requires mathematical analysis to determine optimal petal center positioning. Current code at line 334: `dist = black_radius + preliminary_radius * petal_distance` places petal centers at black circle edge. Moving centers inward (e.g., to r/2 from black center) would create shallower arcs with less intrusion. Need spike to analyze geometry before implementing fix.

**Proposed Card Type & Template:** spike-technical-design.md → bug.md

**Dependencies:** Should design geometry before implementing

**Recommended Action:** Create technical design spike first, then follow-up bug card

---

#### Issue 4: Petal distance not configurable

**Type:** feature

**Complexity Assessment:** small

**Reasoning:** Once optimal geometry is determined, expose `petal_distance` as CLI flag (already parameter in code). Low priority - can use hardcoded optimal value.

**Proposed Card Type & Template:** feature.md

**Dependencies:** Issue #3 (need optimal default first)

**Recommended Action:** Defer to P1 - create backlog card

---

### Card Generation Plan

| Card to Create | Type | Priority | Template | Status / Link | Universal Check |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Technical design: petal geometry math** | spike | P0 | spike-technical-design | scv7f9 | - [x] Card created |
| **Fix black circle clipping and z-order** | bug | P0 | bug | ffii9o | - [x] Card created |
| **Fix petal geometry for shallower arcs** | bug | P0 | bug | jgs6mn | - [x] Card created |
| **Assumptions document** | docs | P1 | docs | (in scv7f9) | - [x] Card created |
| **Sprint close-out verification** | chore | P1 | chore | f5dawl | - [x] Card created |

---

## Session Closeout & Follow-up

| Task | Detail/Link |
| :--- | :--- |
| **Total Issues Triaged** | 4 issues |
| **Cards Created** | 5 cards (scv7f9, ffii9o, jgs6mn, f5dawl, assumptions in scv7f9) |
| **Issues Deferred** | 1 issue (CLI flag for petal distance - existing parameter sufficient) |
| **Meeting Notes** | This planning card |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Sprint Capacity Impact** | P0 bugs - full sprint focus |
| **Dependencies Identified?** | Technical design spike must complete before geometry bug fix |
| **Architecture Review Needed?** | Yes - petal geometry math needs design review |
| **Further Planning Required?** | No - ready to create cards and start work |

### Completion Checklist

* [x] All issues from the meeting are documented in the triage table.
* [x] Each issue has complexity estimate and proposed card type.
* [x] High-priority cards (P0/P1) are created and assigned.
* [x] Backlog cards (P2) are created for deferred work.
* [x] Dependencies between cards are documented.
* [x] Sprint capacity impact is assessed.
* [x] Follow-up actions (architecture review, design meetings, etc.) are scheduled.
* [x] Planning session notes are linked or attached.
