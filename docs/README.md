# Documentation Index

Welcome to the DotMatrix documentation! This index helps you find the right documentation for your needs.

## Quick Navigation

| I want to... | Go to |
|--------------|-------|
| **Get started using DotMatrix** | [README.md](../README.md) |
| **Set up a development environment** | [DEVELOPMENT.md](DEVELOPMENT.md) |
| **Understand coding standards** | [Architectural Guidelines](architectural-guidelines.md) |
| **Learn how rendering works** | [Rendering Architecture](architecture/rendering-architecture.md) |
| **Understand color handling** | [Color Pipeline](architecture/color-pipeline.md) |
| **See why decisions were made** | [ADR Index](adr/README.md) |
| **Optimize CMYK/halftone detection** | [CMYK Halftone Guide](OPTIMAL_USAGE.md) |

---

## Documentation Structure

```
docs/
├── README.md                    # This index (you are here)
├── DEVELOPMENT.md               # Developer setup & onboarding
├── OPTIMAL_USAGE.md             # CMYK halftone detection guide
├── architectural-guidelines.md  # Coding principles & patterns
│
├── architecture/                # Technical deep-dives
│   ├── color-pipeline.md        # BGR convention, color processing
│   ├── pipeline-overview.md     # Full system data flow
│   ├── rendering-architecture.md # Renderer patterns, how to add renderers
│   └── system-overview-flowchart.md # Visual system diagram
│
├── adr/                         # Architecture Decision Records
│   ├── README.md                # ADR index with all decisions
│   ├── ADR-001-*.md             # Large file processing, SVG output
│   ├── ADR-002-*.md             # CLI UX, jitter strategy, scalability
│   ├── ADR-003-block-renderer.md
│   ├── ADR-004-gpu-acceleration.md
│   ├── ADR-005-cluster-rendering-pipeline.md
│   ├── ADR-006-cluster-pixel-counting.md
│   ├── ADR-007-logging-architecture.md
│   └── ADR-008-edge-detection-algorithm.md
│
└── research/                    # Research notes and experiments
```

---

## By Audience

### For Users

- **[README.md](../README.md)** - Installation, basic usage, CLI reference
- **[OPTIMAL_USAGE.md](OPTIMAL_USAGE.md)** - Tips for CMYK/halftone images

### For Contributors

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Environment setup, testing, workflow
- **[Architectural Guidelines](architectural-guidelines.md)** - Coding principles, patterns, ADR guidance

### For Architects

- **[Architecture Overview](architecture/pipeline-overview.md)** - 6-layer pipeline, data flow
- **[Rendering Architecture](architecture/rendering-architecture.md)** - Renderer catalog, extension guide
- **[Color Pipeline](architecture/color-pipeline.md)** - BGR convention, color algorithms
- **[ADRs](adr/README.md)** - All architectural decisions with context

---

## Key Concepts

### The 6-Layer Pipeline

DotMatrix processes images through six distinct layers:

1. **Input Layer** - Image loading, configuration
2. **Detection Layer** - Circle/shape detection algorithms
3. **Color Layer** - Color extraction and palette detection
4. **Cluster Layer** - CMYK cluster analysis (produces `ClusterResult`)
5. **Rendering Layer** - Visual output generation
6. **Output Layer** - File writing, manifests

See [Pipeline Overview](architecture/pipeline-overview.md) for details.

### ClusterResult Data Contract

The `ClusterResult` dataclass is the central data contract between layers:

```python
from dotmatrix.cluster_pixel_counter import ClusterResult

# Contains: x, y, cyan, magenta, yellow, black, red, green, blue, partial, bbox
```

All renderers consume `ClusterResult` - this enables mixing any detection method with any renderer.

### BGR Color Convention

**All colors use BGR format** (OpenCV native). See [Color Pipeline](architecture/color-pipeline.md).

```python
# Import centralized colors
from dotmatrix.colors import COLORS, COLORS_BGR, LAYER_ORDER
```

---

## Recent Updates

- **2026-01-08**: ARCHDEBT sprint - Centralized color definitions to `colors.py`, added `RenderParams` to config
- **2026-01-07**: ARCHREVIEW sprint - Created architectural guidelines, rendering architecture docs
- **2025-12-01**: v0.2.0 - Added GPU acceleration, convex edge detection

---

## Getting Help

- **GitHub Issues** - Bug reports and feature requests
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development environment help
- **[Troubleshooting](../README.md#troubleshooting)** - Common issues in README
