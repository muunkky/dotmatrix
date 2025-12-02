## Stakeholder Review & Signoff

**Stakeholder Notes:**
<!-- Space for notes, concerns, feedback -->

**Approval Checklist:**
- [x] CAMERON personally approves this feature for implementation

---

## Description

Add debug visualization mode to cluster_pixel_counter.py that outputs color-coded cluster visualizations.

When debugging clustering issues, it's difficult to understand which pixels are assigned to which cluster. This feature adds a `--debug-clusters` CLI flag that outputs a visualization image where each cluster is drawn in a unique color, making it easy to verify clustering behavior.

**Value**: Essential debugging tool for understanding clustering behavior. Helps identify mis-assigned pixels, cluster boundary issues, and edge cases. Dramatically reduces debugging time for clustering problems.

**Target Users**: Developers debugging clustering issues, users validating detection quality, QA engineers reviewing halftone analysis results.

**Estimated Effort**: 4 hours

---

## Acceptance Criteria

- [x] Add `generate_cluster_debug_image()` function to cluster_pixel_counter.py
- [x] Function outputs image where each cluster is a unique, visually distinct color
- [x] Cluster centers marked with crosshairs or dots
- [x] Partial (edge) clusters shown with hatched pattern or different opacity
- [x] CLI flag `--debug-clusters` saves debug image to output directory
- [x] Optional overlay mode: clusters drawn semi-transparent over original image

---

## Implementation Plan

### Overview

Create a visualization function that takes cluster labels and outputs a debug image. Each cluster gets a unique color from a perceptually-distinct palette. Optionally overlay on original image for comparison.

### Implementation Steps

1. **Create color palette generator**: Generate N visually distinct colors for N clusters:
   ```python
   def generate_cluster_colors(n_clusters: int) -> List[Tuple[int, int, int]]:
       # Use HSV with evenly spaced hues for maximum distinction
       colors = []
       for i in range(n_clusters):
           hue = int(180 * i / n_clusters)  # OpenCV uses 0-180 for hue
           colors.append(cv2.cvtColor(np.array([[[hue, 255, 200]]], dtype=np.uint8), 
                                       cv2.COLOR_HSV2BGR)[0, 0])
       return colors
   ```

2. **Create generate_cluster_debug_image() function**:
   ```python
   def generate_cluster_debug_image(
       labels: np.ndarray,
       centers: List[Tuple[int, int]],
       partial_flags: List[bool],
       original_image: Optional[np.ndarray] = None,
       overlay_alpha: float = 0.5
   ) -> np.ndarray:
       # Create colored cluster visualization
       # Mark centers with crosshairs
       # Handle partial clusters with different styling
   ```

3. **Add to cluster_and_count_pixels()**: Return optional debug image alongside results.

4. **Add CLI flag**: `--debug-clusters` that saves cluster_debug.png to output.

5. **Write tests**: Verify output image has expected properties (dimensions, unique colors per cluster).

### Technical Considerations

- **Architecture**: Standalone visualization function, no impact on core clustering
- **Performance**: One-time image generation, negligible overhead
- **User Experience**: Consider adding legend showing cluster ID → color mapping

### Visualization Modes

1. **Solid colors**: Each cluster filled with unique color
2. **Outline only**: Cluster boundaries drawn, interior transparent
3. **Overlay**: Semi-transparent clusters over original image
4. **With labels**: Cluster ID numbers drawn at cluster centers

---

## Testing Strategy (optional)

### Unit Tests

- [x] Test output image has correct dimensions
- [x] Test each cluster has unique color in output
- [x] Test centers are marked at correct coordinates
- [x] Test partial clusters have distinct styling

### Manual Testing Scenarios

1. **Visual verification**: Generate debug image for known halftone, verify clusters visually make sense
2. **Edge cases**: Image with clusters at all edges, single cluster, 100+ clusters

---

## Related Cards (optional)

**Related**: krzyj6 - ADR: CMYK Cluster Pixel Counting Architecture (parent ADR with "Future TODOs")
