

## Research Question
What are the best algorithms for jitter randomization in dot placement?

## Time Box
4 hours

## Acceptance Criteria
- [ ] 3 distinct algorithms identified and analyzed
- [ ] Prototype implementations for visual comparison
- [ ] Recommendation for the best algorithm for V2

## Context
Part of V2IDEAS research to improve visual naturalness of dot matrix generation.

## Test Plan
- [ ] Manual visual verification of prototypes
- [ ] Peer review of algorithm selection
- [ ] Performance benchmarking of algorithms

## Edge Cases & Constraints

### Black-Dominated Clusters
**Problem:** Some clusters are almost entirely black with only minimal color showing (e.g., small flower petals barely visible against dark background). These clusters pose special challenges:

1. **Minimal Jitter Response:** When 90%+ of a cluster is black/background, jittering the small visible portion has negligible visual impact
2. **Drift Constraints:** For drift (balanced randomization), maintaining color balance becomes impractical when the color mass is too small relative to the cluster size
3. **Risk of Disappearance:** Aggressive jitter/drift could push the tiny colored portion completely out of the cluster boundary, making it invisible
4. **Computational Waste:** Iterative balance algorithms spend cycles trying to balance clusters that are fundamentally unbalanced by design

**Potential Solutions to Investigate:**

* **Threshold-Based Skipping:** Define a minimum color mass threshold (e.g., <5% of cluster area). Skip jitter/drift for clusters below this threshold
* **Clamped Jitter:** For low-mass clusters, reduce jitter intensity proportionally (e.g., scale jitter by color_mass_percentage)
* **Anchor Mode:** Treat black-dominated clusters as "anchors" - apply no jitter, let them stabilize the composition
* **Selective Drift:** Only apply drift to clusters with sufficient color diversity (e.g., require at least 2 colors with >5% mass each)
* **Hybrid Strategy:** Full jitter for balanced clusters, reduced/zero jitter for black-dominated ones

**Research Questions:**
- What's the optimal threshold for determining "black-dominated"?
- Should threshold be absolute (pixel count) or relative (percentage)?
- Do black-dominated clusters benefit from any jitter, or should they be fully static?
- How does this interact with the "Eclipse" algorithm (Occlusion Culling) from the design docs?

**Test Scenarios:**
- Image with high black content (dark flowers, night scenes)
- Cluster with 95% black, 5% yellow petal
- Cluster with 50% black, 25% cyan, 25% magenta (balanced despite black dominance)
- Edge case: cluster with 100% black (should definitely skip)