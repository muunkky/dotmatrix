## Description

Add black dot ground truth verification for radius calibration

In CMYK halftone printing, black (K) dots have special properties that make them ideal for verifying detection settings:
- **Always on top**: Black is printed last, so dots are never occluded
- **Well-defined edges**: High contrast against all other colors  
- **Complete circles**: Not partially hidden by other ink layers
- **Consistent sizing**: Black screen typically uses uniform dot sizes

This makes black dot count an excellent "ground truth" metric for validating that `--min-radius` and `--max-radius` settings are correct. If the detection is finding significantly fewer black dots than exist in the image, the radius settings are likely wrong.

**Problem Context**: User observed missing dots in certain image regions where even black circles (usually easiest to detect) were sparse. This suggests the detection parameters may be misconfigured for that area's dot sizes.

**Value**: Provides a quick sanity check before running full CMYK detection. Users can verify their radius settings are correct by comparing detected black dots against expected count, saving time on failed detection runs.

**Target Users**: Users processing CMYK halftone images who need to calibrate detection parameters

**Estimated Effort**: 1-2 days

---

## Acceptance Criteria

- [x] Enable black dot verification by default for CMYK detection (disable with `--no-verify-black`)
- [x] Display accuracy/verification stats in console output upon completion
- [x] Report black dot count and radius distribution statistics
- [x] Show visual coverage map of where black dots were found
- [x] Warn if detected count seems low relative to image area (sparse detection)
- [x] Warn if radius distribution is clustered at min or max bounds (bad settings)
- [x] Provide suggested radius range based on detected black dot sizes
- [x] Option to abort full detection if verification fails threshold
- [x] Works with both standard and chunked processing modes

---

## Implementation Plan

### Overview

Create a verification pass that detects only black dots (simplest case) before running full CMYK separation. Analyze the results to validate detection settings and provide feedback.

### Implementation Steps

1. **Add black-only detection function**: `verify_black_dot_detection()`
   - Extract K (black) channel from image
   - Run convex edge detection on black channel only
   - Return detected circles with statistics

2. **Compute verification metrics**:
   - Total black dot count
   - Radius distribution (min, max, mean, std)
   - Spatial distribution (coverage per grid cell)
   - Detection density (dots per 1000 sq pixels)

3. **Implement warning heuristics**:
   - If >30% of detected radii are at min_radius → "min_radius may be too high"
   - If >30% of detected radii are at max_radius → "max_radius may be too low"
   - If density varies >3x across image regions → "possible detection gaps"
   - If total count < expected_density * area → "possible missed detections"

4. **Add CLI integration**:
   - Verification enabled by default for CMYK palette detection
   - `--no-verify-black` flag to disable verification pass
   - `--verify-threshold N` to set minimum expected dots (optional)
   - Display accuracy stats in console upon completion (always visible)
   - Include verification data in manifest.json
   - `--verify-abort` to stop if verification fails

5. **Create verification report output**:
   ```
   Black Dot Verification Report
   =============================
   Detected: 1,247 black dots
   Radius range: 12-48 pixels (mean: 28, std: 8)
   Coverage: 94% of image regions have detections
   Density: 2.3 dots per 1000 sq pixels
   
   Status: PASS - Settings appear correct
   
   Warnings:
   - Region (2000,3000)-(3000,4000) has 40% fewer dots than average
   ```

6. **Optional: Visual coverage map**:
   - Generate heatmap showing detection density across image
   - Highlight regions with sparse detection
   - Save as `verification_map.png` in output directory

### Technical Considerations

- **Performance**: Black-only detection is fast (single channel, no color separation)
- **Threshold tuning**: Default heuristics may need adjustment based on real-world testing
- **Integration**: Should work with existing `--debug` flag for additional output

---

## Testing Strategy

### Unit Tests

- [x] Test verification metrics calculation
- [x] Test warning heuristics trigger correctly
- [x] Test radius suggestion algorithm

### Integration Tests

- [x] Test `--verify-black` flag produces report
- [x] Test verification with known good settings passes
- [x] Test verification with known bad settings warns appropriately
- [x] Test `--verify-abort` stops processing when threshold not met

---

## Related Cards

**Related**: urmjmz - CMYK subtractive color blending (both improve CMYK workflow)

---


## Notes

### Implementation Summary

**Core Module** (`src/dotmatrix/black_verification.py`):
- `verify_black_dot_detection()`: Main function that extracts black channel, detects circles, and returns metrics
- `calculate_verification_metrics()`: Computes density, coverage, radius statistics
- `generate_verification_warnings()`: Analyzes metrics and produces actionable warnings
- `suggest_radius_range()`: Calculates optimal min/max radius based on detected distribution using mean ± 2σ with 20% padding
- `generate_coverage_map()`: Creates heatmap visualization showing detection density across image regions
- `format_verification_output()`: Formats results for console display with warnings and suggestions

**CLI Integration** (`src/dotmatrix/cli.py`):
- Enabled by default when `--palette cmyk` is used
- Runs before full detection to validate settings early
- `--no-verify-black` flag to disable
- `--verify-abort` flag to stop processing if verification fails
- Saves coverage map to `black_verification_coverage.png` when `--debug` is enabled
- Skipped in sliding window mode (runs per-tile, verification is for full image)

**Test Coverage** (`tests/test_black_verification.py`):
- Comprehensive unit tests for all verification functions
- Tests for metric calculation, warning generation, coverage map
- Integration tests verifying CLI behavior

### Design Decisions

- **Decision**: Focus on black dots only for verification
- **Rationale**: Black is the most reliable ink layer - if we can't detect black dots correctly, other colors will definitely fail
- **Alternatives Considered**: Verify all CMYK channels (too slow, defeats purpose of quick check)

### Future Enhancements

- Could extend to verify each CMYK channel independently
- Could learn expected dot density from sample of known-good images
- Could auto-suggest optimal min/max radius based on black dot analysis
