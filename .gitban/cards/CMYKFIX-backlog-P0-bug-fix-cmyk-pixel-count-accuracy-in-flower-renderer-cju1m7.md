## Bug Description

**Summary**: Reconstituted CMYK halftone images have significant pixel count errors vs source

The flower renderer produces images where CMYK pixel counts don't match the source image. Cyan shows ~36% error, magenta shows ~63% error. This makes the reconstitution feature unreliable.

**Severity**: P0/Critical

**Value of Fix**: Core functionality of dotmatrix halftone reconstitution is broken. Users cannot trust the output accuracy.

**Discovered**: During CMYK accuracy testing on 2025-11-30

**Reporter**: CAMERON

---

## Steps to Reproduce

### Prerequisites
- dotmatrix installed
- Test image: inputs/test-images/cmyk-halftone-500px.png

### Reproduction Steps

1. **Run reconstitute command**:
   ```bash
   python -m dotmatrix.cli reconstitute inputs/test-images/cmyk-halftone-500px.png --blend-overlaps
   ```

2. **Check accuracy metrics**:
   ```bash
   # Look at accuracy output in run manifest or console
   ```

3. **Observe error rates**:
   - Cyan: ~36% error
   - Magenta: ~63% error

### Expected Behavior
- Rendered CMYK pixel counts match source within acceptable tolerance (<5% error)

### Actual Behavior
- Rendered cyan: 33,674 pixels (expected: 53,370)
- Rendered magenta: 10,192 pixels (expected: 27,798)

---

## Environment

### System Environment
- **OS**: Linux (WSL2)
- **Python Version**: 3.10

### Software Environment
- **Application Version**: Current development branch
- **Key Dependencies**: numpy, opencv-python, scipy

---

## Root Cause Analysis (optional)

### Investigation Findings

Under investigation in card 8zjmm6. Potential causes:

1. **Adjacent cluster interference**: `used` mask causes pixel loss between overlapping flowers
2. **Edge clipping**: Clusters near image boundaries have truncated petals
3. **Cluster target mismatch**: sum(cluster.cyan) may not equal source_cyan_decomposed

### Technical Details

Key files:
- `src/dotmatrix/circle_renderer.py:350-430` - blend_overlaps rendering
- `src/dotmatrix/cluster_pixel_counter.py` - CMYK decomposition

---

## Solution

### Fix Strategy

TBD - Pending root cause confirmation from card 8zjmm6

**Possible Approaches**:
1. If inter-cluster interference: Adjust rendering order or geometry
2. If edge clipping: Handle boundary clusters differently
3. If target mismatch: Fix cluster assignment or decomposition

### Implementation Steps

1. **Complete root cause analysis** (card 8zjmm6)
2. **Get user validation** (card fx7toj)
3. **Implement fix** based on confirmed root cause
4. **Verify accuracy** meets user-defined threshold

---

## Testing & Verification (optional)

### Bug Reproduction Verification

- [x] Confirm bug is reproducible in current version
- [x] Document reproduction rate before fix
- [x] Capture screenshots/logs of bug manifestation

### Fix Verification

- [ ] Apply fix to test environment
- [ ] Verify original reproduction steps no longer trigger bug
- [ ] Confirm expected behavior now occurs
- [ ] Test fix multiple times (10+ attempts for intermittent bugs)

### Regression Testing

- [ ] All existing unit tests pass
- [ ] All existing integration tests pass
- [ ] Manual testing of related functionality
- [ ] No new bugs introduced by fix

---

## Prerequisites (optional)

**DO NOT START THIS CARD UNLESS:**

- [ ] Root cause analysis complete (card 8zjmm6)
- [ ] User validation checkpoints complete (card fx7toj)
- [ ] Fix approach confirmed with user

**Why**: Fix must address the actual root cause, not symptoms

---

## Related Issues (optional)

### Related Bugs

**Related**: 8zjmm6 - CMYK Accuracy Root Cause Analysis
**Related**: fx7toj - User Validation Checkpoints

### Cross-References

- Previous CMYKFIX attempts in conversation history
- Render order fix (black first)
- Petal distance fix (0.5)
- Binary search bounds fix (*10)

---

## Progress Notes (optional)

**Session 2025-11-30 (CAMERON):**

🔍 **Investigation:**
- Multiple fix attempts made but error persists
- Per-cluster calculations appear correct
- Total rendered pixels don't match expected totals

⚠️ **Blockers:**
- Root cause not yet confirmed

📋 **Next Steps:**
1. Complete root cause analysis
2. Get user validation
3. Implement confirmed fix
