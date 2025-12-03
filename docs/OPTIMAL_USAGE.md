# Optimal Usage Guide for DotMatrix

## For CMYK Overlapping Circle Images

If you have an image with a known number of colors (like CMYK: cyan, magenta, yellow, black) and heavily overlapping circles, use these optimal parameters:

### Recommended Command

```bash
dotmatrix \
  --input image.png \
  --sensitivity strict \
  --min-radius 30 \
  --min-distance 50 \
  --edge-sampling \
  --edge-method band \
  --exclude-background \
  --max-colors 4 \
  --extract output/
```

### Parameter Explanations

**Circle Detection:**
- `--sensitivity strict` - Reduces false positives from overlapping regions
- `--min-radius 30` - Filters out tiny artifacts (adjust based on your image scale)
- `--min-distance 50` - Prevents duplicate detections of the same circle

**Color Extraction:**
- `--edge-sampling` - Use edge-based sampling instead of area (better for overlaps)
- `--edge-method band` - Sample from pixel band around circle edge (best for CMYK)
- `--exclude-background` - Filter out near-white background colors (RGB > 240)
- `--max-colors 4` - Use k-means clustering to group into N color groups

**Output:**
- `--extract output/` - Save circles grouped by color to separate PNG files

### Expected Results

For test_dotmatrix.png (4 black, 4 cyan, 4 magenta, 4 yellow circles):
- Detects: 16 circles total ✓
- Outputs: 4 PNG files (one per color group) ✓
- Each file contains all circles of that color ✓

### Why These Parameters?

**Problem:** Overlapping circles create color blending at edges
- Black circle over cyan creates dark blue pixels
- Yellow near white background creates pale beige pixels
- Anti-aliasing creates gradient pixels

**Solution:**
1. **Strict detection** - Reduces false positive circles from artifacts
2. **Band edge sampling** - Samples thin ring around circle edge, avoiding center overlap
3. **Background exclusion** - Removes white/near-white colors from results
4. **K-means clustering** - Groups similar colors together (handles minor variations)

### Alternative: Without K-means

If you want to see all unique colors detected (before clustering):

```bash
dotmatrix \
  --input image.png \
  --sensitivity strict \
  --min-radius 30 \
  --min-distance 50 \
  --edge-sampling \
  --edge-method band \
  --exclude-background \
  --color-tolerance 40 \
  --extract output/
```

This uses tolerance-based grouping instead of k-means. You may get 5-8 groups due to color blending.

### Edge Method Comparison

We tested 4 edge sampling methods:

| Method | Description | Result |
|--------|-------------|--------|
| **band** | Samples pixel ring (radius ±3px) | ✓ Best - clean CMYK separation |
| canny | Samples actual Canny edge pixels | Good - some artifacts |
| exposed | Samples only visible arcs (occlusion-aware) | Fair - needs refinement |
| circumference | Samples 360° around edge (default) | Poor - too many blended colors |

**Winner:** `--edge-method band` for overlapping CMYK circles

### Troubleshooting

**Too many circles detected?**
- Increase `--min-distance` (try 60-80)
- Increase `--min-radius` (filter smaller circles)
- Use `--sensitivity strict`

**Too few circles detected?**
- Decrease `--min-distance` (try 30-40)
- Decrease `--min-radius` (allow smaller circles)
- Use `--sensitivity relaxed`

**Wrong colors?**
- Try different `--edge-method` (band, canny, exposed)
- Adjust `--max-colors` to match expected color count
- Use `--exclude-background` to filter white/pale colors

**Colors too similar/different?**
- **Too similar:** Decrease `--color-tolerance` or use `--max-colors`
- **Too different:** Increase `--color-tolerance` or use k-means clustering

### Test Your Settings

Run this test script to find optimal detection parameters:

```bash
#!/bin/bash
for min_dist in 30 40 50 60 70; do
    count=$(dotmatrix --input image.png \
                     --sensitivity strict \
                     --min-radius 30 \
                     --min-distance $min_dist \
                     --format json | \
            python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
    echo "min-distance=$min_dist -> $count circles"
done
```

Adjust until you get the expected circle count.

### Performance Notes

- **Band method:** ~2-5ms per circle (fast, numpy-optimized)
- **Canny method:** ~5-10ms per circle (Canny edge detection overhead)
- **Exposed method:** ~10-20ms per circle (occlusion detection overhead)

For 100+ circles, band method is recommended for speed.
