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

### Planned for v0.2.0
- Partial circle detection at image edges
- Debug visualization mode
- Improved overlapping circle separation

---

**Note**: This changelog follows [Keep a Changelog](https://keepachangelog.com/) conventions:
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities
