## Refactoring Goal

Output directory organization (`src/dotmatrix/run_manager.py`, `cli.py`) - user experience overhaul

The current extraction output scatters files into color-named subdirectories without bundling related artifacts together. This refactoring creates a run-centric organization where all outputs from a single detection are bundled together with the input file for reproducibility.

**Value**: Better UX - users can find all related outputs in one place, reproduce runs, and understand what settings produced what results

**Complexity**: Medium - affects CLI defaults, output logic, and existing tests

**Estimated Effort**: 1-2 sessions

---

## Current State

Files are organized by color, with no input file copy and scattered data.

### Code Location

**Path**: `src/dotmatrix/run_manager.py`, `src/dotmatrix/cli.py`

**Modules Affected**:
- `run_manager.py`: Creates run directories, handles file organization
- `cli.py`: Handles `--extract` flag and output paths
- `image_extractor.py`: Extracts individual circle images by color

### Problems with Current Code

1. **No Default Output Directory**:
   - **Impact**: User must always specify `-e output/` explicitly
   - **Example**: `dotmatrix -i img.png` outputs JSON to stdout but no files

2. **Color-Centric Organization**:
   - **Impact**: Layer files scattered in `cyan/`, `magenta/` subdirs instead of unified
   - **Example**: `output/cyan/circle_001.png` instead of `output/run-xxx/cyan.png`

3. **Missing Input File Copy**:
   - **Impact**: Can't reproduce run without finding original input
   - **Example**: No way to know what input produced a given output

4. **Unclear Run Bundling**:
   - **Impact**: Data file (manifest.json) not co-located with extracted images
   - **Example**: Hard to correlate detection results with visual outputs

### Technical Debt

- **Design Issues**: Output logic scattered across cli.py and run_manager.py
- **Maintainability Issues**: Adding new output types requires touching multiple files

---

## Desired State

All outputs bundled per-run in a consistent directory structure.

### Target Architecture

```
output/                           # Default output root
└── run-2024-11-26-143022/       # Run bundle (timestamped or named)
    ├── input.png                 # Copy of original input
    ├── manifest.json             # Detection data + settings
    ├── cyan.png                  # Cyan layer (if CMYK mode)
    ├── magenta.png               # Magenta layer
    ├── yellow.png                # Yellow layer
    └── black.png                 # Black (key) layer
```

### Design Improvements

1. **Default Output Directory**:
   - **New Structure**: `output/` is default when extracting
   - **Benefit**: Users don't need to specify `-e` path

2. **Run-Bundled Organization**:
   - **New Structure**: Each run creates a timestamped subdirectory
   - **Benefit**: All artifacts in one place, easy to share/archive

3. **Input File Copy**:
   - **New Structure**: Copy input file to run directory
   - **Benefit**: Reproducibility - run is self-contained

4. **Layer Files Instead of Circle Files**:
   - **New Structure**: Generate composite layer images per color
   - **Benefit**: Useful for printing/separation workflows

---

## Benefits

### Code Quality Benefits

- **Readability**: Output logic consolidated in run_manager.py
- **Maintainability**: Single place to add new output artifacts
- **Testability**: Can test complete run bundles

### Engineering Benefits

- **Velocity**: Adding new output types is straightforward
- **Reliability**: Self-contained runs are reproducible
- **Onboarding**: Output structure is intuitive

### Business Benefits

- **Feature Velocity**: Easier to add export formats
- **Quality**: Users can verify and share complete runs
- **Risk**: Reduced support for "where are my files?" questions

---

## Refactoring Steps

### Phase 1: Preparation

1. **Establish Safety Net**:
   - [x] Review existing tests for run_manager.py
   - [x] Review existing tests for output organization
   - [x] Document current behavior

2. **Create Branch & Baseline**:
   - [x] Create feature branch
   - [x] Document current output structure

### Phase 2: Incremental Refactoring

3. **Update Default Output Directory**:
   - [x] Make `output/` the default when `-e` is used without path
   - [x] Run tests

4. **Implement Run-Bundled Structure**:
   - [x] Update run_manager.py to create run directories
   - [x] Move manifest.json into run directory
   - [x] Run tests

5. **Add Input File Copy**:
   - [x] Copy input file to run directory on extraction
   - [x] Run tests

6. **Implement Layer File Generation**:
   - [x] Create composite layer images per CMYK color
   - [x] Write layer files to run directory
   - [x] Run tests

7. **Update CLI Help and Defaults**:
   - [x] Update --extract help text
   - [x] Update examples in CLI help
   - [x] Run tests

### Phase 3: Validation

8. **Final Validation**:
   - [x] All tests pass
   - [x] Manual testing of `dotmatrix -i img.png -e`
   - [x] Manual testing of `dotmatrix -i img.png -m cmyk-sep -e`
   - [x] Verify run directory structure

### Refactoring Techniques

- [x] **Extract Method**: Layer generation logic
- [x] **Consolidate**: Output path handling in run_manager.py

---

## Testing Strategy

### Pre-Refactoring Testing

- [x] All existing tests pass
- [x] Document current output structure with examples

### During Refactoring

- [x] Run test suite after each step
- [x] Add tests for new run bundle structure
- [x] Add tests for input file copy
- [x] Add tests for layer file generation

### Post-Refactoring Validation

- [x] All tests pass
- [x] Manual verification of output structure
- [x] Verify backward compatibility (old workflows still work)

---

## Notes

### CLI Changes

**Before:**
```bash
dotmatrix -i image.png -e output/  # Required explicit path
# Creates: output/cyan/circle_001.png, output/magenta/circle_002.png...
```

**After:**
```bash
dotmatrix -i image.png -e          # Uses default output/
# Creates: output/run-xxx/input.png, output/run-xxx/cyan.png...
```

### Backward Compatibility

- Existing `-e path/` syntax continues to work
- New `-e` without path uses `output/` default
- `--no-organize` flag preserved for flat output
