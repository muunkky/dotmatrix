# ADR-001: Large File Processing Strategy

## Status

**Accepted**

## Date

2025-11-25

## Context

DotMatrix needs to handle image files up to 10MB+ reliably. Users work with various image sizes from small icons to large scanned documents and photographs. We need to establish performance requirements and determine if any special handling is needed for large files.

## Decision

**We will use pixels (megapixels) as the primary unit for performance thresholds**, not file size in MB. This is because:

1. File size varies wildly based on content and compression (PNG with circles compresses ~40x better than noisy photos)
2. Memory usage directly correlates with pixel count, not file size
3. Processing time scales with pixel count, not compressed file size

### Key Thresholds (Based on Benchmark Data)

| Metric | Hough Detection | Convex Detection |
|--------|-----------------|------------------|
| **30s threshold** | >100 MP | ~25 MP |
| **Memory per MP** | ~5-8 MB | ~20 MB |
| **Recommended max** | 64+ MP (no limit found) | 20 MP |

### Performance Characteristics

**Hough Detection (Standard):**
- Extremely fast: 1.2s for 64 megapixels (8000x8000)
- Linear memory scaling: ~5 MB per megapixel
- No practical limit found in testing
- 99%+ detection accuracy

**Convex Edge Detection (Overlapping Circles):**
- Slower: ~2s per megapixel
- Higher memory: ~20 MB per megapixel
- 30-second threshold at ~25 megapixels (5000x5000)
- 87-92% detection accuracy

### Reference: Megapixels to File Size

| Resolution | Megapixels | Typical PNG Size |
|------------|------------|------------------|
| 1000x1000 | 1 MP | 1-2 MB |
| 2000x2000 | 4 MP | 5-8 MB |
| 3000x3000 | 9 MP | 12-20 MB |
| 4000x4000 | 16 MP | 20-40 MB |
| 5000x5000 | 25 MP | 40-60 MB |

A **10MB file target** corresponds to approximately **4-9 megapixels** depending on content.

## Implementation Recommendations

### 1. No Chunking/Tiling Required

The benchmark data shows that:
- Hough detection handles 64+ MP images in <2 seconds
- Convex detection handles 20 MP images in <30 seconds
- A 10MB PNG is typically 4-9 MP, well within comfortable limits

**Tiling/chunking is NOT needed for the target file sizes.** The complexity of handling circles at tile boundaries is not justified.

### 2. Add Optional Size Warnings

For user experience, add warnings for:
- `--convex-edge` with images >20 MP: "Large image detected. Convex detection may take 30+ seconds."
- Images >50 MP with convex: Suggest using standard detection or downscaling

### 3. Add Progress Reporting for Long Operations

For operations >5 seconds, provide progress feedback:
- Processing stage (quantization, detection, deduplication)
- Estimated time remaining (based on megapixel scaling)

### 4. Memory Guidelines

Document memory requirements:
- Hough: Reserve 5-10 MB per megapixel
- Convex: Reserve 20-25 MB per megapixel
- For 10MB files: 100-200 MB memory is sufficient

### 5. Optional Future Enhancements (Not Required Now)

If future requirements exceed current limits:
- **Downscaling option**: `--max-megapixels 20` to auto-scale large images
- **Tiled convex detection**: Only if >50 MP support is needed
- **Progress callbacks**: For integration into GUI applications

## Consequences

### Positive
- Simple implementation (no tiling complexity)
- Current architecture handles target file sizes easily
- Clear performance expectations for users
- Pixel-based thresholds are consistent regardless of file format

### Negative
- Convex detection is slow for very large images (>25 MP)
- No special optimizations for edge cases
- Users must choose between speed (Hough) and accuracy (Convex) for overlapping circles

### Neutral
- Documentation should use megapixels, not MB, for performance guidance
- Test suite should include large file tests

## Benchmark Data

Full benchmark results are stored in:
- `benchmarks/realistic_benchmark_results.json`
- `benchmarks/benchmark_results.json`

### Summary Table

```
Resolution    Method   Time(s)   Memory(MB)   Detection Rate
---------------------------------------------------------
1000x1000     hough    0.02      69           100%
1000x1000     convex   0.48      108          100%
2000x2000     hough    0.04      193          100%
2000x2000     convex   2.74      254          91%
3000x3000     hough    0.16      200          102%
3000x3000     convex   11.61     277          90%
4000x4000     hough    0.30      220          100%
4000x4000     convex   28.15     311          91%
5000x5000     hough    0.51      250          101%
5000x5000     convex   30.0      443          94%
8000x8000     hough    1.22      362          100%
```

## References

- Spike Card: w804xa (Large File Handling Performance Research)
- OpenCV HoughCircles documentation
- Python memory_profiler and psutil libraries
