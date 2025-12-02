## Purpose

**CMYK Pixel Counting Accuracy Test** - Reconstituted Image Validation

Validate that the flower renderer reconstitutes images with accurate CMYK pixel counts by comparing source and output using subtractive color decomposition.

**Value**: Provides a quantitative accuracy metric for the entire detection→rendering pipeline. Unlike visual inspection, this gives hard numbers for regression testing.

**Estimated Effort**: 2-4 hours

---

## The Core Algorithm

The test implements **subtractive color decomposition** to extract pure CMYK counts from RGB images:

### Subtractive CMY Color Model

In subtractive color mixing (like print/ink), combining primary colors creates secondary colors:

| Combination | Result | Why |
|-------------|--------|-----|
| Magenta + Yellow | **Red** | Absorbs G and B, reflects R |
| Cyan + Yellow | **Green** | Absorbs R and B, reflects G |
| Cyan + Magenta | **Blue** | Absorbs R and G, reflects B |
| C + M + Y | **Black** | Absorbs all (theoretical) |

### Decomposition Logic

When we see a secondary color in an image, we need to **attribute it back to its primaries**:

```python
def decompose_pixel_to_cmyk(rgb_pixel):
    """
    Decompose any pixel to CMYK contributions.

    Key insight: Secondary colors are combinations of primaries:
    - Red pixel → contributes to BOTH Magenta AND Yellow
    - Green pixel → contributes to BOTH Cyan AND Yellow
    - Blue pixel → contributes to BOTH Cyan AND Magenta
    """
    r, g, b = rgb_pixel

    # Primary colors (contribute to single channel)
    cyan_contrib = 1 if is_cyan(pixel) else 0
    magenta_contrib = 1 if is_magenta(pixel) else 0
    yellow_contrib = 1 if is_yellow(pixel) else 0
    black_contrib = 1 if is_black(pixel) else 0

    # Secondary colors (contribute to TWO channels each)
    if is_red(pixel):      # Red = M + Y
        magenta_contrib += 1
        yellow_contrib += 1
    if is_green(pixel):    # Green = C + Y
        cyan_contrib += 1
        yellow_contrib += 1
    if is_blue(pixel):     # Blue = C + M
        cyan_contrib += 1
        magenta_contrib += 1

    return {'c': cyan_contrib, 'm': magenta_contrib, 'y': yellow_contrib, 'k': black_contrib}
```

### Full Image Decomposition

```python
def decompose_to_cmyk(image_path: str, tolerance: int = 20) -> dict:
    """
    Decompose entire image to CMYK pixel counts.

    Returns:
        {'cyan': int, 'magenta': int, 'yellow': int, 'black': int,
         'total_primary': int, 'total_secondary': int}

    Note: Total counts may exceed pixel count because secondary colors
    contribute to multiple channels.
    """
    img = cv2.imread(image_path)  # BGR format

    # Define color ranges (BGR format for OpenCV)
    COLORS = {
        'black':   (0, 0, 0),
        'cyan':    (255, 255, 0),    # BGR
        'magenta': (255, 0, 255),    # BGR
        'yellow':  (0, 255, 255),    # BGR
        'red':     (0, 0, 255),      # BGR (secondary: M+Y)
        'green':   (0, 255, 0),      # BGR (secondary: C+Y)
        'blue':    (255, 0, 0),      # BGR (secondary: C+M)
    }

    # Count each color with tolerance for anti-aliasing
    counts = {name: count_color(img, bgr, tolerance) for name, bgr in COLORS.items()}

    # Decompose to CMYK
    return {
        'cyan':    counts['cyan'] + counts['green'] + counts['blue'],
        'magenta': counts['magenta'] + counts['red'] + counts['blue'],
        'yellow':  counts['yellow'] + counts['red'] + counts['green'],
        'black':   counts['black'],
        # Diagnostic info
        'primary_pixels': counts['cyan'] + counts['magenta'] + counts['yellow'] + counts['black'],
        'secondary_pixels': counts['red'] + counts['green'] + counts['blue'],
        'raw_counts': counts
    }
```

---

## Tasks

### Phase 1: Core Module

- [ ] **Task 1**: Create `src/dotmatrix/cmyk_accuracy.py` module
  - `count_color(img, bgr, tolerance) -> int` - count pixels matching color
  - `decompose_to_cmyk(image_path, tolerance) -> dict` - full decomposition
  - Handle BGR vs RGB correctly (OpenCV uses BGR)
  - Handle white/background pixels (ignore them)

- [ ] **Task 2**: Unit tests for decomposition
  - Test with synthetic images (known exact colors)
  - Test tolerance handling for anti-aliased edges
  - Test secondary color decomposition (red→M+Y, etc.)

### Phase 2: Comparison Function

- [ ] **Task 3**: Implement `compare_cmyk_vectors(source: dict, reconstituted: dict) -> dict`
  - Per-channel absolute difference
  - Per-channel percentage error
  - Total weighted error metric
  - Pass/fail threshold evaluation

```python
def compare_cmyk_vectors(source: dict, recon: dict, threshold: float = 0.10) -> dict:
    """
    Compare CMYK vectors and calculate accuracy metrics.

    Returns:
        {
            'per_channel': {'cyan': {'diff': 100, 'pct': 0.05}, ...},
            'total_error': 0.03,
            'passed': True,
            'threshold': 0.10
        }
    """
```

### Phase 3: E2E Test

- [ ] **Task 4**: Create `tests/test_cmyk_accuracy.py`
  - `test_decompose_synthetic_cmyk` - synthetic image with known colors
  - `test_decompose_synthetic_secondary` - image with red/green/blue
  - `test_reconstituted_cmyk_matches_source` - full pipeline test
  - `test_accuracy_with_blend_mode` - test with `--blend-overlaps`

### Phase 4: CLI Integration (Optional)

- [ ] **Task 5**: Add `--verify-accuracy` flag to CLI
  - Run decomposition on source and output
  - Print accuracy report
  - Return non-zero exit code if threshold exceeded

---

## Test Scenarios

### Happy Path

| Test | Setup | Expected | Threshold |
|------|-------|----------|-----------|
| Basic CMYK | Halftone with pure CMYK | <5% error per channel | 5% |
| With Blending | `--blend-overlaps` enabled | <10% error (blending creates secondary colors) | 10% |
| Dense Overlap | Heavy circle overlap | <15% error | 15% |

### Edge Cases

- [ ] **Pure Black Only**: Image with only K dots, verify C/M/Y = 0
- [ ] **Single Color**: Image with only cyan dots
- [ ] **No Black**: Image with only CMY, no K
- [ ] **Secondary Colors**: Source has red/green/blue from blending
- [ ] **Size Mismatch**: What if reconstituted has more total pixels? (petal geometry can add area)
- [ ] **Anti-aliasing Heavy**: Source with many edge pixels (tests tolerance)

### Error Conditions

- [ ] **Missing Input**: Source file not found
- [ ] **Wrong Format**: Non-image file passed
- [ ] **Empty Image**: All white/transparent

---

## Acceptance Criteria

### Functional
- [ ] `decompose_to_cmyk()` correctly handles all 7 colors (C, M, Y, K, R, G, B)
- [ ] Secondary colors decompose to correct primaries (red→M+Y verified)
- [ ] Tolerance parameter handles anti-aliased edges
- [ ] Comparison function calculates meaningful error metrics

### Tests
- [ ] Unit tests for synthetic images (100% pass)
- [ ] E2E test on real halftone image passes with <10% error
- [ ] Tests are deterministic (no flaky behavior)
- [ ] Full test suite runs in <30 seconds

### Documentation
- [ ] Docstrings explain subtractive color model
- [ ] Example usage in module docstring
- [ ] Test file documents expected accuracy thresholds

---

## Diagnostic Output Format

When running accuracy tests, output detailed report:

```
=== CMYK Accuracy Report ===

Source: inputs/halftone_cmyk.png
Reconstituted: output/run_20251129/reconstituted.png

--- Decomposition ---
         Source    Recon     Diff    Error
Cyan:    12,456    12,301    -155    -1.2%
Magenta: 8,234     8,445     +211    +2.6%
Yellow:  15,678    15,890    +212    +1.4%
Black:   22,100    21,950    -150    -0.7%

Secondary colors detected:
  Source:  Red=234, Green=156, Blue=89
  Recon:   Red=312, Green=201, Blue=112

--- Summary ---
Total Error: 1.5% (weighted average)
Threshold:   10.0%
Result:      PASS

```

---

## Implementation Notes

### Color Matching with Tolerance

```python
def is_color_match(pixel_bgr: tuple, target_bgr: tuple, tolerance: int) -> bool:
    """Check if pixel matches target within tolerance."""
    return all(abs(p - t) <= tolerance for p, t in zip(pixel_bgr, target_bgr))

def count_color(img: np.ndarray, target_bgr: tuple, tolerance: int) -> int:
    """Count pixels matching target color within tolerance."""
    # Vectorized for performance
    diff = np.abs(img.astype(int) - np.array(target_bgr))
    matches = np.all(diff <= tolerance, axis=2)
    return int(np.sum(matches))
```

### Handling White/Background

White pixels (255, 255, 255) should be ignored - they're background:

```python
def count_non_white_pixels(img: np.ndarray, white_threshold: int = 250) -> int:
    """Count pixels that are NOT white/background."""
    is_white = np.all(img >= white_threshold, axis=2)
    return int(np.sum(~is_white))
```

### Why Total CMYK > Total Pixels?

Secondary colors contribute to **two** primary channels:
- 1 red pixel → +1 magenta AND +1 yellow
- So `total_cmyk_contributions >= actual_colored_pixels`

This is expected behavior, not a bug!

---

## Related Work

- **FLOWERFIX Sprint**: Fixed petal geometry and black clipping - this test validates those fixes produce accurate output
- **fit_metric.py**: Existing diff-based accuracy measurement - complementary metric
- **Visual Diff**: `output/*/diff.png` shows pixel-level differences - this test quantifies them

---

## Future Enhancements

1. **Histogram Visualization**: Plot CMYK distribution for source vs reconstituted
2. **Per-Region Analysis**: Break down accuracy by image quadrant
3. **Trend Tracking**: Store accuracy metrics across runs for regression detection
4. **Golden Image Tests**: Compare against known-good reference outputs
