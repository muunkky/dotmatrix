# ADR-001: SVG Output Architecture

**Status:** Accepted

**Date:** 2026-01-24

**Decision Makers:** Cameron (Tech Lead), V2IDEAS Sprint Team

## Context

DotMatrix generates vector-based circle geometry during the detection/clustering phase (flower renderer), but currently rasterizes this data into numpy arrays for PNG output. Users working with print/design workflows need lossless vector output that preserves the geometric precision and allows editing in vector tools (Adobe Illustrator, Inkscape, Figma).

### Problem Statement
- Current architecture: Detect → Vector data → Rasterize to numpy → PNG only
- Users need: Lossless vector output for print/design workflows
- Inefficiency: Vector→Raster→Vector round-trip loses precision and editability
- Use cases: Halftone printing, screen printing, plotter output, graphic design

### Architectural Insight
The flower renderer already generates circle geometry (x, y, radius, CMYK values). We can emit SVG directly from this vector data without intermediate rasterization, making SVG a **first-class output format** rather than an export-only feature.

## Decision

Implement SVG output as a native rendering path alongside PNG, with the following architecture:

### SVG Structure
- **Element Type**: `<circle>` elements (not `<path>`)
  - Rationale: Better editability, inspector-friendly, semantic
  - Trade-off: Slightly larger file size vs `<path>`, but better DX
  
- **Grouping Strategy**: CMYK color layers with `<g>` groups
  ```xml
  <g id="cyan-layer" fill="#00FFFF" style="mix-blend-mode: multiply">
    <circle cx="..." cy="..." r="..."/>
    ...
  </g>
  <g id="magenta-layer" fill="#FF00FF" style="mix-blend-mode: multiply">
    ...
  </g>
  ```
  - Rationale: Layer-based editing in design tools, group-level attribute inheritance
  - Benefits: Easy to hide/show layers, recolor entire layers, export individual plates
  
- **Blend Mode**: `mix-blend-mode: multiply` for proper CMYK color mixing
  - Rationale: SVG uses painter's algorithm (later elements paint over earlier ones)
  - Without blend mode: Overlapping circles don't mix (only top color visible)
  - With multiply: Cyan + Magenta = Blue, Cyan + Yellow = Green (subtractive mixing)
  - Result: Proper CMYK-like color blending when circles overlap
  
- **CMYK-to-RGB Conversion**: Standard formula
  ```python
  R = 255 * (1 - C/100) * (1 - K/100)
  G = 255 * (1 - M/100) * (1 - K/100)
  B = 255 * (1 - Y/100) * (1 - K/100)
  ```
  - Colors: Cyan=#00FFFF, Magenta=#FF00FF, Yellow=#FFFF00, Black=#000000
  - Rationale: Standard conversion, editor-compatible, vibrant on-screen preview

### File Size Optimizations
1. **Coordinate Precision**: 1 decimal place (e.g., `cx="100.5"`)
   - Saves ~15 bytes per circle
   - Precision: 0.1px is sufficient for screen/print (0.004 inches at 300 DPI)
   
2. **Attribute Inheritance**: Group-level `fill` attribute
   - Saves ~12 bytes per circle
   - Example: `<g fill="#00FFFF">` instead of per-circle `fill="#00FFFF"`

3. **Blend Mode**: Group-level `style="mix-blend-mode: multiply"`
   - Adds ~27 bytes per group (negligible overhead for proper color mixing)
   - Essential for CMYK-like subtractive blending when circles overlap

4. **Result**: ~102 bytes per circle (includes blend mode overhead)

### Performance Thresholds
- **Target**: <100 KB for typical halftone images (1000 circles)
- **Validated**: Linear scaling, 97.4 KB for 1000 circles
- **Benchmark Results**:
  | Clusters | File Size | Bytes/Cluster |
  |----------|-----------|---------------|
  | 25       | 2.9 KB    | ~118 bytes    |
  | 100      | 10.0 KB   | ~102 bytes    |
  | 400      | 39.0 KB   | ~100 bytes    |
  | 1000     | 97.6 KB   | ~100 bytes    |
  
  Note: Includes `mix-blend-mode: multiply` overhead (~27 bytes per CMYK group)

### CLI Integration
- **Flag**: `--output-svg` (generates SVG alongside PNG)
- **Usage**: `dotmatrix -i image.png -m halftone --reconstitute --output-svg`
- **Output**: `reconstituted.svg` in run directory
- **Behavior**: SVG generation is optional, does not replace PNG output

## Consequences

### Positive
- **Lossless Vector Output**: No precision loss from raster round-trip  
- **First-Class Render Target**: SVG emitted directly from vector data  
- **Editor Compatibility**: Tested in Inkscape, Illustrator, web browsers  
- **Layer-Based Workflow**: CMYK layers independently editable  
- **File Size Efficiency**: ~100 bytes/cluster, linear scaling  
- **Future-Proof**: Enables jitter, drift-balanced jitter, ASCII directly in SVG  
- **Zero Dependencies**: Uses Python stdlib (`xml.etree.ElementTree` for tests)

### Negative
- **Maintenance**: Two output paths to maintain (PNG + SVG)  
- **Complexity**: SVG rendering logic separate from numpy-based rendering  
- **Feature Parity**: Future features need both PNG and SVG implementations  
- **Testing**: SVG-specific test suite required (15 tests added)

### Trade-offs
- **`<circle>` vs `<path>`**: Chose editability over 5-10% file size savings
- **CMYK Layers**: Better workflow, but ~27 bytes overhead per layer
- **Precision**: 1 decimal place balances size vs quality (0.1px precision)

## Options Considered

### Option 1: SVG Export (Post-Rasterization) - REJECTED
Convert numpy array back to circles using contour detection or blob analysis.

**Pros:**
- Single code path (only PNG rendering)
- Simple implementation

**Cons:**
- Lossy: Raster→Vector conversion loses precision
- Circles may not round-trip correctly (anti-aliasing artifacts)
- Inefficient: Already have perfect circle data from flower renderer

### Option 2: Native SVG Rendering - SELECTED
Emit SVG directly from flower renderer's circle geometry.

**Pros:**
- Lossless: No precision loss
- Efficient: Skip rasterization entirely
- First-class: SVG is native output, not export
- Future-proof: Enables vector-only features (jitter, ASCII)

**Cons:**
- Two output paths to maintain
- More complex architecture

**Rationale:** The pros far outweigh the cons. Vector data is already available, and maintaining two output paths is manageable with proper abstraction.

### Option 3: `<path>` Elements (Arc Notation) - REJECTED
Use `<path d="M cx,cy m -r,0 a r,r 0 1,0 2*r,0 a r,r 0 1,0 -2*r,0"/>` for circles.

**Pros:**
- 5-10% smaller file size

**Cons:**
- Harder to read/edit manually
- Less semantic (not immediately recognizable as circles)
- Poor inspector UX (no `r` attribute, must parse `d`)

**Rationale:** Editability and developer experience outweigh minor file size savings.

## References

### Research & Documentation
- **Research Card**: 4janms "Step 1: Research SVG output formats"
- **Prototype Card**: 7jk86r "Step 2: Prototype SVG output mode"
- **Validation Card**: wikyff "Step 4: Validate SVG file size and performance" (pending)

### Implementation
- **Module**: `src/dotmatrix/svg_renderer.py` (265 lines, 92% test coverage)
- **Tests**: `tests/test_svg_output.py` (213 lines, 15 tests, all passing)
- **CLI Integration**: `src/dotmatrix/cli.py` lines 252, 420, 1433-1442

### Standards & Best Practices
- **SVG 1.1 Specification**: https://www.w3.org/TR/SVG11/
- **CMYK-to-RGB Conversion**: Standard formula (industry-accepted approximation)
- **File Size Benchmarks**: Validated 25-1000 cluster range

### Test Results
- 15/15 tests passing
- 92% code coverage
- Colors visible and correct in demos
- File sizes better than estimates (~100 bytes/cluster vs 120 predicted)
- Editor compatibility validated (Inkscape, Illustrator, browsers)

### Future Work
- **Jitter Integration**: `render_svg_with_jitter()` placeholder added
- **ASCII Output**: Can leverage SVG path for text rendering
- **Drift-Balanced Jitter**: Vector-based displacement directly in SVG
- **Partial Circles**: SVG arcs for edge-case rendering

---

**Implementation Notes:**
This ADR documents the architecture decision made during V2IDEAS sprint Step 3. The prototype (Step 2) validated all technical assumptions. Step 4 (performance validation) will test at scale (10k-100k circles) and verify editor compatibility in production workflows.
