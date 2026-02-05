## Feature Overview & Context
* **Associated Ticket/Epic:** V2IDEAS Sprint - Advanced Artistic Rendering
* **Feature Area/Component:** Rendering Pipeline - Jitter/Drift System
* **Target Release/Milestone:** V2: Advanced Artistic Rendering

Required Checks:
* [ ] **Associated Ticket/Epic** link is included above.
* [ ] **Feature Area/Component** is identified.
* [ ] **Target Release/Milestone** is confirmed.

## Documentation & Prior Art Review
* [ ] `README.md` or project documentation reviewed.
* [ ] Existing architecture documentation or ADRs reviewed.
* [ ] Related feature implementations or similar code reviewed.
* [ ] API documentation or interface specs reviewed (if applicable).

| Document Type | Link / Location | Key Findings / Action Required |
| :--- | :--- | :--- |
| **README.md** | `/README.md` | Current jitter research in progress |
| **Architecture Docs** | `/docs/research/Typographic Halftoning Engine/design.md` | Contains "Scatter Swarm" and "Eclipse" algorithms with jitter concepts |
| **Similar Features** | Card `0aojwh` (prototype-jitter-rendering-mode) | Basic jitter implementation planned, drift extends this |
| **API Specs** | CLI arguments | Will need --drift and --drift-tolerance parameters |
| **ADR (New)** | Card `bh0tpw` (adr-jitter-randomization-approach) | Existing ADR covers jitter, may need drift addendum |

## Design & Planning

### Initial Design Thoughts & Requirements

**Core Concept:** "Drift" is cluster-aware balanced randomization where each dot's movement is constrained by maintaining the overall color balance of its cluster. Unlike basic jitter (purely random displacement), drift incorporates feedback loops to prevent color distribution violations.

**Key Requirements:**
* Must extend existing jitter system with cluster-aware constraints
* Each iteration recalculates displacement parameters to maintain color balance
* Tolerance threshold defines acceptable deviation from target color distribution
* If a cluster element extends too far (e.g., petal protrudes), it compensates by shrinking
* System must track per-cluster color mass to validate balance
* Should work iteratively: apply displacement → measure deviation → adjust parameters → repeat

**Design Thoughts:**
* Build on top of jitter research findings (from spike card kja0uf)
* Use cluster metadata from color_clustering module
* Implement feedback control system: target_mass vs actual_mass
* Tolerance parameter controls strictness (loose/normal/strict like existing config)
* May need iterative solver (gradient descent or simulated annealing)

**Constraints:**
* Must maintain backward compatibility with basic jitter mode
* Performance: iterative balancing adds computational cost
* Visual coherence: drift should enhance, not destroy, artistic intent
* Collision detection: balanced drift must still respect minimum dot distances

**Known Unknowns:**
* Optimal convergence criteria for balance iteration
* Performance impact of per-cluster mass calculations
* Best tolerance threshold ranges for different image types
* Whether to apply drift per-frame or across animation sequences

**Dependencies:**
* Jitter system implementation (card 0aojwh)
* Cluster detection and metadata (existing color_clustering.py)
* Color mass calculation utilities
* Configuration system for tolerance parameters

### Acceptance Criteria
* [ ] Drift mode available via CLI flag (--drift, --drift-tolerance)
* [ ] Each cluster maintains color balance within tolerance threshold
* [ ] Compensatory adjustments work (extension → shrink, shrink → extend)
* [ ] Tolerance parameter configurable (values 0.0-1.0, default 0.2)
* [ ] Per-cluster mass tracking implemented and validated
* [ ] Iterative convergence completes within reasonable time (<5 iterations typical)
* [ ] Visual output shows balanced organic movement without color bleeding
* [ ] Works with all existing rendering modes (circles, blocks, clusters)
* [ ] Performance degradation <30% compared to basic jitter mode
* [ ] Deterministic output with fixed random seed

## Feature Work Phases

| Phase / Task | Status / Link to Artifact or Card | Universal Check |
| :--- | :--- | :---: |
| **Design & Architecture** | Spike: Design drift balance algorithm and convergence strategy | - [ ] Design Complete |
| **Test Plan Creation** | Document test scenarios for cluster balance validation | - [ ] Test Plan Approved |
| **TDD Implementation** | Implement DriftRenderer with balance feedback loop | - [ ] Implementation Complete |
| **Integration Testing** | Test drift with various image types and cluster densities | - [ ] Integration Tests Pass |
| **Documentation** | Update README, add drift usage examples, document tolerance tuning | - [ ] Documentation Complete |
| **Code Review** | PR review with focus on algorithm correctness and performance | - [ ] Code Review Approved |
| **Deployment Plan** | Merge to V2 feature branch | - [ ] Deployment Plan Ready |

## TDD Implementation Workflow

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Write Failing Tests** | Tests for cluster mass calculation, balance validation, compensatory adjustments | - [ ] Failing tests are committed and documented |
| **2. Implement Feature Code** | DriftRenderer class, cluster balance tracker, iterative solver | - [ ] Feature implementation is complete |
| **3. Run Passing Tests** | All drift balance tests pass | - [ ] Originally failing tests now pass |
| **4. Refactor** | Optimize convergence algorithm, extract reusable components | - [ ] Code is refactored for clarity and maintainability |
| **5. Full Regression Suite** | All rendering modes tested with drift enabled/disabled | - [ ] All tests pass (unit, integration, e2e) |
| **6. Performance Testing** | Benchmark drift vs jitter, validate <30% overhead target | - [ ] Performance requirements are met |

### Implementation Notes

**Test Strategy:**
* Unit tests: cluster mass calculation accuracy
* Unit tests: convergence algorithm with known inputs
* Unit tests: tolerance threshold boundary conditions
* Integration tests: full pipeline with various cluster densities
* Visual regression: compare drift output with expected balanced distributions
* Performance: benchmark suite comparing jitter vs drift modes

**Key Implementation Decisions:**
* Extend JitterRenderer (when implemented) or create DriftRenderer subclass
* Use iterative approach with max_iterations safety limit (default 10)
* Store cluster metadata (center, original_mass, current_mass) in data structure
* Calculate mass via pixel counting or analytical geometry (TBD during spike)
* Tolerance as fractional deviation: |current_mass - target_mass| / target_mass < tolerance

**Algorithmic Pseudocode:**
```python
class DriftRenderer:
    def apply_drift(self, dots, clusters, tolerance=0.2, max_iterations=10):
        for iteration in range(max_iterations):
            # Apply random displacement (jitter)
            displaced_dots = apply_jitter(dots)
            
            # Calculate current cluster masses
            current_masses = calculate_cluster_masses(displaced_dots, clusters)
            
            # Check balance
            deviations = [(current - target) / target 
                         for current, target in zip(current_masses, target_masses)]
            
            if all(abs(dev) < tolerance for dev in deviations):
                return displaced_dots  # Balanced!
            
            # Apply compensatory adjustments
            for cluster_id, deviation in enumerate(deviations):
                if deviation > tolerance:  # Too much mass, shrink
                    shrink_cluster_dots(displaced_dots, cluster_id, deviation)
                elif deviation < -tolerance:  # Too little mass, extend
                    extend_cluster_dots(displaced_dots, cluster_id, -deviation)
        
        # Fallback: return best attempt if convergence fails
        return displaced_dots
```

## Validation & Closeout

| Task | Detail/Link |
| :--- | :--- |
| **Code Review** | PR with detailed algorithm explanation and test coverage report |
| **QA Verification** | Visual inspection of drift output with various images and tolerances |
| **Staging Deployment** | Deploy to feature branch for team testing |
| **Production Deployment** | Merge to main when V2 release ready |
| **Monitoring Setup** | N/A (CLI tool, no runtime monitoring) |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Postmortem Required?** | TBD after implementation |
| **Further Investigation?** | May need animation/temporal drift for video sequences |
| **Technical Debt Created?** | Document: iterative solver may need optimization for large images |
| **Future Enhancements** | Consider ML-based balance prediction to reduce iterations |

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

## Implementation Notes

## Implementation Progress - Drift v1

### Implementation Started: 2026-01-06

**Architecture Decision:**
- Iterate-and-correct approach (simpler than prediction)
- Size-based compensation (adjust radii to maintain balance)
- GPU-first implementation (extends gpu_renderer.py)
- Per-petal per-cluster mass tracking

**Implementation Details:**

1. **CLI Integration:**
   - Added `--drift` flag (boolean, enables drift mode)
   - Added `--drift-tolerance` parameter (float, default 0.2)
   - Flags require jitter to be enabled (drift builds on jitter)

2. **GPU Renderer Extension:**
   - Added drift parameters to `render_flower_global_blend_gpu()` signature
   - New Phase 1d: Drift-balanced jitter (runs after Phase 1c radius optimization)
   - Implemented `_apply_drift_compensation()` helper function
   - Implemented `_measure_cluster_local_mass()` for cluster-local rendering (option B)

3. **Algorithm Flow:**
   ```
   Phase 1d (if drift enabled):
   1. Apply jitter to positions (existing logic)
   2. Apply jitter to sizes (existing logic)
   3. FOR each iteration (max 10):
      a. FOR each cluster:
         - FOR each petal (C/M/Y):
           * Measure actual pixel mass (cluster-local render)
           * Calculate deviation from target
           * If |deviation| > tolerance:
             - Adjust size: scale_factor = sqrt(target/actual)
             - Update circle radius
      b. If all balanced, break
   4. Return adjusted circles
   ```

4. **Mass Measurement (Option B - Cluster-Local):**
   - Render petal + black circle in isolation
   - Count exposed pixels (petal - black overlap)
   - Does not account for inter-cluster overlaps
   - Fast and simple, suitable for v1

**Code Changes:**
- `src/dotmatrix/cli.py`: Added drift flags, wired through call chain
- `src/dotmatrix/gpu_renderer.py`: Added drift logic + 2 helper functions

**Testing Status:**
- Syntax validation: PASS (no syntax errors)
- Import validation: PASS (module loads successfully)
- Functional testing: NOT YET STARTED
- Integration testing: NOT YET STARTED

**Next Steps:**
1. Test with real image + jitter + drift flags
2. Validate convergence behavior
3. Measure performance overhead
4. Add CPU version (render_flower_global_blend)
5. Write unit tests for drift logic
6. Document results in ADR

## Implementation Notes

### SVG Drift Implementation Added (2026-01-06)

**Corrected Architecture:**
User clarification: SVG is the production path, not PNG. Moved drift implementation priority to SVG renderer.

**New Implementation:**
- Added drift support to `render_flower_svg()` (primary rendering path)
- New helper: `_apply_drift_to_svg_circles()` - applies drift to collected circles before SVG generation
- New helper: `_measure_svg_circle_mass()` - cluster-local mass measurement for SVG
- Wired drift parameters through both CLI call sites

**SVG-Specific Considerations:**
- SVG generation collects all circles first, then generates markup
- Added cluster tracking: `cluster_metadata` and `cluster_circle_map` lists
- Drift runs after circle collection, before SVG generation
- Same algorithm as GPU version: iterate-and-correct with cluster-local rendering

**Code Changes:**
- `src/dotmatrix/circle_renderer.py`: Added drift to `render_flower_svg()` + 2 helpers
- `src/dotmatrix/cli.py`: Wired drift params to both `render_flower_svg()` calls

**Testing:**
- Syntax validation: PASS
- Ready to test with: `--jitter-position 50 --jitter-size 50 --drift --output-format svg`

## Bug Fixes

### CRITICAL BUG FIX (2026-01-06)

**Bug Report from User Testing:**
- Tested on corner_test image
- Black dots jittered correctly (small movement)
- Petal dots went "bananas" - some grew to 1/3 of entire image
- GPU rendering much slower than expected

**Root Cause Analysis:**
1. **Runaway scaling bug:** When `actual_pixels ≈ 0` (petal mostly covered by black):
   - `scale_factor = sqrt(target / 0)` → infinity
   - Causes massive circle growth in single iteration
   - No bounds checking on scale_factor

2. **Performance issue:** Drift uses CPU numpy/cv2 for mass measurement, not GPU
   - Each measurement creates numpy arrays and calls cv2.circle
   - Happens per-petal per-iteration (potentially 15K clusters × 3 petals × 10 iterations)
   - GPU flag passed but not utilized

**Fixes Applied:**
1. Added `actual_pixels < 5` threshold - skip unreliable measurements
2. Clamped `scale_factor` to [0.5, 2.0] - max 2x growth or 0.5x shrinkage per iteration
3. Prevents exponential growth from near-zero measurements

**Code Changes:**
- `circle_renderer.py`: Added bounds to `_apply_drift_to_svg_circles()`
- `gpu_renderer.py`: Added bounds to `_apply_drift_compensation()`

**Testing Status:**
- Unit tests: NONE EXIST (as user suspected)
- Integration test: FAILED on corner_test
- Performance: SLOW (CPU-bound, not using GPU)

**Remaining Issues:**
- GPU not utilized for mass measurement (performance bottleneck)
- No unit tests for drift algorithm
- Need validation on diverse test images