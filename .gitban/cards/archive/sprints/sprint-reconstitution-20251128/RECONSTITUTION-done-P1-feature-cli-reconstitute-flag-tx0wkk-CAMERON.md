## Description

**CLI --reconstitute Flag** - Add command-line option to generate reconstituted cluster images.

Integrates the bullseye renderer with the existing CLI workflow. When `--reconstitute` is specified (in CMYK mode), generates a `reconstituted.png` showing all clusters rendered as bullseye patterns.

**Value**: Enables users to generate reconstituted images from the command line, integrating with existing run directory and manifest workflow.

**Target Users**: CLI users running CMYK detection who want visual cluster output

**Estimated Effort**: 2-4 hours

---

## Acceptance Criteria

- [x] `--reconstitute` flag added to Output Options group
- [x] Requires CMYK mode (like `--cluster-count`)
- [x] Generates `reconstituted.png` in run directory
- [x] Added to manifest.json output_files
- [x] Works with or without `--cluster-count` flag
- [x] Outputs message: "Generated reconstituted.png"
- [x] Error message if used without CMYK palette

---

## Implementation Plan

### Overview

Add `--reconstitute` flag to cli.py, call the renderer after cluster counting, save output to run directory alongside composite.png.

### Implementation Steps

1. **Add CLI option**
   - Add to Output Options group (near `--no-composite`)
   - `--reconstitute` is_flag=True
   - Help: "Generate reconstituted cluster image (CMYK mode only)"

2. **Validate requires CMYK**
   - Check palette is cmyk or cmyk-sep
   - Error if not CMYK mode

3. **Integrate with detection flow**
   - After cluster counting, call `render_bullseye()`
   - Save to `reconstituted.png` in run directory
   - Add to output_files list for manifest

4. **Add integration tests**
   - Test flag produces output file
   - Test requires CMYK validation
   - Test manifest includes file

### Technical Considerations

- **Architecture**: Follows same pattern as composite.png generation
- **Backwards Compatibility**: Flag is optional, no breaking changes

### Dependencies

- **Depends on**: Bullseye Cluster Renderer (qm8cnj)

---

## Testing Strategy

### Unit Tests

- [x] Test CLI parses --reconstitute flag
- [x] Test validation error for non-CMYK

### Integration Tests

- [x] Test reconstituted.png created in run directory
- [x] Test file is valid PNG image
- [x] Test manifest includes reconstituted.png
- [x] Test works alongside composite.png and diff.png

---

## Related Cards

### Dependencies

**Depends on**: qm8cnj - Bullseye Cluster Renderer (must complete first)
