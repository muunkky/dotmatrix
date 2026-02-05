# Feature Development Template

**When to use this template:** Use this for any new feature work that requires planning, design, implementation, testing, and documentation. Perfect for features following TDD methodology with clear acceptance criteria and quality gates.

## Feature Overview & Context

* **Associated Ticket/Epic:** Roadmap V2 > M2 > Artistic Rendering > planetary-render
* **Feature Area/Component:** `circle_renderer.py`, `gpu_renderer.py`, `cli.py`
* **Target Release/Milestone:** V2.1.0 - Artistic Rendering

**Required Checks:**
* [x] **Associated Ticket/Epic** link is included above.
* [x] **Feature Area/Component** is identified.
* [x] **Target Release/Milestone** is confirmed.

## Required Reading

Before starting implementation, review these essential documents:

| Document | Location | Purpose |
| :--- | :--- | :--- |
| Flower Renderer Implementation | `src/dotmatrix/circle_renderer.py` | Reference architecture for petal positioning |
| Jitter Implementation | `src/dotmatrix/circle_renderer.py` | Apply jitter to planetary dots |
| CLI Render Methods | `src/dotmatrix/cli.py` | Pattern for adding new render methods |
| GPU Renderer | `src/dotmatrix/gpu_renderer.py` | GPU acceleration patterns |
| ADR-002 Jitter Strategy | `docs/adr/ADR-002-jitter-randomization-strategy.md` | Jitter algorithm details |

## Grep Terms

Use these search terms to find relevant code sections:

| Term | Purpose |
| :--- | :--- |
| `render_flower_svg` | Main SVG flower renderer (base for planetary) |
| `render_flower_global_blend` | PNG flower renderer with blending |
| `render_flower_cluster` | Per-cluster flower rendering |
| `PETAL_ANGLES` | CMY petal angle constants |
| `petal_distance` | Petal positioning parameter |
| `--render-method` | CLI option for render methods |
| `radius_from_pixels` | Circle sizing from pixel counts |
| `apply_position_jitter` | Position jitter helper |
| `apply_size_jitter` | Size jitter helper |

## Documentation & Prior Art Review

First, confirm the minimum required documentation has been reviewed for context.

- [x] `README.md` or project documentation reviewed.
- [x] Existing architecture documentation or ADRs reviewed.
- [x] Related feature implementations or similar code reviewed.
- [x] API documentation or interface specs reviewed (if applicable).

| Document Type | Link / Location | Key Findings / Action Required |
| :--- | :--- | :--- |
| **README.md** | [README.md](README.md) | Render methods documented in "Flower Options" section |
| **Architecture Docs** | `circle_renderer.py` | Flower renderer uses PETAL_ANGLES at 120° spacing with petal_distance for positioning |
| **Similar Features** | `render_flower_svg()`, `render_flower_cluster()` | Petals positioned at distance from center, overlap with black |
| **API Specs** | CLI `--render-method` | Currently supports: bullseye, block, treemap, exact, flower, cmyk-blend |
| **ADR (New)** | N/A | May need ADR for planetary positioning algorithm if complex |

## Design & Planning

### Initial Design Thoughts & Requirements

> **Key Difference from Flower:** In flower mode, CMY petals overlap with and hide behind the black center. In planetary mode, CMY dots sit fully visible ON the surface of the black circle like moons orbiting a planet.

**Geometric Approach:**
* CMY dots positioned at distance = `black_radius + cmy_radius` from center
* This ensures dots are tangent to the black circle surface (touching but not overlapping)
* Same 120° angular spacing as flower (cyan=0°, magenta=120°, yellow=240°)
* Rotation modes (fixed, random, cluster-hash) apply identically to flower

**Visual Effect:**
* More "atomic" or "molecular" appearance
* Better color separation - CMY dots don't get occluded by black
* Larger total footprint per cluster than flower mode

**Implementation Strategy:**
* Create `render_planetary_svg()` and `render_planetary()` functions
* Copy flower implementation as starting point
* Modify petal positioning to use `black_radius + petal_radius` distance
* No exposed-area compensation needed (dots are fully visible)
* Reuse all jitter, rotation, and drift infrastructure

### Acceptance Criteria

Define clear, testable acceptance criteria for this feature:

- [x] `--render-method planetary` CLI option added and documented
- [x] CMY dots positioned tangent to black circle (distance = black_r + cmy_r)
- [x] 120° angular spacing maintained (same as flower)
- [x] All rotation modes work (fixed, random, cluster-hash)
- [x] All jitter options work (position, size, seed, algorithm, exclude)
- [x] Drift-balanced jitter works with planetary render
- [x] Multi-step jitter (`--jitter-steps`) works with planetary
- [x] SVG output format supported
- [x] PNG output format supported with `--blend-overlaps`
* [ ] GPU acceleration supported for PNG output
- [x] README documentation updated with planetary examples
* [ ] Unit tests cover planetary-specific positioning logic
* [ ] Visual comparison test confirms dots don't overlap black center

## Feature Work Phases

| Phase / Task | Status / Link to Artifact or Card | Universal Check |
| :--- | :--- | :---: |
| **Design & Architecture** | See "Design & Planning" section above | - [x] Design Complete |
| **Test Plan Creation** | TDD: Write failing tests first for planetary positioning | - [ ] Test Plan Approved |
| **TDD Implementation** | `render_planetary_svg()`, `render_planetary()`, CLI option | - [x] Implementation Complete |
| **Integration Testing** | Test with real cluster data and jitter options | - [ ] Integration Tests Pass |
| **Documentation** | README.md, inline docstrings | - [x] Documentation Complete |
| **Code Review** | PR with tests passing | - [ ] Code Review Approved |
| **Deployment Plan** | Release with next version | - [ ] Deployment Plan Ready |

## TDD Implementation Workflow

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Write Failing Tests** | `tests/test_planetary_renderer.py` - test dot positioning, jitter, rotation | - [x] Failing tests are committed and documented |
| **2. Implement Feature Code** | `circle_renderer.py`, `gpu_renderer.py`, `cli.py` | - [x] Feature implementation is complete |
| **3. Run Passing Tests** | All planetary tests pass | - [ ] Originally failing tests now pass |
| **4. Refactor** | Extract common code between flower and planetary if beneficial | - [ ] Code is refactored for clarity and maintainability |
| **5. Full Regression Suite** | Run full test suite, ensure flower renderer still works | - [ ] All tests pass (unit, integration, e2e) |
| **6. Performance Testing** | Compare planetary vs flower performance with 15K+ clusters | - [ ] Performance requirements are met |

### Implementation Notes

**Positioning Algorithm:**
```python
# Flower positioning (dots overlap black):
petal_distance = black_radius * petal_distance_fraction  # e.g., 0.35
petal_x = cx + petal_distance * cos(angle)
petal_y = cy + petal_distance * sin(angle)

# Planetary positioning (dots tangent to black surface):
orbital_distance = black_radius + petal_radius  # Tangent point
petal_x = cx + orbital_distance * cos(angle)
petal_y = cy + orbital_distance * sin(angle)
```

**Test Strategy:**
- Unit test: Verify planetary dot centers are exactly `black_r + cmy_r` from cluster center
- Unit test: Verify no overlap between CMY dots and black circle
- Integration test: Generate SVG and verify circle positions in output
- Visual test: Compare flower vs planetary with same input

**Key Files to Modify:**
1. `src/dotmatrix/circle_renderer.py` - Add `render_planetary_svg()`, `render_planetary()`
2. `src/dotmatrix/gpu_renderer.py` - Add `render_planetary_gpu()` if GPU acceleration needed
3. `src/dotmatrix/cli.py` - Add 'planetary' to `--render-method` choices
4. `tests/test_planetary_renderer.py` - New test file
5. `README.md` - Document planetary render method

## Validation & Closeout

| Task | Detail/Link |
| :--- | :--- |
| **Code Review** | PR with tests |
| **QA Verification** | Visual inspection of planetary vs flower output |
| **Staging Deployment** | N/A (CLI tool) |
| **Production Deployment** | Release with next version |
| **Monitoring Setup** | N/A (CLI tool) |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Postmortem Required?** | TBD |
| **Further Investigation?** | Consider "orbital" mode where dots can orbit at different distances |
| **Technical Debt Created?** | Consider extracting common flower/planetary positioning code |
| **Future Enhancements** | Variable orbital distances, multiple rings, animation export |

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
