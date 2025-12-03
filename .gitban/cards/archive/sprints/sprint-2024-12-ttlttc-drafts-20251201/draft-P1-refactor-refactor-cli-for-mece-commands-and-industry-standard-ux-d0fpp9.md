## Refactoring Goal

CLI interface (`src/dotmatrix/cli.py`) - comprehensive UX overhaul

The current CLI has grown organically with 30+ flags, unclear defaults, and non-intuitive behavior patterns. This refactoring will create MECE (Mutually Exclusive, Collectively Exhaustive) command groups with intuitive defaults that follow industry CLI norms for discoverability.

**Value**: Better developer experience, reduced learning curve, more intuitive behavior for common workflows

**Complexity**: Medium - behavior changes need backward compatibility consideration

**Estimated Effort**: 2-3 sessions

---

## Current State

The CLI has accumulated options without a cohesive design philosophy, resulting in:
- 30+ options at the root level (overwhelming `--help` output)
- Inconsistent defaults (e.g., `--extract` defaults to 'output' but always runs extraction)
- Inverted flag logic questions (should `--extract` be opt-in or should `--data-only` be opt-out?)
- Detection mode sprawl (`--convex-edge`, `--color-separation`, `--use-histogram`)
- Help text that doesn't guide users to common workflows

### Code Location

**Path**: `src/dotmatrix/cli.py`

**Modules Affected**:
- `cli.py`: Main CLI definition (955 lines)
- `runs.py`: Subcommand for run management
- `config_loader.py`: Config file handling

### Problems with Current Code

1. **Option Overload**: 30+ flags at root level
   - **Impact**: `dotmatrix --help` is overwhelming, hard to find what you need
   - **Example**: Users must scroll through radius, color, sampling, calibration, chunking, output options

2. **Inverted Default Logic**: `--extract` defaults to 'output' but extraction always happens
   - **Impact**: Confusing - users expect "detect circles, output JSON" as default, not "extract images"
   - **Example**: User wants JSON output only, has to figure out how to disable extraction

3. **Detection Mode Sprawl**: Multiple exclusive detection approaches aren't grouped
   - **Impact**: Hard to understand when to use `--convex-edge` vs `--color-separation` vs standard
   - **Example**: `--convex-edge --palette cmyk-sep` vs `--convex-edge --palette cmyk` vs `--color-separation`

4. **Help Text Gap**: No workflow guidance in help
   - **Impact**: Users don't know what options to use for their use case (halftone vs simple circles)
   - **Example**: Help shows flags but not "for halftone images, use --convex-edge --palette cmyk-sep"

### Technical Debt

- **Code Smells**: Long function (_do_detect is 550+ lines), flag sprawl
- **Design Issues**: Missing command grouping, unclear defaults philosophy
- **Maintainability Issues**: Hard to add new features without adding more flags

### Metrics (Current)

- **CLI Options**: 30+ at root level
- **Main Function Length**: ~550 lines (_do_detect)
- **Help Readability**: Low (wall of options)

---

## Desired State

A CLI with MECE command structure, sensible defaults for common workflows, and industry-standard discoverability patterns.

### Target Architecture

```
dotmatrix [input] [options]                    # Default: detect + JSON output
dotmatrix detect [input] [options]             # Explicit detect command
dotmatrix extract [input] [options]            # Extract images (current --extract behavior)
dotmatrix runs list|show|replay                # Run management (existing)

Global options: -i/--input, -o/--output, -f/--format, --debug, -c/--config
Detection presets: --mode [standard|halftone|cmyk-sep]
```

### Design Improvements

1. **Invert Default Behavior**: Default to detection + data output
   - **New Structure**: `dotmatrix -i img.png` outputs JSON by default
   - **Benefit**: Most intuitive first experience - "detect circles, give me data"

2. **Add Presets/Modes**: High-level detection mode selection
   - **New Structure**: `--mode halftone` sets appropriate flags automatically
   - **Benefit**: Users don't need to know implementation details

3. **Group Advanced Options**: Hide complexity behind groups
   - **New Structure**: Detection options, Color options, Output options, Performance options
   - **Benefit**: Cleaner `--help` output, progressive disclosure

4. **Better Help Structure**: Workflow-oriented help
   - **New Structure**: Examples section, "For halftone images..." guidance
   - **Benefit**: Users can self-serve common use cases

### Target Metrics

- **CLI Options at Root**: ~10 (core options) + grouped advanced options
- **Main Function Length**: <200 lines (extract logic to functions)
- **Help Readability**: High (grouped options with examples)

---

## Benefits

### Code Quality Benefits

- **Readability**: Shorter functions, clearer option grouping
- **Maintainability**: New features fit into existing option groups
- **Testability**: Smaller functions are easier to test

### Engineering Benefits

- **Velocity**: Easier to add new detection modes or options
- **Onboarding**: New users understand CLI faster
- **Documentation**: Code structure matches mental model

### Business Benefits

- **Feature Velocity**: Less time explaining CLI to users
- **Quality**: Fewer "wrong options" support issues
- **Risk**: Reduced chance of breaking changes from flag accumulation

### Measurable Improvements

- **Before → After**:
  - Root options: 30+ → ~10 visible + grouped advanced
  - _do_detect length: 550 lines → <200 lines
  - Help sections: 1 (flat list) → 4 (grouped)

---

## Refactoring Steps

### Phase 1: Research & Design

1. **Review Industry CLI Patterns**:
   - [ ] Study Click best practices for option grouping
   - [ ] Review similar tools (ImageMagick, ffmpeg, ruff) for UX patterns
   - [ ] Document findings in ADR

2. **Design Decision: Default Behavior**:
   - [ ] Decide: Should detection + JSON be default, or detection + extraction?
   - [ ] User research: What do users expect from `dotmatrix -i image.png`?
   - [ ] Document decision rationale

### Phase 2: Incremental Refactoring

3. **Extract _do_detect into smaller functions**:
   - [ ] Create `_setup_detection()` for detection mode selection
   - [ ] Create `_run_detection()` for actual detection
   - [ ] Create `_handle_output()` for output/extraction logic
   - [ ] Run tests after each extraction

4. **Add --mode preset option**:
   - [ ] Implement `--mode standard|halftone|cmyk-sep` preset
   - [ ] Map presets to existing flag combinations
   - [ ] Add deprecation warning for replaced flags (optional)
   - [ ] Run tests

5. **Restructure help output**:
   - [ ] Group options using Click option groups
   - [ ] Add examples section to help
   - [ ] Add "For X use case..." guidance
   - [ ] Run tests

6. **Review and adjust defaults**:
   - [ ] Evaluate `--extract` default behavior
   - [ ] Consider `--data-only` vs `--extract` semantics
   - [ ] Ensure backward compatibility or document breaking changes

### Phase 3: Validation

7. **Final Validation**:
   - [ ] All tests pass
   - [ ] Manual testing of common workflows
   - [ ] Help output review
   - [ ] Backward compatibility verified

### Refactoring Techniques

- [ ] **Extract Method**: _do_detect split into setup/run/output
- [ ] **Introduce Parameter Object**: Detection config dataclass
- [ ] **Replace Conditional with Polymorphism**: Detection mode strategies (optional)

---

## Testing Strategy

### Pre-Refactoring Testing

- [ ] **Capture Current Behavior**:
  - [ ] All existing tests pass
  - [ ] Document current default behavior
  - [ ] Capture example outputs for comparison

### During Refactoring

- [ ] **Test After Each Step**:
  - [ ] Run full test suite after each commit
  - [ ] No test should fail due to refactoring
  - [ ] Add new tests for preset modes

### Post-Refactoring Validation

- [ ] **Comprehensive Verification**:
  - [ ] All tests still pass
  - [ ] Manual testing of:
    - `dotmatrix -i img.png` (default behavior)
    - `dotmatrix -i img.png --mode halftone`
    - `dotmatrix -i img.png --mode cmyk-sep`
    - `dotmatrix extract -i img.png`
  - [ ] Help output is readable and helpful

---

## Key Design Questions to Resolve

Before implementation, these questions need answers:

1. **Default Output Behavior**:
   - Current: Always extracts images to output/
   - Option A: Default to JSON only, use `dotmatrix extract` for images
   - Option B: Keep current, add `--data-only` to skip extraction
   - **Recommendation**: Option A (data-first is more intuitive for CLI tools)

2. **Backward Compatibility**:
   - Should old flag combinations still work?
   - Deprecation warnings vs breaking change?
   - **Recommendation**: Deprecation warnings for 1-2 versions

3. **Preset vs Fine-Grained Control**:
   - Should presets replace detailed flags or complement them?
   - **Recommendation**: Complement - presets set defaults, flags override

---

## Notes

### Industry CLI Patterns

Good CLI patterns to emulate:
- **ruff**: `ruff check` vs `ruff format` - clear verb commands
- **docker**: Grouped subcommands with common options
- **gh**: Context-aware defaults, helpful error messages
- **git**: Porcelain (user) vs plumbing (script) commands

### References

- Click documentation on option groups
- CLI Guidelines: https://clig.dev/
