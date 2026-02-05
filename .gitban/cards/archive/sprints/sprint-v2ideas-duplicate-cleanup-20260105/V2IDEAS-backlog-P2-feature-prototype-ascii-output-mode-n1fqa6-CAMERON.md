

## Description
Implement a prototype for rendering the image as ASCII/ANSI art for terminal output and text-based displays.

## Acceptance Criteria
- [ ] ASCII output format available in CLI
- [ ] Characters accurately represent local pixel density or color
- [ ] Output fits standard terminal widths (configurable)
- [ ] Color support via ANSI codes (optional but desired)

## Implementation Plan
- [ ] Create AsciiRenderer class
- [ ] Define character set for density mapping (e.g., " .:-=+*#%@")
- [ ] Implement block-to-character conversion logic
- [ ] Add --output-format ascii CLI argument
- [ ] Test output in standard terminals

## Test Plan
- [ ] Unit tests for density mapping
- [ ] Verify correct character selection
- [ ] Test output dimensions
- [ ] Integration test with main pipeline