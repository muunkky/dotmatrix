## Description

Add automatic output directory organization with timestamped and named runs.

Currently, `--extract output/` overwrites previous outputs. Users running many experiments need organized output structure to track different runs with different settings and source files.

**Value**: Users can run many experiments without losing previous results, and easily find specific runs later.

**Target Users**: Anyone running dotmatrix multiple times with different settings/images

---

## Acceptance Criteria

- [x] `--extract` creates timestamped subdirectory by default (e.g., `output/run_20251125_143022/`)
- [x] `--run-name` flag allows custom naming (e.g., `output/my-experiment/`)
- [x] Each run directory contains all output files for that run
- [x] Existing `--extract dir/` behavior preserved with `--no-organize` flag
- [x] Output shows path to created directory
- [x] Directory names are filesystem-safe (no special characters)

---

## Implementation Plan

### Overview

Modify the `--extract` behavior to create organized subdirectories by default, with options for custom naming or flat output.

### Implementation Steps

1. **Add CLI flags**:
   - `--run-name NAME` - Custom name for this run
   - `--no-organize` - Disable subdirectory creation (flat output)

2. **Create run directory logic**:
   ```python
   def create_run_directory(base_dir, run_name=None):
       if run_name:
           subdir = sanitize_filename(run_name)
       else:
           subdir = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
       run_dir = base_dir / subdir
       run_dir.mkdir(parents=True, exist_ok=True)
       return run_dir
   ```

3. **Update extract logic in cli.py**:
   - Create run directory before extraction
   - Pass run directory to `extract_circles_to_images()`
   - Display created directory path to user

4. **Add filename sanitization utility**:
   - Replace spaces with underscores
   - Remove special characters
   - Truncate long names

---

## Testing Strategy

### Unit Tests

- [x] Test timestamped directory naming format
- [x] Test custom run name sanitization
- [x] Test directory creation with parents
- [x] Test `--no-organize` preserves flat behavior

### Integration Tests

- [x] Test full extraction creates organized directory
- [x] Test multiple runs create separate directories
- [x] Test custom `--run-name` creates expected directory
