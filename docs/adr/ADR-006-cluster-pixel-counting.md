# ADR-006: CMYK Cluster Pixel Counting Architecture

## Status
**ACCEPTED** - 2024-11-28

## Context
We need to analyze halftone CMYK images by counting pixels per ink channel, clustered around black (K) anchor dots. This enables accurate color reproduction analysis without relying on circle geometry.

## Decision

### Output Format
Each cluster outputs a 9-element tuple:
```python
[x, y, cyan, magenta, yellow, black, red, green, blue]
```
- `x, y`: Center point of the black dot (anchor)
- 7 pixel counts with **no double counting**

### Algorithm

#### Phase 1: Midtone Completion
For each midtone (C, M, Y):
1. Start with ink separation mask
2. Include RGB pixels that contain this ink (complete broken circles)
   - Cyan mask += pixels where C channel active (including G, B overlaps)
   - Magenta mask += pixels where M channel active (including R, B overlaps)
   - Yellow mask += pixels where Y channel active (including R, G overlaps)

#### Phase 2: Clustering via Nearest Pixel
1. For each non-black pixel, find nearest black pixel
2. Assign pixel to that black dot's cluster
3. No centroid calculation needed - just pixel distance

Note: Could also use nearest K center (centroid), but nearest pixel is simpler.

#### Phase 3: Pixel Counting with Deduplication

**Problem:** In Phase 1, we "completed" midtones by including RGB overlaps:
- Cyan mask includes Green (C∩Y) and Blue (C∩M) pixels
- Magenta mask includes Red (M∩Y) and Blue (C∩M) pixels
- Yellow mask includes Red (M∩Y) and Green (C∩Y) pixels

This causes double-counting if we report both midtones AND overlaps.

**Example:** A Red pixel (M∩Y overlap)
- Counted in M_total (because it has Magenta)
- Counted in Y_total (because it has Yellow)
- Counted in R_count (because it's M∩Y)
- That's 3 counts for 1 pixel!

**Solution:** Subtract RGB from parent midtones:
```python
# For each cluster:

# 1. Count RGB overlaps (these are definitive)
R = count(M ∩ Y pixels)  # Red = Magenta AND Yellow
G = count(C ∩ Y pixels)  # Green = Cyan AND Yellow
B = count(C ∩ M pixels)  # Blue = Cyan AND Magenta

# 2. Subtract overlaps from midtone totals
C_final = C_total - G - B   # Remove green & blue (both contain C)
M_final = M_total - R - B   # Remove red & blue (both contain M)
Y_final = Y_total - R - G   # Remove red & green (both contain Y)

# 3. K stays as-is (no overlaps with CMY in our model)
K_final = K_total

# Output: [x, y, C_final, M_final, Y_final, K_final, R, G, B]
# Each pixel counted exactly once!
```

### Validation Rules
- **Max 1** of each color (C, M, Y) per cluster
- **0 is valid** (not all dots have all colors)
- **2+ is noise** (acceptable error, don't fail)

### Edge Handling
- Process edge clusters last
- Include even if center off-map
- Flag as `partial: true`

### White/Background
- No virtual clusters for K-less regions
- White = remaining pixels after all 7 channels counted

## Consequences

### Positive
- Accurate pixel-level color analysis
- No double counting in final output
- Handles broken/fragmented circles gracefully
- Simple output format for downstream processing

### Negative
- More complex than circle-based approach
- Nearest neighbor clustering may mis-assign in dense areas
- Edge cases with 2+ same-color dots treated as noise

### Future TODOs
- Centroid calculation as alternative anchor
- Bounding box output option
- Binary mask output for reconstruction
- Debug visualization mode

## Related
- Implemented in: `src/dotmatrix/cluster_pixel_counter.py`
- Related ADR: ADR-005 (Cluster Rendering Pipeline)
- Gitban card: krzyj6
