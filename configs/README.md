# DotMatrix Configuration Files

This directory contains preset configurations for common use cases.

## Usage

```bash
dotmatrix --config configs/cmyk-overlapping.json --input image.png --extract output/
```

CLI arguments override config file values:

```bash
# Use config but override max_colors
dotmatrix --config configs/cmyk-overlapping.json --input image.png --max-colors 5 --extract output/
```

## Available Configs

### cmyk-overlapping.json

**Use case:** Images with heavily overlapping CMYK circles (cyan, magenta, yellow, black)

**Settings:**
- Strict detection to avoid false positives
- Band edge sampling for clean color separation
- Background filtering to exclude white
- K-means clustering to 4 color groups

**Expected output:** 4 PNG files (one per color)

**Example:**
```bash
dotmatrix --config configs/cmyk-overlapping.json --input test_dotmatrix.png --extract output/
```

## Creating Custom Configs

### JSON Format

```json
{
  "description": "Description of use case",
  "sensitivity": "strict|normal|relaxed",
  "min_radius": 30,
  "max_radius": null,
  "min_distance": 50,
  "edge_sampling": true,
  "edge_method": "band|canny|exposed|circumference",
  "edge_samples": 36,
  "exclude_background": true,
  "max_colors": 4,
  "color_tolerance": 20,
  "min_confidence": null,
  "format": "json|csv",
  "debug": false
}
```

### YAML Format (requires PyYAML)

```yaml
description: Description of use case
sensitivity: strict
min_radius: 30
min_distance: 50
edge_sampling: true
edge_method: band
exclude_background: true
max_colors: 4
```

## Parameter Reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `sensitivity` | string | Detection sensitivity: `strict`, `normal`, `relaxed` |
| `min_radius` | int | Minimum circle radius in pixels |
| `max_radius` | int/null | Maximum circle radius in pixels |
| `min_distance` | int | Minimum distance between circle centers |
| `edge_sampling` | bool | Use edge-based sampling instead of area |
| `edge_method` | string | Edge sampling method: `band`, `canny`, `exposed`, `circumference` |
| `edge_samples` | int | Number of sample points for edge sampling |
| `exclude_background` | bool | Filter out near-white colors (RGB > 240) |
| `max_colors` | int/null | K-means cluster to N colors |
| `color_tolerance` | int | RGB distance for grouping similar colors |
| `min_confidence` | int/null | Minimum confidence score (0-100) |
| `format` | string | Output format: `json` or `csv` |
| `debug` | bool | Enable debug output |

## Tips

- **Use `null` for optional parameters** to use defaults
- **CLI args override config** - Great for testing variations
- **Comments not supported in JSON** - Use a `"description"` field instead
- **Boolean flags:** Set to `true`/`false` in config, just presence in CLI

## Examples by Use Case

### Non-overlapping circles (simple)
```json
{
  "sensitivity": "normal",
  "edge_sampling": false
}
```

### High precision detection
```json
{
  "sensitivity": "strict",
  "min_radius": 20,
  "min_distance": 30,
  "min_confidence": 80
}
```

### Many small circles
```json
{
  "sensitivity": "relaxed",
  "min_radius": 5,
  "min_distance": 10
}
```

### Reduce to specific colors
```json
{
  "edge_sampling": true,
  "edge_method": "band",
  "max_colors": 6,
  "exclude_background": true
}
```
