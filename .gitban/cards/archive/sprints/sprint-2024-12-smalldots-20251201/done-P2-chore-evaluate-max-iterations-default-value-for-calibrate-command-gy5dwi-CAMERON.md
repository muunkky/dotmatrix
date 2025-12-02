## Purpose

Evaluate whether the `--max-iterations` default value of 10 is appropriate for the calibrate command now that tolerance-based early exit has been removed.

With the removal of the tolerance parameter (commit `97cfbab`), the calibration algorithm now runs until bounds stabilize or max iterations is reached. The current default of 10 may need adjustment to ensure the algorithm has enough iterations to find the true minimum error.

**Value**: Ensures optimal calibration results by default without requiring users to manually increase iterations.

**Estimated Effort**: 30 minutes

---

## Project Location

**Path**: `src/dotmatrix/cli.py`

### Files/Modules Affected

- `src/dotmatrix/cli.py`: `--max-iterations` option default value (line ~1195)
- `src/dotmatrix/calibration.py`: `calibrate_radius()` function parameter default

---

## Tasks

- [x] **Analyze current behavior**: Run calibration on test images and observe if 10 iterations is typically sufficient for convergence
- [x] **Test with higher defaults**: Try 15, 20, 25 iterations and measure if results improve
- [N/A] **Update default if needed**: No change warranted - 10 iterations is MORE than sufficient
- [N/A] **Update tests**: No change warranted - default unchanged
- [N/A] **Document change**: No change warranted - default unchanged

---

## Success Criteria

- [x] Default max-iterations value is validated as appropriate for typical use cases
- [x] Calibration converges reliably with the chosen default
- [N/A] Tests pass with updated default (if changed) - No change warranted

---

## Notes

### Context

This card was created after removing the `--tolerance` parameter from the calibrate command. Previously, the algorithm could exit early if error fell below tolerance. Now it must rely solely on convergence detection (bounds stabilizing) or hitting max iterations.

### Related Work

- Commit `97cfbab`: "Remove tolerance parameter from calibration algorithm"
- Card `clsczj`: Auto-calibrate radius parameters from black dot ground truth


## Evaluation Results

**Evaluation completed on 2025-11-28:**

1. **Testing with default bounds [10, 300]**: Algorithm converged in 2 iterations
2. **Testing with wide bounds [5, 500]**: Algorithm still converged in 2 iterations
3. **Conclusion**: Default of 10 max iterations is MORE than sufficient - algorithm typically converges in just 2 iterations

**Bonus finding**: During evaluation, discovered and fixed a bug where tighter bounds weren't being saved when error was equal (commit `f47d023`). Changed `if error < best_error:` to `if error <= best_error:` to prefer tighter bounds.

**No changes needed**: Default of 10 iterations is appropriate. The remaining tasks (update default, update tests, document change) are marked N/A since no default change was warranted.