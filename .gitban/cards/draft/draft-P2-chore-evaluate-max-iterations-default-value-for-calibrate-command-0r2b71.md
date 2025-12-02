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

- [ ] **Analyze current behavior**: Run calibration on test images and observe if 10 iterations is typically sufficient for convergence
- [ ] **Test with higher defaults**: Try 15, 20, 25 iterations and measure if results improve
- [ ] **Update default if needed**: Change the default value in cli.py and calibration.py if warranted
- [ ] **Update tests**: Ensure test assertions work with new default
- [ ] **Document change**: Update help text if default changes

---

## Success Criteria

- [ ] Default max-iterations value is validated as appropriate for typical use cases
- [ ] Calibration converges reliably with the chosen default
- [ ] Tests pass with updated default (if changed)

---

## Notes

### Context

This card was created after removing the `--tolerance` parameter from the calibrate command. Previously, the algorithm could exit early if error fell below tolerance. Now it must rely solely on convergence detection (bounds stabilizing) or hitting max iterations.

### Related Work

- Commit `97cfbab`: "Remove tolerance parameter from calibration algorithm"
- Card `clsczj`: Auto-calibrate radius parameters from black dot ground truth
