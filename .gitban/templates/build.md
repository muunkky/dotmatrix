
## Build System Goal

[What needs to be improved in the build/package system and why - REQUIRED]

**Value**: [How this improves developer experience, build speed, or deployment]

**Estimated Effort**: [Time estimate - e.g., 2-4 hours, 1-2 days]

---

## Current State

[Description of current build setup and its limitations]

### Current Build Configuration

**Build Tool**: [setuptools / poetry / webpack / gradle / maven / cargo / etc.]

**Config Files**:
- `[config file 1]`: [Current state]
- `[config file 2]`: [Current state]

### Current Issues

1. **[Issue 1]**: [Problem with current build]
   - **Impact**: [How this hurts developers or deployments]
   - **Frequency**: [How often this causes problems]

2. **[Issue 2]**: [Problem]
   - **Impact**: [How this hurts]
   - **Frequency**: [How often]

### Current Metrics

- **Build Time**: [X minutes/seconds]
- **Package Size**: [X MB]
- **Dependency Count**: [X packages]
- **Build Success Rate**: [X%]

---

## Proposed Changes

[Specific improvements to build system]

- [ ] **Change 1**: [Description]
  - **Benefit**: [How this improves things]
  - **Effort**: [Small/Medium/Large]

- [ ] **Change 2**: [Description]
  - **Benefit**: [How this improves things]
  - **Effort**: [Small/Medium/Large]

- [ ] **Change 3**: [Description]
  - **Benefit**: [How this improves things]
  - **Effort**: [Small/Medium/Large]

### Target Metrics

- **Build Time**: [Target improvement]
- **Package Size**: [Target size]
- **Dependency Count**: [Target count]
- **Build Success Rate**: [Target %]

---

## Build Tools

[Tools and configuration being modified]

### Build System

- **Primary Tool**: [Tool name and version]
- **Configuration**: [Main config file]
- **Build Commands**: `[command to build]`

### Package Manager

- **Manager**: [pip / npm / yarn / maven / gradle]
- **Lock File**: [requirements.txt / package-lock.json / Cargo.lock]
- **Registry**: [PyPI / npm / Maven Central]

### Dependencies

**Current Dependencies**:
```[format]
[list of key dependencies]
```

**Proposed Changes**:
- Add: [New dependencies and why]
- Remove: [Dependencies to remove and why]
- Update: [Dependencies to upgrade and why]

### Build Scripts

**Current Scripts**:
- `[script 1]`: [What it does]
- `[script 2]`: [What it does]

**Proposed Scripts**:
- `[new script]`: [What it will do]
- `[modified script]`: [Changes needed]

---

## Impact

[How this improves the project]

### Developer Experience

- **Build Speed**: [How much faster]
- **Setup Time**: [Easier onboarding]
- **Error Messages**: [Better debugging]
- **Documentation**: [Clearer instructions]

### CI/CD Impact

- **Pipeline Speed**: [How much faster]
- **Reliability**: [Fewer build failures]
- **Resource Usage**: [CPU/memory improvements]
- **Deployment**: [Faster or more reliable deployments]

### End User Impact

- **Package Size**: [Smaller downloads]
- **Installation Speed**: [Faster installs]
- **Compatibility**: [Better platform support]

---

## Testing

[Verifying build changes work correctly]

### Build Testing

- [ ] **Local Build**:
  - [ ] Clean build succeeds
  - [ ] Incremental build works
  - [ ] Build artifacts are correct
  - [ ] No warning/error regressions

- [ ] **CI Build**:
  - [ ] All CI platforms succeed
  - [ ] Build times acceptable
  - [ ] Artifacts uploaded correctly

### Installation Testing

- [ ] **Package Installation**:
  - [ ] Install from source works
  - [ ] Install from package works
  - [ ] Dependencies install correctly
  - [ ] No conflicting dependencies

### Platform Testing

- [ ] Test on all supported platforms
- [ ] Test with different tool versions
- [ ] Test in clean environments

### Commands to Test

```bash
# Build commands
[build command 1]
[build command 2]

# Installation test
[install command]

# Verification
[verification command]
```

---

## Prerequisites

[Requirements before changing build system]

**⚠️ DO NOT START THIS CARD UNLESS:**

- [ ] [Understanding of current build process]
- [ ] [Backup of current working build]
- [ ] [Testing environment available]
- [ ] [Team coordination for build changes]

**Why**: [Build changes affect all developers - needs careful planning]

### Required Knowledge

- [ ] Familiarity with build tool being used
- [ ] Understanding of dependency management
- [ ] Knowledge of CI/CD integration

### Required Access

- [ ] Access to package registries
- [ ] CI/CD configuration access
- [ ] Ability to test builds locally

---

## Related Cards

[Connections to features or infrastructure work]

### Depends On

**Depends on**: [Card ID] - [Dependency description]

[Prerequisites for build changes]

### Blocks

**Blocks**: [Card ID] - [What this unblocks]

[Work waiting for build improvements]

### Related

**Related**: [Card ID] - [Relationship]

[Related infrastructure or tooling work]

---

## Notes

[Additional context or build considerations]

### Build Philosophy

[Project build principles]

- [Principle 1]
- [Principle 2]

### Migration Strategy

[How to transition to new build system]

1. [Migration step 1]
2. [Migration step 2]

### Rollback Plan

[How to revert if issues arise]

1. [Rollback step 1]
2. [Rollback step 2]

### Resources

[Helpful build documentation]

- [Build tool docs]: [Link]
- [Migration guide]: [Link]

---

## Progress Notes

[Track build improvements session by session]

**Session [YYYY-MM-DD] ([Your Name]):**

✅ **Completed:**
- [Build change made]
- [Testing completed]

🔄 **In Progress:**
- [Current work]

⚠️ **Issues:**
- [Problem]: [Resolution]

📋 **Next Session:**
1. [Next task]
2. [Testing needed]

**Build Notes:**
[Observations about build performance or issues]

---

<!--
EXTENSION POINTS:

## Caching Strategy
[Build caching for faster builds]

## Monorepo Support
[Multi-package build configuration]

## Cross-Compilation
[Building for multiple platforms]

## Optimization Techniques
[Specific build optimizations]

Add project-specific sections as needed!
-->
## Additional Notes (optional)

**📝 FREEFORM SECTION - Add anything you need from this point onward!**

Feel free to add any custom sections, notes, or documentation specific to your project below this line. No validation is enforced here - organize additional information however works best for your workflow.
