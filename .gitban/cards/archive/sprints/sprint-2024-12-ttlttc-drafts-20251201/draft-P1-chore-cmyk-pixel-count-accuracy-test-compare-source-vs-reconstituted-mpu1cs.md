## Purpose

**CMYK Pixel Counting Accuracy Test** - Reconstituted Image Validation

Validate that the flower renderer reconstitutes images with accurate CMYK pixel counts by comparing source and output using subtractive color decomposition.

**Value**: Provides a quantitative accuracy metric for the entire detection→rendering pipeline. Unlike visual inspection, this gives hard numbers for regression testing.

**Estimated Effort**: 2-4 hours

---

## The Core Algorithm

The test implements **subtractive color decomposition** to extract pure CMYK counts from RGB images:

**Color Math (Subtractive CMY Model)**:
- Red = Magenta + Yellow (M+Y absorbs G and B, reflects R)
- Green = Cyan + Yellow (C+Y absorbs R and B, reflects G)  
- Blue = Cyan + Magenta (C+M absorbs R and G, reflects B)

**Decomposition Logic**:
```
For each pixel in image:
  Yellow += Y channel (from direct yellow OR from red)
  Magenta += M channel (from direct magenta OR from red)
  Cyan += C channel (unchanged)
  Black += K channel (unchanged)
```

**More specifically**:
- `yellow_total = pure_yellow_pixels + red_pixels` (because red = M + Y)
- `magenta_total = pure_magenta_pixels + red_pixels` (because red = M + Y)
- `cyan_total = pure_cyan_pixels` (cyan doesn't combine to make other colors in source)
- `black_total = pure_black_pixels`

---

## Tasks

### Phase 1: CMYK Decomposition Function

- [ ] **Task 1**: Implement `decompose_to_cmyk(image_path) -> dict`
  - Handle BGR vs RGB correctly (OpenCV uses BGR)
  - Define CMYK color ranges with tolerance
  - Count pure colors + decompose composite colors (red → M+Y)

```python
def decompose_to_cmyk(image_path: str, tolerance: int = 20) -> dict:
    """
    Decompose image to CMYK pixel counts using subtractive color model.
    
    Returns:
        {'cyan': int, 'magenta': int, 'yellow': int, 'black': int}
        
    Note: Red pixels contribute to BOTH magenta and yellow counts
    because red = magenta + yellow in subtractive color model.
    """
    img = cv2.imread(image_path)
    
    # Define color ranges (BGR format)
    BLACK = (0, 0, 0)
    CYAN = (255, 255, 0)     # BGR
    MAGENTA = (255, 0, 255)  # BGR  
    YELLOW = (0, 255, 255)   # BGR
    RED = (0, 0, 255)        # BGR
    
    # Count each color (with tolerance for anti-aliasing)
    black_count = count_color(img, BLACK, tolerance)
    cyan_count = count_color(img, CYAN, tolerance)
    magenta_pure = count_color(img, MAGENTA, tolerance)
    yellow_pure = count_color(img, YELLOW, tolerance)
    red_count = count_color(img, RED, tolerance)
    
    # Decompose red into M+Y contribution
    return {
        'cyan': cyan_count,
        'magenta': magenta_pure + red_count,  # Red = M+Y
        'yellow': yellow_pure + red_count,     # Red = M+Y
        'black': black_count
    }
```

### Phase 2: Comparison Function

- [ ] **Task 2**: Implement `compare_cmyk_vectors(source, reconstituted) -> dict`
  - Calculate per-channel error percentage
  - Calculate total error
  - Return detailed metrics for debugging

### Phase 3: E2E Test

- [ ] **Task 3**: Write pytest test `test_cmyk_accuracy.py::test_reconstituted_cmyk_matches_source`
  - Load real halftone source image
  - Run full pipeline (detection + reconstitution)
  - Decompose both images
  - Assert accuracy within threshold

### Phase 4: Integration

- [ ] **Task 4**: Add test to test suite and verify CI passes

---

## Test Scenarios

### Happy Path

1. **Basic CMYK Accuracy Test**:
   - Setup: Load halftone source image
   - Action: Decompose source to [C,M,Y,K], run pipeline, decompose reconstituted
   - Expected: Vectors within tolerance (e.g., 10% per channel)
   - Test: `assert abs(source_vec - recon_vec) / source_vec < 0.10`

### Edge Cases

- [ ] Image with only black dots (no CMY)
- [ ] Image with only cyan dots (no MYK)
- [ ] Image with heavy overlap (tests CMY blending)
- [ ] What if reconstituted has more pixels than source? (possible with petal geometry)

---

## Acceptance Criteria

- [ ] `decompose_to_cmyk()` function implemented and unit tested
- [ ] `compare_cmyk_vectors()` function implemented
- [ ] E2E accuracy test runs successfully on reference image
- [ ] Per-channel error < 10% (threshold configurable)
- [ ] Test is deterministic (no flaky behavior)
- [ ] Test runs in < 30 seconds

---

## Notes

### Why This Test Matters

Current testing is visual/subjective. This test provides:
1. **Quantitative accuracy metric** for pipeline validation
2. **Regression detection** when changes affect output
3. **Ground truth comparison** for different algorithm versions

### Color Math Reference

**Subtractive CMY Model**:
```
Cyan + Magenta = Blue (absorbs R and G)
Cyan + Yellow = Green (absorbs R and B)
Magenta + Yellow = Red (absorbs G and B)
```

### Tolerance Considerations

Anti-aliased pixels will have intermediate colors. The decomposition needs tolerance:
- Exact match: `pixel == color`
- With tolerance: `all(abs(pixel[i] - color[i]) <= tolerance for i in range(3))`

---

## Related Cards

**Tests**: FLOWERFIX sprint - validates the petal geometry and black clipping fixes produce accurate output
