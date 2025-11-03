## Description

Add `--max-radius` CLI flag to control detection of very large circles. Helps focus on specific size ranges and improves performance on large images.

**Value**: Users can limit detection to relevant circle sizes and avoid false positives from very large circles.

**Target Users**: Users processing images with specific size requirements

**Estimated Effort**: 0.5 days

---

## Acceptance Criteria

- [x] `--max-radius N` flag added to CLI
- [x] Default value: 500px (current hardcoded value)
- [x] Configurable up to image dimension (auto-adjusted)
- [x] Circles with radius > max-radius are excluded from output
- [x] Works with JSON, CSV, and PNG extraction
- [x] Auto-adjustment warning when max-radius > image size
- [x] Tests for filtering behavior
- [x] Documentation updated in README.md and --help

---

## Implementation Plan

### Implementation Steps

1. **Add CLI flag**: Add `--max-radius` to cli.py
   - Default: 500 (matches current maxRadius)
   - Type: int
   - Help text: "Maximum circle radius in pixels (default: 500)"

2. **Update circle_detector.py**: Make maxRadius configurable
   - Add parameter to detect_circles(image, min_radius=10, max_radius=500)
   - Pass to cv2.HoughCircles maxRadius parameter
   - Auto-adjust if max_radius > min(image dimensions)

3. **Add tests**: Test filtering behavior
   - Test default behavior (500px)
   - Test custom values (100px, 1000px)
   - Test auto-adjustment with small images

---

## Documentation Updates

### 📝 IMPORTANT: Update CHANGELOG.md
- [x] **Add entry to CHANGELOG.md under [Unreleased]**
  - Use "Added" for new features
  - Include: "Add `--max-radius` flag to control maximum circle size"

### Other Documentation
- [x] Update README.md CLI options
- [x] Update ROADMAP.md - check off M2 task
