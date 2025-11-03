
## Testing Goal

[Component or module to test - REQUIRED] - Test Coverage Improvement

[What needs test coverage and why it's important]

**Value**: [Why testing this code matters - prevent regressions, enable refactoring, ensure quality]

**Current Coverage**: [Current percentage]%

**Target Coverage**: [Target percentage]%

**Estimated Effort**: [Time estimate, e.g., 1 day, 3 days]

---

## Test Scope

[Specific modules, functions, or features to test]

### Modules to Test

- [ ] **[Module/Package 1]**: [Description and priority]
  - `[function/class 1]`: [Why test this]
  - `[function/class 2]`: [Why test this]

- [ ] **[Module/Package 2]**: [Description and priority]
  - `[function/class 3]`: [Why test this]
  - `[function/class 4]`: [Why test this]

### Code Paths to Cover

- [ ] Happy path scenarios
- [ ] Error handling paths
- [ ] Edge cases and boundary conditions
- [ ] Concurrency/async scenarios
- [ ] Integration points
- [ ] Performance-critical paths

### Out of Scope

[What won't be tested in this card and why]

- [Item 1]: [Reason - covered elsewhere, low priority, etc.]
- [Item 2]: [Reason]

---

## Test Types (optional)

[Types of tests needed for comprehensive coverage]

### Unit Tests

- [ ] Test individual functions in isolation
- [ ] Mock external dependencies
- [ ] Cover all code branches
- [ ] Test with valid inputs
- [ ] Test with invalid/edge case inputs
- [ ] Test error conditions

**Target**: [X unit tests covering Y% of module code]

### Integration Tests

- [ ] Test interactions between components
- [ ] Test with real dependencies (databases, APIs, services)
- [ ] Test data flow through system
- [ ] Test configuration variations
- [ ] Test deployment scenarios

**Target**: [X integration tests for Y critical flows]

### End-to-End Tests

- [ ] Test complete user workflows
- [ ] Test across full stack
- [ ] Test with production-like data
- [ ] Test multiple user scenarios

**Target**: [X E2E tests for Y user journeys]

### Property-Based Tests

- [ ] Define properties that must always hold
- [ ] Use Hypothesis for generative testing
- [ ] Test with randomized inputs
- [ ] Find edge cases automatically

**Target**: [X property tests for Y invariants]

### Performance Tests

- [ ] Benchmark critical operations
- [ ] Test under load
- [ ] Measure response times
- [ ] Profile memory usage
- [ ] Identify bottlenecks

**Target**: [X performance tests ensuring Y benchmarks]

### Other Test Types

- [ ] Snapshot tests (for UI/API contracts)
- [ ] Mutation tests (test the tests)
- [ ] Fuzz testing (security-critical code)
- [ ] Regression tests (previously found bugs)

---

## Coverage Goals (optional)

[Measurable targets for test coverage]

### Current State

- **Overall Coverage**: [Current percentage]%
- **Module Coverage**: [Breakdown by module]
- **Critical Path Coverage**: [Coverage of important code]
- **Branch Coverage**: [If/else branch coverage]

### Target State

- **Overall Coverage**: [Target percentage]%
- **Module Coverage Goals**:
  - `[module 1]`: [Current]% → [Target]%
  - `[module 2]`: [Current]% → [Target]%
- **Critical Path Coverage**: 100% (must cover all critical paths)
- **Branch Coverage**: [Target]%

### Coverage Gaps

[Areas currently lacking test coverage]

1. **[Gap 1]**: [Module/function] - [Current coverage] - [Why gap exists]
2. **[Gap 2]**: [Module/function] - [Current coverage] - [Why gap exists]

### Success Metrics

- [ ] Target coverage percentage achieved
- [ ] All critical paths covered
- [ ] Zero flaky tests
- [ ] Tests run in <X minutes
- [ ] No skipped or disabled tests

---

## Test Scenarios

[Comprehensive scenarios to test]

### Happy Path Scenarios

[Normal, expected usage patterns]

1. **[Scenario 1]**: [Description]
   - Setup: [Initial state]
   - Action: [What happens]
   - Expected: [Result]
   - Test: [What to assert]

2. **[Scenario 2]**: [Description]
   - Setup: [Initial state]
   - Action: [What happens]
   - Expected: [Result]
   - Test: [What to assert]

### Edge Cases

[Boundary conditions and unusual inputs]

- [ ] Empty/null inputs
- [ ] Minimum values
- [ ] Maximum values
- [ ] Special characters
- [ ] Unicode/internationalization
- [ ] Concurrent access
- [ ] Large datasets
- [ ] Timeout scenarios

### Error Conditions

[How system handles failures]

- [ ] Invalid inputs
- [ ] Missing required data
- [ ] Permission failures
- [ ] Network errors
- [ ] Database errors
- [ ] External service failures
- [ ] Resource exhaustion

### Regression Scenarios

[Previously found bugs that must not return]

- [ ] Bug [ID]: [Scenario that triggered bug]
- [ ] Bug [ID]: [Scenario that triggered bug]

---

## Implementation Plan (optional)

[Step-by-step approach to adding tests]

### Phase 1: Setup & Infrastructure

1. **Test Environment Setup**:
   - [ ] Configure test framework (pytest, jest, etc.)
   - [ ] Set up test fixtures and factories
   - [ ] Configure mocking utilities
   - [ ] Set up test databases/services
   - [ ] Configure CI integration

2. **Test Utilities**:
   - [ ] Create reusable test helpers
   - [ ] Create test data generators
   - [ ] Create custom assertions
   - [ ] Create test fixtures

### Phase 2: Core Tests

3. **Unit Tests**:
   - [ ] Test [module 1] - [X tests]
   - [ ] Test [module 2] - [Y tests]
   - [ ] Test error handling
   - [ ] Test edge cases

4. **Integration Tests**:
   - [ ] Test [integration 1] - [X tests]
   - [ ] Test [integration 2] - [Y tests]
   - [ ] Test data flows

### Phase 3: Advanced Tests

5. **Property-Based/E2E Tests**:
   - [ ] Property tests for [invariants]
   - [ ] E2E tests for [workflows]

6. **Performance Tests**:
   - [ ] Benchmark [critical operations]
   - [ ] Load tests

### Test Writing Guidelines

**Test Structure** (Arrange-Act-Assert):
```python
def test_example():
    # Arrange: Set up test state
    [setup code]

    # Act: Perform action being tested
    result = [function under test]

    # Assert: Verify expected outcome
    assert result == expected
```

**Naming Convention**:
- `test_[function]_[scenario]_[expected]`
- Example: `test_create_user_with_valid_email_succeeds`

**Test Independence**:
- Each test should be independent
- No shared state between tests
- Use fixtures for common setup

---

## Acceptance Criteria

[When testing work is complete]

### Coverage Achieved

- [ ] Target coverage percentage met: [Target percentage]%
- [ ] All modules in scope covered
- [ ] All critical paths have tests
- [ ] Branch coverage targets met

### Test Quality

- [ ] All tests pass consistently
- [ ] No flaky tests (< 0.1% failure rate)
- [ ] Tests are well-named and documented
- [ ] Tests follow project conventions
- [ ] Tests are maintainable and readable

### Test Performance

- [ ] Full test suite runs in <[X minutes]
- [ ] Individual tests are fast (<100ms for unit tests)
- [ ] CI pipeline not significantly slowed

### Documentation

- [ ] Test fixtures documented
- [ ] Complex test scenarios explained
- [ ] Test data generation documented
- [ ] Contributing guide updated with testing practices

---

## Testing Tools (optional)

[Tools and libraries used]

### Test Framework

- **Primary Framework**: [pytest / jest / mocha / JUnit]
- **Version**: [Specific version]
- **Configuration**: [Config file location]

### Testing Libraries

- **Mocking**: [unittest.mock / sinon / mockito]
- **Assertions**: [pytest assertions / chai / assertj]
- **Fixtures**: [pytest fixtures / factory_boy / faker]
- **Property Testing**: [Hypothesis / JSVerify / QuickCheck]
- **Performance**: [pytest-benchmark / k6 / JMeter]

### Coverage Tools

- **Coverage Tool**: [coverage.py / istanbul / JaCoCo]
- **Report Format**: [HTML / XML / LCOV]
- **CI Integration**: [Codecov / Coveralls]

### Test Data

- **Data Generation**: [Faker / Factory Boy / AutoFixture]
- **Test Databases**: [SQLite / H2 / Test containers]
- **Sample Data**: [Location of test datasets]

### CI/CD Integration

- **CI System**: [GitHub Actions / GitLab CI / Jenkins]
- **Test Commands**: `[command to run tests]`
- **Coverage Reporting**: `[command to generate coverage]`

---

## Prerequisites (optional)

[Requirements before starting test work]

**⚠️ DO NOT START THIS CARD UNLESS:**

- [ ] [Code to be tested is complete and working]
- [ ] [Test framework and tools are set up]
- [ ] [Understanding of code being tested]
- [ ] [Test data or fixtures available]

**Why**: [Tests should verify working code, not be written for incomplete features]

### Required Knowledge

- [ ] Familiarity with code being tested
- [ ] Understanding of test framework
- [ ] Knowledge of mocking strategies
- [ ] Understanding of expected behavior

### Required Setup

- [ ] Development environment configured
- [ ] Test dependencies installed
- [ ] Test databases/services available
- [ ] CI pipeline ready for tests

---

## Related Cards (optional)

[Connections to features, bugs, or other work]

### Features Being Tested

**Tests**: [Feature Card ID] - [Feature being tested]

[List features that need these tests]

### Bugs Being Prevented

**Prevents**: [Bug ID] - [Bug scenario being tested]

[List bugs that regression tests prevent]

### Related Testing Work

**Related**: [Card ID] - [Related testing efforts]

[Other testing cards or test infrastructure work]

### Blocks

**Blocks**: [Card ID] - [Work waiting for these tests]

[Refactoring or features that need tests first]

---

## Notes (optional)

[Additional context or testing considerations]

### Testing Strategy

[Approach to testing this code]

- **Focus Areas**: [What to test most thoroughly]
- **Risk Areas**: [Code most likely to break]
- **Testing Philosophy**: [Project-specific testing approach]

### Test Data Strategy

[How test data is managed]

- **Data Generation**: [Automated vs manual test data]
- **Data Isolation**: [How to prevent test data conflicts]
- **Data Cleanup**: [How test data is cleaned up]

### Known Testing Challenges

[Difficulties in testing this code]

- **Challenge 1**: [Issue and how to address]
- **Challenge 2**: [Issue and how to address]

### Future Test Improvements

[Ideas for better testing after this card]

- [Improvement 1]
- [Improvement 2]

### Resources

[Helpful testing resources]

- [Testing guide]: [Link]
- [Example tests]: [Link]
- [Testing best practices]: [Link]

---

## Progress Notes (optional)

[Track testing progress session by session]

**Session [Date] ([Your Name]):**

✅ **Tests Written:**
- [Module/feature]: [X tests added]
- Coverage: [Before]% → [After]%

🔄 **In Progress:**
- [Current module being tested]
- [Tests remaining]

📊 **Metrics:**
- Total tests: [Count]
- Coverage: [Percentage]
- Test execution time: [Duration]

⚠️ **Issues:**
- [Flaky test]: [Description and fix]
- [Challenge]: [How addressed]

📋 **Next Session:**
1. [Next module to test]
2. [Next test type to add]
3. [Test performance optimization needed]

**Testing Notes:**
[Observations about code quality, test patterns that work well, etc.]

---

<!--
EXTENSION POINTS:

This template can be extended with additional sections as needed:

## Mutation Testing (optional)
[For testing the quality of tests themselves]

## Visual Regression Testing (optional)
[For UI testing with screenshot comparison]

## Security Testing (optional)
[For penetration testing, vulnerability scanning]

## Accessibility Testing (optional)
[For WCAG compliance, screen reader testing]

## Load Testing (optional)
[For stress testing, scalability testing]

## Chaos Engineering (optional)
[For resilience testing, failure injection]

Add any project-specific sections your team needs!
-->
## Additional Notes (optional)

**📝 FREEFORM SECTION - Add anything you need from this point onward!**

Feel free to add any custom sections, notes, or documentation specific to your project below this line. No validation is enforced here - organize additional information however works best for your workflow.
