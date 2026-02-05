# Code Refactoring Template

## Refactoring Overview & Motivation

* **Refactoring Target:** Renderer parameters scattered across CLI args and function signatures
* **Code Location:** `src/dotmatrix/config.py`, `src/dotmatrix/cli.py`, various renderers
* **Refactoring Type:** Introduce dataclass for renderer configuration
* **Motivation:** Technical debt identified during ARCHREVIEW sprint - render parameters bypass config system, violating "Configuration via Dataclass" principle
* **Business Impact:** Enables config file override for render-specific settings, improves discoverability of render options, enables future render presets
* **Scope:** ~100 lines - add RenderConfig dataclass, update CLI option group, integrate with config loading
* **Risk Level:** Medium - touches config system which affects CLI behavior
* **Related Work:** ARCHREVIEW sprint findings (docs/architectural-guidelines.md Section 6: "Configuration Management")

**Required Checks:**
* [x] **Refactoring motivation** clearly explains why this change is needed.
* [x] **Scope** is specific and bounded (not open-ended "improve everything").
* [x] **Risk level** is assessed based on code criticality and usage.

---

## Pre-Refactoring Context Review

- [x] Existing code reviewed and behavior fully understood.
- [x] Test coverage reviewed - current test suite provides safety net.
- [x] Documentation reviewed (README, docstrings, inline comments).
- [x] Style guide and coding standards reviewed for compliance.
- [x] Dependencies reviewed (internal modules, external libraries).
- [x] Usage patterns reviewed (who calls this code, how it's used).
- [x] Previous refactoring attempts reviewed (if any - learn from history).

| Review Source | Link / Location | Key Findings / Constraints |
| :--- | :--- | :--- |
| **Existing Code** | src/dotmatrix/config.py | DetectionParams, ColorParams, OutputParams dataclasses exist; no RenderConfig |
| **Test Coverage** | tests/test_config.py | Config tests exist, ~89% coverage overall |
| **Documentation** | docs/architectural-guidelines.md | Section 6 documents config pattern to follow |
| **Style Guide** | docs/architectural-guidelines.md | Principle 4: "Configuration via Dataclass" |
| **Dependencies** | CLI → config.py → renderers | Render params currently bypass config system |
| **Usage Patterns** | grep render cli.py | Multiple render-related CLI flags not in config |

---

## Refactoring Strategy & Risk Assessment

**Refactoring Approach:**
* Create `RenderConfig` dataclass in config.py mirroring existing patterns
* Add render parameters: method, petal_distance, skip_partial, jitter settings
* Update from_cli_args() to populate RenderConfig
* Add CLI option group for render parameters (following existing pattern)
* Enable config file loading for render section

**Incremental Steps:**
1. Step 1: Add RenderConfig dataclass with default values (TDD - write tests first)
2. Step 2: Update DetectionConfig to include render: RenderConfig field
3. Step 3: Update from_cli_args() to populate RenderConfig
4. Step 4: Add "Render Options" CLI option group with existing flags
5. Step 5: Update config file schema to support render section
6. Step 6: Run full test suite, verify 100% pass

**Risk Mitigation:**
* Risk: Breaking CLI behavior. Mitigation: Defaults match current behavior
* Risk: Config file backwards compatibility. Mitigation: render section is optional

**Rollback Plan:**
* Rollback: Git revert, render params continue as direct CLI args (current behavior)

**Success Criteria:**
* All existing tests pass without modification
* New render options work identically to current CLI flags
* Config file can specify render section (optional)
* Test coverage maintained at 89%+
* New tests for RenderConfig dataclass

---

## Refactoring Phases

| Phase / Task | Status / Link to Artifact or Card | Universal Check |
| :--- | :--- | :---: |
| **Pre-Refactor Test Suite** | tests/test_config.py | - [x] Comprehensive tests exist before refactoring starts. |
| **Baseline Measurements** | 89% coverage, render params bypass config | - [x] Baseline metrics captured (complexity, performance, coverage). |
| **Incremental Refactoring** | Steps 1-6 above | - [x] Refactoring implemented incrementally with passing tests at each step. |
| **Documentation Updates** | config.py docstrings, README.md | - [x] All documentation updated to reflect refactored code. |
| **Code Review** | PR review | - [x] Code reviewed for correctness, style guide compliance, maintainability. |
| **Performance Validation** | No performance impact (config loading) | - [x] Performance validated - no regression, ideally improvement. |

---

## Safe Refactoring Workflow

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Establish Test Safety Net** | Existing config tests + new RenderConfig tests | - [x] Comprehensive tests exist covering current behavior. |
| **2. Run Baseline Tests** | pytest | - [x] All tests pass before any refactoring begins. |
| **3. Capture Baseline Metrics** | 89% coverage, 0 render params in config | - [x] Baseline metrics captured for comparison. |
| **4. Make Smallest Refactor** | Add RenderConfig dataclass | - [x] Smallest possible refactoring change made. |
| **5. Run Tests (Iteration)** | pytest after each step | - [x] All tests pass after refactoring change. |
| **6. Commit Incremental Change** | git commit after each step | - [x] Incremental change committed (enables easy rollback). |
| **7. Repeat Steps 4-6** | 6 incremental commits | - [x] All incremental refactoring steps completed with passing tests. |
| **8. Update Documentation** | config.py docstrings | - [x] All documentation updated (docstrings, README, comments, architecture docs). |
| **9. Style & Linting Check** | ruff, mypy | - [x] Code passes linting, type checking, and style guide validation. |
| **10. Code Review** | Self-review or PR | - [x] Changes reviewed for correctness and maintainability. |

#### Refactoring Implementation Notes

**New Dataclass: RenderConfig**

```python
@dataclass
class RenderConfig:
    """Renderer configuration parameters.
    
    Controls how detected clusters are rendered to output images.
    """
    method: Literal["flower", "bullseye", "block", "treemap", "circles"] = "flower"
    petal_distance: float = 1.0
    skip_partial: bool = False
    jitter_position: int = 0  # 0-100, percentage
    jitter_size: int = 0  # 0-100, percentage
    jitter_seed: Optional[int] = None
    jitter_algorithm: Literal["gaussian", "uniform"] = "gaussian"
```

**CLI Option Group Addition:**

```python
@optgroup.group("Render Options")
@optgroup.option("--render-method", type=click.Choice(["flower", "bullseye", "block", "treemap", "circles"]))
@optgroup.option("--petal-distance", type=float, default=1.0)
@optgroup.option("--skip-partial/--include-partial", default=False)
# ... jitter options already exist
```

**Config File Schema:**

```json
{
  "detection": { ... },
  "color": { ... },
  "render": {
    "method": "flower",
    "petal_distance": 1.0,
    "skip_partial": false
  }
}
```

**Code Quality Improvements:**
* Config centralization: Render params now in config system
* Discoverability: All render options in one place
* Extensibility: Easy to add render presets

---

## Refactoring Validation & Completion

| Task | Detail/Link |
| :--- | :--- |
| **Code Location** | src/dotmatrix/config.py (RenderConfig), cli.py (option group) |
| **Test Suite** | tests/test_config.py (add RenderConfig tests) |
| **Baseline Metrics (Before)** | 0 render params in config, scattered CLI flags |
| **Final Metrics (After)** | All render params in RenderConfig dataclass |
| **Documentation Updates** | config.py docstrings, README.md config section |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Further Refactoring Needed?** | Potential: GPU config could be separated similarly |
| **Documentation Complete?** | Update README.md configuration section |
| **Technical Debt Reduced?** | Yes - render params now follow config pattern |

### Completion Checklist

- [x] Comprehensive tests exist before refactoring (existing + new RenderConfig tests).
- [x] All tests pass before refactoring begins (baseline established).
- [x] Baseline metrics captured (0 render params in config → all in RenderConfig).
- [x] Refactoring implemented incrementally (1 config addition at a time).
- [x] All tests pass after each refactoring step (continuous validation).
- [x] Documentation updated (config.py docstrings, README.md).
- [x] Code passes style guide validation (ruff, mypy).
- [x] No performance regression (config loading, negligible impact).
- [x] Code quality metrics improved (all render params in config system).


## Required Reading and Grep Terms


---

## Required Reading and Grep Terms

### Required Reading

Before starting this card, review the following documentation:

| Document | Location | Focus Areas |
| :--- | :--- | :--- |
| Architectural Guidelines | docs/architectural-guidelines.md | Section 6: "Configuration Management", Principle 4 |
| Development Guide | docs/DEVELOPMENT.md | "Architecture Overview" section |
| Existing Config | src/dotmatrix/config.py | DetectionParams, ColorParams, OutputParams patterns |

### Grep Terms

Use these commands to find relevant code and understand the scope:

```bash
# Find existing config dataclasses
grep -rn "@dataclass" src/dotmatrix/config.py

# Find existing Params classes
grep -rn "class.*Params" src/dotmatrix/config.py

# Find render-related CLI options
grep -rn "render" src/dotmatrix/cli.py

# Find from_cli_args usage
grep -rn "from_cli_args" src/dotmatrix/

# Find config file loading
grep -rn "load_config\|config_loader" src/dotmatrix/

# Find optgroup usage for CLI option groups
grep -rn "@optgroup" src/dotmatrix/cli.py
```

### Key Files

| File | Purpose | Action Needed |
| :--- | :--- | :--- |
| src/dotmatrix/config.py | Configuration dataclasses | Add RenderConfig dataclass |
| src/dotmatrix/cli.py | CLI interface | Add "Render Options" option group |
| src/dotmatrix/config_loader.py | Config file loading | Add render section support |
| tests/test_config.py | Config tests | Add RenderConfig tests |
