## Description

Initialize Python Project Structure with modern tooling and dependencies for DotMatrix circle detection CLI.

**Value**: Establishes the foundation for the entire DotMatrix project with proper package structure, dependency management, and development tooling. This enables all subsequent feature development.

**Target Users**: Developers working on DotMatrix

**Estimated Effort**: 1 hour

---

## Acceptance Criteria

- [ ] pyproject.toml configured with project metadata and dependencies
- [ ] Package structure created (src/dotmatrix/)
- [ ] pip install -e . runs successfully in editable mode
- [ ] dotmatrix --help displays usage information
- [ ] Dependencies installed: click, opencv-python, numpy, pillow, pytest

---

## Implementation Plan

### Overview

Set up a modern Python package using pyproject.toml with src layout, configure CLI entry point with Click, and install computer vision dependencies.

### Implementation Steps

1. **Create package structure**:
   - Create src/dotmatrix/ directory
   - Create __init__.py and __main__.py
   - Create cli.py for Click CLI entry point

2. **Configure pyproject.toml**:
   - Set project metadata (name, version, description)
   - Define dependencies: click>=8.0, opencv-python>=4.8, numpy>=1.24, pillow>=10.0
   - Define dev dependencies: pytest>=7.0, pytest-cov
   - Configure entry point: dotmatrix = dotmatrix.cli:main

3. **Create basic CLI structure**:
   - Implement main() function with Click
   - Add --help documentation
   - Add --version flag

### Dependencies

- **Library Dependencies**: click, opencv-python, numpy, pillow, pytest

---

## Testing Strategy

### Unit Tests

- [ ] Test package imports successfully
- [ ] Test CLI entry point is accessible
- [ ] Test --help flag displays usage

---

## Documentation Updates

- [ ] Create README.md with installation instructions
- [ ] Add development setup instructions