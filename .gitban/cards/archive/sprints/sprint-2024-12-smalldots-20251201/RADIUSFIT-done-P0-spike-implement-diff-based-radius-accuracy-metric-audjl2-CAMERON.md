# Implement diff-based radius accuracy metric

## Research Question

**Question**: How can we quantitatively measure circle fit accuracy using the diff image, and what metric best captures radius overestimation vs underestimation?

The diff image shows white rings around detected circles, indicating radius overestimation. We need a computable metric to:
1. Measure current fit quality
2. Guide parameter optimization
3. Provide feedback for TDD-style iteration

---

## Time Box

**Maximum Time**: 4 hours

---

## Success Criteria

**We'll know this spike is successful when**:
- [x] Diff image pixel analysis implemented
- [x] Metric distinguishes overfit (white halos) from underfit (colored residue)
- [x] Baseline measurement captured for current detection
- [x] Metric can be computed automatically after each run

---

## Context

**Background**: After adding radius padding (`HOUGH_RADIUS_PADDING = 3`) and fallback detection, circles are now being detected but are visually too large. The diff image shows white rings around circles - the "halo effect" where drawn circles extend beyond original dot boundaries.

**Urgency**: This blocks achieving high-quality detection. Without a metric, we're tuning parameters blindly.

---

## Approach

**Investigation Strategy**:
1. Analyze diff image pixel composition:
   - White pixels = overfit (circle drawn beyond original)
   - Colored pixels = underfit (original not covered by circle)
   - Ratio indicates fit bias
2. Define metric: `fit_score = 1 - (white_pixels + colored_pixels) / total_non_background`
3. Implement in `black_verification.py` or new `fit_metric.py`
4. Add to CLI output and manifest

**Proposed Metric**:
```python
def calculate_fit_accuracy(diff_image, background_color=(255,255,255)):
    # White pixels (overfit halos)
    white_mask = np.all(diff_image == [255,255,255], axis=-1)
    overfit_pixels = np.sum(white_mask)
    
    # Non-white, non-background (underfit - original color showing)
    background_mask = np.all(diff_image == background_color, axis=-1)
    underfit_pixels = np.sum(~white_mask & ~background_mask)
    
    total = diff_image.shape[0] * diff_image.shape[1]
    
    return {
        'overfit_ratio': overfit_pixels / total,
        'underfit_ratio': underfit_pixels / total,
        'fit_score': 1 - (overfit_pixels + underfit_pixels) / total
    }
```

---

## Deliverables

**Created Artifacts**:
- [x] `src/dotmatrix/fit_metric.py` with metric implementation
- [x] Integration with CLI to output fit score
- [x] Baseline measurement documented
