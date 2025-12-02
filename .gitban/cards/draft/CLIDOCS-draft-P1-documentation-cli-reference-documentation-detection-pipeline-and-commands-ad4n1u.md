# CLI Reference Documentation - Detection Pipeline and Commands

## Location

**File Path**: `docs/cli-reference.md`

**Related Files**:
- `src/dotmatrix/cli.py`: CLI implementation (source of truth for options)
- `src/dotmatrix/convex_detector.py`: Convex edge detection algorithm
- `src/dotmatrix/circle_detector.py`: Standard Hough detection
- `README.md`: High-level overview (cross-reference)
- `OPTIMAL_USAGE.md`: Existing usage guide (superseded or linked)

---

## Documentation Goal

Create comprehensive CLI reference documentation that exhaustively documents the detection pipeline sequence from command invocation to completion, including all CLI options, flags, their interactions, and impacts on detection quality and performance.

**Purpose**: Technical reference for CLI users and developers

**Problem Being Solved**: The dotmatrix CLI has grown complex with multiple detection modes (standard Hough, convex edge), palettes (RGB, CMYK, custom), calibration, large file handling, and output organization. No comprehensive reference documents the full command-to-completion flow.

**Value**: 
- Users can understand exactly what happens when they run a command
- Developers can debug detection issues by understanding the pipeline
- The "why" behind flag combinations is documented (e.g., why `--convex-edge` with `--palette cmyk`)

**Estimated Effort**: 4-6 hours

---

## Audience

**Primary Audience**: CLI users (developers, data scientists, print technicians)

### Audience Characteristics

- **Role**: Technical user processing halftone/dot images
- **Experience Level**: Intermediate (comfortable with CLI tools)
- **Goals**: Extract circle data accurately and efficiently
- **Context**: Running from terminal, possibly in automation pipelines
- **Prerequisites**: Basic command line familiarity, understanding of image processing concepts

### User Scenarios

1. **CMYK Halftone Processing**: User has a print proof and needs to extract CMYK dot positions
   - Needs: Understanding of `--convex-edge --palette cmyk` workflow
   - Success: Can run full detection and understand output structure

2. **Large File Processing**: User has 30+ MP image
   - Needs: Understanding of `--chunk-size` and memory considerations  
   - Success: Can process large images without memory errors

3. **Debugging Detection**: User gets poor results, needs to tune parameters
   - Needs: Understanding of radius, palette, and mode interactions
   - Success: Can diagnose and fix detection quality issues

---

## Scope

- [x] **Detection Pipeline Sequence**: Full flow from command to completion
- [x] **All CLI Commands**: detect, calibrate, runs, config
- [x] **All Options/Flags**: Exhaustive documentation with defaults, types, interactions
- [x] **Example Commands**: Real-world usage patterns with explanations
- [x] **Output Structure**: Run directories, manifest, results.json format

### In Scope

- Complete CLI reference for all commands and options
- Detection pipeline architecture explanation
- Flag interaction documentation (e.g., `--convex-edge` requires `--palette`)
- Performance considerations for large files
- Output format specifications

### Out of Scope

- Algorithm implementation details (covered in ADRs)
- API/programmatic usage (separate doc)
- Contributing guide (separate doc)

---

## Documentation Type (Diátaxis)

### Primary Type

- [x] **Reference** (information-oriented)
  - **Goal**: Comprehensive technical description of CLI
  - **Structure**: Structured by command, then by option
  - **Tone**: Neutral, precise, technical

### Supporting Types

- [x] **How-To Guide**: Detection pipeline flow section

---

## Acceptance Criteria

### Content Completeness

- [ ] Detection pipeline sequence documented (image load → palette → detection → dedup → output)
- [ ] All CLI commands documented (detect, calibrate, runs list/show/compare, config)
- [ ] All detect command flags documented with type, default, description
- [ ] Flag interactions documented (e.g., --convex-edge enables --palette requirement)
- [ ] Output structure documented (run directories, manifest.json, results.json)
- [ ] Example commands for common workflows

### Technical Accuracy

- [ ] All default values verified against cli.py
- [ ] All flag names match implementation exactly
- [ ] Example commands tested and working
- [ ] Output format matches actual tool output

### Quality Standards

- [ ] Consistent formatting for option documentation
- [ ] Clear section hierarchy
- [ ] Cross-references to related documentation

---

## Deliverables

### Primary Deliverable

- **File**: `docs/cli-reference.md`
- **Format**: Markdown
- **Length**: ~2000-3000 words

### Supporting Deliverables

- [ ] Update README.md with link to CLI reference
- [ ] Update OPTIMAL_USAGE.md cross-references

---

## Detection Pipeline Overview (Draft Content)

When you run:
```bash
python -m dotmatrix -i "inputs/corner_test.png" --convex-edge --palette cmyk --min-radius 15 --max-radius 50
```

The following sequence executes:

1. **Image Loading** (`image_loader.py`)
   - Load image from path
   - Validate format (PNG, JPG, TIFF supported)
   - Convert to RGB if necessary

2. **Palette Setup** (`convex_detector.py:parse_palette`)
   - Parse `--palette cmyk` → [(0,255,255), (255,0,255), (255,255,0), (0,0,0)]
   - Custom palettes parsed as comma-separated RGB values

3. **Per-Color Detection Loop**
   - For each color in palette:
     a. **Color Filtering**: Create binary mask of pixels matching color
     b. **Connected Components**: Find discrete blobs
     c. **Convex Edge Analysis**: Filter points to convex hull edges
     d. **HoughCircles Fitting**: Fit circles to filtered edge points
     e. **Fallback Detection**: If Hough fails, use centroid + area-derived radius
     f. **Deduplication**: Remove overlapping detections (KD-tree spatial indexing)

4. **Output Generation** (`run_manager.py`, `image_extractor.py`)
   - Create timestamped run directory
   - Generate per-color layer PNGs
   - Generate composite.png and diff.png
   - Write manifest.json with settings
   - Write results.json with circle data

---

## Notes

### Writing Guidelines

- Use consistent option formatting: `--option-name` (TYPE, default: VALUE)
- Group related options together
- Include "Why use this?" context for non-obvious options

