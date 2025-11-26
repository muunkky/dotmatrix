# Changelog

All notable changes to DotMatrix will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [Unreleased]

### Added
- `--min-radius` CLI flag to filter circles below specified radius (default: 10px)
- `--max-radius` CLI flag to control maximum circle size detection (default: 500px)
- `--min-distance` CLI flag to set minimum distance between circle centers (default: 20px)
- `--color-tolerance` CLI flag to adjust color grouping sensitivity (default: 20, range: 0-100)
- `--max-colors` CLI flag for intelligent color grouping using k-means clustering (requires --extract)
- `--sensitivity` CLI flag with presets: strict, normal (default), relaxed for detection tuning
- `--min-confidence` CLI flag to filter low-confidence detections (0-100 range)
- `--edge-sampling` CLI flag for edge-based color sampling (better for overlapping circles)
- `--edge-samples` CLI flag to configure number of edge sample points (default: 36)
- Confidence scores for each detected circle based on detection order (0-100%)
- K-means color clustering module (`color_clustering.py`) with scikit-learn integration
- Smart color reduction: automatically groups similar colors to N color groups
- Sensitivity presets for easy HoughCircles parameter tuning without OpenCV knowledge
- Edge-based color sampling: samples colors from circle perimeter instead of area
- Configurable min/max radius, min_distance, and sensitivity parameters in `detect_circles()` function
- Configurable tolerance and max_colors parameters in `extract_circles_to_images()` function
- Configurable use_edge_sampling and num_samples parameters in `extract_color()` function
- Confidence field added to JSON and CSV output formats
- 24 new tests for edge sampling, k-means, sensitivity, confidence, and min_distance (75 total tests, 90% coverage)
- 2 new integration tests for max_colors feature

### Technical Details
- Added `scikit-learn>=1.3.0` dependency for k-means clustering
- K-means clustering in RGB color space with automatic cluster count adjustment
- max_colors parameter overrides tolerance-based grouping when specified
- Sensitivity presets map to OpenCV HoughCircles param1/param2 parameters
- min_distance parameter maps directly to HoughCircles minDist parameter
- Confidence calculated using detection order as proxy (HoughCircles sorts by accumulator)
- Quadratic falloff formula: confidence = 100 * (1 - index/(n-1))^2
- Edge sampling uses evenly-spaced points around circumference (default: 36 samples)
- Median color calculation for edge samples (robust to outliers and partial occlusions)
- Edge sampling significantly improves color accuracy for overlapping circles

### Added (Convex Edge Detection - v0.2.0)
- `--convex-edge` CLI flag for detecting heavily overlapping circles using convex edge analysis
- `--palette` CLI flag for specifying color palette: preset names (`cmyk`, `rgb`) or custom RGB values (`255,0,0;0,255,0`)
- `--quantize-output` CLI flag to save quantized image for debugging
- New `convex_detector.py` module implementing convex edge detection algorithm:
  - Color quantization to limited palette using Euclidean distance
  - Per-color filtering to isolate circle segments
  - Convexity defect analysis to identify convex-only edges (using `cv2.convexityDefects`)
  - Circle fitting on convex edges only (using `cv2.HoughCircles`)
  - Best-circle-per-blob selection with coverage scoring
  - Deduplication of similar circles
- Preset color palettes: `cmyk` (White, Black, Cyan, Magenta, Yellow) and `rgb` (White, Black, Red, Green, Blue)
- 27 unit tests for convex_detector module (85% coverage)
- 10 integration tests for convex-edge CLI functionality

### Technical Details (Convex Edge Detection)
- Algorithm validated on test image with 16 overlapping CMYK circles - 100% detection accuracy
- Performance: <5 seconds for 1776x1696 image
- Key parameters: defect depth threshold 5px, non-convex margin 20px, dedup distance 20px
- Convex edge detection bypasses standard HoughCircles when `--convex-edge` is enabled
- Results compatible with existing JSON/CSV formatters and `--extract` functionality

### Added (Workflow Features - WORKFLOW Sprint)
- **Organized Output Directories**: Extraction now creates timestamped subdirectories
  - `--run-name` flag for custom run naming (e.g., `my-experiment_20251125_143022/`)
  - `--no-organize` flag to output files directly (flat mode) for backward compatibility
  - Automatic timestamping in `run_YYYYMMDD_HHMMSS` format
  - Directory name sanitization for filesystem safety
- **Configuration Save/Load**: Reusable detection settings
  - `--save-config` flag to save settings to YAML/JSON file
  - `--config` flag to load settings from file
  - Supports both flat and nested config formats
  - Config schema with default values and descriptions
  - CLI arguments always override config file values
- **Run Manifests**: Automatic metadata generation
  - `manifest.json` auto-generated in each run directory
  - Includes: version, timestamp, source file hash, all settings, results summary
  - SHA256 hash for source file verification
  - Circle count per color for quick reference
  - `--no-manifest` flag to disable generation
- **Run Management CLI**: Query and replay past runs
  - `dotmatrix runs list` - List all runs with name, date, source, circle count
  - `dotmatrix runs list --source FILE` - Filter by source filename
  - `dotmatrix runs list --after DATE` - Filter by date (YYYY-MM-DD)
  - `dotmatrix runs show RUN_NAME` - Display full manifest details
  - `dotmatrix runs replay RUN_NAME` - Re-run with same settings
  - `dotmatrix runs replay --dry-run` - Show command without executing
- New modules: `run_manager.py`, `manifest.py`, `runs.py`
- 79 new tests for workflow features (now 222 total tests)
- 5 end-to-end workflow tests covering the complete detection pipeline

### Technical Details (Workflow Features)
- CLI converted to click group for subcommand support (backward compatible)
- Config schema defines all configurable parameters with defaults and types
- Manifests use JSON format for easy parsing and tool integration
- Run discovery scans for `manifest.json` files in output subdirectories
- Replay reconstructs CLI command from manifest settings

### Added (Large File Support - LARGEFILE Sprint)
- **Performance documentation**: README now includes Performance section with benchmarks
- **Size warnings**: Warning displayed for `--convex-edge` on images >20 megapixels
- **Progress indicators**: "Detecting circles..." message for convex detection on large images
- **Helper function**: `get_image_megapixels()` for consistent size measurement
- New benchmark scripts: `benchmarks/large_file_benchmark.py`, `benchmarks/realistic_benchmark.py`
- ADR-001 documenting large file processing strategy and findings
- 12 new tests for large file handling (now 210 total tests)

### Technical Details (Large File Support)
- Per ADR-001: Use megapixels (not MB) as performance metric
- Hough detection: ~0.02s/MP, ~5 MB memory/MP - handles 64+ MP in <2 seconds
- Convex detection: ~2s/MP, ~20 MB memory/MP - handles 20 MP in <30 seconds
- No tiling/chunking needed: current architecture handles 10MB+ files efficiently
- Warning threshold: 20 megapixels (~4500×4500 pixels)
- Progress message threshold: 5 megapixels

### Added (Color Detection - COLORDETECTION Sprint)
- **Auto-palette detection**: `--palette auto` option to automatically detect dominant colors
  - Histogram-based color detection identifies dominant colors from image
  - `--num-colors N` option to specify number of colors to detect (default: 6)
  - White/background colors automatically excluded from detected palette
  - Black always included in detected palette when present
  - Detected palette displayed to user (e.g., "Detected palette: ~black, ~cyan, ~magenta, ~yellow")
  - Works with chunked processing and all existing convex-edge features
- New `color_palette_detector.py` module with histogram analysis
- 25 unit tests for palette detection (test_palette_detection.py)

### Technical Details (Color Detection)
- Color quantization (bucket_size=20) reduces anti-aliasing noise
- Image subsampling (every 10th pixel) for performance on large images
- Minimum color presence threshold (0.5%) filters out noise
- Detection uses histogram peak analysis (no k-means dependency for palette detection)

### Added (Occluded Circle Detection - COLORDETECTION Sprint)
- `--sensitive-occlusion` CLI flag for detecting heavily occluded circles
  - Adjusts detection parameters for partially visible circles
  - More permissive thresholds for edge detection
  - Better coverage of overlapping circle regions
- `--morph-enhance` CLI flag for morphological enhancement
  - Applies morphological operations to improve circle edges
  - Opening (erosion + dilation) removes small noise
  - Closing (dilation + erosion) fills small gaps in circle edges
  - Configurable kernel size based on circle radius

### Added (Radius Auto-Calibration - COLORDETECTION Sprint)
- `--auto-calibrate` CLI flag to auto-detect radius bounds from reference color
  - Uses darkest color (typically black) as reference for initial detection
  - Statistical analysis (mean ± 2σ) determines tight radius bounds
  - 10% padding applied for safety margin
  - Two-pass detection: first detect reference, then apply calibrated bounds
- `--calibrate-from` CLI flag to specify reference color by name
  - Supports color names: "black", "cyan", "magenta", "yellow", "red", "green", "blue"
  - Reference color detection provides reliable radius samples
- New calibration functions in `convex_detector.py`:
  - `RadiusCalibration` dataclass for calibration results
  - `calculate_radius_statistics()` computes mean, std, min, max
  - `calibrate_radius_from_reference()` creates calibration from detected circles
  - `select_reference_color()` picks darkest color from palette
  - `detect_with_calibration()` main entry point for calibrated detection
- 7 new tests for radius calibration (TestRadiusCalibration class)

### Technical Details (Radius Calibration)
- Reference color selection uses luminance: L = 0.299*R + 0.587*G + 0.114*B
- Calibration bounds: mean ± 2σ with 10% padding, enforced min_radius >= 5
- Requires minimum 3 detected circles for reliable calibration
- Calibration result includes reference color, count, and statistics

### Added (Scaling Performance - SCALING Sprint)
- **KD-tree spatial indexing**: O(n log n) circle deduplication replacing O(n²) nested loops
- **Chunked/tiled processing**: `--chunk-size` CLI flag for processing large images in tiles
  - `--chunk-size auto`: Automatic chunking for images >20 MP (default behavior)
  - `--chunk-size 2000`: Explicit chunk size in pixels
  - `--chunk-size 0`: Disable chunking (process entire image at once)
- **Boundary deduplication**: Circles on tile boundaries correctly deduplicated using overlap regions
- 12 new tests for chunked processing (TestGenerateTiles, TestCalculateChunkSize, TestProcessChunked)
- 45 total tests for convex detector with 94% coverage

### Technical Details (Scaling Performance)
- **KD-tree deduplication**: scipy.spatial.KDTree with query_ball_point() for O(n log n) neighbor searches
- **Tile overlap**: 2×max_radius to ensure boundary circles are fully captured in at least one tile
- **Minimum chunk size**: Enforced minimum of 3×overlap to prevent excessive tiling
- **Auto-chunking threshold**: Images >20 MP trigger automatic chunking
- **38 MP benchmark**: CMYK halftone image (6480×6000) processes in <5 minutes with ~8,000 circles detected
- **Deduplication benchmark**: 50,000 circles deduplicate in <10 seconds with KD-tree (vs minutes with nested loops)

### Planned for v0.2.0
- Partial circle detection at image edges
- Debug visualization mode

---

**Note**: This changelog follows [Keep a Changelog](https://keepachangelog.com/) conventions:
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities
