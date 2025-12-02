# Chore Template

## Description
[What maintenance task needs doing - REQUIRED]

**Type**: [Dependency update / Refactoring / Cleanup / Tooling]

**Value**: [Why this chore is important]

## Task Details
[Specific work to be done - REQUIRED]

[Detailed description of the chore]

**Current State**: [What exists now]

**Desired State**: [What it should be]

## Implementation Steps
[How to do the chore - REQUIRED]

1. **Step 1**: [Description]
2. **Step 2**: [Description]
3. **Step 3**: [Description]

## Verification (optional)
[How to verify it's done correctly]

- [ ] Changes tested
- [ ] No regressions introduced
- [ ] Documentation updated (optional)

## Closeout Procedure
[Required steps for internal maintenance work]

- [ ] All commits follow conventional commits format (chore: / refactor: / etc.)
- [ ] All decision table items below completed
- [ ] Tests passing (if applicable - many chores don't need tests)

### Decision Table
Answer Y/N for each. If Y, the Details column becomes **required**.

| Requirement | Y/N | Details (required if Y) |
|-------------|-----|-------------------------|
| CHANGELOG update required | | Reason (rarely Y - only if affects users/developers) |
| Dependency updates included | | List updated dependencies and versions |
| Breaking changes introduced | | What breaks and why (should typically be N) |
| CI/build pipeline changes | | Description of pipeline modifications |
| Developer tooling changes | | Instructions for team to update local setup |

**Note**: Chores are internal work. Most should answer N to CHANGELOG and breaking changes.

### Commit Summary (optional)
Only fill this out for complex multi-commit chores:

| Hash | Type | Message | Files |
|------|------|---------|-------|
| abc123 | chore | update dependencies | 3 |

## Additional Notes (optional)
📝 FREEFORM SECTION - Add anything project-specific
