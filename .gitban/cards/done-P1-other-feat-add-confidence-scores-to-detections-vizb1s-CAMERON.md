## Description

Add confidence score (0-100%) to each detected circle based on accumulator value from HoughCircles. Add optional `--min-confidence` filter to exclude low-confidence detections.

**Value**: Helps users filter unreliable detections and understand detection quality.

**Target Users**: Users processing noisy images who need to filter false positives.

**Estimated Effort**: 1.5 days

---

## Acceptance Criteria

- [x] Confidence score added to Circle dataclass
- [x] Calculated from HoughCircles accumulator value
- [x] Normalized to 0-100% range
- [x] Added to JSON/CSV output
- [x] `--min-confidence N` flag (optional filter)
- [x] Default: no filtering (all detections)
- [x] Tests with synthetic images
- [x] Documentation updated

---

## Implementation Plan

### Implementation Steps

1. **Update Circle dataclass**: Add confidence field
   - Add confidence: float to circle_detector.py Circle class
   - Update __repr__ and serialization

2. **Calculate confidence**: Extract from HoughCircles
   - cv2.HoughCircles returns 4th value: accumulator value
   - Normalize to 0-100 range (need to determine max value)
   - Store in Circle object

3. **Add CLI filter**: `--min-confidence` flag
   - Optional int flag, range 0-100
   - Filter circles below threshold after detection

4. **Update formatters**: Include confidence in output
   - JSON: add "confidence" field
   - CSV: add confidence column

---

## Testing Strategy

### Unit Tests

- [x] Test confidence calculation and normalization
- [x] Test Circle with confidence field
- [x] Test min-confidence filtering

### Integration Tests

- [x] Verify confidence values are reasonable (0-100)
- [x] Test filtering with various thresholds
- [x] Verify output includes confidence

---

## Documentation Updates

### 📝 IMPORTANT: Update CHANGELOG.md
- [x] **Add entry to CHANGELOG.md under [Unreleased]**
  - Use "Added": "Add confidence scores to each detection"
  - Note: "Add `--min-confidence` flag for filtering"

### Other Documentation
- [x] Update README.md with confidence examples
- [x] Update ROADMAP.md - check off M2 task

---

## Prerequisites

- [x] Research HoughCircles accumulator value range
- [x] Determine normalization strategy

---

## Notes

### Design Decisions

- **Decision**: Use accumulator value for confidence
- **Rationale**: Directly reflects HoughCircles certainty
- **Alternatives**: Edge strength (complex), manual heuristic (arbitrary)
- **Trade-offs**: Confidence scale may vary with image size


## Research Results

### HoughCircles Accumulator Research

**Finding**: cv2.HoughCircles does NOT expose accumulator values in Python API

**Alternative Approach**:
1. Use **detection order as confidence proxy** - HoughCircles sorts by accumulator internally
2. First detection = 100% confidence, scale down for subsequent detections
3. Formula: `confidence = 100 * (1 - index / total_circles)^2`

This provides:
- Most confident circles get highest scores
- Reasonable distribution (quadratic falloff)
- Simple implementation without OpenCV modifications
- Deterministic and reproducible

**Trade-offs**:
- Not true accumulator values
- Relative confidence (within detection set), not absolute
- Good enough for filtering low-quality detections
