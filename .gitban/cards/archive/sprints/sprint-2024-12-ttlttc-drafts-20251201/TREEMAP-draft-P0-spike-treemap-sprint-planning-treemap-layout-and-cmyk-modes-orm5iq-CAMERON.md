# TREEMAP Sprint Planning - Treemap Layout and CMYK Modes

**Type:** Spike
**Priority:** P0
**Status:** todo
**Created:** 2025-11-29

## Problem Statement
The current block renderer creates vertically stacked horizontal bars that overflow cluster bounds. We need:
1. Treemap-style layout that fills rectangles proportionally (like WinDirStat)
2. Fix overflow issues where bars extend beyond cluster boundaries
3. Add absolute CMYK mode that ignores overlap colors (simpler for printing)
4. Review CLI architecture as render methods proliferate

## Time Box
- Planning: 30 minutes
- Implementation: 4 hours estimated

## Success Criteria
- [ ] Sprint cards updated with detailed acceptance criteria
- [ ] Dependencies identified and ordered
- [ ] Roadmap updated with TREEMAP milestone
- [ ] Technical approach documented

## Research Notes

### Treemap Algorithm Analysis
Treemap algorithms subdivide a rectangle into smaller rectangles proportional to values:
- **Slice-and-dice**: Alternates horizontal/vertical splits - simple but poor aspect ratios
- **Squarified**: Optimizes for square-ish rectangles - better visual but complex
- **Binary tree**: Recursive halving - balanced performance

For CMYK colors (4-7 values), slice-and-dice is sufficient given small color count.

### Sprint Card Dependencies
1. `zzjf16` (Fix overflow) - FIRST: Must fix bounds before treemap works
2. `xkgrd1` (Treemap layout) - Core feature, depends on fixed bounds
3. `2j70hj` (Absolute CMYK) - Independent, simpler color model
4. `yu2vhb` (CLI refactor) - LAST: After features stabilize

### Technical Approach

**Treemap Layout (`xkgrd1`)**:
- Input: cluster bounds (x, y, width, height) + color pixel counts
- Output: subdivided rectangles for each color
- Algorithm: Slice-and-dice with alternating H/V splits
- Ensure total area equals sum of pixel counts

**Overflow Fix (`zzjf16`)**:
- Calculate cluster bounding box from grid spacing
- Constrain all rendering to stay within bounds
- Scale if necessary to fit

**Absolute CMYK (`2j70hj`)**:
- New cluster counting mode: just C, M, Y, K (4 colors)
- Ignore overlap detection (no red, green, blue)
- Simpler output for halftone separation printing

## Decision Log
- Using slice-and-dice treemap for simplicity (4-7 colors doesn't need squarified)
- Overflow fix is prerequisite for treemap to work correctly
- CLI refactor happens last after features stabilize

## Open Questions
- Should treemap preserve aspect ratios or allow any rectangle?
- What cluster spacing/grid size to use for bounds calculation?
