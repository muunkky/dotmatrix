## Summary

Generate Voronoi cells around each black dot center, creating non-overlapping regions that cover the entire image.

## Motivation

Each pixel should belong to exactly one cell (the nearest black dot). This eliminates overlap issues and ensures 100% coverage.

## Implementation

### New Module: cell_partitioner.py

```python
from scipy.spatial import Voronoi
import numpy as np

@dataclass
class Cell:
    center: Tuple[int, int]  # Black dot center
    radius: int              # Black dot radius
    polygon: np.ndarray      # Voronoi cell vertices
    mask: np.ndarray         # Boolean mask for this cell

def create_voronoi_cells(
    black_dots: List[Tuple[int, int, int]],
    image_shape: Tuple[int, int],
) -> List[Cell]:
    """Create Voronoi cells around black dot centers."""
```

### Algorithm
1. Extract (x, y) from black_dots as seed points
2. Add boundary points to ensure all cells are finite
3. Create scipy.spatial.Voronoi
4. Clip cells to image bounds
5. Generate boolean mask for each cell

## Acceptance Criteria

- [ ] Voronoi cells generated from black dot centers
- [ ] All cells properly clipped to image bounds
- [ ] Every pixel belongs to exactly one cell
- [ ] Cell masks can be used for CMYK sampling
- [ ] Unit tests for cell generation
- [ ] Edge cases handled (dots near borders)

## Dependencies

- Black Dot Detection Only Mode (need dot centers)

## Notes

scipy.spatial.Voronoi may create infinite regions at edges - need to handle with boundary points.
