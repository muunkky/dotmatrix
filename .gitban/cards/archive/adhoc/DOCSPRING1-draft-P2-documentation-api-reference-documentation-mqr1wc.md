# Documentation Card

## Overview

Create API reference documentation for the dotmatrix Python modules, enabling programmatic usage beyond the CLI.

**Documentation Type:** Reference
**Target Audience:** Developers, Library Users
**Estimated Effort:** 2 days

## Scope

### What Will Be Documented

* [ ] Public module interfaces
* [ ] Key classes and their methods
* [ ] Function signatures with type hints
* [ ] Usage examples for common operations
* [ ] Import patterns and dependencies
* [ ] Which modules are stable vs. internal

### Success Criteria

| Criterion | How to Verify |
| :--- | :--- |
| All public modules documented | Index of public API |
| Type hints documented | Signatures include types |
| Examples provided | Each major class has example |
| Stability indicated | Public vs internal marked |

### Dependencies

| Dependency | Status | Blocker? |
| :--- | :--- | :---: |
| Architecture Deep Dive spike (4ftn9c) | Module relationships | Yes |
| Module Docstring Audit (mskwrn) | Base docstrings in place | Partial |

## Implementation Plan

### Tasks

* [ ] Identify public API surface (which modules/classes are user-facing)
* [ ] Document CircleDetector and detection interfaces
* [ ] Document GPU utilities (gpu.py, gpu_renderer.py)
* [ ] Document cluster pipeline (cluster_pixel_counter.py, cluster_renderer.py)
* [ ] Document color separation API
* [ ] Document renderers (block_renderer.py, circle_renderer.py)
* [ ] Add usage examples for common workflows
* [ ] Consider Sphinx/autodoc generation

### Documentation Structure

```
docs/api-reference/
├── index.md (Overview, stability policy)
├── detection.md
│   ├── CircleDetector
│   └── ConvexDetector
├── gpu.md
│   ├── GPU Detection
│   └── GPU Renderers
├── clusters.md
│   ├── ClusterPixelCounter
│   └── ClusterRenderer
├── color.md
│   ├── Color Separation
│   └── CMYK Processing
├── renderers.md
│   ├── BlockRenderer
│   └── CircleRenderer
└── examples.md
```

## Notes

This is a P2 card - valuable for library usage but not critical for CLI-focused handoff. Consider whether to use Sphinx autodoc or hand-written docs.

Start with the most commonly used classes from the CLI entry point and work outward. The Architecture Deep Dive spike will identify which modules are truly public vs internal implementation details.
