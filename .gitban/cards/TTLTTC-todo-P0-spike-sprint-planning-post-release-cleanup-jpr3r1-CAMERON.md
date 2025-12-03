# TTLTTC Sprint Planning - Post-Release Cleanup

## Research Question

How should we structure the post-v0.2.0 cleanup work to efficiently clear gitban cruft, remove temp files, and synchronize documentation with the actual project state?

## Time Box

**Duration:** 2-3 hours (single session cleanup)
**Deadline:** End of December 1, 2025 session

## Success Criteria

- [x] Sprint cards created for all cleanup categories
- [x] Prioritization clear (P0 → P1 → P2 order)
- [x] Each card has actionable, verifiable completion criteria
- [x] No analysis paralysis - cleanup is straightforward

## Context

### Current State Analysis

**Gitban Statistics (as of sprint start):**
- **61 draft cards** - Many are duplicates, obsolete planning spikes, stale close-out cards
- **15 todo cards** - Mix of SMALLDOTS obsoletes, the TTLTTC parent, and real future work
- **20 backlog cards** - Needs triage for relevance

**Root Directory Cruft (15+ items):**
| Category | Items |
|----------|-------|
| Temp scripts | `analyze_blanks.py`, `demo_create_test_image.py`, `test_color_separation.py`, `test_hybrid_approach.py` |
| Shell scripts | `demo_edge_methods_comparison.sh`, `extract_cmyk.ps1`, `extract_cmyk.sh`, `test_config.sh`, `test_detection_params.sh` |
| Test images | `demo_circles.png`, `test_dotmatrix.bmp`, `test_dotmatrix.png` |
| Malformed paths | `=1.3.0`, `--format=json/` |
| Temp folders | `output_test/`, `output_test2/`, `output_test3/`, `output_test_cell/`, `demo_output/` |

**Documentation State:**
- Changelog: Only 2 entries (0.1.0 and 0.2.1) - missing v0.2.0 and feature history
- Roadmap: Only V1 defined, status shows "todo" but work is substantially complete

### Sprint Card Breakdown

| Card Type | Title | Priority | Description |
|-----------|-------|----------|-------------|
| chore | Gitban Draft Card Cleanup | P0 | Archive/delete 61 draft cards |
| chore | Gitban Todo Triage | P0 | Review 15 todo cards, close SMALLDOTS obsoletes |
| chore | File System Cleanup | P1 | Remove root dir cruft and temp folders |
| docs | Changelog Full History | P0 | Document all v0.1.0 → v0.2.0 development |
| docs | Roadmap Milestone Update | P1 | Update roadmap to reflect V1 completion |
| chore | TTLTTC Closeout Verification | P1 | Verify all cleanup complete |

### Approach

**Execution Order:**
1. **Gitban Cleanup First** (drafts → todo) - Clears mental clutter
2. **File System Cleanup** - Quick wins with visible results  
3. **Documentation Sync** - Requires thought, do with fresh mind
4. **Closeout Verification** - Final validation pass

**Automation Opportunities:**
- Use `archive_cards()` batch for obsolete drafts
- Use `move_cards()` for todo triage
- Shell commands for file deletion

## References

- Parent card: hmhppf (TTLTTC comprehensive scope)
- v0.2.0 release: Small halftone dot detection fix
- SMALLDOTS sprint: Completed, 69 cards archived

## Research Notes

This is a cleanup sprint, not a research spike. The planning structure ensures:
1. Work is broken into parallelizable chunks
2. Each card is completable in 15-30 minutes
3. Clear verification criteria for closeout
4. Documentation updates happen with context fresh

## Next Steps

- [x] Create all sprint cards with TTLTTC tag
- [ ] Execute in priority order
- [ ] Verify cleanup complete with stats check
- [ ] Commit changes
