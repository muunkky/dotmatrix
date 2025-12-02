# Verify CPU Baseline Rendering Works Correctly

## Description

Verify that the CPU baseline rendering implementation produces correct output before implementing GPU acceleration.

**Value**: Establishes ground truth for GPU equivalence testing. Without verified CPU output, we cannot validate GPU implementation correctness.

**Target Users**: Developers working on GPU acceleration

**Estimated Effort**: 2 hours

---

## Overview

Before implementing GPU acceleration, we must verify the current CPU implementation produces correct output. This serves as the ground truth for GPU equivalence testing.

## Acceptance Criteria

- [ ] Run CPU render on small test image (100x100 pixels)
- [ ] Run CPU render on medium test image (500x500 pixels)
- [ ] Verify output images visually look correct (flowers properly formed)
- [ ] Save baseline outputs for later comparison
- [ ] Document CPU render times at each size for benchmark comparison
- [ ] Verify local ROI mask optimization produces identical output to original

## Test Images

1. **Small**: Create synthetic 100x100 test image with known CMYK dot pattern
2. **Medium**: Use cropped region from input_large.png (500x500)
3. **Large**: Full input_large.png (for timing only, after small/medium verified)

## Verification Checklist

- [ ] Black circles render at correct positions
- [ ] Petal colors (C, M, Y) render correctly
- [ ] Overlap blending produces expected colors
- [ ] No artifacts or missing elements
- [ ] Output pixel counts match expectations

## Dependencies

None - this is the prerequisite for all other sprint work.

## Notes

If CPU baseline has bugs, fix them before proceeding with GPU implementation.
Reference: Original circle_renderer.py implementation


## Implementation Plan

### Overview

Run CPU renderer on progressively larger test images, verify output correctness, save baselines.

### Implementation Steps

1. **Create Small Test Image**: Generate synthetic 100x100 CMYK dot pattern
   - Create known arrangement of CMYK dots
   - Document expected pixel counts per color

2. **Run CPU Baseline Small**: Test on 100x100 image
   - Run: `python3 -m dotmatrix -i test_small.png --reconstitute --render-method flower`
   - Verify output looks correct visually
   - Save output as baseline

3. **Run CPU Baseline Medium**: Test on 500x500 cropped region
   - Crop from input_large.png
   - Run same command
   - Document timing

4. **Verify Correctness**: Manual and automated checks
   - Verify flower shapes are properly formed
   - Verify colors are correct (C, M, Y petals, K centers)
   - Save outputs for GPU comparison