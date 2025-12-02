## Summary

Create an adapter that converts CellCMYK data into ClusterInfo objects compatible with the existing flower renderer.

## Motivation

The flower renderer expects ClusterInfo objects with specific fields. We need to bridge cell-based data to this interface without modifying the renderer.

## Implementation

```python
def cell_to_cluster(cell_cmyk: CellCMYK) -> ClusterInfo:
    """Convert cell-based CMYK data to ClusterInfo for rendering."""
    return ClusterInfo(
        black_center=cell_cmyk.cell.center,
        black_radius=cell_cmyk.cell.radius,
        color_circles=[
            # Synthesize circle data from pixel counts
            # Each CMY color becomes a "virtual circle"
        ],
    )

def cells_to_clusters(
    cells: List[CellCMYK],
) -> List[ClusterInfo]:
    """Convert all cells to clusters for batch rendering."""
```

### Key Design Decisions

1. **Pixel counts to circle radius**: How to convert N cyan pixels to a petal radius?
   - Option A: sqrt(N / pi) = equivalent circle radius
   - Option B: Scale proportionally to black dot radius

2. **Circle positions**: Where to place virtual CMY circles?
   - Use fixed petal positions around black center (like flower renderer expects)

## Acceptance Criteria

- [ ] Adapter converts CellCMYK to ClusterInfo
- [ ] Output compatible with existing flower renderer
- [ ] Pixel count to radius conversion is sensible
- [ ] All existing render options work (rotation, blend, etc.)
- [ ] Unit tests for adapter logic

## Dependencies

- CMYK Pixel Sampling (need CellCMYK data)

## Notes

This is the bridge between the new cell-based system and existing rendering code.
