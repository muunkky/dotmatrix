## Description

Automatically generate a manifest file in each run directory that records what settings produced the output.

When users have many run directories, they need to know what settings and source file produced each result. A manifest file provides this traceability.

**Value**: Users can always trace back from output to the exact settings and source file that created it.

**Target Users**: Anyone managing multiple experiment runs

---

## Acceptance Criteria

- [x] Each run directory contains `manifest.json` with run metadata
- [x] Manifest includes: timestamp, source file path, all CLI settings, output file list
- [x] Manifest includes dotmatrix version for reproducibility
- [x] Manifest includes detection results summary (circle count per color)
- [x] Manifest is auto-generated when `--extract` creates output
- [x] `--no-manifest` flag disables manifest generation

---

## Implementation Plan

### Overview

After successful extraction, write a manifest.json file to the run directory containing all metadata needed to understand and reproduce the run.

### Implementation Steps

1. **Define manifest schema**:
   ```python
   manifest = {
       "dotmatrix_version": __version__,
       "timestamp": "2025-11-25T14:30:22",
       "source_file": "test_dotmatrix.png",
       "source_file_hash": "sha256:abc123...",  # For verification
       "settings": {
           "convex_edge": True,
           "palette": "cmyk",
           "min_radius": 80,
           # ... all settings
       },
       "results": {
           "total_circles": 16,
           "circles_by_color": {
               "black": 4,
               "cyan": 4,
               "magenta": 4,
               "yellow": 4
           }
       },
       "output_files": [
           "circles_color_000_000_000.png",
           "circles_color_118_193_241.png",
           # ...
       ]
   }
   ```

2. **Create manifest generator in cli.py**:
   - Collect all settings after config merge
   - Hash source file for integrity verification
   - Count results by color
   - List generated output files

3. **Write manifest after extraction**:
   - Write to `{run_dir}/manifest.json`
   - Pretty-print with indent for readability

4. **Add `--no-manifest` flag** to skip generation

---

## Testing Strategy

### Unit Tests

- [x] Test manifest contains all required fields
- [x] Test source file hash is computed correctly
- [x] Test results summary is accurate
- [x] Test output file list is complete

### Integration Tests

- [x] Test extraction creates manifest.json
- [x] Test `--no-manifest` skips generation
- [x] Test manifest is valid JSON
