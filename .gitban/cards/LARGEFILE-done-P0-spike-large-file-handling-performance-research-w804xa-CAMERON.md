## Problem Statement

**Decision**: What are the optimal strategies for processing large image files (up to 10MB+) in DotMatrix without degrading performance or running out of memory?

We need to determine:
- At what file size/resolution does current detection become too slow or memory-intensive?
- Should we implement chunked/tiled processing for large files?
- What are industry best practices for large image processing in OpenCV/Python?
- How do we detect when chunking is needed vs when full-image processing is acceptable?

---

## Time Box

**Maximum Time**: 4 hours

Research phase to establish performance baselines and identify optimal chunking thresholds.

---

## Success Criteria

**We'll know this spike is successful when**:
- [x] Performance baseline established for various file sizes (1MB, 5MB, 10MB, 20MB)
- [x] Memory usage profiled for different image resolutions
- [x] Chunking threshold identified (file size/resolution where chunking becomes necessary)
- [x] Recommended approach documented with rationale
- [x] Edge cases identified (circles spanning chunk boundaries)
- [x] ADR drafted with findings and recommendations

---

## Solution Options (optional)

### Option 1: Full-Image Processing (Current Approach)

**Description**: Process entire image at once, regardless of size

**Pros**:
- Simple implementation (already exists)
- No chunk boundary handling needed
- Works well for smaller files

**Cons**:
- Memory usage scales linearly with image size
- May cause OOM for very large files
- Processing time may exceed acceptable limits

**Complexity**: Low (status quo)

### Option 2: Tiled/Chunked Processing

**Description**: Split large images into overlapping tiles, process each tile independently, then merge results

**Pros**:
- Bounded memory usage regardless of file size
- Parallelization potential
- Scales to arbitrarily large files

**Cons**:
- Complex boundary handling for circles spanning tiles
- Overhead for tile management and deduplication
- May miss circles at tile boundaries without proper overlap

**Complexity**: High

### Option 3: Adaptive Processing

**Description**: Automatically choose full-image or chunked processing based on file size/available memory

**Pros**:
- Best of both worlds
- Simple files stay simple
- Only complex when needed

**Cons**:
- Two code paths to maintain
- Threshold tuning needed
- Testing complexity

**Complexity**: Medium

### Option 4: Image Pyramid/Resolution Reduction

**Description**: Downsample large images to a maximum resolution, process at reduced scale

**Pros**:
- Simple implementation
- Predictable memory usage
- Fast processing

**Cons**:
- Loses precision for small circles
- May not meet accuracy requirements
- Scaling artifacts

**Complexity**: Low

---

## Comparison Matrix (optional)

| Criteria | Full-Image | Chunked | Adaptive | Downscale | Weight |
|----------|------------|---------|----------|-----------|--------|
| Implementation | Exists | New | New | Simple | Medium |
| Memory Usage | Unbounded | Bounded | Bounded | Bounded | High |
| Accuracy | High | Medium | High | Low | High |
| Performance | Variable | Predictable | Optimal | Fast | High |
| Maintenance | Low | High | Medium | Low | Medium |

---

## Investigation Tasks

### Phase 1: Baseline Measurement

1. **Test current implementation with various file sizes**:
   - 1MB (~1000x1000 pixels)
   - 5MB (~2500x2500 pixels)
   - 10MB (~3500x3500 pixels)
   - 20MB (~5000x5000 pixels)

2. **Measure**:
   - Processing time
   - Peak memory usage
   - Detection accuracy (if test images available)

3. **Tools**:
   - `memory_profiler` for memory tracking
   - `time` module for duration
   - pytest-benchmark for consistent measurement

### Phase 2: Research

1. **OpenCV best practices for large images**
2. **Python memory management for image processing**
3. **Chunk overlap strategies for circle detection**
4. **Industry standards for "large file" threshold**

### Phase 3: Prototype (if time permits)

- Quick POC of chunked processing
- Measure improvement vs complexity

---

## Recommendation

**Decision**: Option 1 (Full-Image Processing) - No changes needed for target file sizes.

**Rationale**: Benchmark results show that:
- Hough detection handles 64+ megapixels in <2 seconds
- Convex detection handles 20 megapixels in <30 seconds  
- A 10MB PNG file is typically 4-9 megapixels
- Current architecture easily handles the target requirements

The complexity of tiled/chunked processing is NOT justified for the target use case.

**Confidence Level**: High

**Key Findings**:
- Use **megapixels** (not MB) as the performance metric
- Hough: ~5 MB memory per megapixel, <0.02s per megapixel
- Convex: ~20 MB memory per megapixel, ~2s per megapixel
- Convex 30s threshold: ~25 megapixels (5000x5000)
- No tiling needed for files up to 10MB (4-9 MP)

---

## Deliverables (optional)

**Recommended outputs**:
- [x] Performance benchmark results (JSON/CSV)
- [x] Memory profile data
- [x] ADR document with recommendations
- [x] Implementation cards for chosen approach

---

## Next Steps (optional)

**If recommendation accepted**:
- [x] Create implementation cards based on findings
- [x] Update roadmap with large file support milestone
- [x] Define performance targets for implementation

---

## Additional Notes (optional)

### Key Questions to Answer

1. What is the practical "large file" threshold for our use case?
2. Does OpenCV's HoughCircles have built-in optimizations for large images?
3. How does convex edge detection scale compared to standard detection?
4. What overlap % is needed for chunked processing to not miss circles?

### Resources

- OpenCV Documentation: https://docs.opencv.org/
- Python Memory Profiler: https://pypi.org/project/memory-profiler/
- Image Processing Best Practices
