

# Fix Large Black Regions - Detect Individual Circles in Dense Areas

## Bug Description

Large black regions (shadows, hair, dark areas) render as enormous single circles instead of the halftone dot pattern. The output shows giant black blobs where there should be many small overlapping circles.

**Root Cause**: The clustering algorithm (`cluster_and_count_pixels`) uses connected-component analysis to group adjacent pixels. When black circles are close together or overlapping, their pixels merge into a single giant cluster instead of being recognized as separate circles.

**Example**: Face shadows in pd_test.png appear as massive black circles instead of the fine halftone pattern visible in the source.

## Steps to Reproduce

1. Run: `python -m dotmatrix process pd_test.png --sliding-window`
2. View `output/run_*/reconstituted.png`
3. Look at dark shadow regions (face, hair)
4. Compare to source image halftone pattern

## Environment

- Module: `src/dotmatrix/cluster_pixel_counter.py`
- Related: `src/dotmatrix/convex_detector.py`

## Solution

Options to investigate:

**Option A: Maximum cluster radius constraint**
- If cluster area > max_expected_circle_area, attempt to split
- Use morphological erosion to separate touching circles
- Re-cluster the separated regions

**Option B: Hough circle detection for dense regions**
- Detect large clusters that exceed threshold
- Apply Hough circle detection to find individual circles
- Override clustering with detected circle positions

**Option C: Grid-based detection**
- Use known halftone grid spacing
- Expect circles at regular intervals
- Use grid to locate individual circles in dense regions

Recommended: Start with Option A (simpler), fall back to B if needed.

## Acceptance Criteria

- [x] Dark shadow regions show halftone dot pattern, not giant blobs
- [x] Individual circles visible in densely overlapping areas
- [x] Face/hair shadows match source image pattern density

## Test Plan

- [x] Run on pd_test.png and compare dark regions to source
- [x] Measure maximum cluster size before/after
- [x] Visual comparison of face shadows
