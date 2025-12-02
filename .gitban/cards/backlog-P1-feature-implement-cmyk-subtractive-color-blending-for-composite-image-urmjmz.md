## Description

Implement CMYK subtractive color blending for composite.png generation

When generating the composite image from detected CMYK halftone circles, the current implementation draws circles with opaque RGB colors on top of each other. This produces incorrect results when CMYK ink circles overlap - the later-drawn circle simply covers the earlier one instead of blending properly.

In actual CMYK printing, inks are **subtractive** - when you layer them on white paper:
- Cyan absorbs Red light
- Magenta absorbs Green light  
- Yellow absorbs Blue light

When CMYK inks overlap, they combine subtractively:
- Cyan + Magenta = Blue (both absorb Red and Green, leaving Blue)
- Cyan + Yellow = Green (absorb Red and Blue, leaving Green)
- Magenta + Yellow = Red (absorb Green and Blue, leaving Red)
- Cyan + Magenta + Yellow = Black (absorb all light)

**Value**: Produces visually accurate composite images that match how the original halftone would appear when printed. Essential for quality assurance when verifying circle detection accuracy on CMYK halftone images.

**Target Users**: Users processing CMYK halftone artwork who need accurate composite previews

**Estimated Effort**: 1-2 days

---

## Acceptance Criteria

- [ ] Overlapping cyan and magenta circles produce blue in the composite
- [ ] Overlapping cyan and yellow circles produce green in the composite
- [ ] Overlapping magenta and yellow circles produce red in the composite
- [ ] Overlapping C+M+Y circles produce near-black in the composite
- [ ] Non-overlapping circles retain their original ink colors
- [ ] White background is used (paper simulation) instead of transparent
- [ ] Add CLI flag `--blend-mode` with options: `overlay` (current), `cmyk` (new subtractive)
- [ ] Default behavior preserved for non-CMYK palettes
- [ ] Unit tests for color blending math
- [ ] Integration test comparing composite against expected reference image

---

## Implementation Plan

### Overview

Implement proper CMYK subtractive blending by treating each CMYK channel as an absorption layer. Instead of drawing opaque circles, accumulate ink coverage per pixel and compute final RGB from the combined CMYK values.

### Implementation Steps

1. **Add CMYK blending function**: Create `blend_cmyk_to_rgb()` function in `image_extractor.py`
   - Input: CMYK values (0-1 range for each channel)
   - Output: RGB tuple
   - Formula: RGB = 255 * (1 - C) * (1 - K), 255 * (1 - M) * (1 - K), 255 * (1 - Y) * (1 - K)
   
2. **Create CMYK accumulation buffers**: For composite generation with CMYK mode
   - Create 4 numpy arrays (C, M, Y, K channels) initialized to 0
   - Each pixel accumulates ink coverage from overlapping circles
   
3. **Draw circles to CMYK buffers**: Map ink colors to channels
   - Cyan circles (0, 255, 255) → add to C channel
   - Magenta circles (255, 0, 255) → add to M channel
   - Yellow circles (255, 255, 0) → add to Y channel
   - Black circles (0, 0, 0) → add to K channel

4. **Compute final RGB from CMYK buffers**: After all circles drawn
   - Clamp each channel to 0-1 range
   - Apply subtractive blending formula per pixel
   - Create final RGB image

5. **Add blend_mode parameter**: Update `generate_composite_image()` signature
   - `blend_mode: str = "overlay"` - current behavior (opaque overlay)
   - `blend_mode: str = "cmyk"` - new subtractive blending

6. **Wire through CLI**: Add `--blend-mode` option
   - Pass to extraction functions

### Technical Considerations

- **Performance**: Use numpy vectorized operations for CMYK→RGB conversion
- **Ink Coverage Model**: Simple additive ink accumulation (circles add to existing ink)
- **Edge Cases**: Handle overflow when multiple circles overlap (clamp to max ink)
- **Transparency**: CMYK blending produces opaque result on white paper background

### Code Location

- Primary changes: `src/dotmatrix/image_extractor.py` - `generate_composite_image()`
- CLI changes: `src/dotmatrix/cli.py` - add `--blend-mode` option

---

## Testing Strategy

### Unit Tests

- [ ] Test `blend_cmyk_to_rgb()` with known color combinations
- [ ] Test C+M = Blue (0, 0, 255)
- [ ] Test C+Y = Green (0, 255, 0)  
- [ ] Test M+Y = Red (255, 0, 0)
- [ ] Test C+M+Y = Black (0, 0, 0)
- [ ] Test individual inks produce correct RGB

### Integration Tests

- [ ] Test composite with overlapping circles produces expected colors
- [ ] Test --blend-mode cmyk flag is recognized
- [ ] Test default behavior unchanged for non-CMYK palettes

---

## Notes

### Design Decisions

- **Decision**: Use simple additive ink accumulation model
- **Rationale**: Matches physical ink behavior without complex halftone simulation
- **Alternatives Considered**: Full halftone screen simulation (too complex for MVP)
- **Trade-offs**: Simple model may not perfectly match printed output, but provides good visual approximation

### Formula Reference

CMYK to RGB conversion (subtractive model):
```python
R = 255 * (1 - C) * (1 - K)
G = 255 * (1 - M) * (1 - K)  
B = 255 * (1 - Y) * (1 - K)
```

Where C, M, Y, K are in range [0, 1] representing ink coverage.
