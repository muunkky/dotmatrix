## Testing Goal

CMYK Accuracy Comparison - Validate Cell-Based Clustering

Compare source vs reconstituted images using cell-based clustering to measure CMYK accuracy.

**Value**: Validates the CELLCLUSTER sprint deliverables - ensure cell-based clustering improves accuracy.

**Current Coverage**: Manual testing only

**Target Coverage**: Automated accuracy measurement with cmyk_accuracy.py

---

## Test Scope

Accuracy comparison between source and reconstituted images using cell-based clustering.

### Modules to Test

- [x] **cmyk_accuracy.py**: CMYK decomposition and comparison
  - `decompose_to_cmyk()`: Extract CMYK pixel counts
  - `compare_cmyk_vectors()`: Calculate per-channel error
  - `measure_accuracy()`: End-to-end accuracy test

### Out of Scope

- Circle detection accuracy (covered by other tests)
- Render method variations (only flower tested)

---

## Test Scenarios

### Happy Path Scenarios

1. **CMYK halftone comparison**:
   - Setup: corner_test.png with CMYK circles
   - Action: Reconstitute with flower renderer
   - Expected: Total error < 10%
   - Test: measure_accuracy() returns passed=True

### Edge Cases

- [x] Images with no yellow (corner_test.png has no yellow)
- [x] Images with secondary colors (blue = C+M overlap)

---

## Findings

### Test Image: `inputs/corner_test.png`
- CMYK halftone pattern with overlapping circles
- Contains blue areas (C+M overlap in subtractive color model)

### Results with `--reconstitute --render-method flower --blend-overlaps`

```
=== CMYK Accuracy Report ===

--- Decomposition ---
                 Source      Recon       Diff      Error
Cyan             48,655     32,758   -15,897     32.7%
Magenta          24,858      6,872   -17,986     72.4%
Yellow                0          0         0      0.0%
Black           117,313    130,359 +   13,046     11.1%

Secondary colors detected:
  Source:  Red=0, Green=0, Blue=15,750
  Recon:   Red=0, Green=0, Blue=70

--- Summary ---
Total Error: 24.6% (weighted average)
Threshold:   10.0%
Result:      FAIL
```

### Key Issues Identified

1. **Blue overlap missing**: Source has 15,750 blue pixels (C+M overlap), Recon has only 70
   - The `--blend-overlaps` flag isn't producing sufficient C+M overlap
   - This is a **flower renderer issue**, not a clustering issue

2. **Magenta underrepresented**: 72.4% error
   - Magenta petals are too small or incorrectly positioned

3. **Black overrepresented**: 11.1% error (130K vs 117K)
   - Black circles are slightly too large

### Root Cause

The cell-based clustering correctly counts CMYK pixels per cell, but the **flower renderer** geometry doesn't accurately reproduce the original overlap patterns. The petal sizes and positions don't create the same C+M overlap that exists in the source.

## Acceptance Criteria

- [x] Run accuracy comparison using cmyk_accuracy.py
- [x] Document metrics from test images
- [x] Identify issues (blend-overlaps not creating enough overlap)
- [x] Create follow-up card for flower renderer improvements (01gzl3)

## Recommendations

1. **New Bug Card**: Fix `--blend-overlaps` to create proper C+M = Blue overlap
2. **Consider**: Alternative render methods that better preserve overlap geometry
3. **Future**: Diff-based visual comparison for localized error analysis

## Test Command

```bash
python3 -m dotmatrix -i inputs/corner_test.png -m halftone --reconstitute \
    --render-method flower --petal-rotation cluster-hash --blend-overlaps \
    --run-name accuracy_test

python3 -c "
from src.dotmatrix.cmyk_accuracy import measure_accuracy
measure_accuracy('inputs/corner_test.png', 'output/accuracy_test_*/reconstituted.png', 
                 tolerance=20, threshold=0.10, verbose=True)
"
```


## Test Plan

1. Run reconstitute with flower renderer on test image
2. Use cmyk_accuracy.measure_accuracy() to compare source vs recon
3. Document per-channel errors and total weighted error
4. Identify root causes for any accuracy issues

**Already Completed:**
- Test run on corner_test.png
- Accuracy report generated (24.6% error - FAIL)
- Root cause identified (blend-overlaps not creating C+M overlap)
- Follow-up bug card created (01gzl3)