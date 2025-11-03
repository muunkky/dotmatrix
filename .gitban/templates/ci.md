
## CI/CD Goal

[What needs to be improved in CI/CD pipeline and why - REQUIRED]

**Value**: [How this improves deployment speed, reliability, or developer experience]

**Estimated Effort**: [Time estimate - e.g., 2-4 hours, 1 day]

---

## Current State

[Description of current CI/CD setup and limitations]

### Current Pipeline

**CI Platform**: [GitHub Actions / GitLab CI / Jenkins / CircleCI / etc.]

**Configuration Files**:
- `[config file]`: [Current state]

**Current Stages**:
1. [Stage 1]: [What it does]
2. [Stage 2]: [What it does]
3. [Stage 3]: [What it does]

### Current Issues

1. **[Issue 1]**: [Problem with current pipeline]
   - **Impact**: [How this hurts team]
   - **Frequency**: [How often]

2. **[Issue 2]**: [Problem]
   - **Impact**: [How this hurts]
   - **Frequency**: [How often]

### Current Metrics

- **Pipeline Duration**: [X minutes]
- **Success Rate**: [X%]
- **Resource Usage**: [CPU/memory/cost]
- **Deployment Frequency**: [X times per day/week]

---

## Proposed Changes

[Specific CI/CD improvements]

- [ ] **Change 1**: [Description]
  - **Benefit**: [How this improves pipeline]
  - **Effort**: [Small/Medium/Large]

- [ ] **Change 2**: [Description]
  - **Benefit**: [How this improves pipeline]
  - **Effort**: [Small/Medium/Large]

- [ ] **Change 3**: [Description]
  - **Benefit**: [How this improves pipeline]
  - **Effort**: [Small/Medium/Large]

### Target Metrics

- **Pipeline Duration**: [Target time]
- **Success Rate**: [Target %]
- **Resource Usage**: [Target efficiency]
- **Deployment Frequency**: [Target frequency]

---

## Benefits

[How CI/CD improvements help the team]

### Developer Experience

- **Faster Feedback**: [How much faster]
- **Reliability**: [Fewer spurious failures]
- **Visibility**: [Better pipeline insights]
- **Debugging**: [Easier to diagnose failures]

### Team Benefits

- **Deployment Speed**: [Deploy X times faster]
- **Confidence**: [More reliable deploys]
- **Automation**: [Less manual work]
- **Cost**: [Reduced CI/CD costs]

---

## Implementation

[How to implement CI/CD changes]

### CI Platform

- **Platform**: [GitHub Actions / GitLab CI / Jenkins]
- **Configuration Files**: [Paths to config files]
- **Runners**: [Self-hosted / cloud runners]

### Pipeline Stages

[New or updated pipeline stages]

1. **[Stage 1]**:
   - **Purpose**: [What this stage does]
   - **Commands**: `[commands to run]`
   - **Duration**: [Expected time]

2. **[Stage 2]**:
   - **Purpose**: [What this stage does]
   - **Commands**: `[commands to run]`
   - **Duration**: [Expected time]

### Configuration Example

```yaml
# CI configuration example
[configuration code]
```

### Secrets & Credentials

[Secrets needed for CI/CD]

- [ ] [Secret 1]: [Purpose and how to set]
- [ ] [Secret 2]: [Purpose and how to set]

---

## Testing

[Verifying CI/CD changes work correctly]

### Pipeline Testing

- [ ] **Local Testing**:
  - [ ] Test configuration syntax
  - [ ] Test scripts locally
  - [ ] Verify all commands work

- [ ] **Branch Testing**:
  - [ ] Test pipeline on feature branch
  - [ ] Verify all stages execute
  - [ ] Check timing and resource usage

- [ ] **Integration Testing**:
  - [ ] Test with real deployments
  - [ ] Verify secrets/credentials work
  - [ ] Test rollback procedures

### Validation

- [ ] All pipeline stages succeed
- [ ] Deployment works correctly
- [ ] Notifications/alerts working
- [ ] Documentation updated

---

## Prerequisites

[Requirements before changing CI/CD]

**⚠️ DO NOT START THIS CARD UNLESS:**

- [ ] [Understanding of current pipeline]
- [ ] [Access to CI/CD configuration]
- [ ] [Ability to test pipeline changes]
- [ ] [Approval for infrastructure changes]

**Why**: [CI/CD changes affect entire team - needs coordination]

### Required Access

- [ ] CI/CD platform admin access
- [ ] Secrets management access
- [ ] Deployment environment access

### Required Knowledge

- [ ] CI/CD platform syntax
- [ ] Deployment procedures
- [ ] Security best practices

---

## Related Cards

[Connections to other infrastructure work]

### Depends On

**Depends on**: [Card ID] - [Dependency description]

[Prerequisites for CI/CD changes]

### Blocks

**Blocks**: [Card ID] - [What this unblocks]

[Work waiting for CI/CD improvements]

### Related

**Related**: [Card ID] - [Relationship]

[Related automation or infrastructure work]

---

## Notes

[Additional context or CI/CD considerations]

### CI/CD Best Practices

[Project CI/CD principles]

- [Practice 1]
- [Practice 2]

### Rollback Plan

[How to revert if issues arise]

1. [Rollback step 1]
2. [Rollback step 2]

### Resources

[Helpful CI/CD documentation]

- [Platform docs]: [Link]
- [Example workflows]: [Link]

---

## Progress Notes

[Track CI/CD improvements session by session]

**Session [YYYY-MM-DD] ([Your Name]):**

✅ **Completed:**
- [CI/CD change made]
- [Testing completed]

🔄 **In Progress:**
- [Current work]

⚠️ **Issues:**
- [Problem]: [Resolution]

📋 **Next Session:**
1. [Next task]
2. [Testing needed]

**CI/CD Notes:**
[Observations about pipeline performance]

---

<!--
EXTENSION POINTS:

## Multi-Environment Deployment
[Different pipelines for dev/staging/prod]

## Matrix Builds
[Testing across multiple platforms/versions]

## Caching Strategy
[Build caching for faster pipelines]

## Security Scanning
[SAST, dependency scanning, container scanning]

Add project-specific sections as needed!
-->
## Additional Notes (optional)

**📝 FREEFORM SECTION - Add anything you need from this point onward!**

Feel free to add any custom sections, notes, or documentation specific to your project below this line. No validation is enforced here - organize additional information however works best for your workflow.
