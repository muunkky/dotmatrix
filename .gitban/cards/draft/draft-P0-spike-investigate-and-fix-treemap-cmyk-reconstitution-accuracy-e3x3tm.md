# Troubleshooting: Treemap CMYK Reconstitution Accuracy

**Card Type**: Spike - Troubleshooting
**Status**: investigation
**Priority**: P0
**Date Started**: 2025-11-29
**Owner**: CAMERON

## Problem Statement

### Symptoms Observed
- **What is broken/not working?** Reconstituted images have very poor color accuracy compared to source images
- **Error messages or unexpected behavior**: R² = 0.19 (should be near 1.0), massive pixel count differences
- **Impact**: Reconstitution feature is unusable for validation - cannot verify detection accuracy
- **Urgency**: Core feature that blocks quality assurance of the detection pipeline

### Environment Context
- **System/Service**: dotmatrix CLI reconstitution pipeline
- **Version**: Current main branch (post-CMYK mode implementation)
- **Configuration**: `--convex-edge --palette cmyk --reconstitute --render-method treemap --color-mode cmyk`
- **Recent Changes**: Added CMYK color mode, treemap renderer, block renderer

### Test Command
```bash
python -m dotmatrix -i inputs/corner_test.png --convex-edge --palette cmyk --reconstitute --render-method treemap --color-mode cmyk --output-dir output
```

### Validation Command
```bash
python scripts/compare_run.py output/run_YYYYMMDD_HHMMSS
```

### Initial Baseline (from compare_run.py)
```
Color                Source          Recon           Diff      % Err
----------------------------------------------------------------------
white                59,123        204,881       +145,758    +246.5%
black               116,256         27,134        -89,122     -76.7%
cyan                 32,253         12,621        -19,632     -60.9%
magenta               8,821          5,344         -3,477     -39.4%
yellow                    0             20            +20       +inf
red                       0              0              0        N/A
green                     0              0              0        N/A
blue                 15,496              0        -15,496    -100.0%

R² (excluding white): 0.191041
```

---

## Investigation Progress

### Pre-Investigation Checklist
- [ ] Problem statement clearly defined
- [ ] Error messages captured verbatim
- [ ] Recent changes reviewed (git log, deployment logs)
- [ ] Similar past issues searched (gitban cards, docs, git history)
- [ ] Monitoring/logs checked for related errors
- [ ] Impact scope assessed (how many users/systems affected)

### Research Performed

#### Related Code to Investigate
- `src/dotmatrix/treemap_renderer.py` - Treemap rendering logic
- `src/dotmatrix/cluster_pixel_counter.py` - Pixel counting and clustering
- `src/dotmatrix/convex_detector.py` - Circle detection
- `src/dotmatrix/cli.py` - Pipeline orchestration

#### Potential Root Causes to Investigate
1. **Cluster size mismatch**: Treemap cluster_size (20) vs actual detection radius
2. **Color counting vs rendering disconnect**: Counted pixels not matching rendered pixels
3. **CMYK mode counting**: May be double-counting or missing pixels
4. **BGR/RGB color format issues**: Historical problem in this codebase
5. **Detection accuracy**: May be missing circles or detecting wrong radii
6. **Treemap subdivision algorithm**: May not be proportionally accurate

---

## Solution Attempts

### Attempt Log

| # | Attempt Name | Hypothesis | Outcome | Status | Notes |
|---|-------------|------------|---------|--------|-------|
| 1 | [To be filled during investigation] | [Hypothesis] | [Outcome] | ⬜ Pending | [Notes] |

### Detailed Attempt Logs

#### Attempt 1: [To be filled during investigation]

**Hypothesis**: [To be determined]

**Steps Performed**:
1. Run detection command
2. Run compare_run.py
3. Analyze diff
4. Form hypothesis
5. Make change
6. Re-test

---

## Success Criteria

### Verification
- [ ] R² > 0.90 (good match)
- [ ] R² > 0.95 (excellent match target)
- [ ] All non-white colors within 10% error
- [ ] No colors missing entirely (blue currently -100%)
- [ ] Total pixel count matches between source and recon

---

## Follow-Up Actions

### Potential Follow-Up Cards
- Fix specific bug(s) discovered during investigation
- Update documentation with findings
- Add automated accuracy tests to CI

---

## Notes

### Investigation Workflow
1. Run: `python -m dotmatrix -i inputs/corner_test.png --convex-edge --palette cmyk --reconstitute --render-method treemap --color-mode cmyk --output-dir output`
2. Check: `python scripts/compare_run.py output/run_*` (latest)
3. Analyze: Review pixel counts, identify largest discrepancy
4. Hypothesize: Form theory about root cause
5. Fix: Make targeted code change
6. Verify: Re-run steps 1-2
7. Iterate: Until R² > 0.95

### Key Questions
- Why is blue -100% (completely missing)?
- Why is black -76.7% (under-detected)?
- Why is white +246.5% (too much background)?
- Are we detecting all circles?
- Are cluster pixel counts correct?
- Is the treemap renderer drawing the right colors?
