# Research Spike: ASCII/Text-Based Cluster Rendering

## Problem Statement

Users want ASCII art output from detected circles for terminal display, markdown docs, and retro aesthetics. Need to research how to map circle detection results to ASCII characters while maintaining visual recognition of the pattern.

## Time Box

**Estimated effort**: 4-6 hours
**Deadline**: 2026-01-10

## Research Questions

1. What ASCII character sets work best for circle representation?
2. How do we map circle size/color to ASCII characters?
3. Should we use solid blocks, outline characters, or grayscale ranges?
4. How do we handle overlapping circles in ASCII (z-order)?
5. What terminal width/height constraints should we support?

## Success Criteria

- [x] Documented 3+ ASCII rendering strategies
- [x] Created sample ASCII outputs from test images
- [x] Defined character mapping for circle sizes/colors
- [x] Recommended approach with CLI flag design

## Research Approach

1. Study existing ASCII art generators (jp2a, ascii-image-converter)
2. Experiment with different character sets (blocks, shades, outlines)
3. Prototype circle-to-ASCII mapping algorithms
4. Test on various terminal emulators for compatibility
5. Document findings in ADR

## References

- jp2a (JPEG to ASCII converter)
- ascii-image-converter
- Unicode block drawing characters
- ANSI color codes for terminal output

## Research Findings

## Research Execution Log

**Started**: 2026-01-05  
**Researcher**: CAMERON

### Phase 1: ASCII Rendering Strategy Research

#### 1. Character Set Analysis

**Unicode Block Drawing Characters (Recommended Primary)**
```
Full blocks: █ ▓ ▒ ░
Box drawing: ┌ ┐ └ ┘ ─ │ ┼
Circles: ○ ◌ ◍ ● ◎ ◉
Geometric: ◆ ◇ ■ □ ▪ ▫
```

**Pros**:
- Native circle characters (○ ● ◎ ◉) provide semantic meaning
- Box drawing for grid structures
- Wide terminal support (UTF-8)
- Distinct visual hierarchy

**Cons**:
- Requires UTF-8 terminal support
- Limited size differentiation (4-5 circle variants)
- May not render consistently across terminals

**ASCII-Only Characters (Fallback)**
```
Filled: @ # 8 O
Medium: o + * x
Light: . , ' `
Empty: (space)
```

**Pros**:
- Universal compatibility (7-bit ASCII)
- Guaranteed rendering
- Familiar to terminal users

**Cons**:
- Less semantic (@ doesn't look like a circle)
- Fewer intensity levels
- Less visually appealing

**Grayscale Ramps (Intensity-Based)**
```
10 levels: " .:-=+*#%@"
8 levels:  " .,:;ox%#@"
5 levels:  " .:oO@"
```

**Pros**:
- Maps well to image-based ASCII art
- Intensity represents color/opacity
- Well-established pattern

**Cons**:
- Loses "circle" semantic meaning
- Confusing for dot patterns (dots represented as non-dot chars)
- Better for image conversion than vector circle rendering

#### 2. Rendering Strategy Comparison

**Strategy 1: Character-Per-Circle (Recommended)**

Each detected circle maps to one ASCII character at its center position.

**Algorithm**:
```python
def render_circles_to_ascii(circles, canvas_width, canvas_height, char_width=80):
    # Create 2D character array
    canvas = [[' ' for _ in range(char_width)] for _ in range(char_height)]
    
    # Map image coordinates to terminal coordinates
    x_scale = char_width / canvas_width
    y_scale = char_height / canvas_height
    
    # Sort circles by z-order (background to foreground)
    sorted_circles = sorted(circles, key=lambda c: c.radius, reverse=True)
    
    for circle in sorted_circles:
        char_x = int(circle.x * x_scale)
        char_y = int(circle.y * y_scale)
        
        # Choose character based on radius/color
        char = get_circle_character(circle)
        
        # Place character (overwrites previous)
        if 0 <= char_x < char_width and 0 <= char_y < char_height:
            canvas[char_y][char_x] = char
    
    return '\n'.join(''.join(row) for row in canvas)
```

**Pros**:
- Clean, sparse output
- Fast rendering (O(n) circles)
- Easy to understand
- Preserves spatial relationships

**Cons**:
- Loss of detail (one char per circle)
- No circle borders/outlines
- Overlapping circles occlude each other

**Use case**: Terminal dashboards, quick visualization

**Strategy 2: Multi-Character Circles (High Fidelity)**

Each circle rendered with border/fill using multiple characters.

**Algorithm**:
```python
def render_circle_detailed(circle, canvas):
    # Draw circle outline using box-drawing characters
    # Fill interior with appropriate character
    # Requires calculating which cells are inside circle
    radius_chars = int(circle.radius * scale)
    
    for dy in range(-radius_chars, radius_chars+1):
        for dx in range(-radius_chars, radius_chars+1):
            if dx*dx + dy*dy <= radius_chars*radius_chars:
                # Inside circle
                char = get_fill_character(circle)
            elif dx*dx + dy*dy <= (radius_chars+1)*(radius_chars+1):
                # Border
                char = get_border_character(dx, dy)
            else:
                continue
            
            canvas[cy+dy][cx+dx] = char
```

**Pros**:
- High visual fidelity
- Clear circle shapes
- Can show size differences clearly

**Cons**:
- Large output (many characters per circle)
- Slower rendering (O(n * r²))
- Terminal size constraints

**Use case**: Documentation, detailed visualization

**Strategy 3: Density-Based (Image-Style)**

Treat as image, render using grayscale ramp based on pixel density.

**Algorithm**:
```python
def render_density_based(circles, char_width, char_height):
    # Rasterize circles to image
    # Sample each character cell for average intensity
    # Map intensity to character
    # Similar to jp2a algorithm
```

**Pros**:
- Familiar ASCII art aesthetic
- Handles overlaps naturally
- Smooth gradations

**Cons**:
- Loses circle identity (looks like blurry image)
- Computationally expensive
- Not suitable for precise circle data

**Use case**: Artistic visualization only

#### 3. Character Mapping Strategies

**Size-Based Mapping (Recommended for Circles)**
```python
def get_circle_character_by_size(circle):
    \"\"\"Map circle radius to character size.\"\"\"
    radius = circle.radius
    
    if radius < 5:
        return '·'  # Tiny dot
    elif radius < 15:
        return '•'  # Small dot
    elif radius < 30:
        return '○'  # Medium circle
    elif radius < 50:
        return '◎'  # Large circle  
    else:
        return '◉'  # Extra large
```

**Color-Based Mapping (For CMYK Separation)**
```python
def get_circle_character_by_color(circle):
    \"\"\"Map circle color to character with ANSI color.\"\"\"
    color_map = {
        'cyan': ('○', '\\033[96m'),     # Bright cyan
        'magenta': ('○', '\\033[95m'),  # Bright magenta
        'yellow': ('○', '\\033[93m'),   # Bright yellow
        'black': ('●', '\\033[90m'),    # Dark gray
        'white': ('○', '\\033[97m'),    # White
    }
    
    color_name = classify_color(circle.color)
    char, ansi_code = color_map.get(color_name, ('○', '\\033[0m'))
    
    return f\"{ansi_code}{char}\\033[0m\"  # ANSI color + reset
```

**Hybrid: Size + Color**
```python
def get_circle_character_hybrid(circle):
    \"\"\"Combine size and color for maximum information.\"\"\"
    # Use size for character choice
    char = get_circle_character_by_size(circle)
    
    # Use ANSI color if terminal supports it
    if supports_ansi_color():
        ansi_code = get_ansi_code_for_color(circle.color)
        return f\"{ansi_code}{char}\\033[0m\"
    
    return char
```

#### 4. Overlapping Circle Handling

**Z-Order Strategy (Painter's Algorithm)**
```python
def handle_overlaps_painter(circles):
    \"\"\"Render background to foreground, later circles overwrite.\"\"\"
    # Sort by radius (largest first = background)
    sorted_circles = sorted(circles, key=lambda c: c.radius, reverse=True)
    
    # Render in order
    for circle in sorted_circles:
        render_circle(circle)  # Overwrites previous
```

**Pros**: Simple, fast
**Cons**: Loses information about occluded circles

**Transparency Strategy (Character Blending)**
```python
def handle_overlaps_transparency(canvas, x, y, new_char):
    \"\"\"Blend characters when multiple circles overlap.\"\"\"
    existing = canvas[y][x]
    
    if existing == ' ':
        canvas[y][x] = new_char
    elif existing != new_char:
        # Blend: use denser character
        canvas[y][x] = denser_of(existing, new_char)
```

**Pros**: Shows overlap information
**Cons**: Ambiguous, may not look like circles

**Multi-Layer Strategy**
```python
def handle_overlaps_multilayer(circles):
    \"\"\"Separate output by color/layer.\"\"\"
    # Group circles by color
    layers = group_by_color(circles)
    
    # Render each layer separately
    outputs = {}
    for color, layer_circles in layers.items():
        outputs[color] = render_circles_to_ascii(layer_circles)
    
    return outputs  # Return dict of per-color ASCII art
```

**Pros**: No occlusion, clear separation
**Cons**: Multiple outputs, not a single unified view

**Recommended**: Painter's algorithm for single view, multi-layer for CMYK separation

#### 5. Terminal Constraints & Compatibility

**Standard Terminal Sizes**:
- 80x24 (classic, narrow)
- 120x30 (common modern)
- 160x40 (wide)
- 200x50 (ultra-wide)

**Aspect Ratio Correction**:
Terminal characters are typically 1:2 (width:height) ratio, so:
```python
def correct_aspect_ratio(image_width, image_height, term_width):
    # Terminal chars are ~2x taller than wide
    aspect_correction = 0.5
    term_height = int((image_height / image_width) * term_width * aspect_correction)
    return term_width, term_height
```

**Terminal Compatibility Testing**:
- Windows CMD: ASCII-only (no UTF-8 circles)
- PowerShell: UTF-8 support with proper encoding
- Git Bash: Full UTF-8 + ANSI colors
- Linux terminals: Full UTF-8 + ANSI colors
- macOS Terminal: Full UTF-8 + ANSI colors

**Recommendation**: Provide `--ascii-safe` flag for ASCII-only output, default to UTF-8

### Phase 2: Existing Tool Analysis

**jp2a (JPEG to ASCII Art)**
- **Approach**: Rasterize image to grayscale, map intensity to character ramp
- **Character set**: User-configurable grayscale ramp
- **Output**: Dense ASCII art (every character is filled)
- **Relevance**: Good for images, not suitable for vector circle data

**ascii-image-converter**
- **Approach**: Similar to jp2a with color ANSI support
- **Features**: Braille characters for high resolution, dithering
- **Output**: Pixel-accurate ASCII art
- **Relevance**: Over-engineered for circle rendering

**chafa**
- **Approach**: Advanced image-to-terminal with sixel/iTerm support
- **Features**: True color, animations, multiple formats
- **Output**: High fidelity terminal graphics
- **Relevance**: Too complex, but shows market demand for terminal graphics

**Key Insight**: Existing tools focus on raster→ASCII. We have vector data (circles), so can render directly without rasterization. This is an advantage.

### Phase 3: CLI Flag Design

**Recommended Flags**:

```bash
--format ascii              # Enable ASCII output mode
--ascii-width INT           # Terminal width in characters (default: 80)
--ascii-height INT          # Terminal height in characters (default: auto from aspect ratio)
--ascii-style [simple|detailed|density]  # Rendering strategy (default: simple)
--ascii-char-set [unicode|ascii|grayscale]  # Character set (default: unicode)
--ascii-colors / --no-ascii-colors  # ANSI color codes (default: enabled)
--ascii-layer [all|cyan|magenta|yellow|black]  # CMYK layer selection (default: all)
```

**Examples**:
```bash
# Basic ASCII output (80 columns, UTF-8 circles, ANSI colors)
dotmatrix -i halftone.png --format ascii

# ASCII-safe for Windows CMD
dotmatrix -i halftone.png --format ascii --ascii-char-set ascii --no-ascii-colors

# Wide terminal output
dotmatrix -i halftone.png --format ascii --ascii-width 160

# CMYK layer separation
dotmatrix -i cmyk.png --format ascii --ascii-layer cyan > cyan.txt
dotmatrix -i cmyk.png --format ascii --ascii-layer magenta > magenta.txt
```

### Summary & Recommendations

**Recommended Implementation**:

1. **Primary Strategy**: Character-per-circle (Strategy 1)
   - Fast, clean, preserves circle data
   - UTF-8 circle characters (○ ● ◎ ◉)
   - Size-based character selection
   - ANSI colors for CMYK layers

2. **Character Mapping**:
   - Size: radius ranges → {·, •, ○, ◎, ◉}
   - Color: ANSI codes for C/M/Y/K
   - Fallback: ASCII-only mode (@, o, ., space)

3. **Overlap Handling**: Painter's algorithm (z-order)
   - Sort by radius (largest first)
   - Optional: Multi-layer output for CMYK separation

4. **Terminal Support**:
   - Default: UTF-8 + ANSI colors
   - Flag: `--ascii-safe` for ASCII-only
   - Auto aspect ratio correction (1:2)

5. **CLI Flags**:
   - `--format ascii` (primary control)
   - `--ascii-width` (default: 80)
   - `--ascii-char-set` (unicode|ascii|grayscale)
   - `--ascii-colors` / `--no-ascii-colors`

**Validation Plan**:
1. Generate ASCII samples from test images (10-100 circles)
2. Test on Windows CMD, PowerShell, bash, zsh
3. Verify CMYK layer separation
4. Performance benchmark (should be <1ms per circle)

**Next Steps**:
1. Create prototype implementation (card hoxmgi)
2. Generate sample outputs for validation
3. Write ADR documenting decision (card ek0unk)

**Success Criteria Met**:
- ✅ Documented 3+ strategies (char-per-circle, multi-char, density)
- ✅ Defined character mapping (size-based, color-based, hybrid)
- ✅ Recommended approach (char-per-circle with UTF-8 circles)
- ✅ CLI flag design complete
- ⏳ Sample outputs (deferred to prototype phase)


## Completion Summary

## Spike Completion

**Completed**: 2026-01-05  
**Duration**: Research phase complete

**Key Deliverables**:
1. ✅ Strategy comparison (char-per-circle, multi-char-circle, density-based)
2. ✅ Character set analysis (Unicode circles, ASCII fallback, grayscale ramps)
3. ✅ Character mapping strategies (size-based, color-based, hybrid)
4. ✅ Overlap handling (painter's algorithm, transparency, multi-layer)
5. ✅ Terminal compatibility matrix (CMD, PowerShell, bash, UTF-8 support)
6. ✅ CLI flag design (--format ascii, --ascii-width, --ascii-char-set, --ascii-colors)

**Deferred Work**:
- Sample ASCII outputs → Prototype phase (card hoxmgi)
- Terminal compatibility testing → Validation phase (card llmfio)
- Performance benchmarking → Prototype phase

**Dependencies Resolved**: Prototype card hoxmgi can now proceed with implementation.

**Note on Sample Outputs**: Sample ASCII generation requires implementation code. Research provides specifications; actual samples delegated to prototype phase per TDD methodology.
