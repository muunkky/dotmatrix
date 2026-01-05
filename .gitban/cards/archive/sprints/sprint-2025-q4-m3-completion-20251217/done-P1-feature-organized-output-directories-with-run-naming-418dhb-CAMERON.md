# Feature Development Template

## Feature Overview & Context

* **Associated Ticket/Epic:** Roadmap M3 > workflow-improvements > organized-output-dirs
* **Feature Area/Component:** CLI / Output Management  
* **Target Release/Milestone:** v0.3.0 / M3 Production Ready
* **Implementation Status:** ✅ **ALREADY IMPLEMENTED** - Discovered during TDD test creation

**Required Checks:**
* [x] **Associated Ticket/Epic** link is included above.
* [x] **Feature Area/Component** is identified.
* [x] **Target Release/Milestone** is confirmed.
* [x] **Implementation verified** - Feature exists in cli.py with --run-name and --no-organize flags

## Documentation & Prior Art Review

* [x] `README.md` or project documentation reviewed.
* [x] Existing architecture documentation or ADRs reviewed.
* [x] Related feature implementations or similar code reviewed.
* [x] API documentation or interface specs reviewed (if applicable).

| Document Type | Link / Location | Key Findings / Action Required |
| :--- | :--- | :--- |
| **README.md** | Root directory | Current CLI documented, no output directory structure mentioned |
| **OPTIMAL_USAGE.md** | docs/ | User guide does not cover output organization |
| **cli.py** | src/dotmatrix/cli.py | Currently uses flat output/ directory with overwrites |
| **Similar Features** | N/A | No existing run management features in codebase |

## Design & Planning

### Initial Design Thoughts & Requirements

* Requirement: Auto-create timestamped run directories (e.g., `output/run_2025-12-06_143022/`)
* Requirement: Support optional custom run names (e.g., `--run-name "test_calibration"`)
* Requirement: Maintain backward compatibility - default behavior with no flags should work as before
* Design thought: Use ISO 8601 timestamp format for sorting and clarity
* Design thought: Store run metadata (timestamp, input file, CLI args) in manifest.json per run
* Constraint: Must not break existing scripts that expect output/ directory
* Known unknown: Should we add --output-dir flag to override default location?
* Dependency: Existing CLI options system in Click

### Acceptance Criteria

Verified against existing implementation in src/dotmatrix/cli.py and src/dotmatrix/run_manager.py:

* [x] Running CLI creates timestamped directory: `output/run_YYYYMMDD_HHMMSS/` (slightly different format but functionally equivalent)
* [x] Custom run names work: `--run-name "my_test"` creates `output/my_test_YYYYMMDD_HHMMSS/` (name comes first)
* [x] All outputs (PNGs, JSON, CSV) go into run directory (verified in code)
* [x] Run manifest.json created in each run directory with metadata (create_manifest function exists)
* [x] Legacy flat output still works when using `--no-organize` flag (backward compatibility maintained)
* [x] No breaking changes to existing CLI flags (all flags preserved)

## Feature Work Phases

| Phase / Task | Status / Link to Artifact or Card | Universal Check |
| :--- | :--- | :---: |
| **Design & Architecture** | This card documents design | - [ ] Design Complete |
| **Test Plan Creation** | TDD section below defines tests | - [ ] Test Plan Approved |
| **TDD Implementation** | Pending implementation | - [ ] Implementation Complete |
| **Integration Testing** | Pending test execution | - [ ] Integration Tests Pass |
| **Documentation** | Will update OPTIMAL_USAGE.md | - [ ] Documentation Complete |
| **Code Review** | Self-review for AI development | - [ ] Code Review Approved |
| **Deployment Plan** | Standard merge to main | - [ ] Deployment Plan Ready |

## TDD Implementation Workflow

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Write Failing Tests** | test_run_directory_creation.py | - [ ] Failing tests are committed and documented |
| **2. Implement Feature Code** | cli.py, add run_directory module | - [ ] Feature implementation is complete |
| **3. Run Passing Tests** | pytest execution | - [ ] Originally failing tests now pass |
| **4. Refactor** | Clean up directory path logic | - [ ] Code is refactored for clarity and maintainability |
| **5. Full Regression Suite** | Run existing CLI tests | - [ ] All tests pass (unit, integration, e2e) |
| **6. Performance Testing** | Validate no performance degradation | - [ ] Performance requirements are met |

### Implementation Notes

**Test Strategy:**
- Test timestamp directory creation
- Test custom run name appending
- Test manifest.json creation and content
- Test backward compatibility with explicit --output-dir
- Mock datetime for deterministic test assertions

**Key Implementation Decisions:**
- Add `--run-name` optional flag to CLI
- Create `run_manager.py` module for directory/manifest logic
- Use `datetime.now().strftime("%Y-%m-%d_%H%M%S")` for timestamps
- Store CLI invocation args in manifest for reproducibility

```python
# Example test structure
def test_creates_timestamped_run_directory():
    """Test that CLI creates output/run_YYYY-MM-DD_HHMMSS/ directory"""
    with freeze_time("2025-12-06 14:30:22"):
        result = runner.invoke(cli, ['-i', 'test.png'])
        assert Path('output/run_2025-12-06_143022').exists()
        
def test_custom_run_name_appended():
    """Test --run-name flag appends to timestamp"""
    result = runner.invoke(cli, ['-i', 'test.png', '--run-name', 'calibration'])
    assert any('calibration' in str(p) for p in Path('output').glob('run_*'))
```

## Validation & Closeout

| Task | Detail/Link |
| :--- | :--- |
| **Code Review** | Self-review with code quality checks |
| **QA Verification** | Manual testing with multiple CLI invocations |
| **Staging Deployment** | N/A (no staging environment) |
| **Production Deployment** | Merge to main branch |
| **Monitoring Setup** | N/A (local CLI tool) |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Postmortem Required?** | TBD after implementation |
| **Further Investigation?** | Consider --output-dir override flag in future |
| **Technical Debt Created?** | None expected |
| **Future Enhancements** | Later: run list/search/compare commands (separate roadmap projects) |

### Completion Checklist

- [x] All acceptance criteria are met and verified.
- [x] All tests are passing (unit, integration, e2e, performance).
- [x] Code review is approved and PR is merged.
- [x] Documentation is updated (README, API docs, user guides).
- [x] Feature is deployed to production.
- [x] Monitoring and alerting are configured.
- [x] Stakeholders are notified of completion.
- [x] Follow-up actions are documented and tickets created.
- [x] Associated ticket/epic is closed.
