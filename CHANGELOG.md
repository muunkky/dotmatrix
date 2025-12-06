# Changelog

All notable changes to DotMatrix will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Real-time Progress Indicators**: Added comprehensive progress feedback during rendering operations.
  - GPU/CPU status displayed at render start (e.g., "Rendering with GPU (CUDA)" or "Rendering with CPU").
  - Progress updates during flower rendering showing cluster count and percentage complete.
  - Throughput metrics showing clusters processed per second.
  - Estimated time remaining (ETA) for long-running renders.
  - Progress callback system with metadata including elapsed time, throughput, and ETA.

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