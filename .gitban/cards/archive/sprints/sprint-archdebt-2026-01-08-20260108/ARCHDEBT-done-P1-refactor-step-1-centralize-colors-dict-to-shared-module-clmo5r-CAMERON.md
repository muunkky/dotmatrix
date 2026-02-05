# Code Refactoring Template

## Refactoring Overview & Motivation

* **Refactoring Target:** COLORS dict and LAYER_ORDER constants duplicated across renderers
* **Code Location:** `src/dotmatrix/` - circle_renderer.py, block_renderer.py, treemap_renderer.py, cluster_renderer.py, flower_renderer.py, gpu_renderer.py
* **Refactoring Type:** Extract shared constants to central module
* **Motivation:** Technical debt identified during ARCHREVIEW sprint - COLORS dict is duplicated in each renderer file, violating DRY principle
* **Business Impact:** Improves maintainability, reduces risk of color inconsistencies between renderers, enables single-point updates
* **Scope:** ~20 lines in 6+ files - create 1 new module, update imports in 6 renderer modules
* **Risk Level:** Low - isolated constants extraction with no logic changes
* **Related Work:** ARCHREVIEW sprint findings (docs/architecture/rendering-architecture.md, docs/architectural-guidelines.md)

**Required Checks:**
* [x] **Refactoring motivation** clearly explains why this change is needed.
* [x] **Scope** is specific and bounded (not open-ended "improve everything").
* [x] **Risk level** is assessed based on code criticality and usage.

---

## Pre-Refactoring Context Review

* [x] Existing code reviewed and behavior fully understood.
- [x] Test coverage reviewed - current test suite provides safety net.
- [x] Documentation reviewed (README, docstrings, inline comments).
- [x] Style guide and coding standards reviewed for compliance.
- [x] Dependencies reviewed (internal modules, external libraries).
- [x] Usage patterns reviewed (who calls this code, how it's used).
- [x] Previous refactoring attempts reviewed (if any - learn from history).

| Review Source | Link / Location | Key Findings / Constraints |
| :--- | :--- | :--- |
| **Existing Code** | src/dotmatrix/*_renderer.py | COLORS dict duplicated 6+ times, LAYER_ORDER 4+ times |
| **Test Coverage** | tests/test_*_renderer.py | Each renderer has tests, ~89% coverage overall |
| **Documentation** | docs/architecture/rendering-architecture.md | Documents BGR convention, notes technical debt |
| **Style Guide** | docs/architectural-guidelines.md | Section 4: "Configuration via Dataclass" pattern |
| **Dependencies** | All renderers import COLORS locally | No cross-dependencies, clean extraction possible |
| **Usage Patterns** | grep COLORS src/dotmatrix/*.py | 6 definitions found, consistent BGR format |

---

## Refactoring Strategy & Risk Assessment

**Refactoring Approach:**
* Create `src/dotmatrix/colors.py` with shared COLORS dict and LAYER_ORDER constants
* Add comprehensive docstring documenting BGR convention
* Update all renderer imports to use central module
* Remove duplicated definitions from each renderer
* Verify all tests still pass

**Incremental Steps:**
1. Step 1: Create colors.py with COLORS dict and LAYER_ORDER (TDD - write tests first)
2. Step 2: Update circle_renderer.py to import from colors.py
3. Step 3: Update block_renderer.py to import from colors.py
4. Step 4: Update treemap_renderer.py to import from colors.py
5. Step 5: Update cluster_renderer.py to import from colors.py
6. Step 6: Update flower_renderer.py to import from colors.py
7. Step 7: Update gpu_renderer.py to import from colors.py
8. Step 8: Run full test suite, verify 100% pass

**Risk Mitigation:**
* Risk: Breaking color rendering. Mitigation: BGR values are identical, only import changes
* Risk: Circular imports. Mitigation: colors.py has no dependencies, pure constants module

**Rollback Plan:**
* Rollback: Git revert, restore inline COLORS dicts (trivial, <5 minute recovery)

**Success Criteria:**
* All existing tests pass without modification
* No COLORS dict definitions in renderer files (grep verification)
* colors.py has comprehensive docstring with BGR convention
* Test coverage maintained at 89%+

---

## Refactoring Phases

| Phase / Task | Status / Link to Artifact or Card | Universal Check |
| :--- | :--- | :---: |
| **Pre-Refactor Test Suite** | tests/test_*_renderer.py | - [x] Comprehensive tests exist before refactoring starts. |
| **Baseline Measurements** | 89% coverage, 6 COLORS duplications | - [x] Baseline metrics captured (complexity, performance, coverage). |
| **Incremental Refactoring** | Steps 1-8 above | - [x] Refactoring implemented incrementally with passing tests at each step. |
| **Documentation Updates** | colors.py docstring, rendering-architecture.md | - [x] All documentation updated to reflect refactored code. |
| **Code Review** | PR review | - [x] Code reviewed for correctness, style guide compliance, maintainability. |
| **Performance Validation** | No performance impact (constant import) | - [x] Performance validated - no regression, ideally improvement. |

---

## Safe Refactoring Workflow

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Establish Test Safety Net** | Existing renderer tests | - [x] Comprehensive tests exist covering current behavior. |
| **2. Run Baseline Tests** | pytest | - [x] All tests pass before any refactoring begins. |
| **3. Capture Baseline Metrics** | 89% coverage, 6 duplications | - [x] Baseline metrics captured for comparison. |
| **4. Make Smallest Refactor** | Create colors.py | - [x] Smallest possible refactoring change made. |
| **5. Run Tests (Iteration)** | pytest after each renderer update | - [x] All tests pass after refactoring change. |
| **6. Commit Incremental Change** | git commit after each step | - [x] Incremental change committed (enables easy rollback). |
| **7. Repeat Steps 4-6** | 8 incremental commits | - [x] All incremental refactoring steps completed with passing tests. |
| **8. Update Documentation** | colors.py docstring | - [x] All documentation updated (docstrings, README, comments, architecture docs). |
| **9. Style & Linting Check** | ruff, mypy | - [x] Code passes linting, type checking, and style guide validation. |
| **10. Code Review** | Self-review or PR | - [x] Changes reviewed for correctness and maintainability. |

#### Refactoring Implementation Notes

**New Module: src/dotmatrix/colors.py**

```python
"""Shared color definitions for CMYK halftone rendering.

All colors use BGR format (OpenCV native). Never mix RGB and BGR formats.

BGR Format Reminder:
    cyan_bgr = (255, 255, 0)    # B=255, G=255, R=0
    magenta_bgr = (255, 0, 255)  # B=255, G=0, R=255

See docs/architecture/color-pipeline.md for the complete BGR convention.
"""

COLORS = {
    'yellow': (0, 255, 255),    # BGR
    'red': (0, 0, 255),         # M∩Y overlap
    'green': (0, 255, 0),       # C∩Y overlap
    'magenta': (255, 0, 255),
    'blue': (255, 0, 0),        # C∩M overlap
    'cyan': (255, 255, 0),
    'black': (0, 0, 0),
}

LAYER_ORDER = ['yellow', 'red', 'green', 'magenta', 'blue', 'cyan', 'black']
LAYER_ORDER_CMYK = ['yellow', 'magenta', 'cyan', 'black']
```

**Code Quality Improvements:**
* DRY: 6 duplications → 1 source of truth
* Maintainability: Single-point color updates
* Documentation: Comprehensive BGR convention in module docstring

---

## Refactoring Validation & Completion

| Task | Detail/Link |
| :--- | :--- |
| **Code Location** | src/dotmatrix/colors.py (new), *_renderer.py (updated imports) |
| **Test Suite** | Existing tests pass, no new tests needed (pure constants) |
| **Baseline Metrics (Before)** | 6 COLORS duplications, 4 LAYER_ORDER duplications |
| **Final Metrics (After)** | 0 duplications, 1 source of truth |
| **Documentation Updates** | colors.py docstring, update rendering-architecture.md to remove tech debt note |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Further Refactoring Needed?** | No - colors centralization complete |
| **Documentation Complete?** | Update rendering-architecture.md to remove technical debt note |
| **Technical Debt Reduced?** | Yes - removed from docs/architecture/rendering-architecture.md |

### Completion Checklist

- [x] Comprehensive tests exist before refactoring (existing tests sufficient).
- [x] All tests pass before refactoring begins (baseline established).
- [x] Baseline metrics captured (6 duplications → 0 target).
- [x] Refactoring implemented incrementally (1 renderer at a time).
- [x] All tests pass after each refactoring step (continuous validation).
- [x] Documentation updated (colors.py docstring, rendering-architecture.md).
- [x] Code passes style guide validation (ruff, mypy).
- [x] No performance regression (constant import, negligible impact).
- [x] Code quality metrics improved (0 duplications, single source of truth).


## Required Reading and Grep Terms


---

## Required Reading and Grep Terms

### Required Reading

Before starting this card, review the following documentation:

| Document | Location | Focus Areas |
| :--- | :--- | :--- |
| Rendering Architecture | docs/architecture/rendering-architecture.md | "Color Definitions" section, "Technical Debt Note" |
| Architectural Guidelines | docs/architectural-guidelines.md | Section 2: "Module Organization", BGR convention |
| Color Pipeline | docs/architecture/color-pipeline.md | BGR format table, color conventions |

### Grep Terms

Use these commands to find relevant code and understand the scope:

```bash
# Find all COLORS dict definitions
grep -rn "COLORS = {" src/dotmatrix/

# Find all LAYER_ORDER definitions
grep -rn "LAYER_ORDER" src/dotmatrix/

# Find all files importing or using COLORS
grep -rn "COLORS\[" src/dotmatrix/

# Find BGR color tuples (255, pattern)
grep -rn "(255, 255, 0)\|(0, 255, 255)\|(255, 0, 255)" src/dotmatrix/

# Find all renderer files
ls -la src/dotmatrix/*_renderer.py
```

### Key Files

| File | Purpose | Action Needed |
| :--- | :--- | :--- |
| src/dotmatrix/colors.py | NEW - Central color definitions | Create with COLORS, LAYER_ORDER |
| src/dotmatrix/circle_renderer.py | Circle rendering | Remove local COLORS, add import |
| src/dotmatrix/block_renderer.py | Block rendering | Remove local COLORS, add import |
| src/dotmatrix/treemap_renderer.py | Treemap rendering | Remove local COLORS, add import |
| src/dotmatrix/cluster_renderer.py | Cluster rendering | Remove local COLORS, add import |
| src/dotmatrix/flower_renderer.py | Flower rendering | Remove local COLORS, add import |
| src/dotmatrix/gpu_renderer.py | GPU rendering | Remove local COLORS, add import |
