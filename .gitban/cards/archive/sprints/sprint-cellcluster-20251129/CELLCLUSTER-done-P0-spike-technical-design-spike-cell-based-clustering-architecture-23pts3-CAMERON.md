## Research Question

**Question**: What is the optimal approach for cell-based clustering to replace circle detection with pixel sampling from Voronoi-like cells around black dots?

Should we use Voronoi tessellation (scipy.spatial.Voronoi), grid cells, or a simpler KDTree nearest-neighbor approach? How do we integrate with the existing flower renderer?

---

## Time Box

**Maximum Time**: 2 hours

---

## Success Criteria

- [x] Architecture decision documented with rationale
- [x] Data flow diagram from detection to rendering
- [x] ClusterInfo adapter interface defined
- [x] CLI integration approach decided
- [x] Edge cases identified and handling strategy defined

---

## Context

**Background**: Current circle detection (convex edge) has issues with:
1. Some circles not being detected (especially heavily occluded ones)
2. Clusters overlapping unintentionally
3. Petals from one cluster bleeding into adjacent clusters
4. Inconsistent coverage leading to accuracy gaps

Cell-based clustering addresses this by:
- Using black dots as reliable anchor points (highest contrast)
- Assigning every pixel to exactly one cell (100% coverage)
- Sampling actual CMYK pixel counts from cells (ground truth)

**Urgency**: This is needed to improve CMYK accuracy in reconstituted images. Current approach shows significant error in CMYK decomposition comparison.

---

## Findings

### Discovery 1: Existing Clustering Already Uses Voronoi-Like Approach

The codebase already has KDTree-based nearest-neighbor clustering in `cluster_pixel_counter.py`:

```python
def create_cluster_labels(black_mask):
    # Uses KDTree nearest-neighbor: each pixel assigned to nearest black dot
```

This IS effectively Voronoi tessellation - every pixel is assigned to its nearest black dot center. The mathematical result is identical to scipy.spatial.Voronoi but simpler to implement.

### Discovery 2: ClusterResult Already Contains CMYK Counts

The `ClusterResult` dataclass already captures exactly what we need:

```python
@dataclass
class ClusterResult:
    x: int          # Black dot center X
    y: int          # Black dot center Y
    cyan: int       # Cyan pixel count
    magenta: int    # Magenta pixel count
    yellow: int     # Yellow pixel count
    black: int      # Black pixel count
    red: int        # Red overlap (M∩Y)
    green: int      # Green overlap (C∩Y)
    blue: int       # Blue overlap (C∩M)
    partial: bool   # Edge cell flag
```

### Discovery 3: The Problem is in Circle Detection, Not Clustering

Current flow:
```
Circle Detection → Cluster Building → Pixel Counting → Rendering
```

The issue is that circle detection misses some circles. But the clustering step uses black mask positions, not detected circles!

**Key insight**: We can skip CMY circle detection entirely and just:
1. Detect black dots only
2. Use existing `cluster_and_count_pixels()` with CMYK masks
3. Feed ClusterResult to flower renderer

### Discovery 4: Flower Renderer Expects ClusterResult

Looking at `circle_renderer.py`, `render_flower()` already accepts `List[ClusterResult]`:

```python
def render_flower(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    ...
) -> np.ndarray
```

No adapter needed! The existing interface is already correct.

### Discovery 5: CLI Already Supports This Flow

The CLI already has `--cluster-count` and `--reconstitute` options that use:
```python
cluster_results = cluster_and_count_pixels(
    cyan_mask, magenta_mask, yellow_mask, black_mask,
    image_shape=image_rgb.shape[:2],
    color_mode=color_mode
)
```

**Key Insights**:
- KDTree nearest-neighbor IS Voronoi tessellation (mathematically equivalent)
- Existing clustering already does what we need
- Problem is that current flow detects CMY circles unnecessarily
- Solution: bypass CMY circle detection, use mask-based clustering directly

---

## Recommendation

**Decision**: Use **existing KDTree-based clustering** with simplified detection flow

**Rationale**:
1. KDTree nearest-neighbor is mathematically equivalent to Voronoi tessellation
2. The infrastructure already exists in `cluster_pixel_counter.py`
3. We only need to change the CLI flow, not add new modules
4. Simpler = fewer bugs, easier maintenance

**Confidence Level**: High

The solution is simpler than originally planned:

```
OLD FLOW (current):
  Image → Detect ALL circles (C,M,Y,K) → Build clusters → Count pixels → Render

NEW FLOW (cell-based):
  Image → Detect BLACK dots only → Create CMYK masks → cluster_and_count_pixels() → Render
```

---

## Architecture Decision

### Data Flow (Cell-Based Clustering)

```
Input Image
    ↓
1. Separate CMYK Inks (existing: separate_cmyk_inks)
   → cyan_mask, magenta_mask, yellow_mask, black_mask
    ↓
2. Detect Black Dot Centers from black_mask (existing: find_black_dot_centers)
   → List[(x, y)] black dot positions
    ↓
3. Create Cluster Labels (existing: create_cluster_labels)
   → 2D array where each pixel = cluster_id of nearest black dot
    ↓
4. Count CMYK Pixels Per Cluster (existing: count_cluster_pixels)
   → List[ClusterResult] with (x, y, C, M, Y, K, R, G, B, partial)
    ↓
5. Render Flower Pattern (existing: render_flower)
   → Reconstituted PNG
```

### CLI Integration

**Approach**: Add `--cell-clustering` flag (minimal change)

```bash
# New usage
dotmatrix -i image.png -m halftone --cell-clustering --reconstitute --render-method flower

# Behavior when --cell-clustering is set:
#   1. Skip HoughCircles / convex detection for CMY colors
#   2. Only detect black dots using convex detection (high reliability)
#   3. Use existing cluster_and_count_pixels() with CMYK masks
#   4. Feed results to flower renderer
```

**Implementation in cli.py**:
```python
@click.option('--cell-clustering', is_flag=True,
    help='Use cell-based clustering (skip CMY circle detection)')

# In _do_detect():
if cell_clustering:
    # Only detect black dots
    ink_masks = separate_cmyk_inks(image)
    black_circles = detect_circles_from_convex_edges(ink_masks['black'], ...)

    # Use existing clustering pipeline
    cluster_results = cluster_and_count_pixels(
        ink_masks['cyan'], ink_masks['magenta'],
        ink_masks['yellow'], ink_masks['black'],
        image_shape=image.shape[:2],
        color_mode='full'
    )
else:
    # Existing detection flow...
```

### Edge Cases

| Edge Case | Handling Strategy |
|-----------|-------------------|
| No black dots detected | Return empty result, warn user |
| Partial cells at edges | Already handled by `partial=True` flag |
| Large images | Existing chunked processing works |
| Overlapping black dots | KDTree deduplication already handles this |

---

## Next Steps

**Immediate Actions**:
- [x] Complete this spike and document decision
- [x] Update card f6u4kx (Black Dot Detection) - scope is smaller now
- [x] Update card x2r1u9 (CLI Integration) - main implementation work
- [x] Skip cards a3b3qg, zofctb, rpsta1 - not needed, existing code suffices

**Follow-up Cards to Create**:
- None needed - existing sprint cards cover the work

**Cards to Archive (not needed)**:
- a3b3qg (Voronoi Cell Generation) - existing `create_cluster_labels` does this
- zofctb (CMYK Pixel Sampling) - existing `count_cluster_pixels` does this
- rpsta1 (ClusterInfo Adapter) - no adapter needed, ClusterResult works directly

---

## Additional Notes

### Simplification from Original Plan

Original plan had 7 cards. After investigation, we only need:

| Card | Status | Reason |
|------|--------|--------|
| 23pts3 (Spike) | COMPLETE | Architecture decided |
| f6u4kx (Black Detection) | SIMPLIFIED | Just ensure black-only mode works |
| a3b3qg (Voronoi) | SKIP | Existing KDTree clustering suffices |
| zofctb (CMYK Sampling) | SKIP | Existing count_cluster_pixels suffices |
| rpsta1 (Adapter) | SKIP | ClusterResult already compatible |
| x2r1u9 (CLI) | MAIN WORK | Add --cell-clustering flag |
| n0qecx (Accuracy Test) | KEEP | Validate improvement |

### Key Files to Modify

1. `cli.py` - Add `--cell-clustering` flag and routing logic
2. `convex_detector.py` - Possibly add black-only detection helper (optional)

### Risk Assessment

- **Low risk**: Using existing, tested clustering code
- **Low complexity**: Single CLI flag addition
- **High confidence**: Architecture already supports this flow


## Acceptance Criteria

This spike is complete when all Success Criteria checkboxes are checked:
- [x] Architecture decision documented with rationale
- [x] Data flow diagram from detection to rendering
- [x] ClusterInfo adapter interface defined
- [x] CLI integration approach decided
- [x] Edge cases identified and handling strategy defined

## Test Plan

This is a technical investigation spike - no code was written, therefore no tests needed.

Validation will occur through:
1. Implementation of the CLI flag (card x2r1u9)
2. CMYK accuracy comparison test (card n0qecx)
