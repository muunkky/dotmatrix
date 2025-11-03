
## Purpose

[Brief description of the maintenance task - REQUIRED]

[Clear explanation of why this chore is needed - maintenance, cleanup, refactoring, upgrade, etc.]

**Value**: [How this improves the codebase, developer experience, or system reliability]

**Estimated Effort**: [Time estimate, e.g., 2 hours, 1 day]

---

## Project Location

**Path**: `[Directory or file path being modified]`

[Specify the location of code, configuration, or infrastructure being modified]

### Files/Modules Affected

- `[path/to/file1]`: [What will be changed]
- `[path/to/file2]`: [What will be changed]
- `[path/to/directory]`: [What will be changed]

---

## Tasks

[Detailed breakdown of work to be done, in order of execution]

- [ ] **Task 1**: [Description of first task]
  - Sub-task or detail
  - Command or action needed

- [ ] **Task 2**: [Description of second task]
  - Sub-task or detail
  - Configuration change needed

- [ ] **Task 3**: [Description of third task]
  - Sub-task or detail
  - Verification step

[Add more tasks as needed]

### Task Dependencies

[If tasks must be done in specific order, explain dependencies here]

1. Task X must be completed before Task Y because [reason]
2. Task Z can be done in parallel with Task A

---

## Outputs

[Concrete deliverables from this chore]

### Files Created/Updated

1. **[Filename or path]**: [What it contains and why]
2. **[Filename or path]**: [What it contains and why]

### Configurations Changed

- [Configuration 1]: [Old value] → [New value] ([Reason])
- [Configuration 2]: [Change description]

### Documentation Updates

- [ ] Update [document name] with [changes]
- [ ] Create runbook for [operational procedure]
- [ ] Update CHANGELOG

### Artifacts

[Build artifacts, reports, or other outputs generated]

---

## Timeline (optional)

**Start Date**: [When to begin]

**Target Completion**: [When to finish]

**Estimated Duration**: [Time estimate for testing]

**Milestones**:
1. [Milestone 1]: [Date] - [Description]
2. [Milestone 2]: [Date] - [Description]

---

## Success Criteria

[How to know this chore is complete and successful]

- [ ] All tasks checked off and verified
- [ ] Tests pass (no regressions introduced)
- [ ] Code quality metrics improved or maintained
- [ ] Documentation updated to reflect changes
- [ ] Changes reviewed and approved
- [ ] Deployed to relevant environments

**Quality Gates**:
- [ ] Linting passes without new warnings
- [ ] Test coverage maintained or improved
- [ ] Performance benchmarks not degraded
- [ ] Security scans show no new issues

---

## Impact (optional)

[What will be improved by completing this chore]

### Positive Impacts

- **Code Quality**: [How code quality improves]
- **Maintainability**: [How this makes future work easier]
- **Performance**: [Performance improvements, if any]
- **Developer Experience**: [How this helps developers]
- **System Reliability**: [Stability or reliability improvements]

### Metrics

[Measurable improvements, if applicable]

- Before: [Current state metric]
- After: [Expected improved metric]

Examples:
- Build time: 5 minutes → 3 minutes
- Test flakiness: 10% → <1%
- Code duplication: 15% → 8%
- Dependency vulnerabilities: 5 high → 0 high

---

## Risks (optional)

[Potential issues, challenges, or risks with this chore]

### Technical Risks

- **Risk 1**: [Description]
  - **Likelihood**: [Low/Medium/High]
  - **Impact**: [Low/Medium/High]
  - **Mitigation**: [How to prevent or handle]

- **Risk 2**: [Description]
  - **Likelihood**: [Low/Medium/High]
  - **Impact**: [Low/Medium/High]
  - **Mitigation**: [How to prevent or handle]

### Operational Risks

- [Risk of downtime, service disruption, data loss]
- [Mitigation strategies]

### Rollback Plan

[How to undo changes if something goes wrong]

1. [Rollback step 1]
2. [Rollback step 2]

---

## Testing (optional)

[How to verify nothing breaks and changes work as intended]

### Pre-Change Validation

- [ ] Capture baseline metrics (performance, test results, error rates)
- [ ] Verify current functionality works as expected
- [ ] Take backups of configurations/data if needed

### Post-Change Validation

- [ ] All existing tests pass
- [ ] No new warnings or errors in logs
- [ ] Manual smoke testing completed
- [ ] Performance metrics unchanged or improved
- [ ] Configuration changes verified

### Regression Testing

- [ ] Core functionality still works
- [ ] Integration points not broken
- [ ] Edge cases still handled correctly

### Test Commands

```bash
# Commands to run tests
[test command 1]
[test command 2]
```

---

## Prerequisites (optional)

[Requirements that must be met before starting this chore]

**⚠️ DO NOT START THIS CARD UNLESS:**

- [ ] [Prerequisite 1 - required tools, access, or setup]
- [ ] [Prerequisite 2 - dependent work completed]
- [ ] [Prerequisite 3 - approvals or coordination needed]

**Why**: [Explain why these prerequisites matter]

### Required Tools/Access

- [Tool 1]: [Why needed and how to install/access]
- [Tool 2]: [Why needed and how to install/access]

### Required Approvals

- [ ] [Approval 1]: [Who needs to approve and why]
- [ ] [Approval 2]: [Who needs to approve and why]

---

## Related Cards (optional)

[Connections to other work]

### Dependencies

**Depends on**: [Card ID] - [Description of dependency]

[Cards that must be completed first]

### Blocks

**Blocks**: [Card ID] - [Description of what this unblocks]

[Cards waiting for this chore]

### Related Work

**Related**: [Card ID] - [Description of relationship]

[Related chores or improvements]

### Tracking

- Parent Epic/Feature: [Link if this is part of larger initiative]
- Related Issues: [Links to bug reports or feature requests]

---

## Notes (optional)

[Additional context, decisions, or important details]

### Background

[History or context explaining why this chore is needed now]

### Design Decisions

[Decisions made about how to approach this chore]

- **Decision**: [What was decided]
- **Rationale**: [Why]
- **Alternatives Considered**: [Other approaches]

### Known Limitations

[What this chore doesn't address or intentionally leaves for later]

### Future Work

[Follow-up chores or improvements to consider after this one]

### Resources

[Helpful links, documentation, or examples]

- [Resource 1]: [Description]
- [Resource 2]: [Description]

---

## Progress Notes (optional)

[Track work session by session]

**Session [Date] ([Your Name]):**

✅ **Completed:**
- [Task completed]
- [Configuration changed]

🔄 **In Progress:**
- [Current work]

⚠️ **Issues Encountered:**
- [Problem]: [How resolved or current status]

📋 **Next Session:**
1. [Next task]
2. [Following task]

**Technical Notes:**
[Important discoveries or learnings from this session]

---

<!--
EXTENSION POINTS:

This template can be extended with additional sections as needed:

## Dependency Update Details (optional)
[For dependency upgrade chores - versions, changelog, breaking changes]

## Migration Strategy (optional)
[For chores requiring data or configuration migration]

## Monitoring & Alerts (optional)
[For chores affecting observability or alerting]

## Security Impact (optional)
[For chores with security implications]

## Compliance Requirements (optional)
[For chores related to regulatory compliance]

## Team Coordination (optional)
[For chores requiring coordination across teams]

Add any project-specific sections your team needs!
-->
## Additional Notes (optional)

**📝 FREEFORM SECTION - Add anything you need from this point onward!**

Feel free to add any custom sections, notes, or documentation specific to your project below this line. No validation is enforced here - organize additional information however works best for your workflow.
