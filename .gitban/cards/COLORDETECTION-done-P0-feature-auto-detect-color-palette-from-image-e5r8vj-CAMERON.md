## Description

**Auto-detect color palette from image histogram analysis**

Implement `--palette auto` option that automatically detects the N most dominant colors in an image instead of requiring manual palette specification. This eliminates the need for users to know the exact colors in their halftone images and improves detection accuracy by using actual image colors rather than preset approximations.

**Value**: Significantly improves user experience by removing the need to manually specify colors. Also improves detection accuracy since the palette will match actual image colors rather than preset approximations (e.g., CMYK preset was missing red and blue in test images).

**Target Users**: All DotMatrix users, especially those with non-standard halftone images

**Estimated Effort**: 2-3 days

---

## Acceptance Criteria

- [x] New `--palette auto` CLI option to auto-detect dominant colors
- [x] New `--num-colors N` CLI option to specify how many colors to detect (default: 6)
- [x] Histogram/k-means based color detection identifies dominant colors
- [x] White/background color automatically excluded from palette
- [x] Black always included in detected palette
- [x] Detection results shown to user (e.g., "Detected palette: black, cyan, magenta, yellow, red, blue")
- [x] Works correctly with chunked processing
- [x] Fallback to CMYK preset if auto-detection fails

**Quality Metrics**:
- [x] Test coverage: >90% for new color detection code
- [x] Detection accuracy: 95%+ of dominant colors correctly identified on test images

---

## Implementation Plan

### Overview

Use k-means clustering or histogram peak detection to identify the N most common non-background colors in the image. The detected palette is then used for the existing convex edge detection pipeline.

### Implementation Steps

1. **Add CLI options**: Add `--palette auto` and `--num-colors N` to cli.py
   - `auto` triggers color detection
   - `--num-colors` defaults to 6 (black + 5 colors)

2. **Implement color detection module**: Create `color_palette_detector.py`
   - Sample pixels from image (subsample for performance)
   - Quantize colors to reduce noise
   - Use k-means or histogram peaks to find dominant colors
   - Filter out white/near-white as background
   - Ensure black is always included

3. **Integrate with convex detector**: Modify `convex_detector.py`
   - Accept auto-detected palette
   - Log detected colors for user visibility

4. **Add tests**: Create `tests/test_palette_detection.py`
   - Test with known color images
   - Test edge cases (grayscale, single color, etc.)

### Technical Considerations

- **Performance**: Subsample large images (every 10th pixel) to keep detection fast
- **Color quantization**: Round RGB to nearest 20 to reduce noise from anti-aliasing
- **Background detection**: Assume most common light color is background
- **Minimum color presence**: Require colors to have >0.5% of pixels to be included

### Dependencies

- numpy (already installed)
- scikit-learn for k-means (already installed)

---

## Testing Strategy

### Unit Tests

- [x] Test color detection on synthetic images with known colors
- [x] Test edge cases: single color, grayscale, all white
- [x] Test background detection/exclusion
- [x] Test black inclusion guarantee

### Integration Tests

- [x] Test `--palette auto` CLI flag
- [x] Test `--num-colors` parameter
- [x] Test combined with `--chunk-size`

---

## Documentation Updates

- [x] **Add entry to CHANGELOG.md under [Unreleased]**
- [x] Update README.md with `--palette auto` documentation
- [x] Add examples of auto-detection output

---

## Related Cards

**Depends on**: 563qpc - Multi-color circle detection research (may inform palette detection approach)

---

## Notes

### Research Findings

From analysis of test image `inputs/Circle test file .png`:
- Top colors: Black (49%), White (25%), Yellow (8%), Cyan (5%), Red (4%), Magenta (3%), Blue (0.4%)
- CMYK preset was missing Red and Blue
- Quantization to nearest 20 RGB effectively reduces noise
