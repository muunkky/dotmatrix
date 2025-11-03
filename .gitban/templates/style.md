
## Style Goal

[What code style/formatting issues need to be addressed and why - REQUIRED]

**Value**: [How this improves code quality, readability, and maintainability]

**Estimated Effort**: [Time estimate - e.g., 1-2 hours, half day]

---

## Scope

[Specific files, modules, or areas to improve]

### Files/Modules Affected

- [ ] **[Module/Package 1]**: [Style issues to fix]
  - `[file1.py]`: [Issues]
  - `[file2.py]`: [Issues]

- [ ] **[Module/Package 2]**: [Style issues to fix]
  - `[file3.py]`: [Issues]
  - `[file4.py]`: [Issues]

### Style Issues to Address

- [ ] **Formatting**: [Inconsistent spacing, line length, etc.]
- [ ] **Naming**: [Inconsistent naming conventions]
- [ ] **Imports**: [Import organization, unused imports]
- [ ] **Documentation**: [Missing/inconsistent docstrings]
- [ ] **Comments**: [Outdated/unclear comments]
- [ ] **Other**: [Other style issues]

---

## Style Standards

[Project style guidelines and tools]

### Code Formatter

- **Tool**: [ruff / black / prettier / gofmt / etc.]
- **Version**: [Specific version]
- **Configuration**: `[config file location]`
- **Command**: `[command to run formatter]`

### Linter

- **Tool**: [ruff / eslint / pylint / golangci-lint / etc.]
- **Configuration**: `[config file location]`
- **Command**: `[command to run linter]`

### Style Guide

- **Guide**: [PEP 8 / Google Style / Airbnb / Standard / etc.]
- **Documentation**: [Link to style guide]

### Project Conventions

[Project-specific style rules]

- **Naming**: [Conventions for variables, functions, classes]
- **Imports**: [Import order and organization]
- **Documentation**: [Docstring format and requirements]
- **Comments**: [When and how to comment]

---

## Changes

[Specific style improvements to make]

### Formatting

- [ ] **Fix line length**: [Shorten lines > 120 chars]
- [ ] **Fix spacing**: [Consistent whitespace]
- [ ] **Fix indentation**: [Consistent 4-space indentation]
- [ ] **Fix blank lines**: [Consistent blank line usage]

### Naming Conventions

- [ ] **Variables**: [snake_case for variables]
- [ ] **Functions**: [snake_case for functions]
- [ ] **Classes**: [PascalCase for classes]
- [ ] **Constants**: [UPPER_CASE for constants]

### Import Organization

- [ ] **Order imports**: [Standard lib, third-party, local]
- [ ] **Remove unused**: [Remove unused imports]
- [ ] **Group imports**: [Group related imports]
- [ ] **Absolute imports**: [Use absolute imports]

### Documentation

- [ ] **Add docstrings**: [Add missing docstrings]
- [ ] **Fix docstring format**: [Consistent format]
- [ ] **Update outdated docs**: [Update stale documentation]
- [ ] **Add type hints**: [Add missing type annotations]

### Comment Cleanup

- [ ] **Remove commented code**: [Delete commented-out code]
- [ ] **Update outdated comments**: [Fix misleading comments]
- [ ] **Add clarifying comments**: [Explain complex logic]

---

## Verification

[How to verify style improvements are correct]

### Style Check Commands

```bash
# Run formatter
[formatter command]

# Run linter
[linter command]

# Run type checker (if applicable)
[type checker command]
```

### Pre-Commit Hooks

- [ ] Configure pre-commit hooks
- [ ] Add formatters to pre-commit
- [ ] Add linters to pre-commit
- [ ] Test hooks work correctly

### CI Integration

- [ ] Add style checks to CI
- [ ] Ensure CI fails on style violations
- [ ] Add badge showing style status

### Verification Checklist

- [ ] All style checks pass
- [ ] Code still functions identically
- [ ] No behavioral changes
- [ ] All tests still pass
- [ ] Pre-commit hooks configured
- [ ] CI pipeline includes style checks

---

## Prerequisites

[Requirements before fixing style]

**⚠️ DO NOT START THIS CARD UNLESS:**

- [ ] [Style standards are documented]
- [ ] [Formatter/linter tools are configured]
- [ ] [All tests pass (style changes shouldn't break tests)]
- [ ] [Team agrees on style standards]

**Why**: [Style changes should be mechanical, not introduce bugs]

### Required Tools

- [ ] Code formatter installed and configured
- [ ] Linter installed and configured
- [ ] Type checker (if applicable)

### Required Coordination

- [ ] Team agreement on style standards
- [ ] Coordination to avoid merge conflicts
- [ ] Decision on auto-fix vs manual fixes

---

## Related Cards

[Connections to other code quality work]

### Enables

**Enables**: [Card ID] - [What consistent style enables]

[Work made easier by consistent style]

### Related

**Related**: [Card ID] - [Related cleanup or quality work]

[Other code quality improvements]

---

## Notes

[Additional context or style considerations]

### Style Philosophy

[Project style principles]

- [Principle 1: e.g., "Consistency over personal preference"]
- [Principle 2: e.g., "Automate style enforcement"]

### Migration Strategy

[How to apply style changes]

- **Approach**: [Big bang / Incremental / Per-module]
- **Git History**: [How to preserve git blame]
- **Review**: [How to review mechanical changes]

### Auto-Fix vs Manual

[What can be automated vs needs manual attention]

- **Auto-Fix**: [Formatting, import sorting]
- **Manual**: [Naming changes, comment updates]

### Resources

[Helpful style resources]

- [Style guide]: [Link]
- [Formatter docs]: [Link]
- [Linter docs]: [Link]

---

## Progress Notes

[Track style improvements session by session]

**Session [YYYY-MM-DD] ([Your Name]):**

✅ **Completed:**
- [Module/files styled]
- [Issues fixed]

📊 **Metrics:**
- Files updated: [Count]
- Lines changed: [Count]
- Violations fixed: [Count]

🔄 **In Progress:**
- [Current module]

⚠️ **Issues:**
- [Automated issue]: [Manual fix needed]

📋 **Next Session:**
1. [Next module to style]
2. [Manual fixes needed]

**Style Notes:**
[Observations about code quality or patterns]

---

<!--
EXTENSION POINTS:

## Code Review Guidelines
[Style points to check in code review]

## Editor Configuration
[EditorConfig, IDE settings for consistency]

## Migration from Old Style
[How to migrate legacy code gradually]

## Style Documentation
[Project style guide documentation]

Add project-specific sections as needed!
-->
## Additional Notes (optional)

**📝 FREEFORM SECTION - Add anything you need from this point onward!**

Feel free to add any custom sections, notes, or documentation specific to your project below this line. No validation is enforced here - organize additional information however works best for your workflow.
