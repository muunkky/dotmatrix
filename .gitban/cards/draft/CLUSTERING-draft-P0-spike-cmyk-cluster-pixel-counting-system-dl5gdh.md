# CMYK Cluster Pixel Counting System

## Problem Statement

Current detection extracts circle geometry (center, radius) but doesn't capture the actual ink distribution. For accurate color reproduction, we need to know the **pixel counts** of each ink layer within each halftone cluster.

## Proposed Approach

1. **Separate ink layers** (C, M, Y, K) using existing `separate_cmyk_inks()`
2. **Cluster around black dots** - each K dot anchors a cluster
3. **For each cluster, count pixels** in 7 categories:
   - Primary inks: Cyan, Magenta, Yellow, Black
   - Overlap colors: Red (M+Y), Green (C+Y), Blue (C+M)

## Output Format (per cluster)

```python
{
    "cluster_id": int,
    "center": (x, y),  # Black dot center
    "pixel_counts": {
        "cyan": int,
        "magenta": int, 
        "yellow": int,
        "black": int,
        "red": int,      # M+Y overlap
        "green": int,    # C+Y overlap
        "blue": int      # C+M overlap
    }
}
```

## Stakeholder Questions

See linked spike card for clarifying questions.

## Success Criteria

- [ ] Each cluster has exactly 1 black dot
- [ ] Each cluster has 0-3 CMY midtone dots (when including RGB overlaps)
- [ ] Pixel counts are accurate within 5% of manual measurement
- [ ] Handles edge cases (missing colors, partial overlaps)
