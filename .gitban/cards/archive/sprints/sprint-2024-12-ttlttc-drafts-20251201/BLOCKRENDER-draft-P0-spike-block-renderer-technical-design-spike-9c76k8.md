# Spike: Block Renderer Technical Design

## Problem Statement

**Decision**: Design a block-based rendering approach for reconstituting CMYK cluster data with 100% pixel accuracy.

The current bullseye renderer achieves ~91% accuracy because circle areas (π*r²) cannot exactly represent integer pixel counts. A block/bar approach uses rectangles which can exactly match any pixel count since area = width × height (both integers).

**Core Concept**: For each cluster at (x, y), render a horizontal bar where each color segment's length is exactly proportional to its pixel count. The bar height is fixed, so segment_length = pixel_count / bar_height.

---

## Time Box

**Maximum Time**: 4 hours

---

## Success Criteria

**We'll know this spike is successful when**:
- [x] Architecture options identified and evaluated
- [ ] Clear recommendation made with rationale
- [ ] Trade-offs documented
- [ ] Implementation approach documented for feature cards

---

## Solution Options

### Option 1: Horizontal Stacked Bar per Cluster

**Description**: Each cluster rendered as a single horizontal bar centered at (x, y). Colors stacked left-to-right in layer order (yellow → black). Bar height fixed (e.g., cluster radius × 2), segment widths = pixel_count / bar_height.

**Pros**:
- Simple geometry - rectangles are trivial to draw
- 100% pixel accuracy achievable (width × height = exact count)
- Fast rendering using cv2.rectangle
- Easy to visualize color distribution

**Cons**:
- Loses circular/dot appearance of original halftone
- Bars may overlap for tightly-packed clusters
- Visual representation differs significantly from source

**Complexity**: Low

### Option 2: Vertical Stacked Bar per Cluster

**Description**: Same as Option 1 but vertical orientation. Colors stacked bottom-to-top.

**Pros**:
- Same accuracy benefits as horizontal
- May fit better in some grid patterns

**Cons**:
- Same visual departure from source
- Vertical bars may look less natural for halftone representation

**Complexity**: Low

### Option 3: Grid/Tile Approach

**Description**: Divide the image into a grid where each cell represents one cluster. Fill each cell with colored pixels matching exact counts.

**Pros**:
- 100% accuracy
- More distributed visual representation

**Cons**:
- More complex geometry
- Requires calculating cell boundaries
- May not align well with detected cluster positions

**Complexity**: Medium

---

## Comparison Matrix

| Criteria | Horizontal Bar | Vertical Bar | Grid/Tile | Weight |
|----------|----------------|--------------|-----------|--------|
| Pixel Accuracy | 100% | 100% | 100% | High |
| Implementation Complexity | Low | Low | Medium | High |
| Visual Clarity | Good | Good | Better | Medium |
| Performance | Fast | Fast | Medium | Medium |
| Alignment with Clusters | Good | Good | Poor | Medium |

---

## Recommendation

**Decision**: Option 1 - Horizontal Stacked Bar

**Rationale**: 
1. Achieves the primary goal of 100% pixel accuracy
2. Simplest implementation - can be done in one feature card
3. Maintains cluster positioning (centered at detected (x, y))
4. Fast rendering with cv2.rectangle
5. Color order (yellow outer → black inner) still visible left-to-right

**Confidence Level**: High

**Risks**: 
- Visual output differs significantly from bullseye approach
- Overlapping bars for dense clusters

**Mitigations**:
- Keep bullseye renderer as alternative visualization
- Add CLI flag to choose rendering method: `--render-method bullseye|block`

---

## Technical Design

### Data Flow

```
ClusterResult(x, y, cyan, magenta, yellow, black, red, green, blue)
    ↓
calculate_bar_dimensions(cluster, bar_height)
    → Dict[color, (x_start, x_end)]
    ↓
render_single_block(cluster, image, bar_height)
    → cv2.rectangle for each color segment
    ↓
render_blocks(clusters, image_shape, bar_height)
    → Full reconstituted image
```

### Key Functions

```python
def calculate_bar_dimensions(
    cluster: ClusterResult,
    bar_height: int
) -> Dict[str, Tuple[int, int, int, int]]:
    """Calculate rectangle bounds for each color segment.
    
    Returns:
        Dict mapping color → (x1, y1, x2, y2) for cv2.rectangle
    """
    pass

def render_single_block(
    cluster: ClusterResult,
    image: np.ndarray,
    bar_height: int
) -> None:
    """Render one cluster as a horizontal color bar."""
    pass

def render_blocks(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    bar_height: int = 20,
    skip_partial: bool = False
) -> np.ndarray:
    """Render all clusters as block patterns.
    
    Main entry point - analogous to render_bullseye().
    """
    pass
```

### Pixel Accuracy Math

For a color with N pixels and bar height H:
- Segment width = N / H (integer division)
- Actual pixels = width × H
- Remainder = N % H

To achieve exactly N pixels:
- Use width = N // H
- If remainder > 0, add partial row or distribute

**Exact approach**: Use width = ceil(N / H), then clip to exact N pixels by:
1. Draw full rectangle
2. Count pixels drawn
3. If over, mask off excess

Or simpler: Accept slight inaccuracy from integer division (error < H pixels per segment).

---

## Deliverables

**Recommended outputs**:
- [ ] Architecture Decision Record using `docs-adr.md` template
- [x] Technical design doc (this spike card)
- [ ] Implementation cards created

**Created artifacts**:
- ADR: To be created
- Feature cards: To be created

---

## Next Steps

**If recommendation accepted**:
- [ ] Create feature card: Implement block_renderer.py
- [ ] Create feature card: Integrate block renderer into CLI
- [ ] Create test card: Write unit tests for block renderer
- [ ] Create chore card: Sprint close-out verification
