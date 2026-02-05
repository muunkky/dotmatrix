# Architectural Guidelines

> **Part of**: [Documentation Index](README.md) - See all docs
>
> **Created**: 2026-01-07 as part of ARCHREVIEW sprint (card 7chgdu)
> **Based on**: Deep architectural review spike (dbwrwj)
> **Last Updated**: 2026-01-08 (ARCHDEBT sprint - colors.py, RenderParams)

This document codifies the architectural principles and patterns that guide dotmatrix development. Following these guidelines ensures consistency, maintainability, and a smooth contributor experience.

## Table of Contents

1. [Core Principles](#core-principles)
2. [Module Organization](#module-organization)
3. [Data Contracts](#data-contracts)
4. [Adding New Renderers](#adding-new-renderers)
5. [GPU Acceleration](#gpu-acceleration)
6. [Configuration Management](#configuration-management)
7. [Error Handling](#error-handling)
8. [Testing Requirements](#testing-requirements)
9. [Performance Guidelines](#performance-guidelines)
10. [Documentation Requirements](#documentation-requirements)
11. [When to Write an ADR](#when-to-write-an-adr)

---

## Core Principles

These principles emerged from architectural review and guide all development decisions:

### 1. Data Contract First

`ClusterResult` is the shared data contract between processing and rendering layers. New features should produce or consume `ClusterResult`:

```python
from dotmatrix.cluster_pixel_counter import ClusterResult

# ClusterResult contains all data needed for rendering:
# - Position: x, y (center coordinates)
# - CMYK counts: cyan, magenta, yellow, black
# - RGB overlaps: red (M∩Y), green (C∩Y), blue (C∩M)
# - Metadata: partial (edge flag), bbox (bounding box)
```

**Rationale**: A single data contract enables loose coupling between layers. Any renderer can work with any detection method as long as both speak `ClusterResult`.

### 2. BGR Throughout

All image data uses **BGR format** (OpenCV native). Never mix RGB and BGR:

```python
# CORRECT: BGR format
cyan_bgr = (255, 255, 0)    # B=255, G=255, R=0
magenta_bgr = (255, 0, 255)  # B=255, G=0, R=255

# WRONG: RGB format will produce incorrect colors
cyan_rgb = (0, 255, 255)  # Don't use this!
```

See [color-pipeline.md](architecture/color-pipeline.md) for the full BGR convention.

### 3. Graceful Degradation

Features should degrade gracefully when dependencies are unavailable:

```python
# CORRECT: Graceful GPU fallback
from dotmatrix.gpu import is_gpu_available

if is_gpu_available():
    result = gpu_accelerated_function(data)
else:
    result = cpu_fallback_function(data)
```

**Never require** GPU, specific file formats, or optional dependencies for core functionality.

### 4. Configuration via Dataclass

Parameters belong in the config system, not scattered through function signatures:

```python
# CORRECT: Parameters in config dataclass
@dataclass
class DetectionParams:
    min_radius: int = 5
    max_radius: int = 100
    sensitivity: Literal["normal", "sensitive"] = "normal"

# AVOID: Magic numbers in function calls
result = detect_circles(image, 5, 100, "normal")  # What are these?
```

### 5. ADR for Decisions

Significant architectural decisions must be documented. See [When to Write an ADR](#when-to-write-an-adr).

### 6. Test Coverage

Maintain **>85% test coverage** for new code. All public functions need tests.

### 7. CLI Option Groups

Organize CLI options into logical groups using Click's `option_group`:

```python
from click_option_group import optgroup

@optgroup.group("Detection Options")
@optgroup.option("--min-radius", default=5)
@optgroup.option("--max-radius", default=100)
```

### 8. Conventional Commits

Use [Conventional Commits](https://www.conventionalcommits.org/) for all changes:

```
feat(renderer): add ASCII art renderer
fix(gpu): handle memory allocation failure
docs(adr): document ASCII renderer decision
test(renderer): add ASCII renderer unit tests
refactor(color): extract shared COLORS dict
```

---

## Module Organization

### Layer Structure

The codebase follows a 6-layer pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: INPUT                                              │
│  cli.py, config.py, config_loader.py, image_loader.py       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: DETECTION                                          │
│  circle_detector.py, convex_detector.py                      │
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
│  cluster_pixel_counter.py (ClusterResult), sliding_window   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 5: GPU ACCELERATION                                   │
│  gpu.py, gpu_renderer.py                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 6: RENDERING & OUTPUT                                 │
│  circle_renderer.py, block_renderer.py, treemap_renderer.py │
│  cluster_renderer.py, svg_renderer.py, formatter.py         │
└─────────────────────────────────────────────────────────────┘
```

### Module Boundaries

- **Lower layers should NOT import from higher layers**
- **Cross-layer communication uses data contracts** (ClusterResult, Circle)
- **Utility modules** (logger, gpu, jitter) can be imported from any layer

### Adding New Modules

1. Identify which layer your module belongs to
2. Create module in `src/dotmatrix/`
3. Add exports to `__init__.py` if public API
4. Add tests in `tests/test_<module>.py`
5. Update `docs/DEVELOPMENT.md` project structure

---

## Data Contracts

### ClusterResult (Primary Contract)

The central data structure connecting processing and rendering:

```python
@dataclass
class ClusterResult:
    """Result for a single halftone cluster."""
    x: int           # Center X (black dot position)
    y: int           # Center Y (black dot position)
    cyan: int        # Cyan pixel count
    magenta: int     # Magenta pixel count
    yellow: int      # Yellow pixel count
    black: int       # Black pixel count
    red: int         # Red overlap (M∩Y) count
    green: int       # Green overlap (C∩Y) count
    blue: int        # Blue overlap (C∩M) count
    partial: bool    # True if cluster at image edge
    bbox: Optional[Tuple[int, int, int, int]]  # Bounding box
```

### Circle (Detection Contract)

Used between detection and color extraction:

```python
@dataclass
class Circle:
    """Detected circle."""
    center_x: int
    center_y: int
    radius: int
    confidence: float
```

### Adding New Data Contracts

If you need a new data structure shared between layers:

1. Define as a `@dataclass` with type hints
2. Place in appropriate layer module
3. Document all fields with docstrings
4. Add `__eq__` and `__hash__` if needed for collections
5. Export from `__init__.py` if public

---

## Adding New Renderers

### Required Pattern

All raster renderers must follow this pattern:

```python
"""<Name> Renderer for CMYK clusters."""

from typing import List, Tuple
import cv2
import numpy as np
from dotmatrix.cluster_pixel_counter import ClusterResult

# Use shared colors (future: from dotmatrix.colors import COLORS, LAYER_ORDER)
COLORS = {
    'yellow': (0, 255, 255),    # BGR
    'red': (0, 0, 255),
    'green': (0, 255, 0),
    'magenta': (255, 0, 255),
    'blue': (255, 0, 0),
    'cyan': (255, 255, 0),
    'black': (0, 0, 0),
}

LAYER_ORDER = ['yellow', 'red', 'green', 'magenta', 'blue', 'cyan', 'black']


def render_<name>(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    skip_partial: bool = False,
    **renderer_specific_params
) -> np.ndarray:
    """Render clusters using <name> method.
    
    Args:
        clusters: List of ClusterResult from cluster_pixel_counter
        image_shape: (height, width) of output image
        skip_partial: If True, skip clusters at image edges
        
    Returns:
        BGR numpy array (cv2 native format)
    """
    h, w = image_shape
    output = np.full((h, w, 3), 255, dtype=np.uint8)  # White background
    
    for cluster in clusters:
        if skip_partial and cluster.partial:
            continue
        render_single_<name>(cluster, output, **renderer_specific_params)
    
    return output


def render_single_<name>(
    cluster: ClusterResult,
    image: np.ndarray,
    **params
) -> np.ndarray:
    """Render one cluster onto image (modified in place)."""
    # Your rendering logic here
    return image
```

### Renderer Checklist

- [ ] Module named `<name>_renderer.py`
- [ ] Follows batch/single function pattern
- [ ] Accepts `List[ClusterResult]` as input
- [ ] Returns BGR numpy array
- [ ] Supports `skip_partial` parameter
- [ ] Uses COLORS dict in BGR format
- [ ] Has comprehensive docstrings
- [ ] CLI option added to `--render-method`
- [ ] Tests in `tests/test_<name>_renderer.py`
- [ ] Documentation updated

See [rendering-architecture.md](architecture/rendering-architecture.md) for detailed guidance.

---

## GPU Acceleration

### When to Use GPU

GPU acceleration is worthwhile for:

- **Batch operations** over >1,000 items
- **Image processing** on images >4 megapixels
- **Distance calculations** with >200 centers
- **Pixel counting** over >1M pixels

### GPU Pattern

```python
from dotmatrix.gpu import is_gpu_available, get_array_module

def process_data(data):
    """Process data with GPU acceleration if available."""
    if is_gpu_available() and len(data) > 1000:
        return _process_gpu(data)
    return _process_cpu(data)

def _process_cpu(data):
    """CPU implementation (always required)."""
    import numpy as np
    # NumPy implementation
    pass

def _process_gpu(data):
    """GPU implementation (optional acceleration)."""
    import cupy as cp
    # CuPy implementation
    pass
```

### GPU Guidelines

1. **Always provide CPU fallback** - GPU is never required
2. **Check `is_gpu_available()` before GPU code**
3. **Set minimum thresholds** - GPU has overhead, not always faster
4. **Handle memory errors** - GPU memory is limited
5. **Test both paths** - Tests should cover CPU and GPU

See [ADR-004](adr/ADR-004-gpu-acceleration.md) for GPU acceleration decisions.

---

## Configuration Management

### Config Hierarchy

Parameters come from multiple sources with this priority:

```
CLI Arguments (highest priority)
    ↓
Config File (JSON/YAML)
    ↓
Dataclass Defaults (lowest priority)
```

### Adding New Parameters

1. **Add to appropriate config dataclass** in `config.py`:

```python
@dataclass
class DetectionParams:
    min_radius: int = 5
    max_radius: int = 100
    new_param: int = 42  # Add with sensible default
```

2. **Add CLI option** in `cli.py`:

```python
@optgroup.group("Detection Options")
@optgroup.option("--new-param", default=42, help="Description of new param")
```

3. **Update `from_cli_args()`** in `config.py`:

```python
@classmethod
def from_cli_args(cls, **kwargs) -> 'DetectionConfig':
    return cls(
        detection=DetectionParams(
            new_param=kwargs.get('new_param', 42),
            # ...
        ),
    )
```

4. **Add tests** for the new parameter

5. **Document** in README.md if user-facing

### Config File Format

```json
{
  "detection": {
    "min_radius": 5,
    "max_radius": 100,
    "sensitivity": "normal"
  },
  "color": {
    "palette": "auto",
    "num_colors": 6
  }
}
```

---

## Error Handling

### Error Strategy

1. **Validate early**: Check inputs at function entry
2. **Fail fast**: Raise exceptions for invalid state
3. **Provide context**: Include helpful error messages
4. **Log appropriately**: Use logger for debugging info

### Error Pattern

```python
from dotmatrix.logger import get_logger

logger = get_logger(__name__)

def process_image(image_path: str) -> np.ndarray:
    """Process image with proper error handling."""
    # Validate inputs
    if not image_path:
        raise ValueError("image_path cannot be empty")
    
    if not Path(image_path).exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Log progress
    logger.debug(f"Loading image: {image_path}")
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to decode image: {image_path}")
        return image
    except cv2.error as e:
        logger.error(f"OpenCV error processing {image_path}: {e}")
        raise RuntimeError(f"Image processing failed: {e}") from e
```

### Logging Levels

| Level | Use For |
|-------|---------|
| `DEBUG` | Detailed diagnostic info (file paths, counts) |
| `INFO` | Normal operation progress |
| `WARNING` | Recoverable issues (fallback used, deprecation) |
| `ERROR` | Failures that stop processing |

---

## Testing Requirements

### Coverage Expectations

- **Minimum**: 85% line coverage for new code
- **Target**: 90%+ for core algorithms
- **Required**: All public functions have at least one test

### Test Organization

```
tests/
├── conftest.py          # Shared fixtures
├── data/                # Test images and data
├── test_<module>.py     # Unit tests per module
└── test_integration.py  # End-to-end tests
```

### Test Pattern

```python
import pytest
import numpy as np
from dotmatrix.cluster_pixel_counter import ClusterResult
from dotmatrix.my_renderer import render_my_method

class TestRenderMyMethod:
    """Tests for render_my_method function."""
    
    def test_empty_clusters(self):
        """Empty cluster list returns white image."""
        result = render_my_method([], (100, 100))
        assert result.shape == (100, 100, 3)
        assert np.all(result == 255)
    
    def test_single_cluster(self, sample_cluster):
        """Single cluster renders correctly."""
        result = render_my_method([sample_cluster], (100, 100))
        assert result.dtype == np.uint8
        # More specific assertions...
    
    def test_skip_partial(self, partial_cluster):
        """skip_partial=True excludes edge clusters."""
        result = render_my_method([partial_cluster], (100, 100), skip_partial=True)
        assert np.all(result == 255)  # Nothing rendered

@pytest.fixture
def sample_cluster():
    """Create a sample ClusterResult for testing."""
    return ClusterResult(
        x=50, y=50,
        cyan=100, magenta=80, yellow=60, black=40,
        red=20, green=15, blue=10,
        partial=False, bbox=(25, 25, 75, 75)
    )
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=dotmatrix --cov-report=html

# Specific module
pytest tests/test_my_renderer.py -v

# GPU tests only
pytest -k "gpu"
```

---

## Performance Guidelines

### Profiling First

Before optimizing, profile to identify actual bottlenecks:

```bash
python -m cProfile -o profile.stats -m dotmatrix input.png
# Then analyze with snakeviz or pstats
```

### Performance Patterns

1. **Vectorize with NumPy**: Avoid Python loops over pixels
2. **Pre-allocate arrays**: Create output arrays once, modify in place
3. **Use cv2 primitives**: `cv2.circle`, `cv2.rectangle` are highly optimized
4. **Consider GPU**: For operations on >1M elements
5. **Subsample for analysis**: Don't process every pixel if sampling works

### Example: Vectorized vs Loop

```python
# SLOW: Python loop
for y in range(height):
    for x in range(width):
        if image[y, x, 0] > 128:
            result[y, x] = 255

# FAST: Vectorized
result[image[:, :, 0] > 128] = 255
```

### Memory Considerations

- Large images (>4K) may need chunked processing
- Use `sliding_window.py` for very large files
- Monitor GPU memory with `nvidia-smi`

---

## Documentation Requirements

### For New Features

Every new feature needs:

1. **Docstrings**: All public functions/classes
2. **README.md update**: If user-facing
3. **DEVELOPMENT.md update**: If affects developers
4. **ADR**: If architectural decision (see below)

### Docstring Format

```python
def render_flower(
    clusters: List[ClusterResult],
    image_shape: Tuple[int, int],
    petal_distance: float = 1.0,
) -> np.ndarray:
    """Render clusters as flower patterns with CMY petals around K center.
    
    Creates a visual representation where each cluster becomes a flower:
    - Black dot at center
    - Cyan, Magenta, Yellow petals radiating outward
    - Petal sizes proportional to pixel counts
    
    Args:
        clusters: List of ClusterResult from cluster_pixel_counter
        image_shape: Output image dimensions as (height, width)
        petal_distance: Multiplier for petal offset from center (default: 1.0)
    
    Returns:
        BGR numpy array with rendered flowers on white background
    
    Raises:
        ValueError: If image_shape contains non-positive dimensions
    
    Example:
        >>> clusters = count_cluster_pixels(image, centers)
        >>> result = render_flower(clusters, image.shape[:2])
        >>> cv2.imwrite("flowers.png", result)
    """
```

---

## When to Write an ADR

Write an Architecture Decision Record when:

### Must Write ADR

- Adding a new rendering method
- Changing data contract (ClusterResult, Circle)
- Adding external dependency
- Changing GPU strategy
- Modifying CLI structure significantly
- Breaking backwards compatibility

### Consider Writing ADR

- Performance optimization trade-offs
- Alternative approaches were evaluated
- Decision affects multiple modules
- Decision is non-obvious to future readers

### ADR Format

ADRs live in `docs/adr/` with format `ADR-XXX-short-title.md`:

```markdown
# ADR-XXX: Short Title

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
What is the issue we're deciding on?

## Decision
What is the change we're making?

## Consequences
What are the trade-offs of this decision?

## Alternatives Considered
What other options did we evaluate?
```

See existing ADRs in `docs/adr/` for examples.

---

## Related Documentation

- [DEVELOPMENT.md](DEVELOPMENT.md) - Developer onboarding
- [rendering-architecture.md](architecture/rendering-architecture.md) - Renderer patterns
- [color-pipeline.md](architecture/color-pipeline.md) - BGR convention and color processing
- [pipeline-overview.md](architecture/pipeline-overview.md) - System architecture
- [docs/adr/](adr/) - Architecture Decision Records
