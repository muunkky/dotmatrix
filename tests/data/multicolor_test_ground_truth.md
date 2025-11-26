# Multi-Color Circle Test Cases

## Expected Detection Results

### Scenario 1: Overlap (x=80-110, y=80)
- Should detect: 2 circles (red and black)
- Challenge: Overlapping region has mixed colors
- Expected behavior: Use dominant color per region

### Scenario 2: 3-Way Overlap (x=250-275, y=80-115)
- Should detect: 3 circles (yellow, magenta, cyan)
- Challenge: Complex overlap region
- Expected behavior: May detect partial circles only

### Scenario 3: Clean Circle (x=80, y=200)
- Should detect: 1 black circle
- Control case: No multi-color issues

### Scenario 4: Anti-Aliased Edge (x=200, y=200)
- Should detect: 1 magenta circle
- Challenge: Edge pixels have gradient
- Expected behavior: Use center color, ignore edges

### Scenario 5: Partial Occlusion (x=320-340, y=200)
- Should detect: 2 circles (cyan behind, black front)
- Challenge: Cyan only partially visible
- Expected behavior: Detect both, cyan may be arc

### Scenario 6: Touching Circles (x=80-140, y=330)
- Should detect: 2 separate circles (red, yellow)
- Control case: No overlap, just adjacent

### Scenario 7: Gradient (x=250, y=330)
- Should detect: 1 circle
- Challenge: No single dominant color
- Expected behavior: Flag as "uncertain" or use center
