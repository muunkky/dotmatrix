# Chore: Write Unit Tests for Block Renderer Module

## Description

Create comprehensive unit tests for `block_renderer.py` module to ensure 100% pixel accuracy in block-based reconstitution and prevent regressions.

---

## Acceptance Criteria

- [ ] Test file `tests/test_block_renderer.py` created
- [ ] Tests for `calculate_bar_dimensions()` function
- [ ] Tests for `render_single_block()` function  
- [ ] Tests for `render_blocks()` main entry point
- [ ] Edge case tests (empty list, zero counts, single color)
- [ ] Pixel accuracy verification tests
- [ ] BGR color format verification tests
- [ ] 95%+ code coverage achieved for block_renderer.py

---

## Implementation Plan

### Test Classes

1. **TestCalculateBarDimensions**
   - `test_basic_calculation_returns_dict`
   - `test_all_colors_included_in_output`
   - `test_segments_sum_to_total_width`
   - `test_zero_count_color_has_zero_width`
   - `test_centering_at_cluster_position`

2. **TestRenderSingleBlock**
   - `test_renders_all_seven_colors`
   - `test_colors_are_bgr_format`
   - `test_bar_centered_at_cluster_position`
   - `test_bar_height_parameter_respected`

3. **TestRenderBlocks**
   - `test_empty_cluster_list_returns_white_image`
   - `test_multiple_clusters_all_rendered`
   - `test_skip_partial_excludes_partial_clusters`
   - `test_image_shape_respected`

4. **TestPixelAccuracy**
   - `test_100_percent_accuracy_divisible_counts`
   - `test_accuracy_within_tolerance_non_divisible`
   - `test_total_colored_pixels_match_input`

### Test Fixtures

```python
@pytest.fixture
def simple_cluster():
    return ClusterResult(
        x=100, y=100,
        cyan=100, magenta=80, yellow=60, black=200,
        red=40, green=30, blue=20,
        partial=False
    )
```

### Pixel Counting Helper

```python
def count_pixels_by_color(image: np.ndarray, color_bgr: tuple) -> int:
    mask = np.all(image == color_bgr, axis=-1)
    return np.sum(mask)
```

---

## Testing Strategy

### Happy Path
- Single cluster with all 7 colors renders correctly
- Multiple clusters render at correct positions
- Bar height parameter affects output dimensions

### Edge Cases
- Empty cluster list → white image
- Zero pixel count for one color → segment omitted
- Single color only → single rectangle
- Cluster at image edge → clips correctly

### Error Conditions
- Invalid bar_height (0, negative) → appropriate error handling

---

## Related Cards

**Tests**: gsqq6k - Implement block renderer module

**Depends on**: gsqq6k must be completed first
