
## Refactoring Goal

[Area or component being refactored - REQUIRED]

[What code needs refactoring and why this improves the codebase]

**Value**: [How this refactoring benefits the system - maintainability, performance, readability]

**Complexity**: [Low/Medium/High complexity assessment]

**Estimated Effort**: [Time estimate, e.g., 1 day, 3 days]

---

## Current State

[Detailed description of current code structure and its problems]

### Code Location

**Path**: `[path/to/code]`

**Modules Affected**:
- `[module 1]`: [Current state]
- `[module 2]`: [Current state]

### Problems with Current Code

1. **[Problem 1]**: [Description]
   - **Impact**: [How this hurts maintainability/performance]
   - **Example**: [Code snippet or scenario]

2. **[Problem 2]**: [Description]
   - **Impact**: [How this hurts]
   - **Example**: [Code snippet]

### Technical Debt

- **Code Smells**: [Duplication, long functions, god classes, etc.]
- **Design Issues**: [Poor abstractions, tight coupling, missing patterns]
- **Performance Issues**: [Inefficiencies, bottlenecks]
- **Maintainability Issues**: [Hard to understand, hard to modify]

### Metrics (Current)

- **Code Complexity**: [Cyclomatic complexity, lines of code]
- **Code Duplication**: [Percentage or instances]
- **Test Coverage**: [Coverage %]
- **Performance**: [Current benchmarks if applicable]

---

## Desired State

[Description of improved code structure after refactoring]

### Target Architecture

[High-level design of refactored code]

```
[Diagram or description of new structure]
```

### Design Improvements

1. **[Improvement 1]**: [What changes]
   - **New Structure**: [Description]
   - **Benefit**: [Why better]

2. **[Improvement 2]**: [What changes]
   - **New Structure**: [Description]
   - **Benefit**: [Why better]

### Target Metrics

- **Code Complexity**: [Target improvement]
- **Code Duplication**: [Target reduction]
- **Test Coverage**: [Maintain or improve to X%]
- **Performance**: [Expected improvements if applicable]

---

## Benefits

[Concrete benefits of this refactoring]

### Code Quality Benefits

- **Readability**: [How code becomes easier to understand]
- **Maintainability**: [How future changes become easier]
- **Testability**: [How testing becomes easier]
- **Reusability**: [How code becomes more modular/reusable]

### Engineering Benefits

- **Velocity**: [How this speeds up future development]
- **Reliability**: [How this reduces bugs or improves stability]
- **Onboarding**: [How this helps new developers]
- **Documentation**: [How code becomes more self-documenting]

### Business Benefits

- **Feature Velocity**: [Faster delivery of new features]
- **Quality**: [Fewer bugs, better user experience]
- **Cost**: [Reduced maintenance cost]
- **Risk**: [Reduced technical risk]

### Measurable Improvements

- **Before → After**:
  - Complexity: [Metric before] → [Metric after]
  - Duplication: [X instances] → [Y instances]
  - Function length: [Avg X lines] → [Avg Y lines]
  - Test time: [X seconds] → [Y seconds]

---

## Refactoring Steps

[Detailed, safe approach to refactoring]

### Phase 1: Preparation

1. **Establish Safety Net**:
   - [ ] Ensure test coverage >80% of code being refactored
   - [ ] Add missing tests for critical paths
   - [ ] Verify all tests pass
   - [ ] Document current behavior

2. **Create Branch & Baseline**:
   - [ ] Create refactoring branch
   - [ ] Capture baseline metrics (complexity, performance)
   - [ ] Document refactoring plan

### Phase 2: Incremental Refactoring

[Small, safe steps with tests passing after each step]

3. **[Step 1 Name]**:
   - [ ] [Specific refactoring action]
   - [ ] Run tests, ensure still passing
   - [ ] Commit with clear message

4. **[Step 2 Name]**:
   - [ ] [Specific refactoring action]
   - [ ] Run tests
   - [ ] Commit

5. **[Step 3 Name]**:
   - [ ] [Specific refactoring action]
   - [ ] Run tests
   - [ ] Commit

[Add more steps - each should be small and independently verifiable]

### Phase 3: Validation

6. **Final Validation**:
   - [ ] All tests pass
   - [ ] Performance benchmarks unchanged or improved
   - [ ] Code review completed
   - [ ] Metrics verified against targets

### Refactoring Techniques

[Specific techniques being applied]

- [ ] **Extract Method**: [Where applied]
- [ ] **Extract Class**: [Where applied]
- [ ] **Introduce Parameter Object**: [Where applied]
- [ ] **Replace Conditional with Polymorphism**: [Where applied]
- [ ] **Decompose Conditional**: [Where applied]
- [ ] **Consolidate Duplicate Conditional Fragments**: [Where applied]
- [ ] **Other**: [Technique and where applied]

### Code Examples

**Before:**
```[language]
[Current code example showing problem]
```

**After:**
```[language]
[Refactored code showing improvement]
```

---

## Testing Strategy

[Ensuring no behavior changes during refactoring]

### Pre-Refactoring Testing

- [ ] **Capture Current Behavior**:
  - [ ] All existing tests pass
  - [ ] Document any flaky tests
  - [ ] Capture baseline coverage: [X%]
  - [ ] Document current performance benchmarks

### During Refactoring

- [ ] **Test After Each Step**:
  - [ ] Run full test suite after each commit
  - [ ] No test should fail due to refactoring
  - [ ] Add new tests for refactored code paths
  - [ ] Maintain or improve coverage

### Post-Refactoring Validation

- [ ] **Comprehensive Verification**:
  - [ ] All tests still pass (no regressions)
  - [ ] Test coverage maintained or improved
  - [ ] Performance benchmarks verified
  - [ ] Manual testing of refactored features
  - [ ] Integration testing with dependent systems

### Behavioral Equivalence

[Proving refactored code behaves identically]

- [ ] Same inputs produce same outputs
- [ ] Same edge cases handled identically
- [ ] Same errors raised in same conditions
- [ ] Same side effects (logging, DB writes, etc.)

### Golden Master Testing

[If applicable - capture current behavior and compare]

- [ ] Capture outputs from current code
- [ ] Compare outputs after each refactoring step
- [ ] Verify bit-for-bit equivalence

---

## Risks (optional)

[Potential issues and mitigation strategies]

### Technical Risks

1. **Breaking Changes**:
   - **Risk**: [Accidental behavior changes]
   - **Mitigation**: [Small steps, comprehensive testing, code review]
   - **Rollback**: [Easy rollback plan]

2. **Performance Regression**:
   - **Risk**: [Refactoring introduces performance issues]
   - **Mitigation**: [Benchmark before/after, profile if needed]

3. **Merge Conflicts**:
   - **Risk**: [Conflicts with ongoing work]
   - **Mitigation**: [Communicate with team, coordinate timing]

### Project Risks

- **Timeline**: [Risk of taking longer than estimated]
  - **Mitigation**: [Time-box effort, break into smaller cards if needed]

- **Scope Creep**: [Risk of over-refactoring]
  - **Mitigation**: [Stick to defined scope, defer other improvements]

### Rollback Plan

[How to quickly revert if issues arise]

1. [Rollback step 1]
2. [Rollback step 2]
3. [Verification after rollback]

---

## Prerequisites (optional)

[Requirements before starting refactoring]

**⚠️ DO NOT START THIS CARD UNLESS:**

- [ ] [Test coverage >80% for code being refactored]
- [ ] [All tests currently passing]
- [ ] [No active work in same code area]
- [ ] [Refactoring plan reviewed and approved]

**Why**: [Safe refactoring requires comprehensive tests and careful planning]

### Required Understanding

- [ ] Deep familiarity with code being refactored
- [ ] Understanding of design patterns being applied
- [ ] Knowledge of potential impact areas

### Required Tools

- [ ] IDE with refactoring support
- [ ] Test suite with fast feedback
- [ ] Profiling tools (if performance-related)
- [ ] Code quality metrics tools

---

## Related Cards (optional)

[Connections to features, tech debt, or improvements]

### Enables

**Enables**: [Card ID] - [Feature or improvement this unblocks]

[Work made easier or possible by this refactoring]

### Addresses

**Addresses**: [Tech Debt Card ID] - [Technical debt being resolved]

[Technical debt items this refactoring fixes]

### Related Refactorings

**Related**: [Card ID] - [Related cleanup or refactoring]

[Other refactoring work in same area or related areas]

### Motivated By

**Motivated By**: [Feature ID] - [Feature that revealed need for refactoring]

[Features or bugs that highlighted need for this refactoring]

---

## Notes (optional)

[Additional context or refactoring considerations]

### Refactoring Philosophy

[Project-specific refactoring principles]

- [Principle 1: e.g., "Always keep tests green"]
- [Principle 2: e.g., "Small commits, frequent integration"]
- [Principle 3: e.g., "Behavior preservation over perfection"]

### Design Decisions

[Key architectural or design decisions made]

- **Decision**: [What was decided]
- **Rationale**: [Why this approach]
- **Trade-offs**: [What was sacrificed for what benefit]

### Alternatives Considered

[Other refactoring approaches evaluated]

- **Alternative 1**: [Approach]
  - **Pros**: [Benefits]
  - **Cons**: [Drawbacks]
  - **Why Not Chosen**: [Reason]

### Lessons Learned

[Insights from previous refactorings]

- [Lesson 1]
- [Lesson 2]

### Resources

[Helpful refactoring resources]

- [Refactoring book/guide]: [Link]
- [Design pattern reference]: [Link]
- [Similar refactoring example]: [Link]

---

## Progress Notes (optional)

[Track refactoring progress session by session]

**Session [Date] ([Your Name]):**

✅ **Completed:**
- [Refactoring step completed]
- [Tests still passing: Yes/No]
- [Commits made: X]

🔄 **In Progress:**
- [Current refactoring step]
- [Current complexity]

📊 **Metrics:**
- Tests passing: [Count / Total]
- Coverage: [Percentage]
- Code complexity: [Before] → [Current]

⚠️ **Issues:**
- [Test failure]: [Resolution]
- [Unexpected behavior]: [How fixed]

📋 **Next Session:**
1. [Next refactoring step]
2. [Tests to add]
3. [Validation to perform]

**Refactoring Notes:**
[Observations, insights, or discoveries during refactoring]

---

<!--
EXTENSION POINTS:

This template can be extended with additional sections as needed:

## Code Smell Catalog (optional)
[Specific code smells being addressed with examples]

## Design Patterns (optional)
[Design patterns being introduced or improved]

## Architecture Evolution (optional)
[How system architecture evolves through this refactoring]

## Team Communication (optional)
[How to coordinate with team during large refactoring]

## Performance Profiling (optional)
[Before/after performance analysis]

Add any project-specific sections your team needs!
-->
## Additional Notes (optional)

**📝 FREEFORM SECTION - Add anything you need from this point onward!**

Feel free to add any custom sections, notes, or documentation specific to your project below this line. No validation is enforced here - organize additional information however works best for your workflow.
