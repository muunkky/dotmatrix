# Feature: Multi-Pass Detection for Small Clusters in Gap Regions

## Description

Implement a multi-pass detection algorithm that first runs standard detection, then identifies gap regions where clusters are expected but missing, and runs a more sensitive detection pass in those gaps only. This ensures complete halftone coverage for $50k+ fine art prints.

**Value**: Current detection misses ~38,586 pixels (small halftone dots), creating visible artifacts in print output. This fix ensures complete cluster detection while minimizing false positives by only using sensitive detection in gap regions.

**Target Users**: End users processing halftone images for high-value printing

**Estimated Effort**: 2 days

---

## Acceptance Criteria

- [ ] First pass: Standard detection runs unchanged
- [ ] Gap detection: Voronoi regions computed, gaps identified where pixel density is high but no cluster exists
- [ ] Second pass: Sensitive detection runs only in gap regions with lower thresholds
- [ ] Merge: Results combined without duplicates (clusters within min_distance merged)
- [ ] Orphan pixel count reduced from ~38,586 to <1,000
- [ ] No significant increase in false positives on standard regions
- [ ] Performance: <20% increase in processing time
- [ ] CLI flag to enable/disable multi-pass detection

---

## Implementation Plan

### Overview

Modify `cluster_pixel_counter.py` to support multi-pass detection:
1. Run standard detection (existing algorithm)
2. Compute Voronoi regions from detected centers
3. For each region, compute non-white pixel density
4. Identify "gap" regions: high density but no detected center
5. Run sensitive detection on gap regions only
6. Merge results, removing duplicates

### Implementation Steps

1. **Add Voronoi computation function**:
   ```python
   def compute_voronoi_regions(centers: np.ndarray, image_shape: Tuple[int, int]) -> np.ndarray:
       # Use scipy.spatial.Voronoi or label-based approach
       # Return label array where each pixel has its nearest center's index
   ```

2. **Add gap detection function**:
   ```python
   def find_gap_regions(labels: np.ndarray, image: np.ndarray, centers: np.ndarray, 
                        density_threshold: float = 0.3) -> List[Tuple[int, int, int, int]]:
       # For each Voronoi region:
       #   - Compute non-white pixel density
       #   - If density high but center is far from region centroid, mark as gap
       # Return list of bounding boxes for gap regions
   ```

3. **Add sensitive detection function**:
   ```python
   def detect_in_region(image: np.ndarray, region_bbox: Tuple, 
                        threshold_ratio: float = 0.3, min_distance: int = 5) -> List[Tuple[int, int]]:
       # Run distance transform detection on cropped region
       # Use more sensitive parameters
       # Return centers in global coordinates
   ```

4. **Add merge function**:
   ```python
   def merge_detections(primary: List, secondary: List, min_distance: int = 10) -> List:
       # Remove secondary detections within min_distance of primary
       # Return combined list
   ```

5. **Integrate into main pipeline**:
   - Add `multi_pass: bool = True` parameter to main detection function
   - Update CLI with `--multi-pass / --no-multi-pass` flag
   - Default to enabled for best quality

### Technical Considerations

- **Architecture**: Keep existing detection unchanged; multi-pass is additive
- **Performance**: Only scan gap regions (typically <10% of image) with sensitive detection
- **Scalability**: Voronoi computation is O(n log n), gap detection is O(pixels)
- **Error Handling**: If no gaps found, return standard detection results
- **Backwards Compatibility**: New flag defaults to True but can be disabled

### Dependencies

- scipy.spatial.Voronoi (already available)
- Existing distance transform detection code
- Orphan diagnostic tool (for validation)

---

## Testing Strategy (optional)

### Unit Tests

- [ ] Test Voronoi computation produces valid regions
- [ ] Test gap detection identifies known gap regions
- [ ] Test merge function removes duplicates correctly
- [ ] Test full pipeline on synthetic images with known small dots

### Integration Tests

- [ ] Test on `input_large.png` - orphan count should drop significantly
- [ ] Test on images without gaps - results should match standard detection
- [ ] Test performance is within 20% of single-pass

### Manual Testing Scenarios

1. **Happy Path**: Process `input_large.png` with multi-pass
   - Expected: Orphan count drops from 38,586 to <1,000
   - Visual inspection shows coverage of previously blank spots

2. **Edge Cases**: Process image with no gaps
   - Expected: Output identical to single-pass detection

---

## Documentation Updates (optional)

### 📝 IMPORTANT: Update CHANGELOG.md
- [ ] **Add entry to CHANGELOG.md under [Unreleased]**
  - Feature: Multi-pass detection for complete halftone coverage
  - New CLI flag: `--multi-pass / --no-multi-pass`

### Other Documentation
- [ ] Update README.md with multi-pass detection description
- [ ] Update CLI help text for new flag

---

## Related Cards (optional)

### Dependencies

**Depends on**: 65jnja - Root cause spike must complete first to confirm parameter approach

**Depends on**: 82ei52 - Diagnostic tool needed to validate results

### Blocks

**Blocks**: Rendering adjustments card - rendering can only be tested once detection is complete
