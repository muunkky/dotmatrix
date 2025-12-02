# Problem
`--palette cmyk` is confusing because users expect halftone (ink separation) processing when they say CMYK. The current behavior has two different modes:
- `cmyk` - just matches to 4 literal colors (not useful)
- `cmyk-sep` - actual CMYK ink separation with subtractive color model (what users expect)

# Solution
1. Rename/merge so `cmyk` always uses halftone/ink separation processing
2. Literal color detection should just use `rgb` or `custom` palettes
3. Remove the confusing `cmyk-sep` option - it should just be `cmyk`

# Notes
- Yellow + Magenta = Red (needs to appear in both layers)
- Cyan + Magenta = Blue
- Cyan + Yellow = Green
- This is what users expect when they specify CMYK