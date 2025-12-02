# Feature: Implement Block Renderer Module

## Description

Implement `block_renderer.py` - a new rendering module that reconstitutes cluster data as horizontal stacked color bars for 100% pixel accuracy.

**Value**: Achieves 100% pixel accuracy in reconstituted images by using rectangular geometry instead of circles. Current bullseye approach achieves ~91% due to π*r² rounding.

**Target Users**: Developers and users who need exact pixel count preservation in reconstituted halftone images.

**Estimated Effort**: 4-6 hours

---

## Acceptance Criteria

- [x] New file `src/dotmatrix/block_renderer.py` created
- [x] `calculate_bar_dimensions()` function implemented
- [x] `render_single_block()` function implemented
- [x] `render_blocks()` main entry point implemented
- [x] All 7 colors rendered (cyan, magenta, yellow, black, red, green, blue)
- [x] Colors rendered in correct layer order (yellow outer → black inner)
- [x] BGR color format used throughout (cv2 native)
- [x] Pixel accuracy verified at 100% for integer-divisible cases
- [x] Function signatures match cluster_renderer.py patterns
- [x] Docstrings follow existing project conventions
- [x] **Height mode parameter implemented** with at least `fixed-segment` mode
- [x] `fixed-segment` mode: all color segments same height, widths vary (for midtone printer overlap)
- [x] Additional height modes as time permits: `fixed-bar`, `variable`, `min-height`

---

## Implementation Plan

### Overview

Create a new renderer module parallel to `cluster_renderer.py` that renders clusters as horizontal stacked bars instead of concentric circles. Each color segment's width = pixel_count / bar_height, achieving exact pixel counts.

### Implementation Steps

1. **Create block_renderer.py skeleton**
   - Create new file at `src/dotmatrix/block_renderer.py`
   - Add module docstring explaining block approach
   - Import dependencies: numpy, cv2, ClusterResult, typing
   - Define COLORS dict (copy from cluster_renderer.py)
   - Define LAYER_ORDER (copy from cluster_renderer.py)

2. **Implement calculate_bar_dimensions()**
   - Input: ClusterResult, segment_height (int), height_mode (str)
   - Support height modes:
     - `fixed-segment`: Each color gets same height row, width = pixels / segment_height
       - Total bar height = 7 × segment_height (one row per color)
       - Colors stack vertically, easy for printer overlap
     - `fixed-bar`: All bars same total height, segment widths vary
     - `variable`: Bar height scales with total pixel count
     - `min-height`: Minimum height enforced
   - For `fixed-segment` mode (primary implementation):
     - Each color rendered as horizontal stripe of height=segment_height
     - Stripe width = pixel_count / segment_height
     - Colors stacked top-to-bottom in LAYER_ORDER
   - Return Dict[str, Tuple[int, int, int, int]] for each color's rectangle bounds

3. **Implement render_single_block()**
   - Input: ClusterResult, image (np.ndarray), bar_height (int)
   - Call calculate_bar_dimensions()
   - For each color in LAYER_ORDER:
     - Get bounds from dimensions dict
     - cv2.rectangle(image, (x1, y1), (x2, y2), COLORS[color], -1)
   - Return modified image

4. **Implement render_blocks() main entry point**
   - Input: List[ClusterResult], image_shape, bar_height=20, skip_partial=False
   - Create white background image
   - For each cluster:
     - Skip if partial and skip_partial=True
     - Call render_single_block()
   - Return final image

### Technical Considerations

- **Pixel accuracy**: Use integer division for widths, accept error < bar_height per color
- **Bar positioning**: Center bar at (cluster.x, cluster.y - bar_height/2)
- **Overlap handling**: Later clusters overwrite earlier ones (same as bullseye)
- **Edge clipping**: Bars extending past image bounds are clipped by numpy array bounds

### Dependencies

- numpy
- cv2 (opencv-python)
- ClusterResult from cluster_pixel_counter.py

---

## Testing Strategy

### Unit Tests

- [x] Test calculate_bar_dimensions returns correct bounds
- [x] Test render_single_block draws all 7 colors
- [x] Test render_blocks handles empty cluster list
- [x] Test pixel counts match expected (within bar_height tolerance)
- [x] Test BGR color format is correct

### Integration Tests

- [x] Test end-to-end with real ClusterResult data
- [x] Compare pixel counts between source and block-rendered output

---

## Related Cards

**Depends on**: hgcp2f - Block renderer technical design spike

**Blocks**: CLI integration card (to be created)

---

## Notes

### Design Decisions

- **Decision**: Use horizontal bars (not vertical)
- **Rationale**: More natural left-to-right color progression matching LAYER_ORDER
- **Trade-offs**: Visual output differs from circular halftone appearance

### Code Structure

```python
# block_renderer.py

COLORS = {...}  # Same as cluster_renderer.py
LAYER_ORDER = [...]  # Same as cluster_renderer.py

def calculate_bar_dimensions(cluster: ClusterResult, bar_height: int) -> Dict[str, Tuple]:
    pass

def render_single_block(cluster: ClusterResult, image: np.ndarray, bar_height: int) -> np.ndarray:
    pass

def render_blocks(clusters: List[ClusterResult], image_shape: Tuple[int, int], 
                  bar_height: int = 20, skip_partial: bool = False) -> np.ndarray:
    pass
```
