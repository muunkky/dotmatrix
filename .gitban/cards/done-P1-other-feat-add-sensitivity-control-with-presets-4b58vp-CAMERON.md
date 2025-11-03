## Description

Add `--sensitivity` CLI flag with presets (strict, normal, relaxed) to control circle detection sensitivity. Maps to HoughCircles param1/param2 parameters for edge detection and accumulator threshold.

**Value**: Gives users easy control over detection strictness without needing to understand OpenCV parameters.

**Target Users**: Users who need to tune detection for noisy images or very clean images.

**Estimated Effort**: 1 day

---

## Acceptance Criteria

- [x] `--sensitivity` flag added to CLI
- [x] Three presets: strict, normal (default), relaxed
- [x] strict: param1=100, param2=40 (fewer detections, high confidence)
- [x] normal: param1=50, param2=30 (current default, balanced)
- [x] relaxed: param1=30, param2=20 (more detections, lower confidence)
- [x] Maps to cv2.HoughCircles parameters
- [x] Tests with synthetic images (low quality, high quality)
- [x] Documentation updated

---

## Implementation Plan

### Implementation Steps

1. **Add CLI flag**: Add `--sensitivity` to cli.py
   - Optional flag with choices: strict, normal, relaxed
   - Default: normal (current behavior)
   - Help text: "Detection sensitivity preset (default: normal)"

2. **Create sensitivity presets**: New module or dict in circle_detector.py
   - Define param1/param2 mappings for each preset
   - strict: (100, 40), normal: (50, 30), relaxed: (30, 20)

3. **Update detect_circles()**: Accept sensitivity parameter
   - Map preset to param1/param2 values
   - Pass to cv2.HoughCircles

4. **Wire through CLI**: Pass sensitivity from CLI to detect_circles

---

## Testing Strategy

### Unit Tests

- [x] Test each preset maps to correct parameters
- [x] Test default preset is normal
- [x] Test invalid preset raises error

### Integration Tests

- [x] Clean image: strict detects fewer, relaxed detects more
- [x] Noisy image: strict filters noise, relaxed catches all
- [x] Verify param1/param2 are passed correctly

---

## Documentation Updates

### 📝 IMPORTANT: Update CHANGELOG.md
- [x] **Add entry to CHANGELOG.md under [Unreleased]**
  - Use "Added": "Add `--sensitivity` flag for easy detection tuning"
  - List presets: strict, normal, relaxed

### Other Documentation
- [x] Update README.md with --sensitivity examples
- [x] Update ROADMAP.md - check off M2 task

---

## Prerequisites

None - uses existing OpenCV parameters

---

## Notes

### Design Decisions

- **Decision**: Use presets instead of raw param1/param2 values
- **Rationale**: More user-friendly, abstracts OpenCV complexity
- **Alternatives**: Expose raw params (too complex), auto-tune (unpredictable)
- **Trade-offs**: Less fine-grained control, but much easier to use
