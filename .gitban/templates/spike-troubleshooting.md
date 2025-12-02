[When to use this template: Use for systematic troubleshooting of production incidents, complex bugs, or system issues requiring investigation. This is a comprehensive template - skip optional sections for straightforward problems. Best for P0/P1 incidents.]
# Troubleshooting: [Brief Problem Description]

**Card Type**: Chore - Troubleshooting
**Status**: [investigation | solution-found | resolved | escalated]
**Priority**: [P0 | P1 | P2]
**Date Started**: YYYY-MM-DD
**Owner**: [Team/Person]

## Problem Statement

### Symptoms Observed
- **What is broken/not working?**
- **Error messages or unexpected behavior**
- **Impact**: [systems affected, data loss, downtime, etc.]
- **Urgency**: [Why this needs immediate attention]

### Environment Context
- **System/Service**:
- **Version**:
- **Configuration**:
- **Recent Changes**: [deployments, config updates, etc.]

---

## Investigation Progress

### Pre-Investigation Checklist
- [ ] Problem statement clearly defined
- [ ] Error messages captured verbatim
- [ ] Recent changes reviewed (git log, deployment logs)
- [ ] Similar past issues searched (gitban cards, docs, git history)
- [ ] Monitoring/logs checked for related errors
- [ ] Impact scope assessed (how many users/systems affected)

### Research Performed

#### Documentation Review
- [ ] Official product documentation consulted
- [ ] Internal documentation/runbooks checked
- [ ] Architecture diagrams reviewed
- [ ] Related ADRs/design docs examined

**Key Documents Referenced**:
- [doc-name](path/to/doc) - Brief relevance description
- [doc-name](path/to/doc) - Brief relevance description

#### Knowledge Base Search
- [ ] Google search performed
- [ ] Stack Overflow / GitHub issues searched
- [ ] Context7 / library documentation consulted
- [ ] Team knowledge / Slack history checked

** Google / Web Search Terms Used**:
1. `"exact error message"` - [Results summary]
2. `component-name error-keyword` - [Results summary]
3. `[other search terms]` - [Results summary]

**Context7 Libraries Referenced**:
- `/org/library-name` - [What was learned]
- `/org/library-name` - [What was learned]


#### Related Gitban Cards:

| Card ID | Card Name | Initial Status | Description of relevance |
|---------|-----------|----------------|--------------------------|
|[card-id]| [card-name] |  [status at time of issue] | [brief description]             |


#### Related Code/Config:
- `path/to/file:line-number` - [What this code does]
- `path/to/file:line-number` - [Configuration setting]

---

## Solution Attempts

### Attempt Log

| # | Attempt Name | Hypothesis | Outcome | Status | Notes |
|---|-------------|------------|---------|--------|-------|
| 1 | [Short name] | [Why we thought this would work] | [What actually happened] | ❌ Fail | [Updated understanding] |
| 2 | [Short name] | [Why we thought this would work] | [What actually happened] | 🔄 Partial | [What worked, what didn't] |
| 3 | [Short name] | [Why we thought this would work] | [What actually happened] | ✅ Success | [Confirmation of fix] |

### Detailed Attempt Logs

#### Attempt 1: [Attempt Name]

**Hypothesis**: [Detailed explanation of why this should work]

**Root Cause Theory**: [What we believed was causing the problem]

**Steps Performed**:
1. [Exact command or action taken]
   ```bash
   # Code/commands executed
   ```
2. [Next step]
3. [Verification step]

**Results**:
- **Observed Behavior**: [What actually happened]
- **Logs/Output**:
  ```
  [Relevant log excerpts]
  ```
- **Unexpected Findings**: [Anything surprising]

**Outcome**: ❌ Failed | ✅ Success | 🔄 Partial

**Updated Hypothesis**: [How our understanding changed]

**Evidence Gathered**:
- [New information learned]
- [What we can rule out]
- [What to try next]

---

#### Attempt 2: [Attempt Name]

[Same structure as Attempt 1]

---

## Root Cause Analysis

### Confirmed Root Cause
**Summary**: [One-sentence description of the actual problem]

**Technical Explanation**:
[Detailed explanation of why the problem occurred]

**Contributing Factors**:
1. [Factor that made this possible/likely]
2. [Another contributing factor]

**Discovery Path**: [How we finally figured it out]

### Why This Wasn't Caught Earlier
- [Gap in monitoring]
- [Gap in testing]
- [Assumption that turned out wrong]

---

## Solution

### Implemented Fix

**What Was Changed**:
```bash
# Commands executed to fix
```

**Files Modified**:
- `path/to/file` - [What changed and why]
- `path/to/file` - [What changed and why]

**Deployment Steps**:
1. [How the fix was deployed]
2. [Verification performed]
3. [Rollback plan if needed]

### Verification

**Success Criteria**:
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]
- [ ] [Measurable outcome 3]

**Verification Performed**:
```bash
# Commands to verify fix
```

**Results**:
- [Metric/behavior before]: [value]
- [Metric/behavior after]: [value]
- **Status**: ✅ Verified working | ⏳ Monitoring | ❌ Still broken

---

## Follow-Up Actions

### Immediate Actions
- [ ] Monitor for recurrence over [timeframe]
- [ ] Update runbooks/documentation
- [ ] Notify affected teams/users

### Long-Term Prevention

  | Prevention Measure | Type | Priority | Owner | Status | Card/Issue |
  |-------------------|------|----------|-------|--------|------------|
  | Add monitoring/alerting for early detection | Monitoring | P1 | [OWNER] | ⬜ Todo / 🔄 In Progress / ✅ Done | [Link to card] |
  | Improve validation/error handling | Code Quality | P1 | [OWNER] | ⬜ Todo / 🔄 In Progress / ✅ Done | [Link to card] |
  | Address underlying architectural issues | Architecture | P2 | [OWNER] | ⬜ Todo / 🔄 In Progress / ✅ Done | [Link to card] |
  | Update code review checklist | Process | P2 | [OWNER] | ⬜ Todo / 🔄 In Progress / ✅ Done | [Link to card] |

**Preventive Work Items Created**:
- `[card-id]` - [Brief description]
- `[card-id]` - [Brief description]

  ### Documentation Updates

  | Document Type | Location | Update Needed | Status | Notes |
  |--------------|----------|---------------|--------|-------|
  | Code comments | [file:line] | [What to document] | ⬜ Todo / 🔄 In Progress / ✅ Done | [Additional context] |
  | API docs | [path/to/doc] | [What changed] | ⬜ Todo / 🔄 In Progress / ✅ Done | [Additional context] |
  | Troubleshooting guide | [path/to/doc] | [Add this case] | ⬜ Todo / 🔄 In Progress / ✅ Done | [Additional context] |
  | Runbook | [path/to/doc] | [Update procedure] | ⬜ Todo / 🔄 In Progress / ✅ Done | [Additional context] |

---

## Lessons Learned

### What Worked Well
- [Effective troubleshooting technique used]
- [Tool/resource that was helpful]
- [Good decision made during investigation]

### What Could Be Improved
- [Wasted time on wrong path because...]
- [Could have found answer faster if...]
- [Gap in our understanding of...]

### Key Takeaways
1. [Important lesson for future troubleshooting]
2. [Insight about system behavior]
3. [Process improvement opportunity]

---

## Timeline

| Time (UTC) | Event | Actor | Outcome |
|------------|-------|-------|---------|
| YYYY-MM-DD HH:MM | Problem first observed | [Person/System] | [Status] |
| YYYY-MM-DD HH:MM | Investigation started | [Person] | - |
| YYYY-MM-DD HH:MM | [Milestone event] | [Person] | [Outcome] |
| YYYY-MM-DD HH:MM | Root cause identified | [Person] | [Finding] |
| YYYY-MM-DD HH:MM | Fix deployed | [Person] | [Status] |
| YYYY-MM-DD HH:MM | Fix verified | [Person] | ✅ Resolved |

---

## Appendices

### Appendix A: Full Error Logs
```
[Complete error logs, stack traces, etc.]
```

### Appendix B: System State Snapshots
```bash
# Commands used to capture system state
$ command output
```

---

**Resolution Status**: [✅ Resolved | ⏳ Monitoring | 🔄 Ongoing | ❌ Escalated]
**Total Investigation Time**: [Hours/days]
**Total Downtime/Impact**: [Duration or scope]
**Prevention Items Created**: [Count] cards
