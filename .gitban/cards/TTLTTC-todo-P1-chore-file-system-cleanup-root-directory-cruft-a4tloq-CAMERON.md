## Purpose

Remove temp files, scripts, and folders from root directory that accumulated during development. These are LLM-generated cruft, test outputs, and malformed paths that clutter the project.

**Value**: Clean professional project structure. Clear root directory with only standard files (pyproject.toml, README.md, CHANGELOG.md, etc.). Prevents confusion for next developers.

**Estimated Effort**: 15 minutes

---

## Project Location

**Path**: `c:\Users\Cameron\Projects\dotmatrix\`

### Files/Modules Affected

**Temp Scripts (DELETE):**
- `analyze_blanks.py`
- `demo_create_test_image.py`
- `test_color_separation.py`
- `test_hybrid_approach.py`

**Shell Scripts (DELETE):**
- `demo_edge_methods_comparison.sh`
- `extract_cmyk.ps1`
- `extract_cmyk.sh`
- `test_config.sh`
- `test_detection_params.sh`

**Test Images (DELETE):**
- `demo_circles.png`
- `test_dotmatrix.bmp`
- `test_dotmatrix.png`

**Malformed Paths (DELETE):**
- `=1.3.0` (invalid file/folder)
- `--format=json/` (LLM command parsing error)

**Temp Folders (DELETE):**
- `output_test/`
- `output_test2/`
- `output_test3/`
- `output_test_cell/`
- `demo_output/`

**Keep for Review:**
- `demo_results/` - may contain valuable examples
- `OPTIMAL_USAGE.md` - may be useful documentation

---

## Tasks

- [ ] **Delete temp Python scripts**: Remove 4 `.py` files from root
  - `Remove-Item analyze_blanks.py, demo_create_test_image.py, test_color_separation.py, test_hybrid_approach.py`

- [ ] **Delete shell scripts**: Remove 5 `.sh` and `.ps1` files
  - `Remove-Item demo_edge_methods_comparison.sh, extract_cmyk.ps1, extract_cmyk.sh, test_config.sh, test_detection_params.sh`

- [ ] **Delete test images**: Remove 3 image files
  - `Remove-Item demo_circles.png, test_dotmatrix.bmp, test_dotmatrix.png`

- [ ] **Delete malformed paths**: Remove invalid entries
  - `Remove-Item "=1.3.0" -Force -Recurse`
  - `Remove-Item "--format=json" -Force -Recurse`

- [ ] **Delete temp output folders**: Remove 5 output directories
  - `Remove-Item output_test, output_test2, output_test3, output_test_cell, demo_output -Recurse -Force`

- [ ] **Review demo_results**: Decide keep or clean
  - Check if any subfolders contain valuable examples
  - If keeping, document why in notes

- [ ] **Review OPTIMAL_USAGE.md**: Decide keep or integrate into README
  - If valuable, move to docs/ folder
  - If redundant, delete

### Task Dependencies

1. Malformed path deletion may require special handling
2. demo_results review before bulk delete decision

---

## Outputs

### Files Created/Updated

1. **Clean root directory**: Only standard project files remain
2. **Potentially moved**: OPTIMAL_USAGE.md to docs/ if valuable

---

## Success Criteria

- [ ] All temp Python scripts deleted (4 files)
- [ ] All shell scripts deleted (5 files)
- [ ] All test images deleted (3 files)
- [ ] Malformed paths deleted (2 items)
- [ ] Temp output folders deleted (5 folders)
- [ ] Root directory contains only standard files

**Quality Gates:**
- [ ] No deletion of important files (pyproject.toml, README.md, etc.)
- [ ] .gitban/ folder preserved
- [ ] src/, tests/, docs/ folders preserved

---

## Acceptance Criteria

- [ ] Root directory has <15 items (down from 30+)
- [ ] No temp/test files remain in root
- [ ] No malformed paths remain
- [ ] No temp output folders remain
- [ ] Project still builds and runs correctly

---

## Test Plan

- [ ] Run `Get-ChildItem .` to verify clean root directory
- [ ] Run `python -m dotmatrix --help` to verify CLI works
- [ ] Run `git status` to see uncommitted deletions
- [ ] Verify expected files still exist (pyproject.toml, README.md, etc.)