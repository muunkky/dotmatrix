# Implement Treemap-Style Block Layout For Proportional Rectangle Filling

**Type:** Feature
**Priority:** P1
**Status:** backlog
**Sprint:** TREEMAP
**Card ID:** xkgrd1

## Description
Replace the current stacked horizontal bar approach with a treemap-style layout that fills a rectangle proportionally with color areas. Similar to how WinDirStat visualizes disk space - each color gets a sub-rectangle proportional to its pixel count.

## Background
Treemap algorithms subdivide rectangles recursively:
- **Slice-and-dice**: Alternates H/V splits, simple but poor aspect ratios
- **Squarified**: Optimizes for squares, better visual but complex
- **Strip**: Good balance of simplicity and aspect ratios

For 4-7 colors, slice-and-dice should work well.

## Acceptance Criteria
- [x] Clusters render as filled rectangles (no overflow)
- [x] Each color gets proportional area (pixel_count / total)
- [x] Colors don't overlap (clean subdivision)
- [x] Total area approximately equals sum of pixel counts
- [x] Visual appearance is "treemap-like" (nested rectangles)

## Implementation Tasks
- [x] Create treemap_renderer.py module
- [x] Implement slice-and-dice subdivision algorithm
- [x] Calculate sub-rectangles for each color proportionally
- [x] Add --render-method=treemap CLI option
- [x] Write unit tests for subdivision algorithm
- [x] Write integration test comparing to block renderer

## Test Plan
- [x] Unit test: subdivision produces correct proportions
- [x] Unit test: no rectangles overlap
- [x] Unit test: all colors rendered
- [x] Integration test: CLI produces valid output

## Dependencies
- zzjf16 (overflow fix) - bounds constraints needed first

## Notes
User explicitly requested "like WinDirStat" visualization style.
