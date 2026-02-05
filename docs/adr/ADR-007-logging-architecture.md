# ADR-007: Logging Architecture

**Status:** Accepted  
**Date:** 2026-01-05  
**Deciders:** Development Team  
**Tags:** infrastructure, logging, observability

## Context

DotMatrix has grown from a simple CLI tool to a complex image processing pipeline with:
- GPU acceleration with fallback to CPU
- Multi-stage detection and rendering pipelines
- Performance-critical operations (CMYK cluster counting, circle detection)
- Debug output scattered across 20+ modules as ad-hoc `print()` statements

Without structured logging, it's difficult to:
- Debug issues in production
- Measure performance of specific operations
- Provide users with appropriate verbosity levels
- Track down bottlenecks in the pipeline

The edge detection feature (M2 milestone) requires performance metrics to validate <20% overhead and <10% false positive rate requirements. Current `print()` statements don't provide structured data for analysis.

## Decision

We will implement a centralized logging system using Python's built-in `logging` module with the following architecture:

### Core Components

1. **Logger Module** (`src/dotmatrix/logger.py`)
   - `setup_logging()`: Configures file and console handlers with rotation
   - `get_logger()`: Returns logger instances for modules
   - `JSONFormatter`: Structured JSON logging for metrics
   - `log_performance()`: Context manager for operation timing
   - `performance_timer()`: Decorator for automatic function timing

2. **Configuration**
   - File logging: `log/dotmatrix.log` with 10MB rotation, 5 backup files
   - Console logging: INFO level by default, DEBUG with `--verbose` flag
   - All file logs: DEBUG level always (for troubleshooting)
   - JSON format option for structured metric collection

3. **CLI Integration**
   - `--verbose` flag: Shows DEBUG logs on console
   - `--debug` flag: Enables debug mode (existing flag, enhanced with logging)
   - Logging initialized at CLI entry point before any operations

### Design Rationale

**Why Python's `logging` module over alternatives?**
- **Standard library**: No dependencies, proven, stable
- **Thread-safe**: Important for future async operations
- **Flexible**: Supports multiple handlers, formatters, levels
- **Performant**: Lazy evaluation of log messages
- **Familiar**: Every Python developer knows it

**Why not alternatives?**
- `loguru`: Adds dependency, not significantly better for our needs
- `structlog`: Overkill for current complexity, can add later if needed
- Custom solution: Reinventing the wheel, maintenance burden

**Why file AND console logging?**
- Console: User feedback, progress indicators (INFO+)
- File: Complete debug trail for troubleshooting (DEBUG always)
- Separation allows verbose debugging without overwhelming users

**Why JSON formatter?**
- Structured data for performance analysis
- Easy to parse for metrics collection
- Future-proof for log aggregation tools (ELK, Datadog, etc.)
- Can be enabled/disabled as needed

### Migration Strategy

1. **Phase 1**: Implement logger module with tests (TDD)
2. **Phase 2**: Add CLI flags and initialization
3. **Phase 3**: Replace `print()` statements in core modules:
   - `cluster_pixel_counter.py`: GPU operations, performance metrics
   - `circle_renderer.py`: Progress indicators
   - `cli.py`: Error messages, warnings
4. **Phase 4**: Leave intentional user output as print() (e.g., `print_gpu_status()`)

## Consequences

### Positive

- **Observability**: Can debug issues with complete log trails
- **Performance tracking**: Structured metrics for optimization
- **User control**: `--verbose` gives power users detailed output
- **Professional**: Production-grade logging for serious users
- **Future-proof**: Easy to add log aggregation, metrics collection

### Negative

- **Small overhead**: Logging adds ~1-2% performance cost (acceptable)
- **File I/O**: Log rotation may cause brief pauses (mitigated by buffering)
- **Migration effort**: Need to update all modules (one-time cost)

### Neutral

- **Log file management**: Users need to manage `log/` directory
  - Mitigated by: Rotation (keeps only 5 x 10MB = 50MB max)
- **Learning curve**: Users need to know `--verbose` flag
  - Mitigated by: Clear help text, documentation

## Performance Impact

Measured overhead of logging system:
- **Disabled logging** (CRITICAL level): <0.1% overhead
- **File logging only**: ~1% overhead  
- **File + console DEBUG**: ~2% overhead
- **JSON formatting**: ~2.5% overhead

All well within <5% target threshold.

## Examples

### Basic Usage
```python
from dotmatrix.logger import setup_logging, get_logger

# In CLI entry point
setup_logging(log_file="log/dotmatrix.log", verbose=args.verbose)

# In modules
logger = get_logger(__name__)
logger.info("Starting circle detection")
logger.debug(f"Image shape: {image.shape}")
```

### Performance Logging
```python
from dotmatrix.logger import log_performance

with log_performance("circle_detection"):
    circles = detect_circles(image)
    
# Outputs JSON: {"operation": "circle_detection", "duration_ms": 245.67}
```

### CLI Usage
```bash
# Normal operation
dotmatrix -i image.png

# Verbose debugging
dotmatrix -i image.png --verbose

# Debug mode with all output
dotmatrix -i image.png --debug
```

## References

- Python logging documentation: https://docs.python.org/3/library/logging.html
- Best practices: https://docs.python-guide.org/writing/logging/
- Performance benchmarks: tests/test_logger.py

## Related

- **Supersedes**: Ad-hoc print() statements across codebase
- **Enables**: M2 edge detection metrics (FPR, performance overhead)
- **Future work**: Log aggregation, metrics dashboard
