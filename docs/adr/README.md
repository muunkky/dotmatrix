# Architecture Decision Records (ADRs)

> **Part of**: [Documentation Index](../README.md)

This directory contains Architecture Decision Records documenting significant architectural choices made in the DotMatrix project.

## Index

| ADR | Title | Status | Date |
|:---|:---|:---|:---|
| [ADR-001a](ADR-001-large-file-processing.md) | Large File Processing | Accepted | 2024-11-10 |
| [ADR-001b](ADR-001-svg-output-architecture.md) | SVG Output Architecture | Accepted | 2026-01-05 |
| [ADR-002a](ADR-002-cli-ux-refactoring.md) | CLI UX Refactoring | Accepted | 2024-11-12 |
| [ADR-002b](ADR-002-jitter-randomization-strategy.md) | Jitter Randomization Strategy | Accepted | 2026-01-05 |
| [ADR-002c](ADR-002-scalability-strategy.md) | Scalability Strategy | Accepted | 2024-11-14 |
| [ADR-003](ADR-003-block-renderer.md) | Block Renderer | Accepted | 2024-11-15 |
| [ADR-004](ADR-004-gpu-acceleration.md) | GPU Acceleration | Accepted | 2024-11-20 |
| [ADR-005](ADR-005-cluster-rendering-pipeline.md) | Cluster Rendering Pipeline | Accepted | 2024-11-22 |
| [ADR-006](ADR-006-cluster-pixel-counting.md) | Cluster Pixel Counting | Accepted | 2024-11-25 |
| [ADR-007](ADR-007-logging-architecture.md) | Logging Architecture | Accepted | 2024-12-01 |
| [ADR-008](ADR-008-edge-detection-algorithm.md) | Edge Detection Algorithm | Accepted | 2024-12-10 |

> **Note:** ADR-001 and ADR-002 have numbering conflicts from parallel work streams.
> Future ADRs should use sequential numbering from ADR-009 onwards.

## ADR Format

Each ADR follows this structure:

```markdown
# ADR-NNN: Title

**Status:** Proposed | Accepted | Deprecated | Superseded

**Date:** YYYY-MM-DD

**Decision Makers:** Names

## Context
What is the issue we're addressing?

## Decision
What change are we making?

## Consequences
What are the positive and negative outcomes?

## Options Considered
Alternative approaches and why they were rejected.

## References
Supporting materials, research, related ADRs.
```

## Creating a New ADR

1. Use the next available ADR number
2. Follow the standard format above
3. Include Context, Decision, Consequences, and Options Considered sections
4. Update this index with the new ADR
5. Commit with message: `docs(adr): add ADR-NNN - Title`
