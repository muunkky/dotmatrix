# Feature Development Template

**When to use this template:** Use this for any new feature work that requires planning, design, implementation, testing, and documentation. Perfect for features following TDD methodology with clear acceptance criteria and quality gates.

**When NOT to use this template:** Do not use for bug fixes (use bug template), refactoring work (use refactor template), or research/exploration (use spike template). For simple chores or maintenance, use the chore template.

## Feature Overview & Context

* **Associated Ticket/Epic:** Depends on spike `feshwj` (Research Target-Guided Dot Optimization Algorithm) - **COMPLETED**
* **Feature Area/Component:** circle_renderer.py, target_guided.py, cli.py
* **Target Release/Milestone:** V2 - Jitter Enhancement

**Required Checks:**
* [x] **Associated Ticket/Epic** link is included above.
* [x] **Feature Area/Component** is identified.
* [x] **Target Release/Milestone** is confirmed.

## Documentation & Prior Art Review

First, confirm the minimum required documentation has been reviewed for context.

- [x] `README.md` or project documentation reviewed.
* [ ] Existing architecture documentation or ADRs reviewed.
- [x] Related feature implementations or similar code reviewed.
* [ ] API documentation or interface specs reviewed (if applicable).

| Document Type | Link / Location | Key Findings / Action Required |
| :--- | :--- | :--- |
| **README.md** | README.md | Jitter section documents position/size/seed/algorithm flags |
| **Architecture Docs** | docs/architecture/flower-renderer.md | Flower rendering pipeline with jitter/drift integration |
| **Similar Features** | circle_renderer.py:_apply_drift_to_svg_circles | Drift balancing adjusts dots iteratively - similar pattern |
| **Similar Features** | jitter.py | Position/size jitter with Gaussian/uniform algorithms |
| **API Specs** | cli.py | Existing flags: --jitter-position, --jitter-size, --drift, --jitter-steps |
| **ADR (New)** | **N/A** (Action Item) | May need ADR for target-guided optimization approach |

## Design & Planning

### Initial Design Thoughts & Requirements

> Use this space for initial design ideas, key requirements, constraints, and architectural considerations.

* **Requirement:** New CLI flag `--target-image PATH` to specify PNG reference image
* **Requirement:** New flag `--target-weight FLOAT` (0.0-1.0) to balance target-matching vs color preservation
* **Requirement:** Support both flower and planetary render methods
* **Constraint:** One dot per color per cluster (topology fixed, only position/size can change)
* **Constraint:** Target is raster PNG - must handle detection or rasterized cost function
* **Design thought:** Extend existing drift infrastructure with target-guided gradient
* **Design thought:** Cost function: `total_cost = position_error + size_error + color_mass_deviation * λ`
* **Dependency:** Spike card `feshwj` ✅ COMPLETED - Algorithm validated, PoC in `src/dotmatrix/target_guided.py`

### Spike Findings (from feshwj)

**Algorithm Selected:** Per-Cluster Local Gradient with K-D tree nearest-neighbor
- Uses `scipy.spatial.KDTree` for O(log n) lookup
- Integrates with existing drift infrastructure
- Three-component cost: position_error + radius_error + mass_deviation

**PoC Code:** `src/dotmatrix/target_guided.py` contains:
- `TargetCircleIndex` for spatial lookup
- `parse_target_image()` for CMYK circle detection
- `apply_target_guided_optimization()` main optimization loop

### Acceptance Criteria

Define clear, testable acceptance criteria for this feature:

- [x] `--target-image PATH` flag added to CLI for flower/planetary render methods
- [x] `--target-weight FLOAT` flag added (default 0.5, range 0.0-1.0)
- [x] Target PNG is parsed to extract reference dot positions/sizes
- [x] Optimization algorithm moves dots toward target arrangement
- [x] CMYK color mass is preserved within drift_tolerance
- [x] Works with SVG output format
- [x] Works with PNG output format
- [x] Reproducible with `--jitter-seed`
- [x] GPU acceleration supported when available
- [x] Progress logging shows target match score improving
- [x] Works with `--jitter-steps` for multi-pass optimization
- [x] Unit tests cover target parsing, optimization, and edge cases
- [x] Integration tests verify end-to-end target matching
- [x] README updated with target-guided examples
* [ ] Performance: <2x overhead compared to standard drift

## Feature Work Phases

| Phase / Task | Status / Link to Artifact or Card | Universal Check |
| :--- | :--- | :---: |
| **Design & Architecture** | Depends on spike feshwj findings | - [ ] Design Complete |
| **Test Plan Creation** | TDD - write tests first | - [ ] Test Plan Approved |
| **TDD Implementation** | Pending design | - [x] Implementation Complete |
| **Integration Testing** | Pending implementation | - [ ] Integration Tests Pass |
| **Documentation** | Pending implementation | - [x] Documentation Complete |
| **Code Review** | Pending PR | - [ ] Code Review Approved |
| **Deployment Plan** | PyPI release | - [ ] Deployment Plan Ready |

## TDD Implementation Workflow

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Write Failing Tests** | tests/test_target_guided.py | - [ ] Failing tests are committed and documented |
| **2. Implement Feature Code** | target_guided.py, circle_renderer.py, cli.py | - [x] Feature implementation is complete |
| **3. Run Passing Tests** | pytest tests/test_target_guided.py | - [ ] Originally failing tests now pass |
| **4. Refactor** | Clean up and optimize | - [ ] Code is refactored for clarity and maintainability |
| **5. Full Regression Suite** | pytest (all tests) | - [ ] All tests pass (unit, integration, e2e) |
| **6. Performance Testing** | Benchmark vs standard drift | - [ ] Performance requirements are met |

### Implementation Notes

> Document key implementation decisions, test approach, and code examples here.

**Test Strategy:**
- Unit tests for target image parsing/circle detection
- Unit tests for cost function calculation
- Unit tests for optimization step (gradient toward target)
- Integration tests for CLI flag handling
- End-to-end tests comparing output to target image

**Key Implementation Decisions:**
(To be determined after spike completion)

**Proposed CLI Interface:**
```bash
# Basic target-guided optimization
dotmatrix -m halftone --reconstitute --render-method flower \
  --target-image reference.png

# With weight tuning (higher = stronger target matching, lower = more color accuracy)
dotmatrix -m halftone --reconstitute --render-method flower \
  --target-image reference.png --target-weight 0.8

# Multi-pass optimization
dotmatrix -m halftone --reconstitute --render-method flower \
  --target-image reference.png --jitter-steps 5 --drift

# Reproducible with seed
dotmatrix -m halftone --reconstitute --render-method flower \
  --target-image reference.png --jitter-seed 42
```

**Proposed Algorithm (pending spike findings):**
```python
def apply_target_guided_optimization(
    circles_by_color: Dict[str, List[Tuple[float, float, float]]],
    target_image: np.ndarray,
    target_weight: float = 0.5,
    max_iterations: int = 10,
    drift_tolerance: float = 0.2,
) -> Dict[str, List[Tuple[float, float, float]]]:
    """Optimize dot positions/sizes to match target image.
    
    Algorithm:
    1. Detect/sample target dot positions from target_image
    2. For each source dot, compute gradient toward nearest target dot
    3. Apply constrained update (maintain CMYK balance)
    4. Repeat until convergence or max_iterations
    """
    # Implementation based on spike findings
    pass
```

## Validation & Closeout

| Task | Detail/Link |
| :--- | :--- |
| **Code Review** | Pending PR |
| **QA Verification** | Manual testing with sample images |
| **Staging Deployment** | N/A (CLI tool) |
| **Production Deployment** | PyPI release |
| **Monitoring Setup** | N/A (CLI tool) |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Postmortem Required?** | Pending completion |
| **Further Investigation?** | Pending completion |
| **Technical Debt Created?** | Pending completion |
| **Future Enhancements** | Potential: interactive mode, multiple target images, style transfer |

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


## Required Reading and Grep Terms

Before implementing this feature, review these key files and search for these terms to understand the existing infrastructure.

### Key Files to Review

| File | Purpose | Priority |
| :--- | :--- | :--- |
| `src/dotmatrix/circle_renderer.py` | Main rendering logic, drift implementation, jitter application | **HIGH** |
| `src/dotmatrix/cli.py` | CLI flag definitions, argument parsing | **HIGH** |
| `src/dotmatrix/jitter.py` | Jitter algorithms - pattern for new optimization | **HIGH** |
| `src/dotmatrix/gpu_renderer.py` | GPU-accelerated drift - extend for target optimization | **MEDIUM** |
| `src/dotmatrix/circle_detector.py` | HoughCircles detection - reuse for target parsing | **HIGH** |
| `src/dotmatrix/config.py` | Configuration dataclass patterns | **MEDIUM** |
| `docs/architecture/rendering-architecture.md` | Drift/jitter architecture docs | **MEDIUM** |

### Grep Search Terms

```bash
# CLI flag patterns (follow these for --target-image)
grep -rn "add_argument.*jitter" src/dotmatrix/cli.py
grep -rn "add_argument.*drift" src/dotmatrix/cli.py

# Drift infrastructure to extend
grep -rn "_apply_drift" src/
grep -rn "drift_tolerance" src/
grep -rn "drift_steps\|jitter_steps" src/

# Circle detection for target parsing
grep -rn "HoughCircles" src/
grep -rn "detect_circles" src/

# Cost function patterns
grep -rn "calculate_mass\|expected_mass" src/
grep -rn "adjustment\|delta" src/dotmatrix/gpu_renderer.py

# Configuration patterns
grep -rn "@dataclass" src/dotmatrix/config.py
grep -rn "JitterConfig\|DriftConfig" src/

# Integration points
grep -rn "render_planetary_svg\|render_flower_svg" src/dotmatrix/cli.py
```

### Key Functions to Extend/Modify

- `cli.py`: Add `--target-image` and `--target-weight` arguments
- `config.py`: Add `TargetOptimizationConfig` dataclass
- `circle_detector.py`: Reuse `detect_circles()` for target parsing
- `circle_renderer.py`: Add `_apply_target_guided_optimization()` function
- `gpu_renderer.py`: Add `apply_target_guided_gpu()` for GPU acceleration

### Implementation Pattern Reference

Follow the existing jitter/drift pattern:
1. CLI parses flags → config object
2. Config passed to render function
3. Optimization applied in render loop
4. GPU acceleration optional via `--use-gpu`
