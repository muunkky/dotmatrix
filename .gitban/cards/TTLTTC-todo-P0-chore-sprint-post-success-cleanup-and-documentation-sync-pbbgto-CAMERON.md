# Sprint Cleanup Template

## Cleanup Scope & Context

* **Sprint/Release:** Post v0.2.0 - First successful 100% halftone reconstitution
* **Primary Feature Work:** Complete CMYK halftone detection and flower rendering pipeline with GPU acceleration
* **Cleanup Category:** Mixed (gitban hygiene + file cruft + roadmap/changelog sync)

**Required Checks:**
* [ ] Sprint/Release is identified above.
* [ ] Primary feature work that generated this cleanup is documented.

---

## Deferred Work Review

First, identify what was deferred or left incomplete during the main feature work. Review commit messages, PR comments, code TODOs, and team discussions for items marked "not in scope" or "do later."

* [ ] Reviewed gitban draft cards (58 cards - many duplicates/obsolete)
* [ ] Reviewed gitban todo cards (14 cards - includes obsolete SMALLDOTS items)
* [ ] Reviewed gitban backlog cards (20 cards - needs triage)
* [ ] Checked root directory for temp scripts and test files

| Cleanup Category | Specific Item / Location | Priority | Justification for Cleanup |
| :--- | :--- | :---: | :--- |
| **Gitban Drafts** | 58 draft cards with duplicates and obsolete items | P0 | Clutters board, confuses next dev team |
| **Gitban Todo** | SMALLDOTS sprint cards (82ei52, kk5hjj, etc.) now obsolete | P0 | Sprint completed with 1-line fix, cards no longer needed |
| **Gitban Backlog** | 20 cards need review for relevance | P1 | May contain obsolete or completed work |
| **Root Dir Scripts** | analyze_blanks.py, demo_*.py, test_*.py, extract_cmyk.* | P1 | LLM-generated cruft cluttering project root |
| **Root Dir Files** | demo_circles.png, test_dotmatrix.*, =1.3.0, --format=json/ | P0 | Obvious cruft and malformed paths |
| **Output Folders** | output_test/, output_test2/, output_test3/, output_test_cell/ | P1 | Temp test output should be cleaned |
| **Demo Folders** | demo_output/, demo_results/ with 50+ subfolders | P2 | May want to keep some examples, review needed |
| **Roadmap** | Only 1 version, needs milestones for completed work | P1 | Should reflect actual V1 completion |
| **Changelog** | Only 2 entries despite months of development | P0 | Critical for next dev team handoff |

---

## Cleanup Checklist

### Gitban Hygiene (REQUIRED)

| Task | Status / Details | Done? |
| :--- | :--- | :---: |
| **Archive/Delete Draft Cards** | Review 58 drafts, archive completed, delete obsolete | - [ ] |
| **Close SMALLDOTS Sprint** | Cards 82ei52, kk5hjj, njope7, 0lz6ew, gnb3ou, afw8hr obsolete | - [ ] |
| **Triage Todo Cards** | Review 14 todo items, close completed, backlog others | - [ ] |
| **Triage Backlog Cards** | Review 20 backlog items for relevance | - [ ] |
| **Update Roadmap** | Add milestones for completed V1 work | - [ ] |
| **Update Changelog** | Add entries for all major features since 0.1.0 | - [ ] |

### File System Cleanup (REQUIRED)

| Task | Status / Details | Done? |
| :--- | :--- | :---: |
| **Remove Root Dir Scripts** | Move or delete: analyze_blanks.py, demo_*.py, test_*.py, extract_cmyk.* | - [ ] |
| **Remove Malformed Paths** | Delete: =1.3.0, --format=json/ | - [ ] |
| **Remove Test Images** | Delete: demo_circles.png, test_dotmatrix.bmp, test_dotmatrix.png | - [ ] |
| **Clean Output Folders** | Remove: output_test/, output_test2/, output_test3/, output_test_cell/ | - [ ] |
| **Review Demo Results** | Keep 1-2 exemplary results, clean the rest in demo_results/ | - [ ] |
| **Review scripts/ Folder** | Ensure scripts/ is organized and documented | - [ ] |

### Documentation Sync (REQUIRED)

| Task | Status / Details | Done? |
| :--- | :--- | :---: |
| **CHANGELOG.md** | Add comprehensive entries for v0.1.0 to v0.2.0 development | - [ ] |
| **ROADMAP.md** | Review and update with actual completed milestones | - [ ] |
| **README.md** | Verify "getting started" path is clear | - [ ] |
| **docs/ Folder** | Verify ADRs and architecture docs are current | - [ ] |

---

## Validation & Closeout

### Pre-Completion Verification

| Verification Task | Status / Evidence |
| :--- | :--- |
| **Gitban < 10 Active Cards** | Target: Only real future work items remain |
| **Root Dir Clean** | Only expected files: pyproject.toml, README.md, CHANGELOG.md, etc. |
| **No Temp Folders** | No output_test*, demo_output with cruft |
| **Changelog Complete** | All major features from v0.1.0 to v0.2.0 documented |
| **Roadmap Accurate** | Reflects actual V1 completion status |

### Completion Checklist

* [ ] All P0 items are complete and verified.
* [ ] All P1 items are complete or have follow-up tickets created.
* [ ] Gitban has < 10 active (non-archived) cards.
* [ ] Root directory contains only standard project files.
* [ ] Changelog comprehensively documents v0.1.0 - v0.2.0 journey.
* [ ] Roadmap milestones reflect actual completed work.
* [ ] Next dev team has clear "start here" path (README → DEVELOPMENT.md).


## Follow-up & Lessons Learned


| Topic | Status / Action Required |
| :--- | :--- |
| **Remaining P2 Items** | Demo folder cleanup can be deferred if time-constrained |
| **Recurring Issues** | LLM agents create files in root - need .gitignore or convention |
| **Process Improvements** | Consider cleanup checkpoint every 10 cards completed |
| **Technical Debt Tickets** | None expected - this is cleanup of completed work |

## Acceptance Criteria


- [ ] Gitban active cards reduced to < 10
- [ ] Root directory contains only standard project files
- [ ] No temp/test output folders remain
- [ ] Changelog documents all major v0.1.0 - v0.2.0 development
- [ ] Roadmap milestones reflect V1 completion
- [ ] Clear onboarding path for next dev team

## Test Plan


- [ ] Run `git status` to verify no untracked cruft files
- [ ] Verify `python -m dotmatrix --help` still works
- [ ] Verify roadmap reflects actual state
- [ ] Review README.md for clarity
- [ ] Commit and tag as cleanup release