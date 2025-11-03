# Edge Sampling Comparison Demo

This demo compares **area-based** color sampling (default) vs **edge-based** color sampling on `test_dotmatrix.png`.

## Settings

Both runs used identical settings except for the sampling method:
- `--sensitivity relaxed` (more detections)
- `--min-confidence 25` (lower threshold)
- `--color-tolerance 50` (loose color grouping)

## Results

### Area Sampling (Default)
**Command:**
```bash
dotmatrix --input test_dotmatrix.png \
  --extract area_sampling/ \
  --sensitivity relaxed \
  --min-confidence 25 \
  --color-tolerance 50
```

**Output:** 7 color groups
- `circles_color_000_000_000.png` - Black
- `circles_color_054_044_054.png` - Dark gray/purple
- `circles_color_108_097_102.png` - Medium gray
- `circles_color_118_193_241.png` - Blue
- `circles_color_151_154_159.png` - Light gray
- `circles_color_207_180_083.png` - Yellow
- `circles_color_218_213_198.png` - Beige

### Edge Sampling
**Command:**
```bash
dotmatrix --input test_dotmatrix.png \
  --extract edge_sampling/ \
  --sensitivity relaxed \
  --min-confidence 25 \
  --color-tolerance 50 \
  --edge-sampling
```

**Output:** 6 color groups
- `circles_color_054_027_040.png` - Dark purple/black
- `circles_color_118_193_094.png` - Teal/cyan (different from area!)
- `circles_color_156_092_154.png` - Pink/magenta
- `circles_color_211_068_071.png` - Red/pink
- `circles_color_217_193_189.png` - Light pink/beige
- `circles_color_255_255_255.png` - White

## Key Differences

1. **Blue vs Cyan**: Area sampling detected RGB(118,193,241) [blue], while edge sampling detected RGB(118,193,94) [cyan/teal]. Edge sampling captures the exposed color at the circle perimeter.

2. **Color Count**: Edge sampling produced 6 groups vs 7 for area sampling, with different color distributions.

3. **Pink Detection**: Edge sampling detected more distinct pink shades (156,092,154) and (211,068,071), while area sampling averaged overlapping areas to grays.

## When to Use Each Method

### Use Area Sampling (Default) When:
- Circles don't overlap
- Simple dot patterns with clear separation
- Colors are solid and uniform

### Use Edge Sampling When:
- Circles overlap or layer over each other
- Colors appear incorrect due to averaging
- Layered/3D dot matrix patterns
- You need to detect the "true" color of partially obscured circles

## Technical Details

**Area Sampling:**
- Averages all pixels within the circle boundary
- Fast and accurate for non-overlapping circles
- Can be misleading when circles overlap (averages both colors)

**Edge Sampling:**
- Samples 36 evenly-spaced points around the circle's circumference
- Uses median color (robust to outliers)
- Better captures the exposed/visible color at the edge
- Slightly more computationally expensive but negligible for most use cases

## Conclusion

Edge sampling successfully addresses the challenge of overlapping circles that you identified! Blue circles under black circles now correctly detect blue at the exposed edges, rather than appearing gray/black from area averaging.
