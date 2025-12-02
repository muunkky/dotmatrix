# Add Absolute CMYK Mode Ignoring Color Overlap

**Type:** Feature
**Priority:** P1
**Status:** backlog
**Sprint:** TREEMAP
**Card ID:** 2j70hj

## Description
Add a simpler output mode that uses only absolute C, M, Y, K values without detecting overlap colors (red, green, blue). This is useful for halftone separation printing where each CMYK channel is printed separately and overlaps naturally during printing.

## Current vs Proposed

**Current (7 colors):**
- Detects C, M, Y, K, R (M+Y), G (C+Y), B (C+M)
- Complex, accounts for overlap in digital image

**Proposed (4 colors):**
- Just C, M, Y, K absolute values
- Simpler, assumes physical printing will create overlaps
- Better for actual halftone separation workflow

## Acceptance Criteria
- [x] New --color-mode=cmyk option (vs default --color-mode=full)
- [x] CMYK mode outputs only 4 color channels
- [x] Cluster counting works with 4-color mode
- [x] Treemap/block renderer handles 4-color clusters
- [x] Output files: cyan.png, magenta.png, yellow.png, black.png

## Implementation Tasks
- [x] Add --color-mode CLI option (full | cmyk)
- [x] Update cluster_pixel_counter for CMYK-only mode
- [x] Update block_renderer LAYER_ORDER for 4 colors
- [x] Update treemap_renderer for 4 colors
- [x] Write tests for CMYK mode
- [x] Update manifest to record color_mode

## Test Plan
- [x] Unit test: CMYK counting ignores overlaps
- [x] Unit test: renderer handles 4-color clusters
- [x] Integration test: CLI produces correct output files

## Dependencies
- None (independent of overflow/treemap work)

## Notes
User said: "we might be able to cheat a little by just using the absolute CMY values and ignoring the overlap"
