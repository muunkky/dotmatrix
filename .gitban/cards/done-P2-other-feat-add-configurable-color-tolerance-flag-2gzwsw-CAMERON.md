## Description

Add `--color-tolerance N` CLI flag to adjust RGB distance threshold for color grouping during PNG extraction. Allows users to control how similar colors must be to group together.

**Value**: Fine-grained control over color grouping for different use cases.

**Target Users**: Users needing precise or loose color grouping

**Estimated Effort**: 0.5 days

---

## Acceptance Criteria

- [x] `--color-tolerance N` flag added to CLI
- [x] Default value: 20 (current hardcoded value)
- [x] Range: 0-100 (0=exact match, 100=very loose)
- [x] Updates tolerance parameter in image_extractor.py
- [x] Works with --extract flag
- [x] Tests verify grouping behavior at different tolerances
- [x] Documentation updated

---

## Implementation Plan

### Implementation Steps

1. **Add CLI flag**: Add `--color-tolerance` to cli.py
   - Default: 20 (current behavior)
   - Type: int, range 0-100
   - Help text: "RGB distance threshold for color grouping (default: 20, range: 0-100)"

2. **Update extract_circles_to_images call**: Pass tolerance parameter
   - Pass tolerance to extract_circles_to_images()
   - Already has tolerance parameter, just needs wiring

3. **Add validation**: Range check for tolerance value

---

## Testing Strategy

### Unit Tests

- [x] Test with tolerance=0 (exact colors only)
- [x] Test with tolerance=50 (loose grouping)
- [x] Test with tolerance=100 (very loose)
- [x] Verify grouping changes with tolerance

---

## Documentation Updates

### 📝 IMPORTANT: Update CHANGELOG.md
- [x] **Add entry to CHANGELOG.md under [Unreleased]**
  - Use "Added": "Add `--color-tolerance` flag to control color grouping sensitivity"

### Other Documentation
- [x] Update README.md with tolerance examples
- [x] Update ROADMAP.md - check off M2 task
