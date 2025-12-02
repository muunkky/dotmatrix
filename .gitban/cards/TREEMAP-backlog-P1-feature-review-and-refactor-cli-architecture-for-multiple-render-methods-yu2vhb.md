# Review And Refactor CLI Architecture For Multiple Render Methods

**Type:** Refactor
**Priority:** P1
**Status:** backlog
**Sprint:** TREEMAP
**Card ID:** yu2vhb

## Description
As we add more render methods and color modes, the CLI is getting cluttered. Review the architecture and refactor for cleaner separation of concerns.

## Current State
- --render-method (bullseye, block, treemap)
- --color-mode (full, cmyk) [proposed]
- --segment-height (block renderer only)
- Multiple palettes, modes, etc.

## Concerns
- Options proliferating without clear organization
- Some options only apply to certain modes
- Help text getting long and confusing
- Code has conditional logic spread throughout

## Acceptance Criteria
- [ ] CLI options logically grouped
- [ ] Mode-specific options clearly documented
- [ ] Help text organized by feature area
- [ ] Code has clean separation of concerns
- [ ] No breaking changes to existing CLI interface

## Implementation Tasks
- [ ] Audit current CLI options and groupings
- [ ] Design improved option organization
- [ ] Refactor cli.py for cleaner structure
- [ ] Update help text with clear groupings
- [ ] Ensure backward compatibility
- [ ] Update CLI documentation

## Test Plan
- [ ] All existing CLI tests pass
- [ ] New organization doesn't break workflows
- [ ] Help text is readable and clear

## Dependencies
- xkgrd1 (treemap) - wait until new methods are implemented
- 2j70hj (CMYK mode) - wait until new options exist

## Notes
User said: "Your CLI architecture probably needs to be looked at if we're adding all these methods"
