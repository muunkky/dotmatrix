

## Description
Implement a prototype for exporting the dot matrix as an SVG file for scalable vector graphics output.

## Acceptance Criteria
- [ ] SVG output format available in CLI
- [ ] Circles are correctly positioned and sized in SVG
- [ ] Colors are correctly applied to SVG elements
- [ ] File size is within reasonable limits for typical inputs

## Implementation Plan
- [ ] Create SvgRenderer class
- [ ] Implement SVG XML generation logic
- [ ] Map internal dot representation to SVG <circle> elements
- [ ] Add --output-format svg CLI argument
- [ ] Validate output in standard SVG viewers (browser, Inkscape)

## Test Plan
- [ ] Unit tests for coordinate mapping
- [ ] Verify valid XML generation
- [ ] Test SVG output with various circle sizes and colors
- [ ] Integration test with main pipeline