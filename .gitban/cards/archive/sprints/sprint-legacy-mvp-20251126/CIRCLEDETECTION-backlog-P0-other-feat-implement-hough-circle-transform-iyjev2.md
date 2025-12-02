## Description

Implement circle detection using OpenCV's Hough Circle Transform (cv2.HoughCircles) to detect circles in grayscale images.

**Value**: Core detection algorithm that identifies circles in images, providing center coordinates and radius for each detected circle.

**Target Users**: Internal detection pipeline

**Estimated Effort**: 3 hours

---

## Acceptance Criteria

- [ ] Detects at least 90% of circles in test images
- [ ] Center detection accuracy within 5px of ground truth
- [ ] Radius detection accuracy within 10% of ground truth
- [ ] Returns list of circles with (x, y, radius)
- [ ] Works on grayscale converted images
- [ ] Handles images with no circles (returns empty list)

---

## Implementation Plan

### Overview

Use cv2.HoughCircles with cv2.HOUGH_GRADIENT method to detect circles after converting image to grayscale and applying Gaussian blur.

### Implementation Steps

1. **Create circle_detector.py module**:
   - Define detect_circles(image: np.ndarray) -> List[Circle] function
   - Convert BGR to grayscale using cv2.cvtColor
   - Apply Gaussian blur to reduce noise

2. **Implement Hough Circle Transform**:
   - Use cv2.HoughCircles with HOUGH_GRADIENT method
   - Parameters: dp=1, minDist=20, param1=50, param2=30, minRadius=10, maxRadius=500
   - Convert output to list of Circle dataclass instances

3. **Create Circle dataclass**:
   - Fields: center_x, center_y, radius
   - Add __repr__ for debugging

### Technical Considerations

- **Algorithm**: Hough Circle Transform uses edge detection + voting
- **Performance**: Gaussian blur reduces noise and false positives
- **Parameters**: Will need tuning based on test image characteristics

### Dependencies

- **Prerequisites**: Card jkvie2 (image loading) must be complete

---

## Testing Strategy

### Unit Tests

- [ ] Test detects single circle in simple image
- [ ] Test detects multiple circles
- [ ] Test returns empty list for image with no circles
- [ ] Test center coordinates within 5px tolerance
- [ ] Test radius within 10% tolerance
- [ ] Test handles various circle sizes (10px to 500px radius)

---

## Documentation Updates

- [ ] Document algorithm parameters and tuning
- [ ] Add docstrings explaining Circle dataclass