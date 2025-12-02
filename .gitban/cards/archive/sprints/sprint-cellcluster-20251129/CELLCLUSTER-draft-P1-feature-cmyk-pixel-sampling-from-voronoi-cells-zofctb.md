## Summary

Sample CMYK pixel counts from each Voronoi cell, creating ground-truth color data for rendering.

## Motivation

Instead of detecting CMY circles, we directly count pixels of each color within each cell. This gives us ground truth for what the flower renderer needs to reproduce.

## Implementation

```python
@dataclass
class CellCMYK:
    cell: Cell
    cyan: int      # Pixel count
    magenta: int   # Pixel count
    yellow: int    # Pixel count
    black: int     # Pixel count

def sample_cmyk_from_cell(
    image: np.ndarray,
    cell: Cell,
    tolerance: int = 20,
) -> CellCMYK:
    """Count CMYK pixels within a cell."""
```

### Algorithm
1. Apply cell mask to image
2. For each color (C, M, Y, K):
   - Count pixels within tolerance of target color
   - Handle secondary colors (R, G, B) -> decompose to primaries
3. Return CellCMYK with counts

## Acceptance Criteria

- [ ] Accurate CMYK counts from cell regions
- [ ] Uses same color tolerance as existing decompose_to_cmyk
- [ ] Secondary colors decomposed correctly (B=C+M, G=C+Y, R=M+Y)
- [ ] Integration with Cell data structure
- [ ] Unit tests for sampling accuracy

## Dependencies

- Voronoi Cell Generation (need cell masks)

## Notes

Reuse color matching logic from cmyk_accuracy.py module.
