# Edge Sampling Methods Comparison

**Test Image:** `test_dotmatrix.png` (1696x1776 pixels)
**Expected Colors:** 4-5 colors (Cyan, Magenta, Yellow, Black, White background)
**Circles Detected:** 773 circles
**K-means Clustering:** max_colors=6 (to consolidate similar colors)

## Results Summary

All five methods extracted exactly 6 color groups (due to k-means clustering with `--max-colors 6`).

### Method 1: CIRCUMFERENCE (Original Edge Sampling)
**Description:** Samples 36 evenly-spaced points around full 360° circumference

**Extracted Colors:**
- RGB(38, 30, 43) - Dark blue-gray
- RGB(121, 145, 119) - Muted green-gray
- RGB(131, 191, 221) - Light blue (Cyan)
- RGB(205, 98, 133) - Pink-magenta
- RGB(231, 202, 152) - Beige-yellow
- RGB(238, 227, 240) - Off-white

**Analysis:** Still produces somewhat blended colors due to sampling overlapping regions.

---

### Method 2: CANNY (Actual Edge Pixels)
**Description:** Samples from actual Canny edge pixels within ±3 pixels of circle radius

**Extracted Colors:**
- RGB(93, 72, 81) - Dark purple-gray
- RGB(131, 130, 128) - Mid gray
- RGB(185, 219, 236) - Light cyan
- RGB(220, 171, 200) - Light magenta-pink
- RGB(228, 149, 114) - Coral/salmon (only 3 small circles!)
- RGB(242, 231, 187) - Cream-yellow

**Analysis:** Better color separation. The coral/salmon group appears to be an artifact from very small circles or edge blending. Otherwise shows cleaner CMYK-like separation.

---

### Method 3: EXPOSED (Occlusion-Aware)
**Description:** Samples only from visible (non-occluded) arcs of each circle

**Extracted Colors:**
- RGB(38, 30, 43) - Dark blue-gray
- RGB(121, 145, 119) - Muted green-gray
- RGB(137, 190, 223) - Light blue (Cyan)
- RGB(206, 101, 137) - Pink-magenta
- RGB(236, 209, 139) - Yellow
- RGB(237, 228, 242) - Off-white

**Analysis:** Similar to circumference method. The occlusion detection logic may need refinement - appears to still sample some overlapping regions.

---

### Method 4: BAND (Edge Pixel Band)
**Description:** Samples all pixels within annular band (radius ±3 pixels)

**Extracted Colors:**
- RGB(21, 17, 21) - Very dark (near-black)
- RGB(124, 119, 125) - Mid gray
- RGB(136, 193, 225) - Light blue (Cyan)
- RGB(213, 99, 136) - Pink-magenta
- RGB(236, 209, 141) - Yellow
- RGB(240, 228, 243) - Off-white/white

**Analysis:** Produces colors closest to CMYK expectations! The very dark color group likely represents actual black circles or heavily overlapped regions.

---

### Method 5: AREA (Baseline)
**Description:** Area-based sampling - averages all pixels within circle

**Extracted Colors:**
- RGB(27, 28, 33) - Very dark (black)
- RGB(67, 67, 71) - Dark gray
- RGB(164, 99, 121) - Muted purple-pink (heavily blended)
- RGB(176, 177, 184) - Light gray (heavily blended)
- RGB(216, 190, 106) - Muted yellow (heavily blended)
- RGB(252, 252, 251) - White/off-white

**Analysis:** Worst performance. Produces heavily blended colors due to averaging overlapping regions. Two gray groups show the blending problem clearly.

---

## Comparison: Closest to Expected CMYK

Mapping extracted colors to expected CMYK:

| Expected | Circumference | Canny | Exposed | Band | Area |
|----------|---------------|-------|---------|------|------|
| **Cyan** | ✓ (131,191,221) | ✓ (185,219,236) | ✓ (137,190,223) | ✓ (136,193,225) | ❌ Blended |
| **Magenta** | ✓ (205,98,133) | ✓ (220,171,200) | ✓ (206,101,137) | ✓ (213,99,136) | ❌ Blended |
| **Yellow** | ✓ (231,202,152) | ✓ (242,231,187) | ✓ (236,209,139) | ✓ (236,209,141) | ❌ Blended |
| **Black** | ~ (38,30,43) | ~ (93,72,81) | ~ (38,30,43) | ✓ (21,17,21) | ✓ (27,28,33) |
| **White** | ✓ (238,227,240) | ✓ (242,231,187) | ✓ (237,228,242) | ✓ (240,228,243) | ✓ (252,252,251) |

**Artifact colors:**
- Circumference: Muted green-gray (121,145,119) - blending artifact
- Canny: Mid gray (131,130,128) + Coral (228,149,114) - edge artifacts
- Exposed: Muted green-gray (121,145,119) - blending artifact
- Band: Mid gray (124,119,125) - likely anti-aliasing
- Area: Dark gray (67,67,71) + Light gray (176,177,184) - heavy blending

---

## Winner: BAND Method

**Best Overall:** The **BAND** method (edge pixel band sampling) produces colors closest to the expected CMYK palette:
- Cleanest cyan detection
- Accurate magenta
- Pure yellow
- Near-black for black circles
- Clean white/off-white

**Runner-up:** The **CANNY** method is second-best, but has a coral/salmon artifact likely from sampling very small circles where edge detection is less reliable.

---

## Recommendations

1. **Use BAND method by default** for overlapping circle detection with CMYK-style images
2. **Use CANNY method** as alternative if band sampling produces artifacts
3. **Avoid AREA method** for overlapping circles - produces heavily blended colors
4. **EXPOSED method needs refinement** - occlusion detection logic may need better circle layering heuristics

---

## Command Line Usage

To use the BAND method (recommended):
```bash
dotmatrix --input image.png --edge-sampling --edge-method band --extract output/
```

To use the CANNY method (alternative):
```bash
dotmatrix --input image.png --edge-sampling --edge-method canny --extract output/
```

To compare all methods:
```bash
./demo_edge_methods_comparison.sh
```

---

## Technical Details

### Band Method Implementation
- Samples all pixels in annular region: `radius ± 3 pixels`
- Uses numpy coordinate grids for efficient pixel selection
- Calculates median color (robust to outliers)
- Falls back to area sampling if no pixels in band

### Canny Method Implementation
- Runs Canny edge detection (50, 150 thresholds)
- Finds edge pixels within `radius ± 3 pixels`
- Samples colors from actual detected edges
- Falls back to area sampling if no edges found

### Exposed Method Implementation
- Generates sample points around circumference
- Checks each point for occlusion by larger circles
- Only samples from non-occluded points
- Falls back to all points if none exposed

### Circumference Method (Original)
- Samples 36 evenly-spaced points around full circle
- No occlusion detection
- Simple and fast but samples overlapping regions
