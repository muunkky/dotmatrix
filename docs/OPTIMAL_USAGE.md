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

**Wrong min/max radius settings?**
- Use black dot verification (enabled by default for CMYK)
- Check the verification output for suggested radius range
- Example output:
  ```
  Black Dot Verification:
    Circles detected: 1247
    Radius: mean=28.3, std=4.2, range=[20, 42]
    Coverage: 12.35%
    Density: 2.1 circles/MP
    Status: ✓ Verification passed
    Suggested radius range: --min-radius 18 --max-radius 48
  ```
- Disable with `--no-verify-black` if not using CMYK
- Use `--verify-abort` to stop if settings are misconfigured
- Check `black_verification_coverage.png` in debug mode for detection density heatmap

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

---

## Black Dot Verification (CMYK Images)

### Overview

When processing CMYK halftone images, DotMatrix automatically validates your detection settings using black (K) dots as ground truth. Black dots are ideal reference points because they're always printed on top and have the highest contrast.

### Automatic Verification

Verification runs automatically before full CMYK detection:

```bash
dotmatrix --input halftone.png --palette cmyk --min-radius 20 --max-radius 50
```

Output shows verification results:
```
Black Dot Verification:
  Circles detected: 1,247
  Radius: mean=28.3, std=6.2, range=[22, 46]
  Coverage: 89.4%
  Density: 2.1 circles/MP
  Status: ✓ Verification passed
```

### Understanding Verification Warnings

**"Very few black circles detected"**
- Your min/max radius settings may be filtering out valid circles
- Try the suggested radius range shown in the output

**"Mean radius close to min_radius"**
- Circles are being cut off at the lower bound
- Lower your `--min-radius` to capture smaller dots

**"Mean radius close to max_radius"**
- Circles are being cut off at the upper bound  
- Raise your `--max-radius` to capture larger dots

**"High radius variation (CV > 40%)"**
- Detection may be inconsistent
- Check image quality or adjust thresholds

### Suggested Radius Range

When verification detects issues, it suggests optimal settings:

```
Black Dot Verification:
  Circles detected: 842
  Radius: mean=31.5, std=8.9, range=[18, 52]
  Warnings:
    ⚠ Mean radius (31.5) is close to max_radius (35).
       Some circles may be cut off. Consider raising max_radius.
  Suggested radius range: --min-radius 15 --max-radius 55
```

Simply copy the suggested parameters to your command.

### Coverage Map (Debug Mode)

Enable `--debug` to save a visual heatmap showing where black dots were detected:

```bash
dotmatrix --input halftone.png --palette cmyk --debug
```

Creates `output/black_verification_coverage.png`:
- **Blue regions**: Few/no detections (possible gaps)
- **Red regions**: Dense detections (good coverage)

Use this to identify problem areas in your image.

### Disabling Verification

If you need to skip verification (e.g., for non-halftone images):

```bash
dotmatrix --input image.png --palette cmyk --no-verify-black
```

### Abort on Failure

Stop processing immediately if verification fails:

```bash
dotmatrix --input halftone.png --palette cmyk --verify-abort
```

Useful in automated pipelines to avoid processing misconfigured images.

### Best Practices

1. **Start with verification**: Let it suggest radius ranges for your specific image
2. **Iterate on settings**: Adjust based on warnings and re-run until verification passes
3. **Use coverage maps**: Identify spatial gaps in detection with `--debug`
4. **Validate once**: Once you find good settings, disable verification for batch processing

