# ADR: CMYK Cluster Pixel Counting Architecture

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

#### Phase 2: Clustering via Nearest Neighbors
1. Detect all black (K) dot centers
2. For each completed midtone mask:
   - Find connected components
   - Assign each component to nearest K center
3. For RGB overlaps (already complete, not fragmented):
   - Assign to nearest K center directly

#### Phase 3: Pixel Counting with Deduplication
For each cluster:
```python
# Raw counts (with overlaps)
R_raw = count(M ∩ Y pixels in cluster)
G_raw = count(C ∩ Y pixels in cluster)  
B_raw = count(C ∩ M pixels in cluster)

# Deduplicated midtone counts
C_final = C_total - G_raw - B_raw
M_final = M_total - R_raw - B_raw
Y_final = Y_total - R_raw - G_raw

# K and RGB stay as-is
K_final = K_total
R_final, G_final, B_final = R_raw, G_raw, B_raw
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
- [ ] Centroid calculation as alternative anchor
- [ ] Bounding box output option
- [ ] Binary mask output for reconstruction
- [ ] Debug visualization mode
