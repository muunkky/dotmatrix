## Summary

Replace cluster detection with a cell-based method that creates rectangular cells around each detected black dot, then samples the CMYK values from each cell to generate synthetic clusters.

## Motivation

Current cluster detection has issues:
1. Some circles not being picked up by detection
2. Clusters overlap each other unintentionally
3. Petals from one cluster bleed into adjacent clusters
4. Inconsistent coverage

**Cell method advantages:**
- 100% coverage guaranteed - every pixel belongs to exactly one cell
- No overlap between clusters
- Simpler algorithm - just divide space around black dots
- Black dots are the most reliable detection (high contrast)
- CMYK values come from actual pixel sampling, not circle detection

## Proposed Algorithm

### Step 1: Detect Black Dots Only
- Use existing black dot detection (most reliable)
- Get list of `(x, y, radius)` for each black center

### Step 2: Create Voronoi-like Cells
- For each pixel in the image, assign it to the nearest black dot center
- This creates irregular polygonal cells around each black dot
- Alternative: use rectangular grid cells centered on black dots

### Step 3: Sample CMYK from Each Cell
- For each cell, count pixels of each CMYK color
- Apply tolerance for anti-aliasing
- Get `{cyan: N, magenta: N, yellow: N, black: N}` per cell

### Step 4: Generate Synthetic Clusters
- Create a `ClusterInfo` for each cell using:
  - Center = black dot center
  - Black pixels = actual black count from cell
  - CMY pixels = actual counts from cell
- Feed these synthetic clusters to existing flower renderer

## Visual Comparison

**Current approach:**
```
[Circle Detection] -> [Cluster Detection] -> [Flower Render]
     ^                      ^
     |                      |
   Misses some        Clusters overlap
```

**Cell approach:**
```
[Black Dot Detection] -> [Voronoi Cells] -> [Sample CMYK] -> [Flower Render]
     ^                        ^                  ^
     |                        |                  |
  Most reliable         100% coverage       Ground truth pixels
```

## Implementation Options

### Option A: Voronoi Tessellation
- Use scipy.spatial.Voronoi to create cells
- Each black dot is a seed point
- Handles irregular dot spacing naturally

### Option B: Grid Cells
- Divide image into rectangular grid
- Assign each grid cell to nearest black dot
- Simpler but may have edge effects

### Option C: Hybrid
- Use Voronoi for cell boundaries
- Clip to rectangular bounds around each dot

## Acceptance Criteria

- [ ] Detect black dots only (skip CMY circle detection)
- [ ] Create cell boundaries around each black dot
- [ ] Sample actual CMYK pixel counts from each cell
- [ ] Generate ClusterInfo objects from cell data
- [ ] Render using existing flower renderer
- [ ] Compare CMYK accuracy vs current cluster detection
- [ ] No inter-cluster overlap in output

## CLI Integration

```bash
# New flag to enable cell-based clustering
dotmatrix -i image.png -m halftone --cell-clustering --reconstitute --render-method flower

# Or as a new mode
dotmatrix -i image.png -m cell --reconstitute --render-method flower
```

## Expected Benefits

1. **Better accuracy**: CMYK values come from actual pixels, not detection
2. **No missed circles**: Every pixel is accounted for
3. **No overlap**: Cells are mutually exclusive
4. **Simpler debugging**: Cell boundaries can be visualized
5. **Ground truth comparison**: Cell CMYK vs rendered CMYK is apples-to-apples

## Notes

This is essentially asking: "What CMYK values do I need in each cell to reproduce this image?" rather than "What circles can I detect?"

The flower renderer then becomes: "Given these CMYK values per cell, render a flower pattern that approximates them."
