## Description

Integrate the proven convex edge detection approach into the dotmatrix CLI as a new detection mode for handling heavily overlapping circles.

The convex edge detection method was developed and validated to successfully extract all 16 overlapping CMYK circles from `test_dotmatrix.png`. It uses color quantization, per-color filtering, convexity defect analysis, and circle fitting on convex-only edges. This approach outperforms all existing methods (`--edge-sampling`, `--color-separation`) for overlapping circle detection.

**Value**: Enables accurate detection of overlapping circles where traditional Hough transform fails. This is the primary use case for dotmatrix - separating overlapping halftone dots.

**Target Users**: Anyone processing images with overlapping circles (halftone prints, CMYK separations, dot matrix patterns)

---

## Acceptance Criteria

- [x] New `--convex-edge` flag enables convex edge detection mode
- [x] `--palette` flag accepts comma-separated RGB values or preset names (e.g., `cmyk`, `rgb`)
- [x] Detection produces correct circle count (verified against test_dotmatrix.png: 16 circles)
- [x] Each detected circle is assigned to correct color group
- [x] Output formats (JSON, CSV) include all detected circles with colors
- [x] `--extract` flag works with convex edge mode to produce color-grouped PNGs
- [x] Performance: Detection completes in <10 seconds for 1776x1696 image
- [x] Graceful fallback to standard detection if convex edge fails

---

## Implementation Plan

### Overview

Create a new `convex_detector.py` module containing the quantization, filtering, and convex edge detection logic. Integrate via new CLI flags that activate this detection path instead of standard HoughCircles.

### Implementation Steps

1. **Create `src/dotmatrix/convex_detector.py` module**
   - `quantize_to_palette(image, palette)` - Map all pixels to nearest palette color
   - `filter_by_color(quantized, color)` - Extract single-color mask
   - `detect_circles_from_convex_edges(mask, color)` - Core algorithm using:
     - Connected components (`cv2.connectedComponentsWithStats`)
     - Convex hull and defects (`cv2.convexHull`, `cv2.convexityDefects`)
     - Circle fitting on convex points only (`cv2.HoughCircles`)
     - Best-circle-per-blob selection with scoring
     - Deduplication of similar circles

2. **Add CLI flags to `cli.py`**
   - `--convex-edge` - Enable convex edge detection mode
   - `--palette` - Color palette specification (RGB values or preset name)
   - `--quantize-output` - Optional: save quantized image for debugging

3. **Integrate with existing pipeline**
   - When `--convex-edge` is set, bypass standard `detect_circles()` 
   - Call `convex_detector.detect_all_circles(image, palette)`
   - Return results in same format as standard detection

4. **Add preset palettes**
   - `cmyk` = White, Black, Cyan (118,193,241), Magenta (217,93,155), Yellow (238,206,94)
   - `rgb` = White, Black, Red, Green, Blue
   - Custom via `--palette "255,0,0;0,255,0;0,0,255"`

5. **Update formatter and extractor**
   - Ensure `format_json()` and `format_csv()` handle convex detection results
   - Ensure `extract_circles_to_images()` works with new detection output

### Technical Considerations

- **Architecture**: New module parallel to `circle_detector.py`, not replacing it
- **Performance**: Connected components + convexity defects is O(n) per blob
- **Error Handling**: Fall back to standard detection if no circles found via convex method

### Dependencies

- OpenCV (`cv2.connectedComponentsWithStats`, `cv2.convexHull`, `cv2.convexityDefects`)
- NumPy for array operations
- No new external dependencies required

---

## Testing Strategy

### Unit Tests

- [x] Test `quantize_to_palette()` with known input/output
- [x] Test `filter_by_color()` produces correct masks
- [x] Test convex point extraction excludes concave regions
- [x] Test circle deduplication merges near-identical circles

### Integration Tests

- [x] Test full pipeline on `test_dotmatrix.png` - expect 16 circles (4 per color)
- [x] Test `--extract` produces 4 color-grouped output files
- [x] Test JSON output contains all 16 circles with correct colors

### Manual Testing Scenarios

1. **Happy Path**: `dotmatrix -i test_dotmatrix.png --convex-edge --palette cmyk --extract output/`
   - Should produce 4 files with 4 circles each

2. **Edge Cases**: 
   - Single color image (no overlaps)
   - Image with no circles
   - Custom palette with wrong colors

---

## Documentation Updates

- [x] Add entry to CHANGELOG.md under [Unreleased]
- [x] Update README.md with `--convex-edge` usage examples
- [x] Add algorithm explanation to docs (color quantization → filtering → convex detection)

---

## Related Cards

**Related**: z5hn8w - Edge-based color sampling (DONE) - earlier attempt at overlap handling
**Related**: unclae - Extract circle colors - will benefit from this detection method
**Related**: iyjev2 - Implement Hough circle transform - this extends that work

---

## Notes

### Algorithm Reference (from successful session)

The working algorithm flow:
1. Quantize image to 5 colors using Euclidean distance to palette
2. For each non-white color, create filtered image (only that color on transparent)
3. For each connected component (blob) in filtered image:
   - Find contour and convex hull
   - Calculate convexity defects (concave regions where circles overlap)
   - Mark points within 20px of defects >5px deep as non-convex
   - Extract convex-only points
   - Run HoughCircles on convex points image
   - Score candidates by coverage of convex points
   - Select best circle per blob
4. Deduplicate circles with centers within 20px
5. Return all detected circles grouped by color

### Key Parameters (validated)

- `dp=1, minDist=50, param1=30, param2=20, minRadius=80, maxRadius=350`
- Defect depth threshold: 5 pixels (256 * 5 in OpenCV units)
- Non-convex region width: 20 points around defects
- Deduplication distance: 20 pixels between centers
