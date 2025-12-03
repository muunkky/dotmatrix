## Purpose

Triage and clean up 15 todo cards. Many are SMALLDOTS sprint cards now obsolete after the successful 1-line fix in v0.2.0. Need to close completed items and move remaining real work to appropriate status.

**Value**: Clear todo queue showing only actionable work. Prevents confusion about what's actually ready to work on.

**Estimated Effort**: 20 minutes

---

## Project Location

**Path**: `.gitban/cards/`

### Files/Modules Affected

- `.gitban/cards/todo-*.md`: 15 todo cards to review
- `.gitban/cards/archive/`: Destination for obsolete cards

---

## Tasks

- [x] **Archive SMALLDOTS obsolete cards**: Sprint completed with 1-line fix
  - 82ei52: orphan-pixel-diagnostic-visualization-tool (no longer needed - 0 orphans)
  - kk5hjj: multi-pass-detection-for-small-clusters (not needed - threshold fix worked)
  - njope7: smalldots-sprint-planning (completed)
  - 0lz6ew: small-cluster-rendering-adjustments (not needed)
  - gnb3ou: tdd-suite-for-small-cluster-detection (not needed - fix was simple)
  - afw8hr: smalldots-sprint-closeout (completed, can archive)

- [x] **Review remaining todo cards**: Determine if still relevant
  - hmhppf: TTLTTC parent card - keep, update as we complete
  - 4ao20k: GPU cluster integration - review if still needed
  - uvtrzw: radius overestimation fix - check if still relevant
  - Others: Evaluate for archive or backlog

- [x] **Move irrelevant cards to archive**: Use archive_cards() for obsolete

- [x] **Move deferred items to backlog**: Items not ready for immediate work

### Task Dependencies

1. SMALLDOTS cards must be verified obsolete before archiving
2. Keep TTLTTC cards active until sprint complete

---

## Outputs

### Files Created/Updated

1. **Archived cards**: SMALLDOTS obsolete items
2. **Updated todo**: Only active, relevant work items

---

## Success Criteria

- [x] SMALLDOTS obsolete cards archived (6 cards)
- [x] Remaining todo cards are actionable
- [x] No orphan work items
- [x] Todo count reduced to <8 real items

**Quality Gates:**
- [x] No accidental archival of active work
- [x] TTLTTC cards preserved

---

## Acceptance Criteria

- [x] SMALLDOTS cards (82ei52, kk5hjj, njope7, 0lz6ew, gnb3ou, afw8hr) archived
- [x] Todo card count reduced from 15 to <8
- [x] TTLTTC parent card (hmhppf) and sprint cards preserved
- [x] Remaining todo items verified as current and actionable

---

## Test Plan

- [x] Run `list_cards(status='todo')` to verify reduced count
- [x] Verify SMALLDOTS cards not in active cards list
- [x] Confirm TTLTTC cards still active
- [x] Run `get_kanban_stats()` to confirm board health
