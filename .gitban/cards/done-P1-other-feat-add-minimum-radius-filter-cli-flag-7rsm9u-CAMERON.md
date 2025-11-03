## Description

Add `--min-radius` CLI flag to filter out circles smaller than a specified radius. This helps ignore noise, flecks, and small artifacts in images.

**Value**: Users can focus on meaningful circles and reduce false positives from image noise.

**Target Users**: All users processing images with noise or unwanted small features

**Estimated Effort**: 1 day

---

## Acceptance Criteria

- [x] `--min-radius N` flag added to CLI
- [x] Default value: 10px (current hardcoded value)
- [x] Configurable range: 1-1000px
- [x] Circles with radius < min-radius are excluded from output
- [x] Works with JSON, CSV, and PNG extraction
- [x] Error validation for invalid values (negative, zero, non-numeric)
- [x] Tests for filtering behavior
- [x] Documentation updated in README.md and --help

---

## Implementation Plan

### Overview

Add Click option to CLI, pass through detection pipeline, filter circles before output.

### Implementation Steps

1. **Add CLI flag**: Add `--min-radius` to cli.py
   - Default: 10 (matches current minRadius in detect_circles)
   - Type: int
   - Validation: 1-1000 range
   - Help text: "Minimum circle radius in pixels (default: 10)"

2. **Update circle_detector.py**: Make minRadius configurable
   - Add parameter to detect_circles(image, min_radius=10)
   - Pass to cv2.HoughCircles minRadius parameter
   - Update docstring

3. **Add post-detection filter**: Filter circles after detection
   - In cli.py, filter results list before color extraction
   - Skip circles where circle.radius < min_radius

4. **Add tests**: Test filtering behavior
   - Test default behavior (10px)
   - Test custom values (20px, 50px, 100px)
   - Test edge cases (1px, 1000px)
   - Test invalid inputs (0, negative, string)
   - Test with PNG extraction

---

## Testing Strategy

### Unit Tests

- [x] Test detect_circles with custom min_radius parameter
- [x] Test CLI argument parsing for --min-radius
- [x] Test validation for invalid values

### Integration Tests

- [x] Test end-to-end with synthetic image (circles 5px, 15px, 50px)
- [x] Verify only circles >= min_radius in output
- [x] Test with --extract flag

---

## Documentation Updates

### 📝 IMPORTANT: Update CHANGELOG.md
- [x] **Add entry to CHANGELOG.md under [Unreleased]** (REQUIRED for user-facing features)
  - Use "Added" for new features
  - Include feature name: "Add `--min-radius` flag to filter small circles"
  - Mention CLI flag: `--min-radius N`

### Other Documentation
- [x] Update README.md CLI options section
- [x] Update README.md with usage example
- [x] Update --help text in CLI
- [x] Update ROADMAP.md - check off M2 task

---

## Notes

### Design Decisions

- **Decision**: Apply filter in two places (HoughCircles parameter + post-detection)
- **Rationale**: HoughCircles minRadius helps detection, post-filter ensures consistency
- **Trade-offs**: Slight redundancy but ensures all circles meet criteria

### Technical Notes

- Current minRadius is hardcoded to 10 in circle_detector.py:74
- Need to make this configurable while maintaining backward compatibility
