## Summary

Implement a detection mode that only finds black dots, skipping CMY circle detection entirely.

## Motivation

Black dots are the most reliable detection target (highest contrast). Cell-based clustering only needs black dot centers as seed points.

## Implementation

### New Function
```python
def detect_black_dots_only(
    image_path: str,
    min_radius: int = 10,
    max_radius: int = 50,
) -> List[Tuple[int, int, int]]:
    """
    Detect only black circles in the image.
    
    Returns:
        List of (x, y, radius) tuples for each black dot center.
    """
```

### Algorithm
1. Load image and quantize to palette (just need black vs not-black)
2. Create black-only mask
3. Use existing convex detector on black mask only
4. Return list of (x, y, radius) for each detected black circle

## Acceptance Criteria

- [ ] Function returns list of black dot centers with radii
- [ ] Works with existing convex detection pipeline
- [ ] Handles edge cases (no black dots, overlapping black)
- [ ] Unit tests for black-only detection
- [ ] Performance acceptable on large images

## Dependencies

None - can start immediately

## Notes

This becomes the foundation for all cell-based operations.
