# Improve Detection of Occluded Circles

## Problem Statement
Cyan circles in test images are often partially hidden behind other circles, appearing as blob-like shapes with only rounded edges exposed. The current detection algorithm struggles with these partially visible circles, resulting in missed detections or poor accuracy.

## Technical Analysis
When circles overlap (common in halftone prints):
- Only arcs/edges remain visible, not full circumference
- Blob-like appearance confuses standard Hough Circle detection
- Convex hull edge detection may miss partial circles
- Color regions become fragmented

## Proposed Approaches

### 1. Arc-Based Detection
- Detect circular arcs rather than complete circles
- Use arc length and curvature to infer full circle parameters
- Minimum arc length threshold (e.g., 25% of circumference)

### 2. Morphological Enhancement
- Dilate color masks to connect fragmented regions
- Use erosion to separate touching circles
- Opening/closing operations to clean up edges

### 3. Template Matching
- Generate circle templates at known radii
- Match partial circles against templates
- Score based on visible edge alignment

### 4. Adjusted Hough Parameters
- Lower `param1` (Canny edge threshold) for sensitive edge detection
- Lower `param2` (accumulator threshold) to accept partial circles
- Risk: May increase false positives

## Acceptance Criteria
- [x] Implement at least one approach from above
- [x] Test on images with known occluded circles
- [x] Detection rate for occluded circles ≥70%
- [x] False positive rate increase <20%
- [x] Document parameter tuning recommendations

## Implementation Tasks
- [x] Create test dataset with occluded circle examples
- [x] Implement arc detection algorithm
- [x] Add morphological preprocessing option
- [x] Tune Hough parameters for partial circles
- [x] Benchmark detection accuracy
- [x] Add CLI flag for occluded-circle mode (if needed)

## Dependencies
- Depends on auto-palette detection (card e5r8vj) for accurate color isolation
- May benefit from radius calibration results

## Notes
- Cyan circles in CMYK test image are most affected
- Black circles detected well - use as reference for expected results
- Trade-off between sensitivity and false positives
