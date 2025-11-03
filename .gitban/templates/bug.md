
## Bug Description

**Summary**: [Brief description of the bug - REQUIRED]

[Clear, concise description of the bug and what's broken]

**Severity**: [P0/Critical, P1/High, P2/Medium, P3/Low]

**Value of Fix**: [Why fixing this bug is important - user impact, business impact, or technical debt]

**Discovered**: [When/how this bug was discovered - production, testing, user report]

**Reporter**: [Who reported this - user, QA, developer, monitoring system]

---

## Impact Assessment (optional)

[Analysis of how this bug affects users, system, and business]

### User Impact

- **Affected Users**: [Number or percentage of users affected]
- **User Impact**: [What users experience - can't complete task, see errors, experience delays]
- **Frequency**: [How often does this occur - always, intermittently, under specific conditions]
- **Workaround Available**: [Yes/No - describe if available]
  - [If yes, describe the workaround]

### System Impact

- **System Availability**: [Does this cause downtime or service degradation]
- **Data Integrity**: [Is data corrupted, lost, or inconsistent]
- **Performance**: [Does this cause slowdowns or resource exhaustion]
- **Cascading Effects**: [Does this trigger other failures or issues]

### Business Impact

- **Revenue Impact**: [Lost sales, blocked transactions, refunds needed]
- **Compliance Impact**: [Regulatory violations, security concerns]
- **Reputation Impact**: [User complaints, negative reviews, trust issues]
- **Operational Impact**: [Support load, manual workarounds needed]

### Priority Justification

**Why [P0/Critical, P1/High, P2/Medium, P3/Low]**:
- [Explanation of why this priority level is appropriate]
- [Comparison to priority definitions for this project]

---

## Steps to Reproduce

[Detailed, numbered steps that consistently reproduce the bug]

### Prerequisites

[Any setup, configuration, or state needed before reproduction]

- [Prerequisite 1]
- [Prerequisite 2]

### Reproduction Steps

1. **[Action 1]**: [Detailed description including UI elements, API calls, or commands]
   ```[language]
   # Code or command if applicable
   [example]
   ```

2. **[Action 2]**: [Detailed description]
   - [Sub-detail if needed]
   - [Expected intermediate state]

3. **[Action 3]**: [Detailed description]

4. **[Action 4]**: [Continue until bug is observed]

### Expected Behavior

[What should happen if the system worked correctly]

- Expected result: [Specific, measurable outcome]
- Expected state: [System state after actions]
- Expected output: [Messages, data, UI state]

### Actual Behavior

[What actually happens - the bug manifestation]

- Actual result: [What went wrong]
- Error messages:
  ```
  [Exact error message text]
  [Stack trace if applicable]
  ```
- Unexpected state: [How system state is incorrect]

### Reproduction Rate

- **Consistency**: [Always/Sometimes/Rarely]
- **Success rate**: [X out of Y attempts]
- **Conditions affecting reproduction**: [Timing, data state, concurrency, etc.]

---

## Environment

[Detailed environment information where bug occurs]

### System Environment

- **OS**: [Windows 11/macOS 14/Ubuntu 22.04/etc.]
- **OS Version**: [Specific version, build number]
- **Architecture**: [x64/ARM/etc.]

### Software Environment

- **Application Version**: [Specific version where bug occurs]
- **Python Version**: [Python 3.11.5]
- **Node Version**: [If applicable]
- **Package Versions**: [Key dependency versions]
  ```
  package1==1.2.3
  package2==4.5.6
  ```

### Runtime Environment

- **Deployment**: [Local dev/Staging/Production]
- **Configuration**: [Relevant config settings]
- **Environment Variables**: [Relevant env vars]

### Browser (if web app)

- **Browser**: [Chrome 120 / Firefox 121 / Safari 17]
- **Device**: [Desktop / Mobile / Tablet]
- **Screen Size**: [If layout-related]

### Data Environment

- **Data Volume**: [How much data involved]
- **Data State**: [Specific data conditions that trigger bug]
- **Test Data**: [Sample data that reproduces issue]

---

## Root Cause Analysis (optional)

[Deep investigation into why this bug occurs - fill in after investigation]

### Investigation Findings

[What was discovered during debugging]

- **Code Location**: [File(s) and line number(s) where bug originates]
  - `[path/to/file.py:123]`: [Description]

- **Logic Error**: [Flawed algorithm, incorrect assumption, off-by-one, etc.]

- **Missing Validation**: [Input validation, boundary checks, null checks missing]

- **Race Condition**: [Concurrency issues, timing dependencies]

- **Integration Issue**: [API contract mismatch, dependency behavior change]

### Technical Details

[Technical explanation of the root cause]

```[language]
# Problematic code
[code snippet showing the bug]
```

**Problem**: [Explanation of what's wrong with this code]

**Why This Happens**: [Circumstances that trigger the bug]

### Historical Context

- **When Introduced**: [Which version/commit introduced this bug]
- **Related Changes**: [Recent changes that may have caused this]
- **Regression**: [Is this a regression of previously working functionality]

---

## Solution

[Proposed fix for the bug]

### Fix Strategy

[High-level approach to fixing the bug]

- **Approach**: [What needs to change - code fix, config change, data migration]
- **Complexity**: [Simple/Medium/Complex]
- **Risk**: [Low/Medium/High risk of side effects]

### Code Changes

[Specific code changes needed]

```[language]
# Fixed code
[code snippet showing the fix]
```

**Explanation**: [Why this fixes the bug]

### Implementation Steps

1. **[Step 1]**: [First change to make]
2. **[Step 2]**: [Second change to make]
3. **[Step 3]**: [Additional steps]

### Alternative Solutions

[Other approaches considered and why not chosen]

- **Alternative 1**: [Description]
  - **Pros**: [Advantages]
  - **Cons**: [Disadvantages]
  - **Why Not Chosen**: [Reason]

### Rollback Plan

[How to quickly revert if fix causes issues]

1. [Rollback step 1]
2. [Rollback step 2]

---

## Testing & Verification (optional)

[Comprehensive testing to ensure bug is fixed]

### Bug Reproduction Verification

- [ ] Confirm bug is reproducible in current version
- [ ] Document reproduction rate before fix
- [ ] Capture screenshots/logs of bug manifestation

### Fix Verification

- [ ] Apply fix to test environment
- [ ] Verify original reproduction steps no longer trigger bug
- [ ] Confirm expected behavior now occurs
- [ ] Test fix multiple times (10+ attempts for intermittent bugs)

### Regression Testing

- [ ] All existing unit tests pass
- [ ] All existing integration tests pass
- [ ] Manual testing of related functionality
- [ ] No new bugs introduced by fix

### Edge Case Testing

[Test boundary conditions and variations]

- [ ] Test with minimum values
- [ ] Test with maximum values
- [ ] Test with null/empty data
- [ ] Test with invalid data
- [ ] Test under load/stress conditions

### Integration Testing

- [ ] Test interactions with dependencies
- [ ] Test API contracts still valid
- [ ] Test UI workflows still function
- [ ] Test data consistency maintained

### Performance Verification

- [ ] Performance not degraded by fix
- [ ] Resource usage unchanged
- [ ] No memory leaks introduced

---

## Regression Prevention (optional)

[Ensure this bug doesn't come back]

### Automated Tests Added

- [ ] **Unit Test**: [Test file and function name]
  - Tests: [What it tests]
  - Coverage: [Code paths covered]

- [ ] **Integration Test**: [Test file and function name]
  - Scenario: [What scenario it verifies]
  - Assertions: [What it checks]

### Test Coverage

- **Before Fix**: [Coverage % of affected code]
- **After Fix**: [Coverage % with new tests]
- **Critical Paths**: [All critical paths now covered]

### Code Quality Improvements

- [ ] Add input validation where missing
- [ ] Add boundary checks
- [ ] Add error handling
- [ ] Add logging for debugging
- [ ] Add type hints/annotations

### Documentation Updates

- [ ] Update inline code comments
- [ ] Document gotchas or edge cases
- [ ] Update API documentation if contracts changed
- [ ] Update troubleshooting guide

### Monitoring & Alerts

- [ ] Add metrics to track related behavior
- [ ] Add alerts for related errors
- [ ] Add logging for related code paths

---

## Prerequisites (optional)

[Requirements before starting bug fix]

**⚠️ DO NOT START THIS CARD UNLESS:**

- [ ] [Bug is reproducible - can consistently recreate issue]
- [ ] [Environment access available for testing]
- [ ] [Understanding of affected code area]
- [ ] [Approval to deploy fix (for production bugs)]

**Why**: [Bug fixes should be based on reproducible issues with understood root causes]

### Required Access

- [ ] Access to affected environment
- [ ] Access to logs and monitoring
- [ ] Ability to deploy fixes
- [ ] Test data or production replica

### Required Understanding

- [ ] Codebase familiarity in affected area
- [ ] Understanding of system architecture
- [ ] Knowledge of related dependencies

---

## Related Issues (optional)

[Connections to other bugs, features, or issues]

### Duplicate Bugs

**Duplicates**: [Issue IDs] - [How they're related]

[List any duplicate bug reports]

### Related Bugs

**Related**: [Bug ID] - [How it's related - same root cause, similar symptoms]

[List bugs that might share root cause or be affected by this fix]

### Blocking Issues

**Blocks**: [Issue ID] - [What this bug prevents]

[Features or work blocked by this bug]

### Caused By

**Caused By**: [Feature Card ID or Commit] - [What introduced this bug]

[Link to feature or change that introduced this regression]

### Cross-References

- **User Reports**: [Links to support tickets or user feedback]
- **Monitoring Alerts**: [Links to error tracking or APM alerts]
- **Code**: [Links to relevant code files or commits]
- **Documentation**: [Links to related documentation]

---

## Notes (optional)

[Additional context, investigation notes, or important details]

### Investigation Notes

[Chronological notes from debugging investigation]

- [Date/Time]: [Observation or finding]
- [Date/Time]: [Hypothesis tested]
- [Date/Time]: [Discovery]

### Workarounds

[Temporary workarounds while waiting for fix]

- **Workaround 1**: [Description]
  - **Steps**: [How to apply workaround]
  - **Limitations**: [What this doesn't fix]

### Communication

- **Users Notified**: [Yes/No - how users were informed]
- **Status Page**: [If public status page updated]
- **Support Team**: [If support team briefed]

### Lessons Learned

[What we can learn from this bug]

- [Lesson 1 - how to prevent similar bugs]
- [Lesson 2 - process improvements]
- [Lesson 3 - testing gaps to address]

### Resources

[Helpful resources used during investigation]

- [Link 1]: [Description]
- [Link 2]: [Description]

---

## Progress Notes (optional)

[Track debugging and fix progress session by session]

**Session [Date] ([Your Name]):**

🔍 **Investigation:**
- [What was investigated]
- [Tools or methods used]
- [Findings]

✅ **Progress:**
- [Reproduction confirmed/improved]
- [Root cause identified/narrowed down]
- [Fix implemented/tested]

⚠️ **Blockers:**
- [Issue]: [Status/resolution]

❓ **Open Questions:**
- [Question]: [Answer once resolved]

📋 **Next Steps:**
1. [Next investigation task]
2. [Next implementation task]
3. [Next testing task]

**Technical Notes:**
[Important technical details discovered this session]

---

## Additional Notes (optional)

**📝 FREEFORM SECTION - Add anything you need from this point onward!**

This template provides the minimum structure for bug cards. Feel free to add:
- Security impact analysis and CVE information
- Data recovery procedures
- Customer communication plans
- Incident reports and postmortems
- Hotfix process documentation
- A/B test results or experimental data
- Or any other content your team needs!

No validation is enforced below this line - organize additional information however works best for your workflow.
