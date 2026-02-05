# Developer Onboarding Guide

Welcome to dotmatrix! This guide will help you set up your development environment and understand the project structure.

> **Documentation Hub**: [docs/README.md](README.md) - Find all documentation from one place
>
> **See Also**: [Architectural Guidelines](architectural-guidelines.md) for coding principles and patterns

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Project Structure](#project-structure)
4. [Running Tests](#running-tests)
5. [Development Workflow](#development-workflow)
6. [Architecture Overview](#architecture-overview)
7. [Key Concepts](#key-concepts)
8. [Common Development Tasks](#common-development-tasks)
9. [Debugging Tips](#debugging-tips)
10. [Code Style](#code-style)
11. [GPU Development](#gpu-development)
12. [Getting Help](#getting-help)

---

## Prerequisites

### Required

- **Python 3.9+** (3.10 or 3.11 recommended)
- **pip** (latest version)
- **git**
- **Virtual environment** (venv, conda, or similar)

### Optional (for GPU acceleration)

- **NVIDIA GPU** with CUDA support
- **CUDA Toolkit 12.x**
- **CuPy** (`pip install cupy-cuda12x`)

Verify your Python version:

```bash
python --version  # Should be 3.9+
```

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/username/dotmatrix.git
cd dotmatrix
```

### 2. Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Windows cmd)
.\venv\Scripts\activate.bat

# Activate (Linux/macOS)
source venv/bin/activate
```

### 3. Install Development Dependencies

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Optional: Install GPU support
pip install -e ".[dev,gpu]"
```

### 4. Verify Installation

```bash
# Check CLI works
dotmatrix --help

# Run tests
pytest

# Check GPU availability (if installed)
python -c "from dotmatrix.gpu import is_gpu_available; print(f'GPU: {is_gpu_available()}')"
```

---

## Project Structure

```
dotmatrix/
├── src/dotmatrix/           # Main package
│   ├── __init__.py          # Package exports
│   ├── __main__.py          # Entry point for `python -m dotmatrix`
│   ├── cli.py               # Click-based CLI (~700 lines)
│   ├── circle_detector.py   # HoughCircles detection
│   ├── color_extractor.py   # RGB color extraction
│   ├── color_separation.py  # CMYK color separation
│   ├── cluster_pixel_counter.py  # Cluster analysis (~1200 lines)
│   ├── cluster_renderer.py  # Bullseye visualization
│   ├── block_renderer.py    # Block renderer (100% accuracy)
│   ├── gpu.py               # GPU utilities and array helpers
│   ├── gpu_renderer.py      # GPU-accelerated rendering
│   └── ...                  # 28 modules total
├── tests/                   # Test suite
│   ├── conftest.py          # Pytest fixtures
│   ├── data/                # Test images and fixtures
│   └── test_*.py            # 37 test files
├── docs/                    # Documentation
│   ├── adr/                 # Architecture Decision Records
│   └── architecture/        # Architecture documentation
├── configs/                 # JSON configuration presets
├── benchmarks/              # Performance benchmarks
└── pyproject.toml           # Project configuration
```

### Key Modules by Function

| Layer | Modules | Purpose |
|-------|---------|---------|
| **Input** | `cli.py`, `image_loader.py`, `config.py` | CLI and image handling |
| **Detection** | `circle_detector.py`, `convex_detector.py` | Shape detection |
| **Color** | `color_extractor.py`, `color_separation.py`, `palette_detection.py` | Color analysis |
| **GPU** | `gpu.py`, `gpu_renderer.py` | GPU acceleration |
| **Cluster** | `cluster_pixel_counter.py` | CMYK cluster analysis |
| **Output** | `cluster_renderer.py`, `block_renderer.py`, `treemap_renderer.py` | Visualization |

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_cluster_pixel_counter.py
```

### Run Tests Matching Pattern

```bash
pytest -k "cluster"  # All tests with "cluster" in name
pytest -k "gpu"      # All GPU-related tests
```

### Run with Coverage

```bash
pytest --cov=dotmatrix --cov-report=html
# Open htmlcov/index.html in browser
```

### Test Organization

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_cluster_pixel_counter.py` | 50 | Core cluster algorithm |
| `test_cli_presets.py` | 20+ | CLI options and presets |
| `test_gpu_acceleration.py` | 15+ | GPU fallback and acceleration |
| `test_block_renderer.py` | 10+ | Block renderer accuracy |

---

## Development Workflow

### Branch Naming

```
feature/short-description   # New features
fix/issue-description       # Bug fixes
docs/what-is-documented     # Documentation
refactor/what-is-refactored # Code improvements
```

### Commit Style

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(cluster): add bounding box to ClusterResult
fix(gpu): handle CuPy import failure gracefully
docs(adr): add ADR-005 cluster rendering decision
test(gpu): add GPU fallback integration tests
refactor(cli): extract color options to separate group
```

### Pull Request Process

1. Create feature branch from `main`
2. Make changes with atomic commits
3. Ensure all tests pass: `pytest`
4. Check formatting: `black . && ruff check .`
5. Create PR with clear description
6. Address review feedback

---

## Architecture Overview

> **Detailed Documentation**: See [architectural-guidelines.md](architectural-guidelines.md) for coding principles and patterns.

Dotmatrix processes images through a **6-layer pipeline**:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: INPUT                                              │
│  cli.py, config.py, config_loader.py, image_loader.py       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: DETECTION                                          │
│  circle_detector.py (Hough), convex_detector.py (CMYK)      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: COLOR PROCESSING                                   │
│  color_extractor.py, color_clustering.py,                   │
│  color_palette_detector.py, color_separation.py             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: CLUSTER PROCESSING                                 │
│  cluster_pixel_counter.py (ClusterResult dataclass)         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: GPU ACCELERATION (optional)                        │
│  gpu.py, gpu_renderer.py                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 6: RENDERING & OUTPUT                                 │
│  circle_renderer.py, block_renderer.py, treemap_renderer.py │
│  cluster_renderer.py, svg_renderer.py, formatter.py         │
└─────────────────────────────────────────────────────────────┘
```

### Central Data Contract

`ClusterResult` is the shared data contract that connects all layers:

```python
from dotmatrix.cluster_pixel_counter import ClusterResult

# All renderers consume List[ClusterResult]
# All cluster processing produces List[ClusterResult]
```

### Three Processing Modes

1. **RGB Mode** (`dotmatrix input.png`): Circle detection + RGB color extraction
2. **CMYK Mode** (`dotmatrix --cmyk input.png`): Full CMYK separation + cluster analysis
3. **Reconstitute Mode** (`dotmatrix reconstitute clusters.json`): Rebuild image from cluster data

### Architecture Documentation

| Document | Purpose |
|----------|---------|
| [architectural-guidelines.md](architectural-guidelines.md) | **Start here** - Coding principles and patterns |
| [architecture/pipeline-overview.md](architecture/pipeline-overview.md) | System-wide data flow |
| [architecture/rendering-architecture.md](architecture/rendering-architecture.md) | How to add renderers |
| [architecture/color-pipeline.md](architecture/color-pipeline.md) | BGR convention, color algorithms |
| [docs/adr/](adr/) | Architecture Decision Records |

### Architecture Decision Records

Key ADRs to understand design decisions:

| ADR | Topic |
|-----|-------|
| ADR-001 | Large file processing with chunked/tiled approach |
| ADR-002 | Jitter randomization strategy |
| ADR-003 | Block renderer for 100% pixel accuracy |
| ADR-004 | GPU acceleration with CuPy |
| ADR-005 | Cluster-based pixel counting for CMYK analysis |

Located in `docs/adr/`. See [docs/adr/README.md](adr/README.md) for full index.

---

## Key Concepts

### Halftone Printing

Dotmatrix analyzes halftone images where continuous tones are represented by dots of varying sizes. Understanding this is essential for working on the cluster pipeline.

### CMYK Color Model

- **C** (Cyan), **M** (Magenta), **Y** (Yellow), **K** (Black)
- Overlaps create secondary colors: C∩M=Blue, M∩Y=Red, C∩Y=Green
- Black (K) dots anchor clusters for pixel counting

### Cluster-Based Counting

Instead of counting pixels per-circle (which fails with overlaps), we:

1. Find black dot centers
2. Assign each pixel to nearest center (Voronoi tessellation)
3. Count colors per cluster

See `cluster_pixel_counter.py` and ADR-005.

### GPU Acceleration

GPU is used for specific operations where it provides speedup:

- NMS (Non-Maximum Suppression) for >200 centers
- Batch color counting for >1M pixels
- Distance transform for merged dot detection

See `gpu.py` and ADR-004.

---

## Common Development Tasks

### Adding a CLI Option

1. Open `src/dotmatrix/cli.py`
2. Add option to appropriate `@option_group`:

```python
@option_group("Detection Options", ...)
@click.option("--new-option", default=42, help="Description")
def main(..., new_option: int):
    # Use new_option in processing
```

3. Add test in `tests/test_cli_presets.py`

### Adding a Test

1. Create or extend test file in `tests/`
2. Use fixtures from `conftest.py`:

```python
def test_my_feature(sample_image_path):
    """Test description."""
    result = process_image(sample_image_path)
    assert result.success
```

3. Run: `pytest tests/test_my_feature.py -v`

### Adding a Renderer

> **Detailed guide**: See [rendering-architecture.md](architecture/rendering-architecture.md) for complete patterns and code templates.

Quick checklist:
1. Create `src/dotmatrix/my_renderer.py`
2. Implement `render_<name>(clusters: List[ClusterResult], image_shape, **params) -> np.ndarray`
3. Use BGR color format (cv2 convention)
4. Add CLI option in `cli.py` for `--render-method`
5. Add tests in `tests/test_my_renderer.py`
6. Update README.md if user-facing

---

## Debugging Tips

### Debug Flag

```bash
dotmatrix --debug input.png
```

Outputs verbose logging and timing information.

### Debug Cluster Visualization

```bash
dotmatrix --cmyk --debug-clusters input.png
```

Creates `cluster_debug.png` showing cluster assignments with unique colors.

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: dotmatrix` | Run `pip install -e .` |
| GPU tests fail | Check CUDA installation: `nvidia-smi` |
| Slow tests | Use `pytest -x` to stop on first failure |
| Import errors | Check you're in venv: `which python` |

### Useful Debug Commands

```bash
# Check package installation
pip show dotmatrix

# Verify imports
python -c "from dotmatrix import cli; print('OK')"

# GPU diagnostics
python -c "from dotmatrix.gpu import gpu_info; print(gpu_info())"
```

---

## Code Style

### Formatting

```bash
# Format code
black .

# Check formatting (CI check)
black --check .
```

### Linting

```bash
# Run linter
ruff check .

# Auto-fix issues
ruff check --fix .
```

### Type Checking

```bash
mypy src/dotmatrix/
```

### Docstring Convention

Use Google-style docstrings:

```python
def process_image(path: Path, threshold: float = 0.5) -> Result:
    """Process an image for circle detection.

    Args:
        path: Path to the input image file.
        threshold: Detection confidence threshold (0-1).

    Returns:
        Result object containing detected circles and metadata.

    Raises:
        FileNotFoundError: If the image file doesn't exist.
    """
```

---

## GPU Development

### Setup

```bash
# Verify CUDA
nvidia-smi

# Install CuPy for CUDA 12.x
pip install cupy-cuda12x
```

### Testing GPU vs CPU

```python
from dotmatrix.gpu import is_gpu_available, get_array_module

# Check availability
print(f"GPU available: {is_gpu_available()}")

# Get appropriate module (NumPy or CuPy)
xp = get_array_module(use_gpu=True)  # Auto-selects
```

### Benchmarking

```bash
# Run GPU benchmarks
python benchmarks/gpu_benchmark.py

# Compare results
cat benchmarks/gpu_benchmark_results.json
```

### GPU Design Guidelines

1. **Always provide CPU fallback** - Use `get_array_module()` pattern
2. **Profile before GPU-ifying** - Not all operations benefit
3. **Consider data transfer costs** - GPU helps only for large arrays
4. **Test both paths** - Tests should run without GPU available

---

## Getting Help

### Documentation

| Document | Purpose |
|----------|---------|
| **README.md** | User-facing installation and usage |
| **[architectural-guidelines.md](architectural-guidelines.md)** | Coding principles and patterns |
| **[docs/architecture/](architecture/)** | Technical architecture docs |
| **[docs/adr/](adr/)** | Architecture Decision Records |
| **CHANGELOG.md** | Version history |
| **ROADMAP.md** | Future development plans |

### Key Architecture Documents

- [rendering-architecture.md](architecture/rendering-architecture.md) - **How to add renderers**
- [color-pipeline.md](architecture/color-pipeline.md) - BGR convention and color processing
- [pipeline-overview.md](architecture/pipeline-overview.md) - System data flow

### Issue Templates

When creating issues, include:

- Python version and OS
- Full error traceback
- Minimal reproduction steps
- Input image (if applicable, redact if sensitive)

### Code Owners

- **Core pipeline**: See `cluster_pixel_counter.py`, `cli.py`
- **GPU acceleration**: See `gpu.py`, `gpu_renderer.py`
- **Renderers**: See `*_renderer.py` modules

### Useful Links

- [OpenCV HoughCircles docs](https://docs.opencv.org/4.x/dd/d1a/group__imgproc__feature.html#ga47849c3be0d0406ad3ca45db65a25d2d)
- [CuPy documentation](https://docs.cupy.dev/en/stable/)
- [Click documentation](https://click.palletsprojects.com/)

---

## Next Steps

After setting up:

1. Run the full test suite: `pytest`
2. Try the CLI: `dotmatrix --help`
3. Read ADR-001 through ADR-005 for design context
4. Pick a "good first issue" or explore the codebase

Welcome to the team! 🎉
