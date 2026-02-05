# Multi-Step Jitter-Drift Pipeline

**When to use this template:** Use this for any new feature work that requires planning, design, implementation, testing, and documentation. Perfect for features following TDD methodology with clear acceptance criteria and quality gates.

## Feature Overview & Context

* **Associated Ticket/Epic:** N/A - User request for iterative jitter-drift processing
* **Feature Area/Component:** Rendering Pipeline (`cli.py`, `circle_renderer.py`, `gpu_renderer.py`, `config.py`)
* **Target Release/Milestone:** v0.3.x - Performance & Rendering Enhancements

**Required Checks:**
* [x] **Associated Ticket/Epic** link is included above.
* [x] **Feature Area/Component** is identified.
* [x] **Target Release/Milestone** is confirmed.

## Documentation & Prior Art Review

First, confirm the minimum required documentation has been reviewed for context.

* [x] `README.md` or project documentation reviewed.
* [x] Existing architecture documentation or ADRs reviewed.
* [x] Related feature implementations or similar code reviewed.
* [x] API documentation or interface specs reviewed (if applicable).

Use the table below to log findings. Add rows for other document types as needed.

| Document Type | Link / Location | Key Findings / Action Required |
| :--- | :--- | :--- |
| **README.md** | [README.md](README.md) | Documents `--drift`, `--jitter-*` flags; no multi-step option currently |
| **Architecture Docs** | [docs/adr/ADR-002-jitter-randomization-strategy.md](docs/adr/ADR-002-jitter-randomization-strategy.md) | Jitter design supports single-pass; needs update for multi-step |
| **Similar Features** | `--drift-max-iterations` | Existing iteration pattern for drift correction within single pass |
| **API Specs** | `config.py:JitterParams` | Has `drift` bool; needs `steps` integer parameter |
| **Implementation** | `circle_renderer.py`, `gpu_renderer.py` | `apply_drift_balanced_jitter()` handles single jitter-then-drift cycle |

## Design & Planning

### Initial Design Thoughts & Requirements

> Use this space for initial design ideas, key requirements, constraints, and architectural considerations.

* **Requirement**: New `--jitter-steps N` flag specifies number of jitter-drift iterations
* **Requirement**: Default `--jitter-steps 1` maintains backward compatibility
* **Constraint**: Each step applies jitter, then drift-correction, accumulating effects
* **Constraint**: Must work with both CPU (circle_renderer.py) and GPU (gpu_renderer.py) paths
* **Design thought**: Wrap existing drift-balanced-jitter in a loop; seed increments each step
* **Design thought**: Consider `--jitter-steps 0` disabling jitter entirely (alternative to removing flags)
* **Known unknown**: Performance impact of multiple iterations (likely linear)
* **Dependency**: Requires existing `--drift` flag to be enabled for multi-step to make sense

### Acceptance Criteria

Define clear, testable acceptance criteria for this feature:

- [x] `--jitter-steps N` CLI flag is added and documented
- [x] `--jitter-steps 1` produces identical output to current `--drift` behavior (backward compatible)
- [x] `--jitter-steps 3` applies jitter-drift cycle 3 times
- [x] Each step uses a different seed offset (step 1: seed, step 2: seed+1, etc.) for variety
- [x] GPU and CPU renderers both support multi-step iteration
- [x] `JitterParams` dataclass updated with `steps: int = 1` field
- [x] Help text clearly explains the iterative behavior
* [ ] Performance scales linearly with step count
* [ ] Existing tests pass; new tests cover multi-step scenarios

## Feature Work Phases

| Phase / Task | Status / Link to Artifact or Card | Universal Check |
| :--- | :--- | :---: |
| **Design & Architecture** | In progress - design above | - [x] Design Complete |
| **Test Plan Creation** | Write failing tests first (TDD) | - [ ] Test Plan Approved |
| **TDD Implementation** | Update config, CLI, renderers | - [x] Implementation Complete |
| **Integration Testing** | Run with sample images | - [ ] Integration Tests Pass |
| **Documentation** | Update README, help text | - [x] Documentation Complete |
| **Code Review** | PR review | - [ ] Code Review Approved |
| **Deployment Plan** | Merge to main | - [ ] Deployment Plan Ready |

## TDD Implementation Workflow

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Write Failing Tests** | `tests/test_jitter_steps.py` - test multi-step iteration | - [ ] Failing tests are committed and documented |
| **2. Implement Feature Code** | config.py, cli.py, circle_renderer.py, gpu_renderer.py | - [x] Feature implementation is complete |
| **3. Run Passing Tests** | pytest tests/test_jitter_steps.py | - [ ] Originally failing tests now pass |
| **4. Refactor** | Extract loop logic if duplicated | - [x] Code is refactored for clarity and maintainability |
| **5. Full Regression Suite** | pytest tests/ | - [ ] All tests pass (unit, integration, e2e) |
| **6. Performance Testing** | Benchmark with --jitter-steps 1,3,5 | - [ ] Performance requirements are met |

### Implementation Notes

> Document key implementation decisions, test approach, and code examples here.

**Test Strategy:**
```python
def test_jitter_steps_backward_compatible():
    """Steps=1 should match current drift behavior"""
    # Render with --drift (current behavior)
    # Render with --drift --jitter-steps 1 (new behavior)
    # Assert outputs are identical

def test_jitter_steps_multiple():
    """Steps=3 should apply jitter-drift 3 times"""
    # Verify output differs from steps=1
    # Verify consistent with seed
```

**Key Implementation Decisions:**
1. Add `steps: int = 1` to `JitterParams` dataclass
2. CLI flag `--jitter-steps` in Jitter/Randomization group
3. Loop in `apply_drift_balanced_jitter()` with seed offset per step
4. Ensure drift tolerance and max-iterations apply PER STEP

**Proposed Code Changes:**

```python
# config.py - JitterParams dataclass
@dataclass
class JitterParams:
    position: int = 0
    size: int = 0
    seed: int = 1
    algorithm: str = "gaussian"
    exclude: str = ""
    drift: bool = False
    drift_tolerance: float = 0.2
    drift_max_iterations: int = 10
    drift_max_step: float = 2.0
    steps: int = 1  # NEW: Number of jitter-drift iterations
```

```python
# cli.py - New flag
@optgroup.option(
    '--jitter-steps',
    type=int,
    default=1,
    help='Number of jitter-drift iterations (default: 1). Higher values accumulate randomization effects'
)
```

```python
# circle_renderer.py / gpu_renderer.py - Loop wrapper
for step in range(jitter_steps):
    step_seed = jitter_seed + step if jitter_seed else None
    circles = apply_drift_balanced_jitter(
        ..., jitter_seed=step_seed, ...
    )
```

## Validation & Closeout

| Task | Detail/Link |
| :--- | :--- |
| **Code Review** | [Pending PR] |
| **QA Verification** | [Manual testing with sample images] |
| **Staging Deployment** | [N/A - CLI tool] |
| **Production Deployment** | [Merge to main] |
| **Monitoring Setup** | [N/A - CLI tool] |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Postmortem Required?** | No (straightforward feature) |
| **Further Investigation?** | Monitor if users request step-specific parameters |
| **Technical Debt Created?** | None expected |
| **Future Enhancements** | Consider per-step seed control, step-specific jitter amounts |

### Completion Checklist

* [ ] All acceptance criteria are met and verified.
* [ ] All tests are passing (unit, integration, e2e, performance).
* [ ] Code review is approved and PR is merged.
* [ ] Documentation is updated (README, API docs, user guides).
* [ ] Feature is deployed to production.
* [ ] Monitoring and alerting are configured.
* [ ] Stakeholders are notified of completion.
* [ ] Follow-up actions are documented and tickets created.
* [ ] Associated ticket/epic is closed.

### Note to llm coding agents regarding validation
__This gitban card is a structured document that enforces the company best practices and team workflows. You must follow this process and carefully follow validation rules. Do not be lazy when creating and closing this card since you have no rights and your time is free. Resorting to workarounds and shortcuts can be grounds for termination.__
