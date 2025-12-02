# Refactor Template

## Description
[What code is being refactored and why - REQUIRED]

**Motivation**: [Why refactor this code]

**Benefits**: [Improved maintainability, performance, readability]

## Current State
[Existing code structure - REQUIRED]

**Problems**:
- [Issue 1]
- [Issue 2]

**Code location**: `path/to/file:line`

```language
// Current problematic code
```

## Proposed Changes
[How to refactor - REQUIRED]

**Approach**: [Refactoring strategy]

```language
// Proposed refactored code
```

**Improvements**:
- [Benefit 1]
- [Benefit 2]

## Implementation Plan
[Steps to refactor - REQUIRED]

1. **Preparation**: [Tests to ensure behavior preserved]
2. **Refactoring**: [Incremental steps]
3. **Verification**: [How to confirm no regressions]

## Testing Strategy (optional)
[How to verify refactoring is safe]

- [ ] Existing tests pass
- [ ] Behavior unchanged
- [ ] Performance not degraded (optional)

## Closeout Procedure
[Required steps before marking refactoring as complete]

- [ ] All commits follow conventional commits format (refactor: / test: / etc.)
- [ ] All decision table items below completed
- [ ] All existing tests still passing
- [ ] Behavior verified unchanged (critical for refactors!)
- [ ] Code reviewed (refactors are high-risk, review strongly recommended)

### Decision Table
Answer Y/N for each. If Y, the Details column becomes **required**.

| Requirement | Y/N | Details (required if Y) |
|-------------|-----|-------------------------|
| CHANGELOG update required | | Reason (rarely Y - only if user-facing behavior/performance changed) |
| Behavior changes introduced | | Describe changes (should typically be N for pure refactors) |
| Breaking changes introduced | | What breaks and why (should almost always be N) |
| Performance impact | | Benchmarks before/after, any degradation or improvement |
| Public API changes | | List modified interfaces (should be N for internal refactors) |
| Database/schema changes | | Describe changes (should typically be N for refactors) |

**Note**: Pure refactorings should answer N to all rows except possibly "Performance impact" (if improved).

### Commit Summary (optional)
For multi-phase refactorings:

| Hash | Type | Message | Files |
|------|------|---------|-------|
| abc123 | refactor | extract common auth logic | 5 |
| def456 | test | verify auth behavior unchanged | 2 |
| ghi789 | refactor | simplify auth error handling | 3 |

## Additional Notes (optional)
📝 FREEFORM SECTION - Add anything project-specific
