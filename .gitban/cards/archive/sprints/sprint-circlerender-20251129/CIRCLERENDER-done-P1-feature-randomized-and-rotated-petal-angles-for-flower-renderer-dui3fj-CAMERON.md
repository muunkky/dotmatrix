## Description

**Randomized and Rotated Petal Angles for Flower Renderer**

Add options to the flower renderer to vary petal angles per cluster instead of using fixed 120° intervals. This creates more natural-looking output that matches real halftone printing where dot positions vary across the image.

**Value**: More realistic reconstruction that better matches source halftone images where dots appear at various angles. Provides artistic flexibility and reduces the "mechanical" appearance of uniform flower orientations.

**Target Users**: Users processing halftone images who want realistic reconstruction

**Estimated Effort**: 2-4 hours

---

## Acceptance Criteria

- [x] Add `--petal-rotation` CLI option with values: `fixed`, `random`, `cluster-hash`
- [x] `fixed` mode: Current behavior, all clusters use same 0°/120°/240° angles
- [x] `random` mode: Each cluster gets random rotation offset (0-360°)
- [x] `cluster-hash` mode: Rotation determined by cluster (x,y) position hash for reproducibility
- [x] Add `--petal-offset` CLI option to set base rotation angle (default 0°)
- [x] Visually verify output looks more natural with random/hash modes

---

## Implementation Plan

### Overview

Add a `rotation_offset` parameter to `render_flower_cluster()` that shifts all petal angles. The offset can be fixed, random, or deterministically computed from cluster position.

### Implementation Steps

1. **Add rotation parameter to render_flower_cluster()**:
   - Add `rotation_offset: float = 0.0` parameter
   - Apply offset to all petal angles: `angle_deg = PETAL_ANGLES[color] + rotation_offset`

2. **Add rotation mode to render_flower()**:
   - Add `rotation_mode: str = 'fixed'` parameter ('fixed', 'random', 'cluster-hash')
   - Add `base_rotation: float = 0.0` parameter
   - Compute per-cluster rotation based on mode

3. **Update CLI**:
   - Add `--petal-rotation` option
   - Add `--petal-offset` option
   - Pass to render_flower()

### Technical Considerations

- **Reproducibility**: `cluster-hash` mode uses position-based hash for deterministic output
- **Random seed**: Consider optional seed parameter for reproducible random mode
- **Performance**: Minimal impact - just angle arithmetic

---

## Testing Strategy (optional)

### Unit Tests

- [x] Test rotation offset correctly shifts petal positions
- [x] Test random mode produces varied angles
- [x] Test cluster-hash mode produces same output for same input
- [x] Test fixed mode preserves current behavior

---

## Notes (optional)

### Design Decisions

- **Decision**: Use hash of (x,y) for cluster-hash mode
- **Rationale**: Deterministic, reproducible, position-dependent variation
- **Alternatives Considered**: Random per-cluster (not reproducible), sequential rotation (too uniform)
