# Feature Sprint Setup Template

## Sprint Definition & Scope

* **Sprint Name/Tag**: GPURENDER
* **Sprint Goal**: Implement GPU-accelerated rendering for halftone circle reconstitution, reducing render time from 73+ minutes to under 2 minutes for large (38.9 MP) images
* **Timeline**: 2025-11-30 - 2025-12-15 (flexible - quality over speed)
* **Roadmap Link**: v1 > m2 > GPU Acceleration
* **Definition of Done**: GPU render achieves <2 min for large images, outputs match CPU baseline, --gpu CLI flag available

**Required Checks:**
* [x] Sprint name/tag is chosen and will be used as prefix for all cards
* [x] Sprint goal clearly articulates the value/outcome
* [ ] Roadmap milestone is identified and linked

---

## Card Planning & Brainstorming

> Use this space to brainstorm what cards you'll need for this sprint. Think about features, bugs, chores, spikes, and documentation work.

### Work Areas & Card Ideas

**Area 1: Environment & Dependencies**
* Spike: Research GPU framework options (PyTorch vs CuPy vs Numba CUDA)
* Chore: Install and verify GPU dependencies (CUDA toolkit, chosen framework)
* Feature: Verify CPU baseline local mask optimization works correctly

**Area 2: GPU Algorithm Design**
* Spike: Analyze render pipeline phases for GPU parallelization opportunities
* Spike: Design batch processing strategy for cluster operations
* Spike: Research GPU-friendly circle drawing algorithms

**Area 3: GPU Implementation**
* Feature: Implement GPU mask generation (parallel circle drawing)
* Feature: Implement GPU exposed pixel counting
* Feature: Implement GPU color compositing

**Area 4: Testing & Validation**
* Test: GPU vs CPU output equivalence tests
* Test: Performance benchmarks on small/medium/large images
* Test: Edge case handling (no GPU, partial GPU support)

**Area 5: CLI Integration & Documentation**
* Feature: Add --gpu CLI flag with auto-detection
* Documentation: GPU usage guide and requirements

**Area 6: Sprint Closeout**
* Chore: Sprint close-out verification and cleanup

### Card Types Needed

* [x] **Features**: ~5 feature cards
* [ ] **Bugs**: 0 (known issues)
* [x] **Chores**: ~2 chore cards
* [x] **Spikes**: ~3 spike cards (research and design)
* [x] **Tests**: ~2 test cards
* [x] **Docs**: ~1 docs card

---

## Batch Card Creation Workflow

Use this workflow to create all sprint cards efficiently using gitban's `batch_create_cards()` tool.

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Create Spike Cards** | [GPU env research, GPU algorithm design] | - [ ] Spike cards created with sprint tag |
| **2. Create Feature Cards** | [CPU baseline verify, GPU render, CLI flag] | - [ ] Feature cards created with sprint tag |
| **3. Create Chore Cards** | [Install dependencies, close-out] | - [ ] Chore cards created with sprint tag |
| **4. Create Test Cards** | [Equivalence tests, benchmarks] | - [ ] Test cards created with sprint tag |
| **5. Verify Sprint Tags** | [Run list_cards with group_by_sprint] | - [ ] All cards show correct sprint tag |
| **6. Fill Detailed Cards** | [Update high-priority cards with full details] | - [ ] P0/P1 cards have full acceptance criteria |

### Workflow Instructions

**Created Card IDs**: [To be filled after batch creation]

**Phase Order (Dependencies)**:
1. **Phase 0**: Verify CPU baseline works (prerequisite for everything)
2. **Phase 1**: Research GPU frameworks (spike) → Install dependencies (chore)
3. **Phase 2**: Design GPU algorithm (spike) → depends on Phase 1
4. **Phase 3**: Implement GPU render (feature) → depends on Phase 2
5. **Phase 4**: Test equivalence and benchmarks → depends on Phase 3
6. **Phase 5**: CLI integration → depends on Phase 4
7. **Phase 6**: Close-out verification

---

## Sprint Execution Phases

Track the major phases of sprint execution. This is lightweight - just checkpoint the key gitban operations.

| Phase / Task | Status / Link to Artifact | Universal Check |
| :--- | :--- | :---: |
| **Roadmap Integration** | [Link to roadmap milestone] | - [ ] Milestone updated with sprint tag |
| **Take Sprint** | [Date sprint was claimed] | - [ ] Used take_sprint() to claim work |
| **Mid-Sprint Check** | [Sprint progress notes] | - [ ] Reviewed list_cards(group_by_sprint=True) |
| **Complete Cards** | [Completed card IDs] | - [ ] Cards moved to done status |
| **Sprint Archive** | [Archive folder name] | - [ ] Used archive_cards() to bundle work |
| **Generate Summary** | [Summary.md location] | - [ ] Used generate_sprint_summary() |
| **Update Changelog** | [Changelog entry] | - [ ] Used update_changelog() |
| **Update Roadmap** | [Milestone status] | - [ ] Marked milestone complete |

---

## Sprint Closeout & Retrospective

| Task | Detail/Link |
| :--- | :--- |
| **Cards Archived** | [To be filled] |
| **Sprint Summary** | [To be filled] |
| **Changelog Entry** | [To be filled] |
| **Roadmap Updated** | [To be filled] |
| **Retrospective** | [To be filled] |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Incomplete Cards** | [To be filled] |
| **Stub Cards** | [To be filled] |
| **Technical Debt** | [To be filled] |
| **Process Improvements** | [To be filled] |
| **Dependencies/Blockers** | [To be filled] |

### What Went Well

* [To be filled at sprint end]

### What Could Be Improved

* [To be filled at sprint end]

### Completion Checklist

* [ ] All done cards archived to sprint folder
* [ ] Sprint summary generated with automatic metrics
* [ ] Changelog updated with version number and changes
* [ ] Roadmap milestone marked complete with actual date
* [ ] Incomplete cards moved to backlog or next sprint
* [ ] Retrospective notes captured above
* [ ] Follow-up cards created for technical debt
* [ ] Sprint closed and celebrated!
