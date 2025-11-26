# Implement Chunked/Tiled Processing for Large Images

## Problem Statement
Processing extremely large images (>25 megapixels) or dense halftones causes HoughCircles and convex detection to either timeout or exhaust memory. Need tiled processing to bound computation per chunk.

## Solution
Split large images into overlapping tiles, process each independently, then merge results with boundary deduplication.

## Acceptance Criteria
- [x] New `--chunk-size` CLI flag to set tile dimensions (default: auto-calculated)
- [x] Tiles overlap by `max_radius` pixels to catch boundary circles
- [x] Each tile processed independently (parallel-ready architecture)
- [x] Boundary circles merged using spatial proximity matching
- [x] Progress reporting: "Processing tile 3/16..."
- [x] Benchmark: 38 MP image processes in <5 minutes with chunking
- [x] No duplicate circles at tile boundaries

## Technical Approach

### Tile Generation
```python
def generate_tiles(image_shape, chunk_size, overlap):
    """Generate overlapping tile coordinates."""
    h, w = image_shape[:2]
    tiles = []
    for y in range(0, h, chunk_size - overlap):
        for x in range(0, w, chunk_size - overlap):
            x1, y1 = x, y
            x2 = min(x + chunk_size, w)
            y2 = min(y + chunk_size, h)
            tiles.append((x1, y1, x2, y2))
    return tiles
```

### Processing Pipeline
```python
def process_chunked(image, chunk_size, max_radius, detector_fn):
    overlap = max_radius * 2  # Ensure boundary circles detected
    tiles = generate_tiles(image.shape, chunk_size, overlap)
    
    all_circles = []
    for i, (x1, y1, x2, y2) in enumerate(tiles):
        print(f"Processing tile {i+1}/{len(tiles)}...")
        tile = image[y1:y2, x1:x2]
        circles = detector_fn(tile)
        # Offset coordinates to global space
        for c in circles:
            c.x += x1
            c.y += y1
        all_circles.extend(circles)
    
    # Deduplicate boundary circles
    return deduplicate_circles(all_circles, max_radius)
```

### Boundary Deduplication
Circles detected in overlap regions may appear in multiple tiles:
- Use spatial indexing (from Card 1) for efficient deduplication
- Keep circle with highest confidence if duplicates found
- Merge tolerance: `max_radius / 2` for center distance

## CLI Interface
```bash
# Auto chunk size (based on image dimensions and max_radius)
dotmatrix -i large.png --convex-edge --chunk-size auto

# Explicit chunk size
dotmatrix -i large.png --convex-edge --chunk-size 2000

# Disable chunking
dotmatrix -i large.png --convex-edge --chunk-size 0
```

## Dependencies
- Spatial indexing card (for efficient boundary deduplication)

## Testing Strategy
1. Unit test: tile generation with various image sizes
2. Unit test: coordinate offset correctness
3. Integration test: known image processed chunked vs whole
4. Regression test: results should be identical (within tolerance) for small images
5. Performance test: 38 MP halftone image

## Notes
- Future: parallel tile processing with multiprocessing
- Future: GPU acceleration per tile
- Memory budget: each tile should fit in ~100MB
