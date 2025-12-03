## Purpose

Archive and clean up 61 draft cards accumulated during v0.1.0 → v0.2.0 development. Many are duplicates, obsolete planning spikes, and stale close-out verification cards that clutter the board.

**Value**: Clean gitban board with only actionable items. Reduces cognitive load, prevents confusion about what needs work, and prepares board for next development phase.

**Estimated Effort**: 30 minutes

---

## Project Location

**Path**: `.gitban/cards/draft/`

### Files/Modules Affected

- `.gitban/cards/draft/*.md`: 61 draft card files to review and archive
- `.gitban/cards/archive/`: Destination for archived cards

---

## Tasks

- [x] **Review P0 drafts (25 cards)**: Identify duplicates, obsolete, and potentially valuable
  - Check for duplicate implementations (e.g., multiple chunked processing cards)
  - Mark obsolete sprint planning spikes for archive
  - Flag any cards that should become real backlog items

- [x] **Review P1 drafts (24 cards)**: Triage for relevance
  - Identify close-out verification cards (obsolete after sprint completion)
  - Check for duplicate bug cards
  - Flag documentation cards that may still be valuable

- [x] **Review P2 drafts (12 cards)**: Quick triage
  - Includes V2IDEAS cards (SVG, jitter, ASCII) - keep these
  - Archive remaining P2 cruft

- [x] **Execute batch archive**: Use archive_cards() for identified obsolete cards
  - Create archive named "2024-12-TTLTTC-drafts"
  - Verify archive manifest created

- [x] **Verify remaining drafts**: Should only be cards with real future value

### Task Dependencies

1. Review must complete before archive execution
2. V2IDEAS cards (l414i0, jahj1f, eni281) should NOT be archived

---

## Outputs

### Files Created/Updated

1. **Archive manifest**: `.gitban/cards/archive/sprints/sprint-2024-12-ttlttc-drafts-{timestamp}/manifest.json`
2. **Cleaned draft folder**: Should have <10 remaining cards

### Configurations Changed

- None

### Documentation Updates

- [x] Note archived card count in session notes

---

## Success Criteria

- [x] All 61 draft cards reviewed
- [x] Obsolete/duplicate cards archived (target: 50+ cards archived)
- [x] V2IDEAS spike cards preserved (l414i0, jahj1f, eni281)
- [x] Remaining drafts are legitimately valuable future work
- [x] Draft card count <10
- [x] Archive has manifest with card metadata

**Quality Gates:**
- [x] No valuable cards accidentally archived
- [x] Archive named descriptively for future reference


## Acceptance Criteria


- [x] Draft card count reduced from 61 to <10
- [x] All obsolete cards archived to "2024-12-TTLTTC-drafts"
- [x] V2IDEAS cards (l414i0, jahj1f, eni281) preserved
- [x] Archive manifest created with metadata
- [x] No valuable future work accidentally archived

## Test Plan


- [x] Run `list_cards(status='draft')` to verify count <10
- [x] Verify V2IDEAS cards still exist: `read_card('l414i0')`, `read_card('jahj1f')`, `read_card('eni281')`
- [x] Check archive exists: `list_dir('.gitban/cards/archive/sprints/')`
- [x] Run `get_kanban_stats()` to confirm overall board health
