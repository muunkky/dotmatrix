## Description

Verify all WORKFLOW sprint features work together end-to-end and update documentation.

**Value**: Ensures the sprint delivers a cohesive user experience and is properly documented.

---

## Acceptance Criteria

- [ ] End-to-end workflow test passes: create runs, list, show, replay
- [ ] README updated with workflow section
- [ ] CHANGELOG updated with all new features
- [ ] All sprint cards completed
- [ ] No regressions in existing functionality

---

## Implementation Plan

1. **E2E test script**: Create test that exercises full workflow
2. **Documentation**: Update README with workflow examples
3. **CHANGELOG**: Add all sprint features under [Unreleased]
4. **Regression check**: Run existing test suite

---

## Checklist

- [ ] All WORKFLOW sprint cards completed
- [ ] E2E workflow test created and passing
- [ ] README.md workflow section added
- [ ] CHANGELOG.md updated
- [ ] `pytest` passes with no regressions
- [ ] Git commit and tag sprint completion
