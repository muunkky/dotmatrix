# Feature Sprint Setup Template

## Sprint Definition & Scope

* **Sprint Name/Tag**: ARCHDEBT
* **Sprint Goal**: Address technical debt items identified during ARCHREVIEW sprint to improve code quality and maintainability before adding more features.
* **Timeline**: 2026-01-07 - 2026-01-14
* **Roadmap Link**: v1 > m3 (Performance & Scale) - improving codebase quality
* **Definition of Done**: All technical debt items resolved, tests passing, documentation updated, code merged.

**Required Checks:**
* [x] Sprint name/tag is chosen and will be used as prefix for all cards
* [x] Sprint goal clearly articulates the value/outcome
* [x] Roadmap milestone is identified and linked

---

## Card Planning & Brainstorming

> Technical debt items identified during ARCHREVIEW sprint's deep architectural review.

### Work Areas & Card Ideas

**Area 1: Color Centralization (Technical Debt - High Impact)**
* Centralize COLORS dict from multiple renderers into shared `colors.py` module
* Consolidate LAYER_ORDER and LAYER_ORDER_CMYK constants
* Update all renderers to import from central location
* Document BGR color convention in module docstring

**Area 2: Config System Enhancement (Technical Debt - Medium Impact)**
* Add RenderConfig dataclass to config.py for renderer parameters
* Integrate render parameters into config file loading
* Add CLI option group for render parameters
* Enable config file override for render-specific settings

**Area 3: ADR-006 Future Work (Lower Priority - Defer)**
* Centroid calculation as alternative anchor (defer to v0.4.0)
* Bounding box output option (defer to v0.4.0)
* Binary mask output for reconstruction (defer to v0.4.0)
* Debug visualization mode (partially exists, defer enhancement)

### Card Types Needed

- [x] **Features**: 0 - No new features
- [x] **Bugs**: 0 - No bugs
- [x] **Chores**: 1 - Sprint closeout
- [x] **Spikes**: 0 - No research needed
- [x] **Refactors**: 2 - COLORS centralization, RenderConfig dataclass

---

## Batch Card Creation Workflow

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Create Refactor Cards** | [To be created] | - [x] Refactor cards created with sprint tag |
| **2. Create Closeout Card** | [To be created] | - [x] Closeout card created with sprint tag |
| **3. Verify Sprint Tags** | [Run list_cards(sprint="ARCHDEBT")] | - [x] All cards show correct sprint tag |
| **4. Fill Detailed Cards** | [Update P1 cards with full details] | - [x] P1 cards have full acceptance criteria |

### Created Card IDs

[To be populated after batch creation]

---

## Sprint Execution Phases

| Phase / Task | Status / Link to Artifact | Universal Check |
| :--- | :--- | :---: |
| **Roadmap Integration** | v1 > m3 (Performance & Scale) | - [x] Milestone context understood |
| **Take Sprint** | [Date sprint was claimed] | - [x] Used take_sprint() to claim work |
| **Mid-Sprint Check** | [Sprint progress notes] | - [x] Reviewed list_cards(sprint="ARCHDEBT") |
| **Complete Cards** | [Completed card IDs] | - [x] Cards moved to done status |
| **Sprint Archive** | [Archive folder name] | - [x] Used archive_cards() to bundle work |
| **Update Changelog** | [Changelog entry] | - [x] CHANGELOG.md updated |

---

## Sprint Closeout & Retrospective

| Task | Detail/Link |
| :--- | :--- |
| **Cards Archived** | [Link to sprint archive folder] |
| **Sprint Summary** | [Link to SUMMARY.md] |
| **Changelog Entry** | [Unreleased section] |
| **Retrospective** | [Date retrospective held] |

### Completion Checklist

- [x] All done cards archived to sprint folder
- [x] Changelog updated with version number and changes
- [x] Incomplete cards moved to backlog or next sprint
- [x] Follow-up cards created for ADR-006 deferred items (if warranted)
- [x] Sprint closed and celebrated!


## Batch Card Creation Results


---

## Batch Card Creation Results

### Created Card IDs (2026-01-07)

| Card ID | Title | Type | Priority | Status |
| :--- | :--- | :--- | :--- | :--- |
| **r25nf2** | ARCHDEBT Sprint Planning | feature | P1 | todo |
| **clmo5r** | Centralize COLORS Dict to Shared Module | refactor | P1 | backlog |
| **n3605m** | Add RenderConfig Dataclass to Config System | refactor | P2 | backlog |
| **d91e1w** | ARCHDEBT Sprint Closeout | spike | P1 | todo |

**Total ARCHDEBT Cards**: 4 cards
- 2 refactor cards (P1 + P2)
- 1 planning card (P1)
- 1 closeout card (P1)

### Sprint Execution Order

1. **clmo5r** - Centralize COLORS dict (P1, prerequisite for clean codebase)
2. **n3605m** - Add RenderConfig dataclass (P2, depends on clean config.py)
3. **d91e1w** - Sprint closeout (final step)

### Verification

- [x] Refactor cards created with ARCHDEBT sprint tag
- [x] Closeout card created with ARCHDEBT sprint tag
- [x] All cards show correct sprint tag
- [x] P1 cards have full acceptance criteria

### Next Steps

1. Run `take_sprint(sprint_name="ARCHDEBT", owner="CAMERON")` to move backlog cards to todo
2. Start with clmo5r (COLORS centralization)
3. Then n3605m (RenderConfig)
4. Finally d91e1w (closeout)
