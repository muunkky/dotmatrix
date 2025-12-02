# Test Template

## Test Description
[What's being tested - REQUIRED]

**Test Type**: [Unit / Integration / E2E / Performance]

**Coverage**: [What functionality this covers]

## Test Scenarios
[Specific test cases - REQUIRED]

### Scenario 1: [Name]
- **Given**: [Initial state]
- **When**: [Action taken]
- **Then**: [Expected result]

### Scenario 2: [Name]
- **Given**: [Initial state]
- **When**: [Action taken]
- **Then**: [Expected result]

## Implementation Plan
[How to implement tests - REQUIRED]

1. **Setup**: [Test fixtures and prerequisites]
2. **Test cases**: [Specific tests to write]
3. **Assertions**: [What to verify]
4. **Cleanup**: [Teardown steps]

## Test Data
[Data needed for tests - REQUIRED]

- Sample data: [Fixtures]
- Edge cases: [Boundary conditions]
- Invalid inputs: [Error cases]

## Acceptance Criteria (optional)
[When tests are complete]

- [ ] All scenarios covered
- [ ] Tests pass consistently
- [ ] Edge cases tested
- [ ] Good test coverage (optional)

## Closeout Procedure
[Required steps before marking test implementation as complete]

- [ ] All commits follow conventional commits format (test: / fix: / etc.)
- [ ] All decision table items below completed
- [ ] All new tests passing consistently
- [ ] Existing tests still passing

### Decision Table
Answer Y/N for each. If Y, the Details column becomes **required**.

| Requirement | Y/N | Details (required if Y) |
|-------------|-----|-------------------------|
| CHANGELOG update required | | Reason (rarely Y - only for new test infrastructure) |
| Test framework changes | | Description of new framework or tooling |
| Performance benchmarks added | | Benchmark names and baseline values |
| Test coverage improved | | Coverage percentage before/after |
| New test fixtures/utilities created | | Description and usage notes for team |

**Note**: Test cards rarely need CHANGELOG entries unless introducing new test infrastructure that affects other developers.

### Commit Summary (optional)
Only for complex test suites:

| Hash | Type | Message | Files |
|------|------|---------|-------|
| abc123 | test | add unit tests for auth module | 3 |
| def456 | test | add integration tests | 2 |

## Additional Notes (optional)
📝 FREEFORM SECTION - Add anything project-specific
