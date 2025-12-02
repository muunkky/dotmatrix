# Feature: Orphan Pixel Diagnostic Visualization Tool

## Description

Create a diagnostic tool to visualize orphan pixels (non-white pixels that are far from any detected cluster center). This tool will be essential for debugging detection issues and validating fixes.

**Value**: Without visualization, it's impossible to understand where detection is failing. This tool enables rapid iteration on detection improvements by showing exactly which pixels aren't being captured by any cluster.

**Target Users**: Developers debugging detection algorithms

**Estimated Effort**: 4 hours

---

## Acceptance Criteria

- [x] Tool accepts cluster JSON and original image as input
- [ ] Generates overlay image showing orphan pixels highlighted
- [ ] Generates distance heatmap (distance from each pixel to nearest cluster)
- [ ] Outputs statistics: total orphans, orphan percentage, region bounds
- [ ] Supports configurable distance threshold (default 50px)
- [ ] Can output to file or display interactively

---

## Implementation Plan

### Overview

Create `src/dotmatrix/orphan_diagnostic.py` with functions to:
1. Load cluster data and original image
2. Compute distance from each non-white pixel to nearest cluster center
3. Identify orphan pixels (distance > threshold)
4. Generate visualizations (overlay, heatmap)
5. Output statistics

### Implementation Steps

1. **Create orphan detection function**:
   - Load cluster centers from JSON
   - Build KDTree for efficient nearest-neighbor queries
   - Find all non-white pixels in original image
   - Compute distance to nearest cluster for each

2. **Create visualization functions**:
   - Overlay: Draw red dots on orphan pixel locations
   - Heatmap: Color-code all pixels by distance to nearest cluster
   - Region bounds: Draw bounding box around orphan concentration

3. **Create CLI integration**:
   - Add `--orphan-diagnostic` flag to main CLI
   - Output visualization files alongside other outputs
   - Print statistics to console

### Technical Considerations

- Use scipy.spatial.cKDTree for efficient queries (already in project)
- Use cv2 for image manipulation (already in project)
- Handle large images efficiently (chunked processing if needed)

---

## Testing Strategy (optional)

### Unit Tests

- [ ] Test orphan detection with known orphan locations
- [ ] Test distance calculations are correct
- [ ] Test visualization output format

### Manual Testing Scenarios

1. **Happy Path**: Run on `input_large.png` with clusters JSON
   - Expected: 38,586 orphan pixels identified
   - Visualization shows orphan region clearly
