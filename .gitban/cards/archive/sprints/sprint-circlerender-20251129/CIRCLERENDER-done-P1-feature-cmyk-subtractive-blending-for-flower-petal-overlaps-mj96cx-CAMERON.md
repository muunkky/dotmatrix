## Description

**CMYK Subtractive Blending for Flower Petal Overlaps**

Enable subtractive color blending in flower mode so overlapping CMY petals create accurate RGB secondary colors. Currently, flower mode draws solid colors that overwrite each other. With proper blending:
- Cyan + Magenta overlap → Blue
- Cyan + Yellow overlap → Green  
- Magenta + Yellow overlap → Red
- Cyan + Magenta + Yellow → near Black

**Value**: More realistic halftone reconstruction that accurately represents how ink colors combine in real printing. Users see secondary colors (RGB) naturally emerge from CMY overlaps, matching the original source image appearance.

**Target Users**: Users reconstructing CMYK halftone images with overlapping dots

**Estimated Effort**: 3-5 hours

---

## Acceptance Criteria

- [x] Flower mode petals blend via subtractive color mixing at overlaps
- [x] C+M overlap produces blue (#0000FF)
- [x] C+Y overlap produces green (#00FF00)
- [x] M+Y overlap produces red (#FF0000)
- [x] C+M+Y overlap produces near-black
- [x] Add `--blend-overlaps` CLI flag to enable this mode
- [x] Non-overlapping regions retain pure CMY colors
- [x] Black circle still drawn on top after blending

---

## Implementation Plan

### Overview

Modify flower rendering to use a multi-layer approach: draw CMY circles on separate layers, blend them using subtractive color model (each ink removes its complementary RGB channel), then composite onto output.

### Implementation Steps

1. **Create blending function for subtractive CMY**:
   ```python
   def blend_cmy_subtractive(
       cyan_mask: np.ndarray,
       magenta_mask: np.ndarray,
       yellow_mask: np.ndarray
   ) -> np.ndarray:
       """Blend CMY masks into BGR image using subtractive model.
       
       C removes R, M removes G, Y removes B.
       """
       h, w = cyan_mask.shape
       result = np.full((h, w, 3), 255, dtype=np.uint8)  # White base
       
       # Subtractive: each ink removes its complementary channel
       result[cyan_mask, 2] = 0    # R channel
       result[magenta_mask, 1] = 0  # G channel
       result[yellow_mask, 0] = 0   # B channel
       
       return result
   ```

2. **Modify render_flower_cluster() for blend mode**:
   - Add `blend_overlaps: bool = False` parameter
   - When enabled:
     - Create CMY masks (circles) without drawing to image
     - Call blend_cmy_subtractive() to generate blended result
     - Copy blended pixels to output image
     - Draw black circle on top

3. **Update render_flower()**:
   - Add `blend_overlaps: bool = False` parameter
   - Pass to render_flower_cluster()

4. **Add CLI option**:
   - Add `--blend-overlaps` flag
   - Pass to render_flower()

### Technical Considerations

- **Layer compositing**: CMY layers blend, then black composites on top
- **Mask generation**: Need pixel-accurate circle masks for blending
- **Memory**: Three masks per cluster (small, ~cluster_size² pixels each)
- **Performance**: Mask operations are vectorized, should be fast

---

## Testing Strategy (optional)

### Unit Tests

- [x] Test C+M overlap produces blue
- [x] Test C+Y overlap produces green
- [x] Test M+Y overlap produces red
- [x] Test C+M+Y overlap produces black (or near-black)
- [x] Test non-overlapping regions retain pure colors
- [x] Test black circle draws on top of blended CMY

---

## Notes (optional)

### Design Decisions

- **Decision**: Use binary mask approach rather than alpha blending
- **Rationale**: Matches how real ink works - ink is either present or not, no transparency
- **Trade-offs**: Sharp edges at boundaries, but matches physical printing

### Research Findings

Subtractive color model:
- CMY inks are subtractive primaries
- Each ink absorbs (subtracts) its complementary RGB component
- C absorbs R, M absorbs G, Y absorbs B
- Combining all three theoretically produces black (in practice, a muddy brown, hence K channel)
