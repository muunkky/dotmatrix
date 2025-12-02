# Troubleshooting: BGR/RGB Color Format Mismatch in Reconstitute Pipeline

**Card Type**: Spike - Troubleshooting
**Status**: investigation
**Priority**: P0
**Date Started**: 2025-11-28
**Owner**: CAMERON

## Problem Statement

### Symptoms Observed
- **What is broken/not working?** The `--reconstitute` command produces images where cyan and blue pixels are missing (0% coverage) while yellow is massively overrepresented
- **Error messages or unexpected behavior**: No errors, but pixel count comparison shows:
  - Cyan: Source has 36,134 pixels, Reconstituted has 0 (0.0% coverage)
  - Blue: Source has 17,236 pixels, Reconstituted has 0 (0.0% coverage)  
  - Yellow: Source has 1 pixel, Reconstituted has 48,898 (4,889,800% overrepresented)
- **Impact**: CMYK halftone reconstitution is unusable - colors are completely wrong
- **Urgency**: Core feature is broken, blocking further development

### Environment Context
- **System/Service**: dotmatrix CLI, reconstitute pipeline
- **Version**: Current HEAD (post quantization commit)
- **Configuration**: `--convex-edge --palette cmyk --reconstitute`
- **Recent Changes**: Added color quantization before CMYK separation (commit 6f4be0c)

---

## Investigation Progress

### Pre-Investigation Checklist
- [x] Problem statement clearly defined
- [x] Error messages captured verbatim
- [x] Recent changes reviewed (git log, deployment logs)
- [ ] Similar past issues searched (gitban cards, docs, git history)
- [x] Monitoring/logs checked for related errors
- [x] Impact scope assessed (how many users/systems affected)

### Research Performed

#### Related Code/Config:

**The Color Pipeline (needs full trace):**
```
cli.py:733     → cv2.cvtColor(image, cv2.COLOR_BGR2RGB) creates image_rgb
cli.py:799     → separate_cmyk_inks(image) - NOW FIXED to pass BGR
convex_detector.py:255 → quantize_to_cmyk_rgb(image) 
convex_detector.py:258-260 → b,g,r = image[:,:,0], image[:,:,1], image[:,:,2]
cluster_pixel_counter.py → Uses ink masks to count pixels
cluster_renderer.py:22-27 → COLORS dict in BGR format
cli.py:847     → cv2.cvtColor(reconstituted, cv2.COLOR_RGB2BGR)
```

**Key Question: What format does each function expect vs receive?**

| Function | Docstring Says | Actually Receives | Problem? |
|----------|---------------|-------------------|----------|
| `separate_cmyk_inks` | BGR | BGR (after fix) | Fixed |
| `quantize_to_cmyk_rgb` | BGR | BGR | OK |
| `cluster_and_count_pixels` | Masks only | Masks | OK |
| `render_bullseye` | Returns RGB (docstring line 134) | ? | **INVESTIGATE** |
| `cv2.cvtColor(...RGB2BGR)` | Expects RGB | ? | **INVESTIGATE** |

---

## Solution Attempts

### Attempt Log

| # | Attempt Name | Hypothesis | Outcome | Status | Notes |
|---|-------------|------------|---------|--------|-------|
| 1 | Add quantization | Anti-aliased pixels failing thresholds | Detected more circles | 🔄 Partial | Quantization works, but colors still wrong |
| 2 | Fix cli.py BGR input | CLI was passing RGB to separate_cmyk_inks | Cluster counts now correct | 🔄 Partial | Cluster data correct, but render still wrong |
| 3 | TBD: Trace render_bullseye | COLORS dict or RGB conversion wrong | TBD | ⬜ Todo | Need to verify render output format |

### Detailed Attempt Logs

#### Attempt 1: Add Quantization

**Hypothesis**: Anti-aliased pixels with gradients fail threshold-based detection

**Root Cause Theory**: PNG images have thousands of unique colors instead of 8 pure CMYK/RGB colors

**Results**:
- Added `quantize_to_cmyk_rgb()` function
- Changed `separate_cmyk_inks()` to use exact color matching
- Test detection increased from 13 to 17 circles

**Outcome**: 🔄 Partial - Detection improved but reconstituted colors still wrong

---

#### Attempt 2: Fix CLI BGR Input

**Hypothesis**: CLI was converting to RGB before calling separate_cmyk_inks which expects BGR

**Steps Performed**:
1. Changed `separate_cmyk_inks(image_rgb)` to `separate_cmyk_inks(image)` at cli.py:799

**Results**:
- Cluster pixel counts now show correct values:
  - Cyan: 36,134 (was 1)
  - Blue (C∩M): 17,236 (was 0)
  - Yellow: 1 (was 36,134)
- BUT reconstituted image still shows 0% cyan, 0% blue

**Outcome**: 🔄 Partial - Cluster data correct, rendering still wrong

**Updated Hypothesis**: The problem is now in render_bullseye or the final RGB2BGR conversion

---

#### Attempt 3: Trace Render Pipeline (TODO)

**Hypothesis**: Either:
1. `render_bullseye` draws CMYK colors but returns in wrong format
2. The `cv2.cvtColor(reconstituted, cv2.COLOR_RGB2BGR)` is incorrect
3. COLORS dict values don't match expected output format

**Steps to Perform**:
1. Add logging at each stage showing sample pixel values
2. Verify render_bullseye returns what its docstring claims (RGB)
3. Check if cv2.circle uses BGR colors even when drawing on "RGB" image
4. Trace pixel values from cluster data → render → final save

---

## Root Cause Analysis

### Suspected Root Causes (to confirm)

1. **cv2.circle uses BGR regardless of image format** - cv2 always interprets color tuples as BGR
2. **Docstring lies** - render_bullseye says "Returns RGB numpy array" but cv2.circle makes it BGR
3. **Double conversion** - If render returns BGR but we convert RGB→BGR, colors flip

### Discovery Path
Need to trace with explicit pixel value logging at each stage.

---

## Follow-Up Actions

### Documentation Updates Needed

| Document Type | Location | Update Needed | Status |
|--------------|----------|---------------|--------|
| Code comments | `convex_detector.py` | Document BGR format requirement | ⬜ Todo |
| Code comments | `cluster_renderer.py` | Correct RGB/BGR claims in docstring | ⬜ Todo |
| Architecture docs | NEW: docs/color-pipeline.md | Mermaid diagram of full data flow | ⬜ Todo |
| ADR | NEW: docs/adr/color-format-convention.md | Establish BGR-everywhere convention | ⬜ Todo |

---

## Key Files to Trace

```
src/dotmatrix/
├── cli.py                    # Lines 733, 799, 847 - format conversions
├── convex_detector.py        # quantize_to_cmyk_rgb, separate_cmyk_inks  
├── cluster_pixel_counter.py  # cluster_and_count_pixels
└── cluster_renderer.py       # render_bullseye, COLORS dict
```

---

**Resolution Status**: 🔄 Ongoing
**Total Investigation Time**: ~2 hours
**Prevention Items Created**: TBD - need docs card
