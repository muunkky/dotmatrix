# Research Adaptive Chunk Sizing Strategy

## Problem Statement
A fixed chunk size may not be optimal for all images:
- Dense halftones: thousands of circles per chunk → O(n²) still expensive
- Sparse images: large chunks are efficient
- Mixed density: some regions dense, others sparse

Need to determine the best strategy for adaptive chunk sizing.

## Time Box
4 hours

## Research Questions
1. **Density-based sizing**: Can we estimate circle density from a sample region?
2. **Exponential backoff**: Start large, reduce if too slow?
3. **Max radius correlation**: Is `chunk_size = f(max_radius)` a good heuristic?
4. **Circle count threshold**: Process until N circles, then subdivide?
5. **Memory-based sizing**: Calculate chunk size from available RAM?

## Success Criteria
- [x] Document 3+ candidate approaches with pros/cons
- [x] Benchmark each approach on 3 test images (sparse, medium, dense)
- [x] Recommend preferred approach for implementation
- [x] Define formula or algorithm for adaptive sizing

## Candidate Approaches

### Approach 1: Fixed Size Based on Max Radius
```python
chunk_size = max(2000, max_radius * 50)
```
- Simple, predictable
- May not adapt to density

### Approach 2: Sample-Based Density Estimation
```python
def estimate_chunk_size(image, max_radius):
    # Sample 1% of image
    sample = random_sample_region(image, 0.01)
    circles = detect_circles(sample)
    density = len(circles) / sample_area
    
    # Target ~1000 circles per chunk
    target_circles = 1000
    chunk_area = target_circles / density
    return int(sqrt(chunk_area))
```
- Adapts to actual content
- Extra processing for sampling

### Approach 3: Progressive Subdivision
```python
def process_adaptive(image, max_chunk=4000, target_circles=2000):
    if detect_circle_count(image) < target_circles:
        return process_full(image)
    
    # Subdivide into 4 quadrants
    quadrants = split_into_quadrants(image)
    results = []
    for q in quadrants:
        results.extend(process_adaptive(q, max_chunk, target_circles))
    return deduplicate(results)
```
- Naturally adapts to density variations
- Recursive overhead

### Approach 4: Exponential Backoff on Timeout
```python
def process_with_backoff(image, initial_chunk=4000, timeout=30):
    chunk_size = initial_chunk
    while chunk_size > 500:
        try:
            return process_chunked(image, chunk_size, timeout)
        except TimeoutError:
            chunk_size //= 2
            print(f"Reducing chunk size to {chunk_size}")
```
- Self-correcting
- May waste time on failed attempts

## Benchmarking Plan
| Image | Pixels | Density | Approach 1 | Approach 2 | Approach 3 | Approach 4 |
|-------|--------|---------|------------|------------|------------|------------|
| sparse.png | 10 MP | Low | ? | ? | ? | ? |
| medium.png | 20 MP | Medium | ? | ? | ? | ? |
| halftone.png | 38 MP | High | ? | ? | ? | ? |

## Deliverables
- [x] ADR-002: Adaptive Chunk Sizing Strategy
- [x] Benchmark results document
- [x] Recommended implementation for chunking card

## Notes
- User's intuition: "maybe some kind of exponential backoff"
- Consider hybrid: sample-based initial estimate + backoff if needed
