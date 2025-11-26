# DotMatrix

**Circle Detection CLI Tool**

DotMatrix is a Python command-line tool that detects circles in images and outputs their center coordinates, radius, and color. It handles overlapping and occluded circles using advanced computer vision techniques.

## Features

- 🎯 Accurate circle detection using Hough Circle Transform
- 🎨 Color extraction for each detected circle (RGB)
- 📊 Multiple output formats: JSON and CSV
- 🖼️ **PNG extraction**: Generate separate images by color with transparent backgrounds
- 🔄 **Handles overlapping circles** with convex edge detection (best-in-class for CMYK/halftone)
- 🚀 Fast processing with optimized algorithms
- 📝 Simple command-line interface

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/username/dotmatrix.git
cd dotmatrix

# Install in editable mode with dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### From PyPI (Coming Soon)

```bash
pip install dotmatrix
```

## Usage

### Basic Usage

```bash
# Detect circles in an image (JSON output to stdout)
dotmatrix --input image.png

# Save output to a file
dotmatrix --input image.png --output results.json

# Use CSV format
dotmatrix --input image.png --format csv --output results.csv
```

### CLI Options

```
Options:
  -i, --input PATH        Input image file path (PNG, JPG, JPEG) [required]
  -o, --output PATH       Output file path (default: stdout)
  -f, --format [json|csv] Output format (default: json)
  --extract PATH          Extract circles to separate PNG images by color
  --min-radius INTEGER    Minimum circle radius in pixels (default: 10)
  --max-radius INTEGER    Maximum circle radius in pixels (default: 500)
  --min-distance INTEGER  Minimum distance between circle centers in pixels (default: 20)
  --color-tolerance INTEGER  RGB distance threshold for color grouping (default: 20, range: 0-100)
  --max-colors INTEGER    Maximum number of color groups using k-means clustering (only with --extract)
  --sensitivity [strict|normal|relaxed]  Detection sensitivity preset (default: normal)
  --min-confidence INTEGER  Minimum confidence score to include detection (0-100)
  --debug                 Enable debug output
  --version               Show version and exit
  --help                  Show this message and exit
```

### Detection Tuning

Control detection sensitivity with easy presets:

```bash
# Strict: Fewer detections, higher confidence (good for clean images)
dotmatrix --input image.png --sensitivity strict

# Normal: Balanced detection (default)
dotmatrix --input image.png --sensitivity normal

# Relaxed: More detections, lower threshold (good for noisy/low-quality images)
dotmatrix --input image.png --sensitivity relaxed
```

**Sensitivity Presets:**
- `strict`: param1=100, param2=40 - Fewer false positives, misses some circles
- `normal`: param1=50, param2=30 - Balanced (default)
- `relaxed`: param1=30, param2=20 - Catches more circles, may include false positives

### Confidence Filtering

Filter detections by confidence score (0-100%):

```bash
# Only include high-confidence detections
dotmatrix --input image.png --min-confidence 80

# Medium confidence threshold (good for noisy images)
dotmatrix --input image.png --min-confidence 50

# Combine with sensitivity for fine control
dotmatrix --input image.png --sensitivity relaxed --min-confidence 60
```

**About Confidence Scores:**
- All detected circles include a confidence score (0-100%)
- Calculated from detection order (HoughCircles returns best circles first)
- First detected circle = 100%, subsequent circles decrease with quadratic falloff
- Higher confidence = more reliable detection
- Use `--min-confidence` to filter out uncertain detections

### Size Filtering

Control which circles are detected based on size:

```bash
# Ignore small circles (noise/flecks)
dotmatrix --input image.png --min-radius 20

# Focus on medium-sized circles only
dotmatrix --input image.png --min-radius 30 --max-radius 100

# Detect only very large circles
dotmatrix --input image.png --min-radius 200

# Combine with sensitivity for fine control
dotmatrix --input image.png --min-radius 20 --sensitivity relaxed
```

### Distance Filtering

Control spacing between detected circles to prevent overlapping detections:

```bash
# Default: 20 pixels minimum distance
dotmatrix --input image.png

# Stricter: more distance required (fewer circles)
dotmatrix --input image.png --min-distance 50

# Looser: allow closer circles (more detections)
dotmatrix --input image.png --min-distance 10

# Combine with other filters
dotmatrix --input image.png --min-distance 30 --min-radius 15
```

**About Distance Filtering:**
- Minimum distance measured between circle centers (not edges)
- Larger values prevent overlapping circle detections
- Useful for grid patterns or well-spaced circles
- Default of 20px works well for most images

### Convex Edge Detection (Best for Overlapping Circles)

For images with heavily overlapping circles (like CMYK halftones), use convex edge detection:

```bash
# Detect overlapping CMYK circles using convex edge analysis
dotmatrix --input image.png --convex-edge --palette cmyk

# With min-radius filter (recommended)
dotmatrix --input image.png --convex-edge --palette cmyk --min-radius 80

# Extract to color-grouped PNGs
dotmatrix --input image.png --convex-edge --palette cmyk --extract output_dir/

# Use custom color palette (RGB values separated by semicolons)
dotmatrix --input image.png --convex-edge --palette "255,0,0;0,255,0;0,0,255"

# Save quantized image for debugging
dotmatrix --input image.png --convex-edge --palette cmyk --quantize-output debug.png
```

**About Convex Edge Detection:**
- Uses convexity defect analysis to separate overlapping circles
- First quantizes image to a limited color palette (handles anti-aliasing)
- Detects circles from convex-only edges (ignores overlapping concave regions)
- Best-circle-per-blob selection ensures accurate detection
- Automatically deduplicates similar circles

**Preset Palettes:**
- `cmyk`: White, Black, Cyan (118,193,241), Magenta (217,93,155), Yellow (238,206,94)
- `rgb`: White, Black, Red, Green, Blue

**When to Use:**
- ✅ **Use convex-edge** for CMYK halftone patterns with overlapping circles
- ✅ **Use convex-edge** when standard detection misses circles due to heavy overlap
- ✅ **Use convex-edge** when you know the exact colors in your image
- ❌ **Use standard detection** for well-separated circles
- ❌ **Use standard detection** when colors are unknown/varied

**Example (16 overlapping CMYK circles):**
```bash
$ dotmatrix --input halftone.png --convex-edge --palette cmyk --min-radius 80
# Detects all 16 circles: 4 black, 4 cyan, 4 magenta, 4 yellow
```

### Edge-Based Color Sampling

For images with overlapping circles, use edge sampling to get more accurate colors:

```bash
# Enable edge-based color sampling (better for overlapping circles)
dotmatrix --input image.png --edge-sampling

# Adjust number of sample points around edge (default: 36)
dotmatrix --input image.png --edge-sampling --edge-samples 72

# Combine with extraction for accurate color grouping
dotmatrix --input image.png --extract output_dir/ --edge-sampling
```

**About Edge Sampling:**
- Samples colors from circle perimeter instead of entire area
- Significantly improves color accuracy when circles overlap
- Uses median of sampled colors (robust to outliers)
- Default: 36 evenly-spaced sample points around circumference
- More samples = more accurate but slightly slower
- **Recommended for:** Layered/3D dot matrix patterns with overlapping circles

**When to Use:**
- ✅ **Use edge sampling** when circles overlap or layer over each other
- ✅ **Use edge sampling** when colors appear incorrect due to averaging
- ❌ **Use area sampling** (default) for non-overlapping circles
- ❌ **Use area sampling** for simple, well-separated dot patterns

**Example:**
Without edge sampling, a blue circle under a black circle appears gray/dark.
With `--edge-sampling`, it correctly detects the blue color from the exposed edge.

### PNG Extraction

Extract detected circles to separate PNG images, grouped by color:

```bash
# Extract circles to a directory
dotmatrix --input image.png --extract output_dir/

# With debug output
dotmatrix --input image.png --extract output_dir/ --debug

# Control color grouping with tolerance
dotmatrix --input image.png --extract output_dir/ --color-tolerance 5  # Strict (more groups)
dotmatrix --input image.png --extract output_dir/ --color-tolerance 50 # Loose (fewer groups)
```

**Output:**
- One PNG file per color group
- Transparent backgrounds (RGBA format)
- Filename format: `circles_color_RRR_GGG_BBB.png`
- Similar colors grouped based on tolerance (default: 20)

**Color Tolerance:**
- `0`: Exact color match only (most groups)
- `20`: Default - groups similar colors (balanced)
- `50`: Loose grouping - combines more colors (fewer groups)
- `100`: Very loose - maximum grouping

**Example:**
```bash
$ dotmatrix --input test.png --extract circles/
Extracted 4 color group(s) to circles/
  - circles_color_255_000_000.png  # Red circles
  - circles_color_000_255_000.png  # Green circles
  - circles_color_000_000_255.png  # Blue circles
  - circles_color_255_255_000.png  # Yellow circles
```

### Smart Color Grouping

Use k-means clustering to intelligently reduce many colors to N groups:

```bash
# Reduce 20 unique colors to 4 intelligent groups
dotmatrix --input image.png --extract output_dir/ --max-colors 4

# Force exactly 2 color groups (e.g., foreground/background)
dotmatrix --input image.png --extract output_dir/ --max-colors 2

# Combine with size filtering
dotmatrix --input image.png --extract output_dir/ --max-colors 3 --min-radius 20
```

**K-means vs Tolerance:**
- `--color-tolerance`: Groups similar colors using RGB distance threshold (simpler, faster)
- `--max-colors`: Uses k-means clustering for intelligent grouping (more sophisticated)
- When both specified: `--max-colors` takes precedence

**Use Cases:**
- Extract dominant color themes from complex images
- Reduce output files when you have many similar colors
- Create clean color-separated layers for editing

**Before/After Example:**
```bash
# Without --max-colors: 20 output files (one per unique color)
$ dotmatrix --input image.png --extract output/
Extracted 20 color group(s) to output/

# With --max-colors: 4 output files (intelligently grouped)
$ dotmatrix --input image.png --extract output/ --max-colors 4
Extracted 4 color group(s) to output/
```

### Example Output

**JSON Format:**
```json
[
  {
    "center": [150.5, 200.3],
    "radius": 45.2,
    "color": [255, 100, 50],
    "confidence": 100.0
  },
  {
    "center": [300.1, 180.7],
    "radius": 60.8,
    "color": [50, 150, 255],
    "confidence": 75.0
  }
]
```

**CSV Format:**
```csv
center_x,center_y,radius,color_r,color_g,color_b,confidence
150.5,200.3,45.2,255,100,50,100.0
300.1,180.7,60.8,50,150,255,75.0
```

## Requirements

- Python >= 3.9
- OpenCV >= 4.8.0
- NumPy >= 1.24.0
- Click >= 8.0.0
- Pillow >= 10.0.0
- scikit-learn >= 1.3.0

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=dotmatrix --cov-report=html
```

### Code Quality

```bash
# Format code with black
black src tests

# Lint with ruff
ruff check src tests

# Type checking with mypy
mypy src
```

## Project Structure

```
dotmatrix/
├── src/
│   └── dotmatrix/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py              # CLI interface
│       ├── circle_detector.py  # Hough Circle Transform
│       ├── convex_detector.py  # Convex edge detection for overlapping circles
│       ├── color_extractor.py  # Color sampling
│       ├── color_clustering.py # K-means color clustering
│       ├── image_extractor.py  # PNG extraction by color
│       └── formatter.py        # JSON/CSV formatters
├── tests/
│   ├── data/                   # Test images and ground truth
│   ├── test_cli.py
│   ├── test_circle_detector.py
│   └── test_color_extractor.py
├── pyproject.toml
└── README.md
```

## Roadmap

### v0.1.0 - MVP (Current)
- [x] Basic project structure
- [ ] Hough Circle Transform detection
- [ ] Color extraction
- [ ] JSON/CSV output
- [ ] Unit tests

### v0.2.0 - Overlapping Circles (Current)
- [x] Convex edge detection for overlapping circles
- [x] Color palette quantization (CMYK, RGB, custom)
- [x] Per-color circle detection with convexity analysis
- [x] `--convex-edge`, `--palette`, `--quantize-output` CLI flags

### v0.3.0 - Production Ready
- [ ] Confidence scores
- [ ] Visualization mode
- [ ] Performance optimizations
- [ ] Comprehensive documentation
- [ ] PyPI release

## Algorithm

DotMatrix uses the **Hough Circle Transform** algorithm:

1. **Preprocessing**: Convert image to grayscale and apply Gaussian blur
2. **Edge Detection**: Detect edges using Canny edge detector
3. **Circle Detection**: Use Hough voting to find circles
4. **Color Extraction**: Sample pixels within circle boundaries
5. **Output**: Format results as JSON or CSV

For overlapping circles (v0.2.0+), we also perform:
- Multi-scale detection for varying circle sizes
- Depth ordering inference from occlusion patterns
- Masked color sampling for accurate color extraction

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Author

Cameron - [GitHub](https://github.com/username)

## Acknowledgments

- OpenCV for computer vision algorithms
- Click for CLI framework
- NumPy for numerical computations
