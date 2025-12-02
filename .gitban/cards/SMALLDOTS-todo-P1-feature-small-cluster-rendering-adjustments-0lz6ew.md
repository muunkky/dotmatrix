# Feature: Small Cluster Rendering Adjustments

## Description

Update the cluster renderer to correctly handle small clusters detected by multi-pass detection. Small clusters may have different characteristics (smaller radii, different layer proportions) that require rendering adjustments for visual consistency.

**Value**: Ensures small clusters are rendered correctly in the output, completing the $50k+ print quality fix. Without this, small detected clusters might render as barely-visible dots or with incorrect proportions.

**Target Users**: End users processing halftone images for high-value printing

**Estimated Effort**: 4 hours

---

## Acceptance Criteria

- [ ] Small clusters (radius < 10px) render correctly as bullseye patterns
- [ ] Minimum visible radius enforced (e.g., 3px minimum for visibility)
- [ ] Small clusters don't create visual artifacts (e.g., single-pixel dots)
- [ ] Layer proportions preserved even for small clusters
- [ ] Visual consistency between small and large clusters
- [ ] No impact on rendering of standard-sized clusters

---

## Implementation Plan

### Overview

Audit and adjust `cluster_renderer.py` to handle small clusters gracefully. Add minimum radius floor and verify cumulative radius calculations work correctly for small pixel counts.

### Implementation Steps

1. **Analyze small cluster characteristics**:
   - Examine clusters detected in gap regions
   - Document typical pixel counts for small clusters
   - Calculate expected radii for each CMYK layer

2. **Add minimum radius handling**:
   ```python
   MIN_VISIBLE_RADIUS = 3  # Minimum radius for visual clarity
   
   def calculate_cumulative_radii(cluster: ClusterResult) -> Dict[str, float]:
       # Existing calculation
       radii = {...}
       # Enforce minimum for visibility
       for layer in radii:
           if 0 < radii[layer] < MIN_VISIBLE_RADIUS:
               radii[layer] = MIN_VISIBLE_RADIUS
       return radii
   ```

3. **Test rendering of small clusters**:
   - Create test clusters with small pixel counts
   - Verify rendered output looks correct
   - Compare visual quality to original halftone

### Technical Considerations

- Very small clusters may collapse multiple layers into one visible dot
- Must maintain layer ordering (Y > M > C > K)
- Consider anti-aliasing for very small circles

---

## Testing Strategy (optional)

### Unit Tests

- [ ] Test minimum radius enforcement
- [ ] Test layer ordering preserved for small clusters
- [ ] Test cumulative radii calculation accuracy

### Manual Testing Scenarios

1. **Happy Path**: Render image with mix of large and small clusters
   - Expected: All clusters visible and correctly colored

---

## Related Cards (optional)

### Dependencies

**Depends on**: kk5hjj - Multi-pass detection must work first

### Blocks

**Blocks**: Sprint closeout - rendering must work for complete verification
