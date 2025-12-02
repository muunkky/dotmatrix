# Add --gpu CLI Flag with Auto-Detection and Fallback

## Description

Add command-line interface support for GPU acceleration with graceful fallback to CPU.

**Value**: User-facing interface for GPU acceleration. Enables users to control GPU usage.

**Target Users**: CLI users

**Estimated Effort**: 2 hours

---

## Acceptance Criteria

- [x] --gpu flag enables GPU rendering
- [x] --no-gpu flag forces CPU rendering
- [x] Auto-detect mode (default) uses GPU if available
- [x] Helpful error message if --gpu specified but GPU unavailable
- [x] Progress output shows GPU status

---

## Implementation Plan

### Overview

Add CLI flag to cli.py, implement auto-detection, add user feedback messages.

### Implementation Steps

1. **Add CLI Flag**: @click.option for --gpu/--no-gpu
2. **Implement Detection**: detect_gpu_available() function
3. **Add Fallback Logic**: Use GPU if available, else CPU
4. **Add User Feedback**: Show GPU status in progress output


## Test Plan

- [x] --gpu flag triggers GPU rendering
- [x] --no-gpu flag triggers CPU rendering
- [x] Auto-detect correctly identifies GPU availability
