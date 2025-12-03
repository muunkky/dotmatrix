# Bug: Calibration uses wrong error metric and optimization

## Problem

The current calibration algorithm has fundamental flaws:

1. **Wrong error metric**: Uses `std * 0.5` which penalizes inherent variance in circle sizes (ground truth), not detection error
2. **Wrong stopping condition**: Stops when bounds "stabilize" not when error is minimized
3. **No real optimization**: Bounds tightening isn't searching parameter space

## Current (broken) behavior

```
error = abs(detected_mean - target_mean) + detected_std * 0.5
```

With 4 black circles of radii 116-256, std=57.6 is **reality**, not error. Algorithm converges in 2 iterations with error=28.8 and declares success.

## Correct approach

```
error = abs(detected_count - actual_count)
goal: error = 0
```

### Algorithm

1. **Establish ground truth**: Detect with very wide bounds [1, max_dimension] → count = N
2. **Binary search min_radius**: Find LARGEST min_r where count still == N
3. **Binary search max_radius**: Find SMALLEST max_r where count still == N
4. These are independent 1D searches (not complex multivariate)

### Why binary search works

- min_radius affects small circle detection (increase → may lose small circles)
- max_radius affects large circle detection (decrease → may lose large circles)
- Each can be optimized independently
- Search space is bounded: [1, smallest_detected] and [largest_detected, image_dimension]

## Tasks

- [ ] Rewrite `calibrate_radius()` with count-based error metric
- [ ] Implement binary search for min_radius (find tightest lower bound)
- [ ] Implement binary search for max_radius (find tightest upper bound)
- [ ] Update `CalibrationResult` to report count-based metrics
- [ ] Update `format_calibration_output()` for new metrics
- [ ] Update tests for new behavior
- [ ] Verify on test_dotmatrix.png: should find bounds ~[116, 256] with error=0

## Success Criteria

- [ ] Calibration achieves error=0 when all circles detected
- [ ] Returns tightest valid bounds (not just "stabilized" bounds)
- [ ] Binary search converges in O(log n) iterations per parameter
- [ ] All existing tests pass or are updated appropriately
