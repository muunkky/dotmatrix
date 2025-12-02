## Description

Structure detection output as JSON/CSV with center coordinates, radius, and RGB color for each detected circle.

**Value**: Provides structured, parseable output that users can consume programmatically or save to files.

**Target Users**: End users consuming detection results

**Estimated Effort**: 1.5 hours

---

## Acceptance Criteria

- [ ] JSON output follows schema: [{"center": [x, y], "radius": r, "color": [r, g, b]}]
- [ ] CSV output has headers: center_x,center_y,radius,color_r,color_g,color_b
- [ ] Both formats output valid, parseable data
- [ ] Handles empty results (no circles detected)
- [ ] Output to stdout or file based on CLI args

---

## Implementation Plan

### Overview

Create formatter module with functions for JSON and CSV output, integrate with CLI to write to stdout or file.

### Implementation Steps

1. **Create formatter.py module**:
   - Define format_json(circles: List[Circle]) -> str function
   - Define format_csv(circles: List[Circle]) -> str function
   - Use json module for JSON formatting
   - Use csv module for CSV formatting

2. **Implement JSON formatter**:
   - Convert Circle objects to dicts
   - Structure: {"center": [x, y], "radius": r, "color": [r, g, b]}
   - Use json.dumps with indent=2 for readability

3. **Implement CSV formatter**:
   - Write header row
   - Write one row per circle
   - Fields: center_x, center_y, radius, color_r, color_g, color_b

4. **Integrate with CLI**:
   - Call appropriate formatter based on --format flag
   - Write to stdout or file based on --output flag

### Technical Considerations

- **Format**: JSON is more structured, CSV is simpler for spreadsheets
- **Empty Results**: Return empty array [] for JSON, header-only for CSV

### Dependencies

- **Prerequisites**: Cards (Hough Transform, Color Extraction) must be complete

---

## Testing Strategy

### Unit Tests

- [ ] Test JSON output with single circle
- [ ] Test JSON output with multiple circles
- [ ] Test JSON output with no circles (empty array)
- [ ] Test CSV output with headers and data
- [ ] Test CSV output with no circles (header only)
- [ ] Test output to file vs stdout

---

## Documentation Updates

- [ ] Document output format schema in README
- [ ] Add example outputs for JSON and CSV