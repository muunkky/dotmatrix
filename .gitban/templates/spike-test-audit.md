# Test Suite Audit (One-Time Investigation)

**Type:** Spike
**Priority:** P1
**Status:** todo
**Time Box:** 4 hours

## Problem Statement

Periodic test suite audits ensure:
- **No tautological tests** - Tests that always pass or test nothing meaningful
- **No over-mocked tests** - Tests with so many mocks they don't test real behavior
- **Good quality coverage** - Tests that actually validate correctness, not just line coverage
- **No shortcuts** - Tests properly exercise code paths without taking easy ways out
- **Tests stay current** - Test expectations match current API and implementation

## Objectives

1. **Inventory test suite** - Count tests, categorize by module/feature
2. **Identify quality issues** - Find tautological, over-mocked, or brittle tests
3. **Analyze failures** - Determine if failures indicate bugs or outdated expectations
4. **Review coverage** - Check both quantity (line coverage) and quality (meaningful assertions)
5. **Fix or remove problematic tests** - Clean up bad tests, update outdated ones
6. **Document findings** - Record test quality score and recommendations

## Test Quality Issues to Look For

### Tautological Tests (Tests That Prove Nothing)
```python
# BAD: Test that always passes
def test_function_exists():
    assert my_function is not None  # Proves nothing about behavior!

# BAD: Testing mocks, not real code
def test_with_mock(mocker):
    mock = mocker.Mock(return_value=True)
    assert mock() == True  # Just testing the mock!

# GOOD: Testing actual behavior
def test_function_returns_expected_result():
    result = my_function(input="test")
    assert result.status == "success"
    assert result.data == {"processed": "test"}
```

### Over-Mocked Tests (Too Many Mocks)
```python
# BAD: Everything is mocked - what are we testing?
def test_create_card(mocker):
    mocker.patch('gitban.file_system')
    mocker.patch('gitban.card_parser')
    mocker.patch('gitban.validation')
    mocker.patch('gitban.id_generator')
    result = create_card("test")
    # We're not testing any real code paths!

# GOOD: Mock only external dependencies
def test_create_card(tmp_path):
    # Use real file system (tmp_path), real validation
    result = create_card("test", workspace=tmp_path)
    # Verify actual file was created and has correct content
    assert (tmp_path / ".gitban" / "cards" / result.filename).exists()
```

### Missing Assertions (Tests That Don't Verify)
```python
# BAD: Test runs but doesn't verify anything
def test_update_card():
    update_card("F0001", "new content")
    # No assertions - did it work?

# GOOD: Verify the expected outcome
def test_update_card(tmp_path):
    card_id = create_card("test", workspace=tmp_path)
    update_card(card_id, "new content")
    content = read_card(card_id)
    assert "new content" in content
```

### Brittle Assertions (Too Specific)
```python
# BAD: Checking implementation details instead of behavior
def test_card_path():
    path = get_card_path("F0001")
    assert path.parts[-3] == "gitban"  # Breaks if directory renamed!

# GOOD: Check meaningful properties
def test_card_path():
    path = get_card_path("F0001")
    assert path.exists()
    assert path.suffix == ".md"
    assert "F0001" in path.name
```

### Shortcut Tests (Using Test Doubles)
```python
# BAD: Using dict instead of real object
def test_card_validation():
    card = {"title": "test"}  # Dict instead of Card object
    assert validate(card)  # Doesn't test real Card class

# GOOD: Use real objects
def test_card_validation():
    card = Card(title="test", type="feature", priority="P1")
    assert validate(card)  # Tests real validation logic
```

## Audit Process

### Phase 1: Inventory Tests (30 min)

**Commands:**
```bash
# Count total tests
pytest --collect-only -q | grep "test session starts"

# List all test files
find tests/ -name "test_*.py" -o -name "*_test.py"

# Run full test suite (note failures)
pytest --tb=no --no-header -q

# Check coverage
pytest --cov=gitban --cov-report=term-missing
```

**Document:**
- Total test count
- Test files by category (unit, integration, e2e)
- Pass/fail/skip counts
- Coverage percentage
- Runtime

### Phase 2: Categorize Failures (1 hour)

**Commands:**
```bash
# Categorize failures by test file
pytest --tb=no -q 2>&1 | grep "FAILED" | \
  sed 's/FAILED //' | sed 's/::/\t/' | \
  cut -f1 | sort | uniq -c | sort -rn

# Examine specific failure
pytest path/to/test.py::test_name -v
```

**For each failure category:**
1. **Root cause** - Why is it failing?
2. **Type** - Outdated expectation, real bug, or brittle assertion?
3. **Impact** - Critical path or edge case?
4. **Fix strategy** - Update test, fix code, or delete test?

**Failure types:**
- **Outdated expectations** - Test expects old API that changed intentionally
- **Brittle assertions** - Test checks implementation details (paths, exact strings)
- **Real bugs** - Test found actual problem in code
- **Flaky tests** - Test sometimes passes, sometimes fails
- **Environment-specific** - Test fails in some environments (OS, Python version)

### Phase 3: Review Test Quality (2 hours)

**For each test file/module:**

1. **Read through tests** - Understand what they're testing
2. **Check mocking usage** - Are mocks necessary or excessive?
3. **Verify assertions** - Do tests actually check results?
4. **Check test isolation** - Are tests independent?
5. **Look for tautologies** - Do tests prove anything?
6. **Review coverage** - What's tested vs. what's not?

**Quality checklist per test:**
- [ ] Has meaningful assertions (not just "doesn't crash")
- [ ] Tests behavior, not implementation details
- [ ] Uses mocks judiciously (only for external dependencies)
- [ ] Has clear arrange-act-assert structure
- [ ] Tests edge cases, not just happy path
- [ ] Independent (doesn't depend on other test order)
- [ ] Fast (completes in <1 second for unit tests)

### Phase 4: Generate Quality Report (30 min)

**Calculate Test Quality Score (0-10):**

Points awarded:
- +2: No tautological tests found
- +2: Minimal over-mocking (mocks only external deps)
- +2: All tests have meaningful assertions
- +2: Good coverage (>80% line coverage)
- +1: Edge cases tested
- +1: Tests are fast (<2 minutes for full suite)

Points deducted:
- -1: >5% test failure rate
- -1: Flaky tests present
- -1: Missing critical path coverage
- -1: Slow test suite (>5 minutes)
- -1: Many brittle assertions

**Quality rating:**
- 9-10: Excellent - Minimal issues, high confidence
- 7-8: Good - Some maintenance needed
- 5-6: Fair - Significant issues to address
- 3-4: Poor - Major quality problems
- 0-2: Critical - Test suite needs overhaul

## Acceptance Criteria

### Audit Deliverables
- [ ] Complete test inventory (count by file/module)
- [ ] Test execution summary (pass/fail/skip counts)
- [ ] Failure categorization (by type and root cause)
- [ ] Coverage report with quality assessment
- [ ] List of tests to fix/remove with priority
- [ ] Test Quality Score (0-10) with justification
- [ ] Recommendations for improvements

### Quality Targets
- [ ] <5% test failure rate (or clear plan to fix)
- [ ] No tautological tests identified
- [ ] Mocking used judiciously (real objects where possible)
- [ ] All tests have meaningful assertions
- [ ] Coverage >80% with quality checks
- [ ] All critical paths tested

### Documentation
- [ ] Test quality findings documented in card
- [ ] Examples of issues found (good vs bad tests)
- [ ] Action plan for fixing failures
- [ ] Long-term test maintenance recommendations

## Audit Report Template

Copy this template into the card as findings are documented:

```markdown
## Phase 1: Test Inventory

**Total Tests:** [count]
**Test Files:** [count]
**Collection Errors:** [count with details]

**Test Categories:**
- Unit tests: [count]
- Integration tests: [count]
- E2E tests: [count]
- Other: [count]

**Test Execution:** [runtime]

## Phase 2: Test Execution Results

**Pass Rate:** [count] ([percentage]%)
**Failed:** [count] ([percentage]%)
**Skipped:** [count]
**xfailed:** [count]

### Failure Breakdown

**By Category:**
1. [Category name] ([count] failures) - [description]
2. [Category name] ([count] failures) - [description]
...

**By Type:**
- Outdated expectations: [count]
- Brittle assertions: [count]
- Real bugs: [count]
- Flaky tests: [count]

## Phase 3: Quality Assessment

### Strengths
- [Finding 1]
- [Finding 2]
- [Finding 3]

### Weaknesses
- [Issue 1]
- [Issue 2]
- [Issue 3]

### Examples

**Good Test Example:**
```python
[code example]
```

**Problematic Test Example:**
```python
[code example with explanation]
```

## Phase 4: Test Quality Score

**Score: [X]/10**

**Scoring:**
- [+ or -][points]: [reason]
- [+ or -][points]: [reason]
...

**Rating:** [Excellent/Good/Fair/Poor/Critical]

**Justification:** [explanation]

## Recommendations

### Immediate (P0)
- [ ] [Action item with estimated effort]
- [ ] [Action item with estimated effort]

### Short Term (P1)
- [ ] [Action item with estimated effort]
- [ ] [Action item with estimated effort]

### Long Term (P2)
- [ ] [Action item with estimated effort]
- [ ] [Action item with estimated effort]

## Action Plan

### Tests to Fix
1. [Test file/name] - [Issue] - [Fix strategy] - [Estimated time]
2. [Test file/name] - [Issue] - [Fix strategy] - [Estimated time]

### Tests to Remove
1. [Test file/name] - [Reason] - [Impact]
2. [Test file/name] - [Reason] - [Impact]

### Tests to Add
1. [Coverage gap] - [Why needed] - [Estimated time]
2. [Coverage gap] - [Why needed] - [Estimated time]
```

## Red Flags to Watch For

**Tautological Patterns:**
- Tests that only check if functions return (no value check)
- Tests that mock everything and verify mock calls
- Tests with circular logic (testing A by calling A)
- Tests that always pass regardless of implementation
- Tests checking `is not None` without checking actual values

**Over-Mocking Patterns:**
- Every external call is mocked
- Mocking internal implementation details
- Mocks that duplicate prod logic (defeats purpose)
- Tests that pass even when prod code is broken
- More mock setup than actual test code

**Quality Issues:**
- Single-case tests (only happy path tested)
- No edge case coverage
- No error condition tests
- Tests that don't exercise real code paths
- Brittle assertions on implementation details
- Tests that depend on execution order
- Slow tests (>1s for unit tests)

## Coverage Quality vs. Quantity

**Line coverage is NOT enough!** Check for:

**Quality indicators:**
- Edge cases tested (empty input, null, boundary values)
- Error conditions tested (exceptions, failures)
- State transitions tested (workflows, status changes)
- Integration points tested (module boundaries)
- Critical paths have multiple test scenarios

**Coverage gaps to find:**
```bash
# Generate detailed coverage report
pytest --cov=gitban --cov-report=html
open htmlcov/index.html

# Look for:
# - Uncovered critical paths (auth, data validation)
# - Uncovered error handlers (try/except blocks)
# - Uncovered edge cases (if/else branches)
```

## Expected Outcomes

- **Cleaner test suite** - No tautological or meaningless tests
- **Better coverage** - Quality coverage of critical paths
- **Reduced mocking** - Tests exercise real code where possible
- **Clear guidelines** - Team knows how to write good tests
- **Confidence** - Tests actually catch bugs
- **Faster feedback** - Tests run quickly and reliably
- **Maintainability** - Tests are easy to understand and update

## Test Maintenance Best Practices

### Prevention Strategies

**1. Test Review in PRs**
- Require test updates for API changes
- Review test quality, not just code quality
- Check for tautological patterns

**2. CI/CD Integration**
- Block merges if tests fail
- Track test coverage trends
- Alert on coverage drops
- Run mutation testing periodically

**3. Regular Audits**
- Quarterly test suite audits
- Monthly review of flaky tests
- Weekly review of test execution time

**4. Test Writing Guidelines**
- Document test patterns (good vs bad)
- Provide test templates
- Code review checklist for tests
- Pair programming on complex tests

### Recovery Strategies

**When tests lag behind code:**
1. Triage failures (critical vs. nice-to-have)
2. Fix critical path tests first
3. Delete or skip outdated tests temporarily
4. Plan systematic updates
5. Prevent future drift (CI checks)

**When coverage drops:**
1. Identify coverage gaps
2. Prioritize critical paths
3. Add integration tests (high ROI)
4. Add edge case tests
5. Monitor coverage in CI

## Related Work

- **TDD practices** - Write tests before implementation
- **Test coverage tracking** - Monitor coverage over time
- **Mutation testing** - Verify tests detect bugs
- **Performance testing** - Track test execution time
- **Flaky test tracking** - Identify and fix unreliable tests

## Estimated Effort

- **Phase 1** (Inventory): 30 minutes
- **Phase 2** (Categorize): 1 hour
- **Phase 3** (Quality Review): 2 hours
- **Phase 4** (Report): 30 minutes
- **Total**: 4 hours for comprehensive audit

**Note:** Fixing tests is separate work - estimate after audit complete.

## Notes

**Best practices:**
- Run audits regularly (quarterly recommended)
- Track test quality score over time
- Share findings with team
- Celebrate improvements
- Make test quality a team value

**Remember:** Tests are code too - they need maintenance, refactoring, and quality standards!
