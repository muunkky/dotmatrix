# ADR-002: CLI UX Refactoring for MECE Commands

**Status:** Accepted
**Date:** 2025-11-26
**Deciders:** Cameron

## Context

The DotMatrix CLI had grown organically to 30+ flags at root level, creating usability problems:
- Overwhelming `--help` output
- No guidance for common workflows (halftone vs simple circles)
- Unclear when to use `--convex-edge` vs `--color-separation` vs standard detection
- `--extract` default behavior was confusing

## Decision Drivers

- **Discoverability**: Users should find relevant options quickly
- **Progressive disclosure**: Hide complexity until needed
- **Industry patterns**: Follow established CLI conventions (ruff, docker, gh, git)
- **Backward compatibility**: Existing scripts should continue to work

## Research: Industry CLI Patterns

### Click Best Practices
- Use `click-option-group` for visual grouping in help output
- Group related options under semantic headers
- Keep core options (input, output, format) at top level
- Use presets/modes for common configurations

### Similar Tools Reviewed

**ruff**: Clear verb commands (`ruff check` vs `ruff format`), sensible defaults
**docker**: Grouped subcommands, common options propagate
**gh (GitHub CLI)**: Context-aware defaults, helpful error messages with suggestions
**ffmpeg**: Preset system for common configurations (`-preset fast`)
**ImageMagick**: Operation chaining, verbose help with examples

### Key Patterns Identified

1. **Mode presets** reduce cognitive load (ffmpeg's `-preset`)
2. **Option groups** organize help output (Click's `optgroup`)
3. **Examples in help** show common workflows
4. **Sensible defaults** make simple cases simple

## Decisions Made

### 1. Default Behavior: Detection + JSON Output

**Decision:** `dotmatrix -i image.png` outputs JSON to stdout by default (no extraction)

**Rationale:**
- Most CLI tools output data, not files, by default
- Users expect `command input` → `stdout` pattern
- Extraction is an explicit action (`-e output/`)
- Aligns with Unix philosophy (composable, pipeable)

**Alternatives Considered:**
- Keep extraction default: Rejected - confusing for new users
- Add `--data-only` flag: Rejected - inverts expected behavior

### 2. Mode Presets

**Decision:** Add `--mode [standard|halftone|cmyk-sep]` preset option

**Rationale:**
- Users shouldn't need to know `--convex-edge --palette cmyk --sensitive-occlusion --morph-enhance`
- Presets encapsulate expert knowledge
- Individual flags still work for fine-tuning

**Mode Mappings:**
| Mode | convex_edge | palette | sensitive_occlusion | morph_enhance |
|------|-------------|---------|---------------------|---------------|
| standard | false | cmyk | false | false |
| halftone | true | cmyk | true | true |
| cmyk-sep | true | cmyk-sep | true | true |

### 3. Option Groups

**Decision:** Organize 30+ options into 7 semantic groups using `click-option-group`

**Groups:**
1. **Core** (always visible): `-i`, `-o`, `-f`, `--debug`, `--mode`, `-c`
2. **Detection Options**: radius, distance, sensitivity, confidence
3. **Detection Methods**: convex-edge, color-separation, histogram, occlusion, morph
4. **Color Options**: palette, num-colors, tolerance, max-colors, exclude-background
5. **Edge Sampling**: enabled, samples, method
6. **Output Options**: extract, run-name, organize, manifest, quantize, save-config
7. **Performance**: chunk-size
8. **Calibration**: auto-calibrate, calibrate-from

**Rationale:**
- Progressive disclosure - users see relevant groups
- Help output is scannable
- Related options are co-located

### 4. Parameter Object (DetectionConfig)

**Decision:** Create `DetectionConfig` dataclass consolidating all parameters

**Structure:**
```python
@dataclass
class DetectionConfig:
    input_path: Optional[Path]
    config_file: Optional[Path]
    mode: Optional[Literal['standard', 'halftone', 'cmyk-sep']]
    debug: bool
    detection: DetectionParams      # min/max radius, distance, sensitivity
    methods: DetectionMethodParams  # convex_edge, color_separation, etc.
    color: ColorParams              # palette, tolerance, etc.
    edge_sampling: EdgeSamplingParams
    output: OutputParams
    performance: PerformanceParams
    calibration: CalibrationParams
```

**Rationale:**
- Replaces 34 function parameters with single config object
- Type-safe with dataclass validation
- Serializable for config files
- Factory method `from_cli_args()` bridges CLI to config

## Consequences

### Positive
- Help output is now organized and scannable
- Common workflows accessible via `--mode`
- New options fit naturally into existing groups
- Config dataclass enables future config file improvements

### Negative
- Additional dependency (`click-option-group`)
- Slight increase in code complexity for option handling

### Neutral
- Backward compatible - all existing flags still work
- No breaking changes to output format

## Implementation

- `cli.py`: Refactored with `@optgroup` decorators, `_apply_mode_presets()` helper
- `config.py`: New module with `DetectionConfig` and sub-dataclasses
- `tests/test_cli_presets.py`: 10 tests for mode presets
- `tests/test_config.py`: 15 tests for config dataclasses

## References

- [Click Option Groups](https://click-option-group.readthedocs.io/)
- [CLI Guidelines](https://clig.dev/)
- Card: lc3xu5 "Refactor CLI for MECE Commands"
