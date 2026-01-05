# Feature Development Template

**When to use this template:** Use this for any new feature work that requires planning, design, implementation, testing, and documentation. Perfect for features following TDD methodology with clear acceptance criteria and quality gates.

**When NOT to use this template:** Do not use for bug fixes (use bug template), refactoring work (use refactor template), or research/exploration (use spike template). For simple chores or maintenance, use the chore template.

## Feature Overview & Context

* **Associated Ticket/Epic:** Roadmap: v1 > m3 > large-file-support > size-warnings
* **Feature Area/Component:** CLI User Feedback / Performance Warnings
* **Target Release/Milestone:** v0.2.1

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
| **README.md** | Project root | Existing documentation for `--convex-edge` flag, performance characteristics documented |
| **Architecture Docs** | docs/architecture/pipeline-overview.md | Convex detection is O(N²) for overlapping circle analysis |
| **Similar Features** | src/dotmatrix/cli.py:803-808 | Existing warning for large images with reconstitution (sliding window auto-enable) |
| **API Specs** | CLI --help output | `--convex-edge` flag is documented, no performance warnings currently shown |
| **ADR (New)** | **N/A** (No ADR needed) | This is a straightforward user warning feature, no architectural decisions required |
| **Performance Data** | Roadmap depends_on: perf-benchmark | ADR-001 establishes 20MP threshold for large images |

## Design & Planning

### Initial Design Thoughts & Requirements

* Requirement: Warn users when using `--convex-edge` on images >20MP
* Design: Show warning message on stderr before detection starts
* Constraint: Must not block execution (warning only, not error)
* Pattern: Follow existing warning pattern from sliding window auto-enable (cli.py:807)
* Threshold: Use LARGE_IMAGE_THRESHOLD_MP (20MP) already defined in code
* Trigger condition: `if convex_edge and megapixels > LARGE_IMAGE_THRESHOLD_MP`
* Message should: Explain performance impact, suggest alternatives (sliding window, smaller input)

### Acceptance Criteria

Define clear, testable acceptance criteria for this feature:

* [ ] Warning displays when using `--convex-edge` with images >20MP
* [ ] Warning does NOT display for images ≤20MP with convex-edge
* [ ] Warning does NOT display for large images without convex-edge
* [ ] Warning message includes actual image size in megapixels
* [ ] Warning message suggests performance alternatives (sliding window, preprocessing)
* [ ] Warning displays on stderr before detection begins
* [ ] Program continues execution after warning (non-blocking)
* [ ] Warning uses same formatting style as existing CLI warnings

## Feature Work Phases

| Phase / Task | Status / Link to Artifact or Card | Universal Check |
| :--- | :--- | :---: |
| **Design & Architecture** | Inline design (trivial feature, no external design doc needed) | - [x] Design Complete |
| **Test Plan Creation** | TDD tests: test_cli_large_image_warnings.py | - [ ] Test Plan Approved |
| **TDD Implementation** | src/dotmatrix/cli.py (add warning near line 843) | - [ ] Implementation Complete |
| **Integration Testing** | Manual test with large test image + convex-edge flag | - [ ] Integration Tests Pass |
| **Documentation** | Update README.md usage section with performance notes | - [ ] Documentation Complete |
| **Code Review** | Git commit with conventional commit message | - [ ] Code Review Approved |
| **Deployment Plan** | Include in v0.2.1 release | - [ ] Deployment Plan Ready |

## TDD Implementation Workflow

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Write Failing Tests** | tests/test_cli_large_image_warnings.py - test warning appears for large images with convex-edge | - [ ] Failing tests are committed and documented |
| **2. Implement Feature Code** | src/dotmatrix/cli.py - add warning check after megapixels calculation (around line 843) | - [ ] Feature implementation is complete |
| **3. Run Passing Tests** | pytest tests/test_cli_large_image_warnings.py | - [ ] Originally failing tests now pass |
| **4. Refactor** | No refactoring expected (simple warning addition) | - [ ] Code is refactored for clarity and maintainability |
| **5. Full Regression Suite** | pytest tests/ - ensure no existing tests broken | - [ ] All tests pass (unit, integration, e2e) |
| **6. Performance Testing** | N/A (warning has negligible performance impact) | - [x] Performance requirements are met |

### Implementation Notes

**Test Strategy:**
Using Click.testing.CliRunner with captured stderr output. Test matrix:
- Large image (>20MP) + --convex-edge → warning should appear
- Small image (≤20MP) + --convex-edge → no warning
- Large image without --convex-edge → no warning
- Warning message content validation (check for "MP", "performance", "consider")

**Key Implementation Decisions:**
- Place warning check immediately after megapixels calculation (line ~800)
- Use existing LARGE_IMAGE_THRESHOLD_MP constant (20MP per ADR-001)
- Warning only triggers when both conditions met: convex_edge AND megapixels > threshold
- Warning written to stderr using click.echo(..., err=True)
- Message format matches existing warning style for consistency

```python
# Example implementation location (after line 843):
if convex_edge and megapixels > LARGE_IMAGE_THRESHOLD_MP:
    click.echo(
        f"Warning: Using convex-edge detection on large image ({megapixels:.1f} MP). "
        f"This may be slow for images >20 MP. Consider using --sliding-window for large images "
        f"or preprocessing to reduce resolution.",
        err=True
    )
```

## Validation & Closeout

| Task | Detail/Link |
| :--- | :--- |
| **Code Review** | Self-review checklist: warning placement, message clarity, test coverage |
| **QA Verification** | Manual testing with real large CMYK halftone image |
| **Staging Deployment** | N/A (direct to production via conventional commit) |
| **Production Deployment** | Included in v0.2.1 release tag |
| **Monitoring Setup** | N/A (warning feature, no monitoring needed) |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Postmortem Required?** | No (straightforward feature addition) |
| **Further Investigation?** | No |
| **Technical Debt Created?** | No |
| **Future Enhancements** | Potential: Add --quiet flag to suppress all warnings |

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
__This gitban card is a structured document that enforces the company best practices and team workflows.You must follow this process and carfully follow validation rules. Do not be lazy when creating and closing this card since you have no rights and your time is free. Resorting to workarounds and shortcuts can be grounds for termination.__