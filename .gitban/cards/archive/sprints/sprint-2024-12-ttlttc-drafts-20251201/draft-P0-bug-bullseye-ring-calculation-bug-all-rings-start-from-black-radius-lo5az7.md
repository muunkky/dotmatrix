# User Test Notes - Bullseye Ring Calculation Bug

## Observations

### Cyan Layer Output
- Cyan layer looks correct
- White where cyan is, black everywhere else
- This is the expected mask format ✓

### Bullseye Rendering Issues
- Black dot in center looks about right
- Wide band of cyan around black
- Sometimes a very thin band of magenta
- **No yellow visible**
- **No proper color layering**

## Suspected Root Cause

The ring radii calculation appears to be using the **same inner radius (black radius)** for all color bands, rather than calculating **concentric cumulative radii**.

Current (broken) behavior:
```
All rings start from r_black:
- Yellow ring: r_black to r_yellow  
- Magenta ring: r_black to r_magenta
- Cyan ring: r_black to r_cyan
- Black circle: 0 to r_black
```

Expected (correct) behavior:
```
Concentric rings:
- Yellow ring: r_magenta to r_yellow (outermost)
- Magenta ring: r_cyan to r_magenta
- Cyan ring: r_black to r_cyan
- Black circle: 0 to r_black (innermost)
```

## Files to Investigate

- `src/dotmatrix/cluster_renderer.py` - `calculate_cumulative_radii()` and `render_single_cluster()`
- Check if the render order draws circles from outer to inner correctly
- Verify cumulative area calculation is being used properly

## Acceptance Criteria

- [ ] Yellow band visible on outer edge of bullseye
- [ ] Magenta band visible between yellow and cyan
- [ ] Cyan band visible between magenta and black
- [ ] Black dot in center
- [ ] Ring widths proportional to pixel counts
