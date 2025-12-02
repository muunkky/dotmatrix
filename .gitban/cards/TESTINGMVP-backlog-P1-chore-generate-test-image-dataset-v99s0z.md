## Purpose

Create synthetic test images with known circle properties (center, radius, color) for validation and regression testing.

## Project Location

- tests/data/images/ - Generated test images
- tests/data/ground_truth/ - JSON files with ground truth
- tests/generate_test_images.py - Generation script

## Tasks

- [ ] Create tests/data/ directory structure
- [ ] Write generate_test_images.py script using PIL
- [ ] Generate single_circle.png test image
- [ ] Generate multiple_circles.png test image
- [ ] Generate small_circles.png test image
- [ ] Generate large_circles.png test image
- [ ] Generate edge_circles.png test image
- [ ] Generate various_colors.png test image
- [ ] Generate ground truth JSON for each image
- [ ] Create tests/data/README.md documenting dataset

## Outputs

- At least 10 test images (PNG format, 512x512)
- Ground truth JSON files matching format: [{"center": [x, y], "radius": r, "color": [r, g, b]}]
- README documenting each test case

## Success Criteria

- [ ] All test images are valid PNG files
- [ ] Ground truth JSON is valid and matches images
- [ ] Manual inspection confirms circles are correct
- [ ] README documents all test scenarios