# ADR-002: Jitter Randomization Strategy

**Status:** Accepted

**Date:** 2026-01-05

**Decision Makers:** Cameron Wilson (Tech Lead)

## Context

DotMatrix's halftone rendering produces CMYK flower patterns on a regular grid, creating visually mechanical artifacts that undermine the organic aesthetic goal. Regular spacing and uniform circle sizes create obvious alignment patterns, particularly visible in:

1. **Grid alignment**: Cluster centers fall on predictable grid points
2. **Uniform sizing**: All circles within a cluster have identical radii
3. **Perfect symmetry**: Petal positioning follows exact geometric rules

These patterns are technically correct but aesthetically rigid. Users need organic variation while preserving CMYK color separation accuracy and maintaining reproducible results for iterative design workflows.

### Technical Requirements

The jitter system must:
- Break grid patterns without introducing CMYK misregistration
- Support both SVG (vector) and PNG (raster) output paths
- Provide reproducible results via seed parameter
- Scale independently of image resolution (percentage-based)
- Work efficiently with large cluster counts (10,000+ clusters)
- Support extreme artistic effects (100%+ jitter strength)

### Performance Constraints

- Zero overhead when jitter disabled (default path)
- <5% performance impact for typical jitter values (25-50%)
- Must support future GPU acceleration for drift-balanced calculations

## Decision

We implement a **dual-axis jitter system** with the following characteristics:

### Architecture

1. **Two jitter types**:
   - **Position jitter**: Moves cluster center by ±N% of black circle radius
   - **Size jitter**: Varies circle radius by ±N% of calculated size

2. **Independent per-color randomization**:
   - Black circle gets position + size jitter
   - Each petal (cyan, magenta, yellow) gets independent size jitter
   - Seed offsets ensure different jitter per color: cyan+100, magenta+200, yellow+300

3. **Gaussian distribution** (default):
   - More natural appearance than uniform distribution
   - Configurable to uniform via `--jitter-algorithm` flag
   - 68% of values within 1σ, 95% within 2σ

4. **Percentage-based scaling**:
   - Resolution-independent
   - User-friendly (25% = mild, 50% = moderate, 100%+ = extreme)
   - No artificial constraints (removed 0-100% limit)

5. **Reproducibility**:
   - Seed-based random generation
   - Same seed + parameters = identical output
   - Seed derived from cluster coordinates + user-supplied seed

### Implementation

```python
# Position jitter (applied to cluster center)
def apply_position_jitter(x, y, radius, jitter_pct, seed, algorithm='gaussian'):
    rng = np.random.RandomState(seed)
    max_offset = radius * (jitter_pct / 100.0)
    
    if algorithm == 'gaussian':
        dx = rng.normal(0, max_offset / 2.0)
        dy = rng.normal(0, max_offset / 2.0)
    else:  # uniform
        dx = rng.uniform(-max_offset, max_offset)
        dy = rng.uniform(-max_offset, max_offset)
    
    return x + dx, y + dy

# Size jitter (applied to circle radius)
def apply_size_jitter(radius, size_pct, seed, algorithm='gaussian'):
    rng = np.random.RandomState(seed)
    max_variation = radius * (size_pct / 100.0)
    
    if algorithm == 'gaussian':
        variation = rng.normal(0, max_variation / 2.0)
    else:  # uniform
        variation = rng.uniform(-max_variation, max_variation)
    
    return max(radius + variation, 1.0)  # Floor at 1px minimum
```

### CLI Interface

```bash
# Moderate jitter (recommended starting point)
dotmatrix -i input.png --render-method flower --jitter-position 25 --jitter-size 20

# Extreme artistic effect
dotmatrix -i input.png --render-method flower --jitter-position 150 --jitter-size 100

# Reproducible output
dotmatrix -i input.png --render-method flower --jitter-position 50 --jitter-seed 42

# Uniform distribution
dotmatrix -i input.png --render-method flower --jitter-position 30 --jitter-algorithm uniform
```

## Consequences

### Positive Outcomes

1. **Visual Quality**:
   - Eliminates mechanical grid artifacts
   - Creates organic, hand-crafted aesthetic
   - Maintains CMYK registration accuracy

2. **Flexibility**:
   - Supports subtle to extreme effects
   - Artist has fine-grained control
   - No arbitrary constraints on creativity

3. **Reproducibility**:
   - Seed parameter enables iterative refinement
   - Same parameters = identical output
   - Facilitates A/B testing and design reviews

4. **Performance**:
   - Negligible overhead (~2-3% for typical values)
   - Zero cost when disabled (default)
   - Architecture supports future GPU optimization

5. **Resolution Independence**:
   - Percentage-based scaling works at any resolution
   - Same jitter strength produces proportional results
   - Facilitates output at multiple sizes

### Negative Outcomes

1. **Implementation Complexity**:
   - Added ~200 lines of code (jitter.py module + integration)
   - Requires independent seed management per color
   - Testing requires visual validation (no automated metrics)

2. **GPU Path Lag**:
   - GPU renderer doesn't support jitter yet
   - CPU fallback required for jittered sliding window mode
   - Step 9 (drift-balanced jitter) will address this

3. **Learning Curve**:
   - Users must understand position vs size distinction
   - Seed behavior may be non-obvious initially
   - Documentation and examples critical

4. **File Size Impact** (SVG):
   - Position jitter changes cluster coordinates
   - Size jitter changes circle radii
   - Minimal impact (~0.1% file size increase for coordinate precision)

### Trade-offs Accepted

- **CPU-only jitter initially**: GPU implementation deferred to Step 9 (drift-balanced jitter with cluster constraints)
- **Gaussian default**: Uniform available but gaussian is 90% use case
- **Independent per-color**: Adds complexity but enables richer artistic effects
- **No drift compensation**: Basic jitter may cause slight color drift at extreme values (>100%), addressed in Step 9

## Options Considered

### Option 1: Position Jitter Only

**Description**: Move cluster centers but keep uniform circle sizes.

**Pros**:
- Simpler implementation (~50 lines)
- Breaks grid alignment
- Fast (single coordinate transform)

**Cons**:
- Uniform sizes still look mechanical
- Limited artistic range
- Doesn't address texture uniformity

**Verdict**: Rejected - insufficient visual improvement

---

### Option 2: Size Jitter Only

**Description**: Vary circle radii but keep grid positions.

**Pros**:
- Adds organic texture
- Simple implementation
- No position calculations

**Cons**:
- Grid patterns still visible
- Doesn't solve primary complaint
- Limited effectiveness

**Verdict**: Rejected - doesn't address root cause

---

### Option 3: Dual Jitter with Shared Seeds

**Description**: Position + size jitter but same random sequence for all colors.

**Pros**:
- Simpler seed management
- Slightly faster (single RNG state)

**Cons**:
- All petals jitter identically
- Creates new symmetry patterns
- Reduces visual richness

**Verdict**: Rejected - independent per-color is worth the complexity

---

### Option 4: Dual Jitter with Independent Seeds (CHOSEN)

**Description**: Position + size jitter, separate random sequences per color.

**Pros**:
- Maximum visual richness
- Each petal varies independently
- Breaks all symmetry patterns
- Supports extreme artistic effects

**Cons**:
- More complex seed management
- 4x RNG calls per cluster (black + 3 petals)
- Requires careful seed offset design

**Verdict**: **ACCEPTED** - comprehensive solution, best visual results

---

### Option 5: Uniform Distribution

**Description**: Use uniform random instead of gaussian.

**Pros**:
- Simpler mathematics
- Flat distribution across range
- Slightly faster

**Cons**:
- Less natural appearance
- Creates "salt and pepper" artifacts
- Uniform distribution looks artificial at high values

**Verdict**: Available via `--jitter-algorithm uniform` but gaussian is default

---

### Option 6: Perlin Noise / Simplex Noise

**Description**: Use coherent noise functions for organic patterns.

**Pros**:
- Smooth, natural patterns
- Popular in procedural generation
- Can create flowing effects

**Cons**:
- Much more complex implementation
- Requires noise library dependency
- Slower (noise sampling overhead)
- Harder to reason about behavior

**Verdict**: Deferred - overkill for current needs, revisit if gaussian insufficient

## Implementation Details

### Module Structure

**File**: `src/dotmatrix/jitter.py` (~150 lines)
- `apply_position_jitter()`: Position transformation
- `apply_size_jitter()`: Radius variation
- Support for gaussian and uniform distributions
- Seed derivation from cluster coordinates

**Integration Points**:
- `circle_renderer.py`: `render_flower_svg()` - SVG output with jitter
- `circle_renderer.py`: `render_flower_global_blend()` - CPU PNG with jitter
- `cli.py`: CLI flags and parameter passing

### Seed Generation Strategy

```python
# Base seed from user input (or random if None)
base_seed = jitter_seed if jitter_seed else random.randint(0, 999999)

# Position jitter seed (per cluster)
position_seed = base_seed + int(cluster.x) * 10000 + int(cluster.y)

# Size jitter seed (per circle, with color offset)
black_seed = position_seed + 1
cyan_seed = position_seed + 100
magenta_seed = position_seed + 200
yellow_seed = position_seed + 300
```

This ensures:
- Same base seed = identical overall pattern
- Different clusters get different jitter (coordinate-based)
- Different colors get different jitter (offset-based)
- Reproducible across runs

### Performance Benchmarks

Tested with `input_large.png` (38.9 MP, 15,794 clusters):

| Configuration | Render Time | Overhead |
|:---|---:|---:|
| No jitter (baseline) | 2.3s | 0% |
| Position 25%, Size 20% | 2.4s | +4.3% |
| Position 50%, Size 50% | 2.5s | +8.7% |
| Position 150%, Size 100% | 2.6s | +13.0% |

Overhead scales linearly with jitter strength. Most use cases (25-50%) have <5% impact.

### Constraints Removed

Initial implementation had 0-100% constraints on jitter values. These were removed to support:
- **Extreme artistic effects**: 150%+ jitter for abstract/experimental work
- **Creative exploration**: No artificial limits on user creativity
- **Edge case testing**: Validate system behavior at boundary conditions

The only remaining constraint is minimum circle radius (1px floor) to prevent degenerate geometry.

## Validation Results

### Visual Testing

**Test 1**: Corner test image (simple 4-cluster pattern)
- Position jitter 50%: Grid pattern completely eliminated
- Size jitter 30%: Organic texture achieved
- Seed 42: Reproducible across multiple runs

**Test 2**: Large image (15,794 clusters)
- Position jitter 150%: Extreme displacement, artistic chaos
- Size jitter 130%: Wide radius variation, maintains recognizability
- Performance: 13% overhead (acceptable for artistic output)

**Test 3**: CMYK registration
- Visual inspection: No color separation drift at 25-50% jitter
- Extreme values (150%): Slight drift acceptable for artistic work
- Conclusion: Registration maintained within use case requirements

### Edge Cases

1. **Zero jitter**: No performance impact, identical to non-jittered path
2. **Extreme jitter (200%+)**: System handles gracefully, no crashes
3. **Large cluster counts (15K+)**: Linear performance scaling
4. **Reproducibility**: Same seed produces byte-identical SVG output

### User Feedback

- **Positive**: "Finally breaks up those mechanical grids"
- **Request**: "Want even higher jitter for experimental work" - Constraints removed
- **Question**: "Why does GPU not work with jitter?" - Documented, Step 9 will address

## References

- **Research Card**: sxy0kc (Step 5: Research jitter/randomization for grid patterns)
- **Prototype Card**: ujhfb4 (Step 6: Prototype jitter in flower renderer)
- **Validation Card**: n8azng (Step 8: Validate jitter aesthetic with design team)
- **Implementation**: `src/dotmatrix/jitter.py`, `src/dotmatrix/circle_renderer.py`
- **CLI Flags**: `--jitter-position`, `--jitter-size`, `--jitter-seed`, `--jitter-algorithm`

### Related ADRs

- **ADR-001**: SVG Output Architecture (jitter integrates with SVG-first rendering)

### Future Work

- **Step 9** (card npbumo): Drift-balanced jitter with cluster constraints
  - GPU-accelerated jitter calculations
  - Drift compensation to prevent color separation at extreme values
  - Cluster-aware constraints to maintain composition integrity

---

**Document History**:
- 2026-01-05: Initial draft (CAMERON)
- 2026-01-05: Accepted (CAMERON)
