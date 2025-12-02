## Description

Add ability to save and load cluster detection results, enabling fast iteration on rendering without re-running the expensive detection phase.

Currently, processing a large image (10MP+) requires ~5 minutes for detection. When iterating on rendering parameters (petal distance, scale, color mode), you must re-run the entire pipeline including detection. This feature separates the pipeline into cacheable stages.

**Value**: 10x faster iteration cycles when tuning rendering parameters. Run detection once, re-render many times in seconds instead of minutes.

**Target Users**: Developers iterating on rendering quality, users processing the same image with different render settings.

**Estimated Effort**: 4-6 hours

---

## Acceptance Criteria

- [x] `--save-clusters <path>` flag saves ClusterResult list to JSON/pickle file after detection
- [x] `--load-clusters <path>` flag loads ClusterResult list and skips detection phase
- [x] Saved file includes metadata: source image hash, detection parameters, timestamp
- [x] Load validates source image hash matches (warn if different)
- [x] Works with both single-image and sliding-window modes
- [x] Manifest includes cluster cache file reference when used

---

## Implementation Plan

### Overview

Add serialization to ClusterResult dataclass, implement save/load CLI flags, and wire into the detection/render pipeline to skip detection when loading cached clusters.

### Implementation Steps

1. **Add serialization to ClusterResult**: 
   - `to_dict()` already exists, add `from_dict()` classmethod
   - Create `save_clusters(clusters, path, metadata)` function
   - Create `load_clusters(path)` function returning (clusters, metadata)
   
2. **Add CLI flags**:
   ```python
   @optgroup.option('--save-clusters', type=click.Path(), help='Save detection results to file')
   @optgroup.option('--load-clusters', type=click.Path(exists=True), help='Load detection results (skip detection)')
   ```

3. **Wire into pipeline**:
   - If `--load-clusters`: skip detection, load clusters, validate metadata
   - If `--save-clusters`: after detection, save clusters with metadata
   - Both can be used together (load, re-detect, save)

4. **Metadata schema**:
   ```json
   {
     "version": "1.0",
     "source_image_hash": "sha256:...",
     "detection_params": {...},
     "timestamp": "...",
     "cluster_count": N,
     "clusters": [...]
   }
   ```

### Technical Considerations

- **Format**: JSON for portability (clusters are small relative to images)
- **Validation**: Warn but don't fail on hash mismatch (user may intentionally use different source)
- **Sliding window**: Save global deduplicated cluster list, not per-tile

---

## Testing Strategy (optional)

### Unit Tests

- [x] Test ClusterResult.from_dict() roundtrip
- [x] Test save_clusters/load_clusters file operations
- [x] Test metadata validation (hash match, parameter check)

### Manual Testing Scenarios

1. **Save/Load roundtrip**: Detect → save → load → render, verify identical output
2. **Parameter mismatch warning**: Load clusters detected with different params
3. **Large file**: Test with 10MP+ image, verify cluster file is reasonable size

---

## Related Cards (optional)

**Related**: p7f44i - Improve CLI logging (would benefit from progress output during load)
