# Auto-Calibrate Radius from Reference Detections

## Problem Statement
Current radius detection requires manual specification of `--min-radius` and `--max-radius`. In practice, black circles in halftone images are often detected perfectly, while other colors struggle. We can use successfully detected circles as a reference to auto-calibrate the radius range for subsequent detections.

## Observation
From CMYK test image analysis:
- Black circles: Detected with high accuracy (clear, high contrast)
- Other colors: Variable detection quality
- All dot sizes in a halftone print are typically uniform

## Proposed Solution

### Phase 1: Reference Color Detection
1. Detect circles for the highest-contrast color (black or darkest)
2. Collect radius statistics from successful detections
3. Calculate mean, std, min, max radius from reference

### Phase 2: Calibrated Detection
1. Use reference statistics to set tight radius bounds
2. Apply calibrated bounds to remaining colors
3. Optionally allow user override

### Algorithm
```python
def auto_calibrate_radius(reference_circles):
    radii = [c.radius for c in reference_circles]
    mean_r = np.mean(radii)
    std_r = np.std(radii)
    
    # Tight bounds: mean ± 2σ (captures 95% of dots)
    min_radius = max(1, mean_r - 2 * std_r)
    max_radius = mean_r + 2 * std_r
    
    return min_radius, max_radius
```

## Acceptance Criteria
- [x] Implement reference color selection (auto or user-specified)
- [x] Calculate radius statistics from reference detections
- [x] Apply calibrated radius to all color detections
- [x] Add `--calibrate-from <color>` CLI flag
- [x] Add `--auto-calibrate` flag for automatic selection
- [x] Document calibration methodology

## Implementation Tasks
- [x] Add radius statistics calculation function
- [x] Implement reference color auto-selection (highest detection count)
- [x] Add calibration pass before full detection
- [x] Create CLI flags for calibration options
- [x] Test with various halftone images
- [x] Add calibration info to output metadata

## CLI Design
```bash
# Auto-calibrate from best-detected color
dotmatrix -i image.png --auto-calibrate

# Calibrate from specific color (black)
dotmatrix -i image.png --calibrate-from black

# Manual override still available
dotmatrix -i image.png --min-radius 15 --max-radius 25
```

## Dependencies
- Benefits from auto-palette detection (card e5r8vj)
- Helps improve occluded circle detection (card nj0ev7)

## Notes
- Black typically works best due to high contrast
- Halftone dots are designed to be uniform size
- Calibration adds one extra detection pass (minimal overhead)
