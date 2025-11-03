## Description

Edge-based color sampling for overlapping circles

Current color extraction averages the entire circle area, causing issues with overlapping circles. When blue circles are positioned under black circles, they appear mostly black instead of blue because the color averaging includes the overlapping black area. This feature will sample colors from the exposed edge/perimeter of circles instead to capture the true color even when circles overlap.

**Value**: Accurately extract circle colors even when circles overlap, improving color classification for layered/3D dot matrix patterns.

**Target Users**: Users analyzing dot matrix images with overlapping circles

**Estimated Effort**: 1-2 days

---

## Acceptance Criteria

- [x] `extract_circle_color()` accepts optional `use_edge_sampling` parameter
- [x] Edge sampling takes N evenly-spaced points around circumference (default: 36 points)
- [x] Returns median color from edge samples instead of area average
- [x] CLI has `--edge-sampling` flag
- [x] Tests verify edge sampling differs from area averaging on overlapping circles
- [x] Documentation updated (CHANGELOG, README, CLI help)

---

## Implementation Plan

### Overview

Modify the color extraction function to optionally sample points along the circle's circumference instead of averaging all pixels within the circle area. Use median color calculation to reduce noise and handle partial occlusions.

### Implementation Steps

1. **Modify extract_circle_color()**: Add `use_edge_sampling` parameter and `num_samples` parameter
   - Generate N evenly-spaced angles around circle (0 to 2π)
   - Calculate (x, y) coordinates for each sample point
   - Extract RGB values at each point
   - Calculate median RGB values from samples

2. **Update CLI**: Add `--edge-sampling` flag
   - Wire through to extract_circle_color() calls
   - Add `--edge-samples` option for number of samples (default: 36)
   - Update help text

3. **Write Tests**: Following TDD RED → GREEN → REFACTOR
   - Test edge sampling parameter exists
   - Test edge sampling returns different results than area averaging
   - Test with synthetic overlapping circles image
   - Test edge sample count parameter

4. **Update Documentation**
   - Add CHANGELOG entry
   - Update README with edge sampling feature
   - Update CLI help text

### Technical Considerations

- **Architecture**: Pure function modification, no architecture changes
- **Performance**: Edge sampling is faster than area averaging (36 samples vs 1000s of pixels)
- **Edge Cases**: Handle circles at image boundaries (clip coordinates)

### Dependencies

- numpy for trigonometry (np.cos, np.sin)
- Existing cv2 and Circle dataclass

---

## Documentation Updates

### 📝 IMPORTANT: Update CHANGELOG.md
- [x] **Add entry to CHANGELOG.md under [Unreleased]**
  - Added `--edge-sampling` flag for edge-based color extraction
  - Added `--edge-samples` option to control sample count
  - Improves color accuracy for overlapping circles

### Other Documentation
- [x] Update README.md with edge sampling feature and example
- [x] Update CLI help text for new flags

---

## Notes

### Design Decisions

- **Decision**: Use median instead of mean for color aggregation
- **Rationale**: Median is robust to outliers and partial occlusions
- **Alternatives Considered**: Mode (too sensitive to noise), mean (affected by outliers)
- **Trade-offs**: Median requires sorting but provides better results

### Research Findings

User observation: "blue circles peeking out from under black circles so technically most of the circle is black but we know by looking at it that it's supposed to be blue if you think of it as a layer underneath"

Solution: Sample edge points where true color is exposed
