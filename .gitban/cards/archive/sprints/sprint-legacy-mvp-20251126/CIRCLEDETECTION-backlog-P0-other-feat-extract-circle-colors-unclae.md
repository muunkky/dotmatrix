## Description

Sample pixels within detected circles to determine average RGB color for each circle.

**Value**: Provides color information for each detected circle, completing the required output data (center, radius, color).

**Target Users**: Internal detection pipeline

**Estimated Effort**: 2 hours

---

## Acceptance Criteria

- [ ] Returns RGB tuple for each circle
- [ ] Average color within 10% tolerance of actual circle color
- [ ] Samples only pixels within circle boundary (not outside)
- [ ] Handles edge cases (circle partially outside image bounds)
- [ ] Converts BGR to RGB for output

---

## Implementation Plan

### Overview

Create a circular mask for each detected circle, sample pixels within the mask, and calculate mean RGB values.

### Implementation Steps

1. **Extend circle_detector.py module**:
   - Define extract_color(image: np.ndarray, circle: Circle) -> Tuple[int, int, int] function
   - Create circular mask using cv2.circle with filled parameter

2. **Implement color sampling**:
   - Create boolean mask for circle region
   - Use mask to select pixels within circle
   - Calculate mean RGB values using np.mean
   - Convert BGR to RGB for output
   - Round to integers

3. **Handle edge cases**:
   - Clip circle to image bounds if extends beyond
   - Ensure at least some pixels are sampled
   - Return (0, 0, 0) if no valid pixels

### Technical Considerations

- **Color Space**: Input is BGR (OpenCV), output is RGB (standard)
- **Sampling**: Sample all pixels within circle for accuracy
- **Edge Handling**: Circles near image edges may be clipped

### Dependencies

- **Prerequisites**: Card (Hough Transform) must be complete

---

## Testing Strategy

### Unit Tests

- [ ] Test extracts correct color for solid color circle
- [ ] Test RGB values within 10% of expected
- [ ] Test handles circle at image edge
- [ ] Test handles circle partially outside bounds
- [ ] Test returns valid RGB tuple (0-255 range)

---

## Documentation Updates

- [ ] Add docstrings explaining color extraction method