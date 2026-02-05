# Changelog

All notable changes to DotMatrix will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Refactored
- **ARCHDEBT Sprint** (2026-01-08): Addressed technical debt identified during ARCHREVIEW sprint.
  - Created [colors.py](src/dotmatrix/colors.py) - Centralized color definitions module with `COLORS`, `COLORS_BGR`, `LAYER_ORDER`, `LAYER_ORDER_CMYK`, `PETAL_ANGLES` constants.
  - Updated 6 renderer files to import from centralized `colors.py` (block_renderer, treemap_renderer, cluster_renderer, circle_renderer, cmyk_accuracy, gpu_renderer).
  - Removed duplicate COLORS dict definitions from all renderer files.
  - Added `RenderParams` and `JitterParams` dataclasses to config.py for renderer configuration.
  - Updated `from_cli_args()` to accept render and jitter parameters.
  - Updated [rendering-architecture.md](docs/architecture/rendering-architecture.md) to reflect centralized color definitions.

### Added
- **Real-time Progress Indicators**: Added comprehensive progress feedback during rendering operations.
  - GPU/CPU status displayed at render start (e.g., "Rendering with GPU (CUDA)" or "Rendering with CPU").
  - Progress updates during flower rendering showing cluster count and percentage complete.
  - Throughput metrics showing clusters processed per second.
  - Estimated time remaining (ETA) for long-running renders.
  - Progress callback system with metadata including elapsed time, throughput, and ETA.
- **Black Dot Verification**: Added ground truth validation for CMYK detection using black (K) channel dots.
  - Automatic verification enabled by default for CMYK palette detection (disable with `--no-verify-black`).
  - Displays verification stats: detected count, radius distribution (mean, std, range), coverage %, density.
  - Intelligent warnings for misconfigured settings (min/max radius too narrow, sparse detection).
  - Suggested radius range based on statistical analysis (mean ± 2σ with padding).
  - Visual coverage heatmap saved in debug mode (`black_verification_coverage.png`).
  - `--verify-abort` flag to stop processing if verification fails threshold.
  - Helps users validate detection parameters before running expensive full CMYK separation.

### Documentation
- **ARCHREVIEW Sprint** (2026-01-07): Comprehensive documentation and architecture review.
  - Created [architectural-guidelines.md](docs/architectural-guidelines.md) - 11-section guide covering coding principles, patterns, and extension guidelines.
  - Created [rendering-architecture.md](docs/architecture/rendering-architecture.md) - Renderer patterns, "How to add a renderer" 6-step guide.
  - Enhanced [color-pipeline.md](docs/architecture/color-pipeline.md) - Color processing algorithms, k-means clustering, palette detection.
  - Enhanced [DEVELOPMENT.md](docs/DEVELOPMENT.md) - 6-layer pipeline diagram, architecture documentation links.
  - Updated [ROADMAP.md](ROADMAP.md) - v0.3.0 status, cluster rendering section, drift/jitter/SVG documentation.
  - Updated [README.md](README.md) - Jitter/randomization options documentation.
  - Audited ADRs - Fixed numbering conflicts, created complete index at [docs/adr/README.md](docs/adr/README.md).
  - Completed deep architectural review spike documenting 6-layer pipeline, ClusterResult data contract, and 8 guiding principles.
- **ADR-006**: Documented architectural decision for CMYK cluster pixel counting algorithm.
  - 3-phase approach: midtone completion, nearest-pixel clustering, deduplication.
  - 9-element output tuple preventing double-counting of RGB overlaps.
  - Validation rules for edge cases and partial clusters.

## [0.2.0] - 2025-12-01

### Added
- **Convex Edge Detection**: `--convex-edge` CLI flag for detecting heavily overlapping circles using convex edge analysis (best for CMYK/halftone). Includes color quantization, convexity defect analysis, and coverage scoring.
- **GPU Acceleration**: comprehensive CuPy/CUDA framework for 30-100x speedup on compatible hardware.
  - `--gpu/--no-gpu` CLI control.
  - GPU-accelerated cluster pipeline (NMS, labeling, color counting).
  - GPU-accelerated flower renderer.
  - Graceful CPU fallback.
- **Large File Support**: Optimized pipeline for high-resolution images (>50MP).
  - Chunked/tiled processing with `--chunk-size`.
  - Spatial indexing (KD-tree) for O(n log n) deduplication.
  - Sliding window processing with seam artifact prevention.
- **Intelligent Color Detection**:
  - `--palette auto` for histogram-based dominant color detection.
  - `--num-colors` to specify target palette size.
  - `--exclude-background` to ignore white/paper colors.
  - `--calibrate-from` to auto-calibrate radius from reference colors.
- **Advanced Rendering Modes**:
  - `flower`: CMYK petals around black center (physically accurate halftone model).
  - `cmyk-blend`: Subtractive color mixing (C+M=Blue, etc.).
  - `treemap`: Proportional area rectangles.
  - `block`: Stacked bar charts.
- **Cluster Analysis Tools**:
  - `--debug-clusters` for visualization.
  - `--cluster-anchor` control (centroid vs pixel).
  - Bounding box calculation.
- **Workflow Enhancements**:
  - Timestamped output directories (e.g., `run_20251125_...`).
  - `manifest.json` generation with full run metadata.
  - Configuration save/load (`--save-config`, `--config`).
  - Run management CLI (`dotmatrix runs list/show/replay`).
- **Documentation**:
  - Comprehensive `docs/DEVELOPMENT.md` guide.
  - Architecture documentation in `docs/architecture/`.
  - ADRs 001-005 covering key architectural decisions.
- **Orphan pixel diagnostic tool**: `scripts/diagnose_orphans.py` for analyzing INPUT images to find halftone dots not captured by detection.

### Fixed
- **Small halftone dot detection**: Fixed critical bug where small dots (1-13px radius) were filtered out during detection due to relative thresholding. Now uses absolute threshold.
  - Zero missed dots in validation set (down from 64).
- **Black Blob Rendering**: Fixed overlapping black dots merging into giant blobs. Now uses distance transform and local maxima detection to separate touching dots.
- **Sliding Window Artifacts**: Fixed flower clipping at tile boundaries by ensuring overlap region clusters contribute petals to core region.
- **Flower Renderer Clipping**: Fixed Z-order issue where black circles were clipped by CMY petals in blend mode.
- **Petal Geometry**: Improved petal positioning formula for shallower, rounder arcs (centers moved inside black circle).

### Changed
- **Refactored Architecture**: Modularized pipeline into functional layers (Input, Detection, Color, GPU, Cluster, Output).
- **Performance**: Replaced O(n²) operations with spatial indexing and GPU acceleration where possible.
- **Output Organization**: Default output now creates structured run folders instead of flat files.

## [0.1.0] - 2025-10-31

### Added
- Initial release of DotMatrix circle detection CLI
- Image loading support for PNG, JPG, JPEG formats
- Circle detection using Hough Circle Transform algorithm
- RGB color extraction from detected circles with circular masking
- JSON output format with circle coordinates, radius, and colors
- CSV output format for spreadsheet compatibility
- `--input` flag for specifying input image path
- `--output` flag for writing results to file (default: stdout)
- `--format` flag for choosing output format (json/csv)
- `--debug` flag for verbose logging
- `--extract` flag for generating separate PNG images by color
  - Groups circles by similar colors (configurable tolerance)
  - Creates transparent background RGBA images
  - One PNG file per color group
  - Descriptive filenames: `circles_color_RRR_GGG_BBB.png`
- Comprehensive test suite with 46 total tests:
  - 33 tests for core detection pipeline (91% coverage)
  - 13 tests for PNG extraction (100% coverage on new module)
- Full documentation in README.md
- MIT License

### Technical Details
- Built with Python 3.9+
- Dependencies: click, opencv-python, numpy, pillow
- Uses Hough Circle Transform with Gaussian blur preprocessing
- Color extraction via masked pixel averaging (BGR to RGB conversion)
- Click-based CLI with path validation
- Hatchling build backend (PEP 660 compliant)

### Performance
- Detection rate: >90% on test images
- Center accuracy: Within 5px
- Radius accuracy: Within 10%
- Color accuracy: Within 10% RGB tolerance
- Successfully tested with 190 circles in single image