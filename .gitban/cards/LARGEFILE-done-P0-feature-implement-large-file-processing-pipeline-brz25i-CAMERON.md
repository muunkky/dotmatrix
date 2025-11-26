# Implement Large File Processing Pipeline

## Description
Based on spike w804xa findings (see ADR-001), the current implementation already handles 10MB+ files efficiently. This card implements user experience improvements:
1. Size warnings for convex detection on very large images (>20 MP)
2. Progress reporting for long operations
3. Large file integration tests

**Key Finding**: No tiling/chunking needed - Hough handles 64+ MP in <2s, Convex handles 20 MP in <30s.

## Dependencies
- ✅ Spike w804xa completed - see ADR-001

## Acceptance Criteria
- [x] Process 10MB images without memory errors (VERIFIED in spike)
- [x] Processing time < 30 seconds for 10MB images (4-9 MP) (VERIFIED in spike)
- [x] Memory usage under 2GB (VERIFIED: ~200-400 MB for 16 MP)
- [x] Warning displayed for convex detection on images >20 MP
- [x] Progress feedback for operations >5 seconds
- [x] Integration tests with large synthetic images

## Implementation Tasks
- [x] Add `get_image_megapixels()` helper function
- [x] Add size warning in CLI for --convex-edge with >20 MP images
- [x] Add progress indicator for convex detection (simple stderr output)
- [x] Add integration tests for large file handling (10 MP, 20 MP)
- [x] Update README with performance guidance

## Test Plan
- [x] Test size warning appears for large images with --convex-edge
- [x] Test progress output for long convex operations
- [x] Test large file processing (10 MP) completes successfully
- [x] Test very large file processing (20 MP) with warning

## Notes
- Per ADR-001: Use megapixels as the metric, not file size (MB)
- Hough: ~5 MB memory per MP, <0.02s per MP
- Convex: ~20 MB memory per MP, ~2s per MP
