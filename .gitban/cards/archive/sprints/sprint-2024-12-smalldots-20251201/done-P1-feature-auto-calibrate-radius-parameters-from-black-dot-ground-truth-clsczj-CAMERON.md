## Description

**Auto-calibration script for min/max radius optimization**

Implement an iterative calibration algorithm that automatically adjusts `--min-radius` and `--max-radius` parameters to minimize the delta between detected circle radii and ground truth black dot radii. The algorithm uses black dots as reference points (since they're always printed on top, never occluded) and recursively refines radius bounds until detection accuracy is maximized.

**Value**: Eliminates manual trial-and-error when configuring radius parameters for new print materials or DPI settings. Users can run calibration once on a test print and get optimal settings automatically.

**Target Users**: Users processing halftone prints who need optimal detection parameters

**Estimated Effort**: 1-2 days

---

## Acceptance Criteria

- [x] CLI command `dotmatrix calibrate` accepts an image with known black dots
- [x] Algorithm iteratively adjusts min/max radius to minimize detection error
- [x] Outputs optimal `--min-radius` and `--max-radius` values
- [x] **Goal is zero error** - algorithm seeks to minimize error, not just satisfy a threshold
- [x] Reports the **minimum error found**, even if zero cannot be achieved
- [x] Optional `--tolerance` for early-exit when error is essentially zero (default: 0.1px)
- [x] Supports max iterations limit to prevent infinite loops (default: 20)
- [x] Outputs calibration report with iteration history
- [x] Can output results as JSON for programmatic consumption

**Quality Metrics**:
- [x] Test coverage: >90% for calibration module
- [x] Convergence within 10 iterations for typical images

---

## Implementation Plan

### Overview

Use binary search optimization on the radius parameter space. Start with wide bounds, run detection, compare detected black dot radii to actual radii from verification, and narrow the search space based on error direction. The black_verification module already provides ground truth metrics (radius_mean, radius_std) that can guide calibration.

### Implementation Steps

1. **Create calibration module** (`src/dotmatrix/calibration.py`):
   - `CalibrationResult` dataclass with optimal params and iteration history
   - `calibrate_radius()` function implementing binary search
   - `calculate_error()` helper to compute delta from ground truth
   ```python
   @dataclass
   class CalibrationResult:
       optimal_min_radius: int
       optimal_max_radius: int
       final_error: float
       iterations: int
       history: List[CalibrationStep]
       converged: bool
   ```

2. **Implement binary search optimization**:
   - Start with user-provided initial bounds (or sensible defaults)
   - Run detection with current params
   - Use black_verification to get actual radius stats
   - Adjust bounds based on whether detected radii are too small/large
   - Repeat until error < tolerance or max iterations reached

3. **Add CLI command** (`dotmatrix calibrate`):
   - Required: `-i/--input` image path
   - Optional: `--initial-min`, `--initial-max` starting bounds
   - Optional: `--tolerance` convergence threshold (default: 2)
   - Optional: `--max-iterations` limit (default: 20)
   - Optional: `--format json` for machine-readable output

4. **Write unit tests** (`tests/test_calibration.py`):
   - Test convergence with synthetic ground truth
   - Test iteration limit behavior
   - Test tolerance threshold behavior
   - Test edge cases (already optimal, no black dots found)

### Technical Considerations

- **Architecture**: New module `calibration.py` that imports `black_verification` and `convex_detector`
- **Algorithm**: Binary search is O(log n) iterations, suitable for radius range ~10-500px
- **Error Metric**: Use `abs(detected_mean - actual_mean) + detected_std` to penalize variance
- **Edge Cases**: Handle images with no black dots (return error), handle non-convergence (return best so far)

### Dependencies

- **Internal**: `black_verification.py`, `convex_detector.py`, `cli.py`
- **External**: None (uses existing numpy/opencv)

---

## Testing Strategy

### Unit Tests

- [x] Test calibration converges on synthetic test image
- [x] Test tolerance threshold stops iteration correctly
- [x] Test max iterations limit prevents infinite loop
- [x] Test error calculation is accurate
- [x] Test handles no-black-dots gracefully

### Integration Tests

- [x] Test CLI `calibrate` command with real test image
- [x] Test JSON output format is valid
- [x] Test calibration results improve detection accuracy

---

## Related Cards

**Depends on**: `ajwv8f` - Black dot ground truth verification (COMPLETED)

**Related**: Builds on verification metrics to enable automated parameter tuning

---

## Notes

### Algorithm Details

**Binary Search Approach**:
```
1. Set low = initial_min, high = initial_max
2. While (high - low) > tolerance and iterations < max:
   a. mid = (low + high) / 2
   b. Run detection with min_radius=low, max_radius=mid
   c. Get black dot radius stats from verification
   d. If detected_mean < actual_mean: low = mid (circles too small, increase min)
   e. Else: high = mid (circles too big, decrease max)
3. Return optimal parameters
```

**Alternative**: Could use gradient descent or Nelder-Mead for more sophisticated optimization, but binary search is simpler and sufficient for 1D parameter tuning.

### Open Questions

- **Q**: Should calibration also optimize `--min-distance` parameter?
- **A**: Defer to follow-up card - keep initial scope focused on radius only
