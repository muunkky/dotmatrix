# Feature: Integrate Block Renderer into CLI

## Description

Add `--render-method` CLI option to choose between bullseye (circles) and block (bars) reconstitution approaches. Enable users to select visualization style while maintaining backward compatibility.

**Value**: Gives users choice between visually appealing bullseye output (~91% accuracy) and pixel-accurate block output (100% accuracy). Supports different use cases: visual inspection vs. data validation.

**Target Users**: CLI users who need either visual fidelity or exact pixel accuracy in reconstituted images.

**Estimated Effort**: 2-3 hours

---

## Acceptance Criteria

- [x] New `--render-method` option added to reconstitute command
- [x] Option accepts values: `bullseye` (default), `block`
- [x] Bullseye remains default for backward compatibility
- [x] Block renderer correctly imported and called when selected
- [x] `--segment-height` option added for block method (height per color row)
- [x] `--height-mode` option added: `fixed-segment` (default), `fixed-bar`, `variable`, `min-height`
- [x] Help text documents both methods and their trade-offs
- [x] Help text explains height modes and midtone printer use case
- [x] Manifest records which render method and height mode was used
- [x] Output filename reflects render method if different from default

---

## Implementation Plan

### Overview

Extend the CLI's reconstitute functionality to support pluggable renderers. Add command-line options for method selection and block-specific parameters.

### Implementation Steps

1. **Add CLI arguments in cli.py**
   - Add `--render-method` with choices=['bullseye', 'block'], default='bullseye'
   - Add `--bar-height` with type=int, default=20 (only used for block)
   - Add to existing reconstitute argument group
   ```python
   parser.add_argument('--render-method', 
       choices=['bullseye', 'block'],
       default='bullseye',
       help='Reconstitution rendering method: bullseye (circles, ~91%% accuracy) or block (bars, 100%% accuracy)')
   parser.add_argument('--bar-height',
       type=int,
       default=20,
       help='Bar height for block render method (default: 20)')
   ```

2. **Import block_renderer in cli.py**
   - Add conditional import or import at top
   ```python
   from dotmatrix.block_renderer import render_blocks
   from dotmatrix.cluster_renderer import render_bullseye
   ```

3. **Modify reconstitute code path**
   - In the reconstitute section (~line 830-850), branch based on render_method
   ```python
   if args.render_method == 'block':
       reconstituted = render_blocks(
           clusters, 
           (img_h, img_w),
           bar_height=args.bar_height,
           skip_partial=True
       )
   else:
       reconstituted = render_bullseye(
           clusters,
           (img_h, img_w),
           skip_partial=True
       )
   ```

4. **Update manifest metadata**
   - Add render_method field to manifest
   - Add bar_height if block method used
   ```python
   manifest['render_method'] = args.render_method
   if args.render_method == 'block':
       manifest['bar_height'] = args.bar_height
   ```

5. **Update output filename (optional)**
   - Consider naming: `reconstituted_block.png` vs `reconstituted.png`
   - Or keep same name, let manifest document method

### Technical Considerations

- **Backward compatibility**: Default to bullseye so existing scripts work unchanged
- **Validation**: bar-height only meaningful for block method - could warn if used with bullseye
- **Performance**: Block rendering should be faster (rectangles vs circles)

### Dependencies

- block_renderer.py module (feature card gsqq6k)

---

## Testing Strategy

### Unit Tests

- [x] Test CLI argument parsing for --render-method
- [x] Test CLI argument parsing for --bar-height
- [x] Test default values are correct

### Integration Tests

- [x] Test reconstitute with --render-method bullseye produces bullseye output
- [x] Test reconstitute with --render-method block produces block output
- [x] Test manifest contains correct render_method value
- [x] Test --bar-height parameter passed correctly to block renderer

---

## Related Cards

**Depends on**: gsqq6k - Implement block renderer module

---

## Notes

### CLI Examples

```bash
# Default bullseye (backward compatible)
dotmatrix reconstitute image.png

# Explicit bullseye
dotmatrix reconstitute --render-method bullseye image.png

# Block renderer with fixed-segment mode (default for block)
# Each color gets a 10px tall row, width varies by pixel count
dotmatrix reconstitute --render-method block image.png

# Block with custom segment height (for midtone printer overlap)
dotmatrix reconstitute --render-method block --segment-height 20 image.png

# Different height modes
dotmatrix reconstitute --render-method block --height-mode fixed-bar image.png
dotmatrix reconstitute --render-method block --height-mode variable image.png
```

### Help Text Draft

```
--render-method {bullseye,block}
    Reconstitution visualization method:
    - bullseye: Concentric circles centered at each cluster (~91% pixel accuracy)
    - block: Stacked color bars with exact pixel counts (100% accuracy)
    Default: bullseye

--height-mode {fixed-segment,fixed-bar,variable,min-height}
    Height mode for block renderer:
    - fixed-segment: Each color gets same height row, widths vary (for midtone printer overlap)
    - fixed-bar: All bars same total height, segment widths vary
    - variable: Bar height scales with total pixel count
    - min-height: Minimum height enforced, scales up for large counts
    Default: fixed-segment
    Only used with --render-method block.

--segment-height N
    Height in pixels for each color segment row (fixed-segment mode).
    Total bar height = 7 × segment_height (one row per color).
    Only used with --render-method block --height-mode fixed-segment.
    Default: 10
```
