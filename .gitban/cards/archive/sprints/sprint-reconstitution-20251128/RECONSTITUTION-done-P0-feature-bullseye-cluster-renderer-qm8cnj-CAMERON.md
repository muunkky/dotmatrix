## Description

**Bullseye Cluster Renderer** - Core rendering module for reconstituting CMYK clusters as concentric circle patterns.

Takes cluster pixel count data (from `--cluster-count`) and renders each cluster as a "bullseye" pattern where circle sizes are proportional to ink coverage. The result is a visual representation that preserves the macro appearance of the original image while using a standardized micro-cluster pattern.

**Value**: Enables visual comparison between original halftone and detected cluster data, providing QA feedback for detection accuracy and a foundation for alternative rendering modes.

**Target Users**: Developers validating detection quality, users wanting simplified halftone representations

**Estimated Effort**: 4-6 hours

---

## Acceptance Criteria

- [x] Renders bullseye pattern for each cluster (concentric circles)
- [x] Circle radii are proportional to pixel counts (area-based)
- [x] Layer order: Yellow (outermost) → Magenta → Cyan → Black (innermost)
- [x] RGB overlaps visible at circle intersections (M∩Y=Red, C∩Y=Green, C∩M=Blue)
- [x] Partial/edge clusters handled (render at position, may clip)
- [x] Output image same dimensions as source
- [x] White background for non-cluster areas
- [x] Function accepts List[ClusterResult] and returns numpy array

**Quality Metrics**:
- [x] Test coverage: >90% for new code
- [x] Performance: <1 second for 100 clusters

---

## Implementation Plan

### Overview

Create `src/dotmatrix/cluster_renderer.py` with a `render_bullseye()` function that converts ClusterResult data into a visual image. Each cluster is drawn as concentric filled circles centered at the black dot position, with radii calculated from pixel counts.

### Implementation Steps

1. **Create cluster_renderer.py module**
   - Define `render_bullseye(clusters: List[ClusterResult], image_shape: Tuple[int, int]) -> np.ndarray`
   - Import ClusterResult from cluster_pixel_counter
   - Return RGB numpy array

2. **Implement radius calculation from pixel counts**
   - Total pixels = C + M + Y + K + R + G + B
   - Each layer's radius based on cumulative area
   - Formula: radius = sqrt(cumulative_area / pi)
   - Yellow = outermost (all pixels), Black = innermost (K pixels only)

3. **Implement circle drawing with proper layering**
   - Draw from outermost to innermost (Y → M → C → K)
   - Use cv2.circle() with filled=-1
   - Colors: Yellow=(255,255,0), Magenta=(255,0,255), Cyan=(0,255,255), Black=(0,0,0)

4. **Handle RGB overlaps naturally**
   - RGB overlaps emerge from layer intersections
   - No special handling needed - drawing order creates overlaps

5. **Handle partial clusters**
   - Option to skip partial clusters (cleaner output)
   - Default: render anyway (clips at edge)

### Technical Considerations

- **Architecture**: Standalone renderer module, decoupled from detection
- **Data Model**: Input is List[ClusterResult], output is np.ndarray (H, W, 3) RGB
- **Performance**: Use vectorized operations where possible; cv2.circle is efficient
- **Backwards Compatibility**: No changes to existing modules

### Dependencies

- **Library Dependencies**: numpy, opencv-python (cv2) - already installed
- **Data Dependencies**: ClusterResult from cluster_pixel_counter.py

---

## Testing Strategy

### Unit Tests

- [x] Test radius calculation: known pixel counts → expected radii
- [x] Test single cluster rendering: output shape, colors at center
- [x] Test multiple clusters: each at correct position
- [x] Test partial cluster flag: skipped or clipped correctly
- [x] Test edge case: cluster with 0 pixels for some channels
- [x] Test edge case: cluster at image corner

### Integration Tests

- [x] Test with real cluster data from test_dotmatrix.png
- [x] Test output image can be loaded by cv2
- [x] Test output dimensions match source

---

## Notes

### Design Decisions

- **Decision**: Draw Y → M → C → K (outer to inner)
- **Rationale**: Matches halftone printing order, RGB overlaps emerge naturally
- **Alternatives Considered**: Draw K first, then composite - more complex
- **Trade-offs**: Simple approach may not perfectly match subtractive blending

### Algorithm Detail

```python
# For each cluster:
# Calculate cumulative areas (from innermost to outermost)
k_area = cluster.black
c_area = k_area + cluster.cyan + cluster.blue + cluster.green  # includes overlaps
m_area = c_area + cluster.magenta + cluster.red - cluster.blue  # avoid double count
y_area = m_area + cluster.yellow - cluster.green - cluster.red  # avoid double count

# Actually simpler: just use proportional radii
total = sum all pixel counts
k_radius = sqrt(cluster.black / pi)
# ... etc

# Or: fixed outer radius, proportional inner radii
outer_radius = estimate from cluster density
```

### Open Questions

- **Q**: Should we support a "scale factor" parameter for larger/smaller clusters?
- **A**: [Defer to implementation - can add if useful]
