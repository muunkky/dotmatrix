# Bug: Reconstitute Output Missing Cyan and Blue Pixels

## Problem Description

The `--reconstitute` command produces images where cyan and blue are completely missing, despite source images having significant cyan (36,134 pixels) and blue (17,236 pixels).

**Reproduction:**
```bash
python3 -m dotmatrix -i inputs/corner_test.png --convex-edge --palette cmyk \
  --reconstitute --min-radius 10 --max-radius 50 --output-dir /tmp/test
```

**Expected:** Reconstituted image has cyan rings around black dots, blue where cyan+magenta overlap
**Actual:** Reconstituted has 0 cyan pixels, 0 blue pixels, yellow massively overrepresented

## Root Cause (Suspected)

After fixing the cli.py BGR input issue, cluster data is now correct:
- Cyan: 36,134 ✅
- Blue (C∩M): 17,236 ✅

But the rendered output still shows wrong colors. The issue is likely in:
1. `cluster_renderer.py` - The `render_bullseye` function or its color handling
2. The final `cv2.cvtColor(reconstituted, cv2.COLOR_RGB2BGR)` conversion at cli.py:847

**Key Insight:** cv2.circle() always interprets color tuples as BGR, even when drawing on a numpy array you consider "RGB". The docstring at cluster_renderer.py:134 says "Returns RGB numpy array" but this may be incorrect.

## Investigation Notes

**Verified Working:**
- `quantize_to_cmyk_rgb()` - correctly quantizes to 8 colors in BGR
- `separate_cmyk_inks()` - correctly separates when given BGR input
- `cluster_and_count_pixels()` - correctly counts pixels from masks

**Needs Verification:**
- [ ] What format does `render_bullseye` actually return?
- [ ] Does cv2.circle on a numpy array produce BGR or follow some other convention?
- [ ] Is the cli.py RGB2BGR conversion backwards?

## Acceptance Criteria

- [ ] Reconstituted image pixel counts match source within 10% for all colors
- [ ] Cyan coverage: source 36,134 → reconstituted ~32,000-40,000
- [ ] Blue coverage: source 17,236 → reconstituted ~15,000-19,000  
- [ ] Yellow coverage: source 1 → reconstituted ~0-10
- [ ] Visual inspection shows correct CMYK bullseye patterns
- [ ] All existing tests pass

## Test Plan

### TDD Approach
1. Write test that asserts reconstituted cyan pixels within 10% of source
2. Write test that asserts reconstituted blue pixels within 10% of source
3. Fix render pipeline until tests pass

### Manual Verification
```bash
# Run reconstitute
python3 -m dotmatrix -i inputs/corner_test.png --convex-edge --palette cmyk \
  --reconstitute --min-radius 10 --max-radius 50 --output-dir /tmp/color_fix

# Compare pixel counts
python3 -c "
import cv2
import numpy as np
src = cv2.imread('inputs/corner_test.png')
rec = cv2.imread('/tmp/color_fix/reconstituted.png')
# Count cyan [255,255,0] in BGR
print('Source cyan:', np.sum(np.all(src == [255,255,0], axis=2)))
print('Recon cyan:', np.sum(np.all(rec == [255,255,0], axis=2)))
"
```

## Implementation Notes

**Files to modify:**
- `src/dotmatrix/cluster_renderer.py` - Fix return format or docstring
- `src/dotmatrix/cli.py:847` - Fix or remove RGB2BGR conversion

**Depends on:** Spike card n8pbv8 (trace data flow first)

## Related Cards
- `n8pbv8` - Troubleshooting spike to trace BGR/RGB data flow
- `bnjfku` - Documentation card for mermaid diagrams
