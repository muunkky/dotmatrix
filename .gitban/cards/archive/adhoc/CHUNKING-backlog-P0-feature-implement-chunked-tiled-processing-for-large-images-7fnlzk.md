# Implement Chunked/Tiled Processing for Large Images

## Problem
Current implementation processes entire image at once. For images >25MP with thousands of circles (like detailed halftones), this causes:
- O(n²) deduplication time explosion
- Memory pressure from holding all circles
- No progress feedback
- Potential timeouts

## Proposed Solution
Split large images into overlapping tiles, process each independently, merge results.

## Acceptance Criteria
- [ ] Process images in configurable tile sizes (e.g., 2000x2000 px)
- [ ] Overlap tiles by max_radius to catch boundary circles
- [ ] Merge results and deduplicate only at tile boundaries
- [ ] Show progress per tile (e.g., "Processing tile 3/16...")
- [ ] Memory usage bounded regardless of image size
- [ ] Final output identical to full-image processing

## Implementation Approach
1. Calculate tile grid based on image size and tile_size param
2. For each tile:
   - Extract tile with overlap margin
   - Run detection on tile
   - Offset circle coordinates to global space
   - Collect results
3. Deduplicate only circles near tile boundaries
4. Return merged results

## Technical Notes
- Overlap = max_radius to ensure circles aren't split
- Only dedupe circles within overlap zones (not all circles)
- This changes O(n²) global dedupe to O(k²) local dedupe where k << n

## Test Plan
- [ ] Test on 38MP halftone image
- [ ] Verify boundary circles detected correctly
- [ ] Compare output to non-chunked (on smaller image)
- [ ] Benchmark memory usage
