## Description

**Run Comparison Script for Color Pixel Accuracy Validation**

Create a standalone Python script that compares source images to reconstituted outputs by counting pixels per color channel and computing error metrics. This enables quick validation of detection/reconstitution quality for any completed run.

**Value**: Provides rapid quantitative feedback on detection accuracy without manual inspection. Essential for debugging radius calibration, comparing render methods, and validating CMYK mode changes.

**Target Users**: Developer (Cameron) during iterative detection tuning

**Estimated Effort**: 2-3 hours

---

## Acceptance Criteria

- [x] Script accepts a run directory path as argument
- [x] Automatically finds `input_*.png` source image in run directory
- [x] Automatically finds `reconstituted.png` output image
- [x] Counts pixels for 8 colors: white, black, cyan, magenta, yellow, red, green, blue
- [x] Displays source counts, reconstituted counts, and difference vector
- [x] Computes and displays R² (coefficient of determination) or similar accuracy metric
- [x] Handles errors gracefully (missing files, invalid paths)
- [x] Works with both Windows and WSL paths

---

## Implementation Plan

### Overview

Create a CLI script `scripts/compare_run.py` that uses OpenCV/numpy for pixel counting with configurable color thresholds. Output formatted table and summary statistics.

### Implementation Steps

1. **Create script skeleton**: Parse CLI argument for run directory path, validate path exists
   ```python
   # scripts/compare_run.py
   import sys
   from pathlib import Path
   import cv2
   import numpy as np
   ```

2. **Find input/output images**: Glob for `input_*.png` and `reconstituted.png` in run directory
   - Handle case where multiple input files exist (use first match)
   - Error if reconstituted.png missing

3. **Implement color counting**: Define BGR color ranges and count matching pixels
   ```python
   COLORS = {
       'white': ([250, 250, 250], [255, 255, 255]),
       'black': ([0, 0, 0], [5, 5, 5]),
       'cyan': ([250, 250, 0], [255, 255, 5]),
       'magenta': ([250, 0, 250], [255, 5, 255]),
       'yellow': ([0, 250, 250], [5, 255, 255]),
       'red': ([0, 0, 250], [5, 5, 255]),
       'green': ([0, 250, 0], [5, 255, 5]),
       'blue': ([250, 0, 0], [255, 5, 5]),
   }
   ```

4. **Compute difference vector and R²**: 
   - Difference = reconstituted - source (per color)
   - R² = 1 - (SS_res / SS_tot) where SS_res is sum of squared differences

5. **Format output**: Pretty-print table with counts and metrics
   ```
   Color      Source    Recon     Diff      
   ─────────────────────────────────────────
   white      10000     9850      -150
   black      500       520       +20
   cyan       1200      1180      -20
   ...
   
   R² = 0.9847
   ```

### Technical Considerations

- Use BGR color space (OpenCV native) for consistency with existing code
- Color matching should use tolerance ranges, not exact matches
- Consider adding `--tolerance` flag for adjustable thresholds

---

## Testing Strategy

### Manual Testing Scenarios

1. **Happy Path**: Run on valid run directory with both images present
   ```bash
   python scripts/compare_run.py output/run_20251129_142642
   ```

2. **Error Handling**: Test with missing reconstituted.png, invalid path, empty directory

---

## Notes

### Design Decisions

- **Standalone script vs CLI subcommand**: Standalone script is faster to implement and easier to iterate on. Can be promoted to CLI subcommand later if useful.
- **R² metric**: Standard regression metric that's intuitive (1.0 = perfect match, lower = worse)

### Open Questions

- **Q**: Should we also output total pixel count to verify images are same size?
- **A**: Yes, add as sanity check

- **Q**: Should we support comparing specific color channels only?
- **A**: Future enhancement, not MVP
