## Problem

The `--blend-overlaps` flag doesn't produce enough C+M overlap to create blue pixels.

## Evidence

From CMYK accuracy comparison:
- **Source**: 15,750 blue pixels (C+M overlap)
- **Recon**: 70 blue pixels

The flower renderer petals are positioned such that cyan and magenta don't sufficiently overlap.

## Root Cause Hypothesis

1. Petal geometry doesn't create enough C+M intersection
2. Petal sizes may be too small after `petal_distance` adjustment
3. Rotation angles may prevent proper overlap

## Acceptance Criteria

- [ ] Blue pixels in recon within 20% of source blue pixels
- [ ] Magenta error reduced from 72% to under 20%
- [ ] Total weighted error under 15%

## Related

- Accuracy card n0qecx documented the issue
- CELLCLUSTER sprint revealed the problem
