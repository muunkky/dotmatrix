# Integrate Spatial Indexing with Chunked Processing

## Problem Statement
After implementing spatial indexing (Card 1) and chunked processing (Card 2), we need to integrate them for optimal performance on extremely large/dense images.

## Solution
Combine chunked processing with spatial indexing for both intra-chunk and inter-chunk deduplication.

## Acceptance Criteria
- [ ] Chunked processing uses spatial indexing within each tile
- [ ] Boundary deduplication uses spatial indexing across tiles
- [ ] Combined approach handles 38 MP halftone in <3 minutes
- [ ] Memory usage stays under 500MB for any image size
- [ ] Progress reporting shows both tile progress and overall progress

## Technical Approach

### Architecture
```
Large Image
    │
    ▼
┌─────────────────────────────┐
│    Tile Generator           │
│  (overlap = 2 * max_radius) │
└─────────────────────────────┘
    │
    ▼ (parallel-ready)
┌─────────────────────────────┐
│  Per-Tile Processing        │
│  ├── Color Quantization     │
│  ├── Convex Edge Detection  │
│  └── Spatial Dedup (local)  │  ← KD-tree per tile
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Global Merge               │
│  └── Spatial Dedup (global) │  ← KD-tree for all results
└─────────────────────────────┘
    │
    ▼
Final Circle List
```

### Implementation Strategy
```python
def process_large_image(image, max_radius, chunk_size=None):
    # Auto chunk size if not specified
    if chunk_size is None:
        chunk_size = calculate_adaptive_chunk_size(image, max_radius)
    
    # Generate overlapping tiles
    tiles = generate_tiles(image.shape, chunk_size, overlap=max_radius*2)
    
    all_circles = []
    for i, tile_coords in enumerate(tiles):
        # Process tile
        tile_circles = process_tile(image, tile_coords, max_radius)
        
        # Local deduplication with spatial indexing
        tile_circles = spatial_deduplicate(tile_circles, max_radius)
        
        # Offset to global coordinates
        offset_circles(tile_circles, tile_coords)
        all_circles.extend(tile_circles)
    
    # Global deduplication for boundary circles
    final_circles = spatial_deduplicate(all_circles, max_radius)
    
    return final_circles
```

## Performance Targets
| Image Size | Circle Count | Target Time | Memory |
|------------|--------------|-------------|--------|
| 10 MP | 1,000 | <5s | <100MB |
| 25 MP | 10,000 | <30s | <200MB |
| 38 MP | 50,000 | <3min | <500MB |
| 100 MP | 100,000 | <10min | <1GB |

## Dependencies
- Card 1: Spatial Indexing (must be complete)
- Card 2: Chunked Processing (must be complete)
- Card 3: Adaptive Chunk Sizing (research complete)

## Testing Strategy
1. Integration test: combined approach matches separate approaches
2. Performance benchmark: 38 MP halftone image (our test file)
3. Memory profiling with `memory_profiler`
4. Stress test: 100 MP synthetic image

## Future Considerations
- Parallel tile processing with `concurrent.futures`
- GPU acceleration for Hough transform per tile
- Streaming output for very large result sets
