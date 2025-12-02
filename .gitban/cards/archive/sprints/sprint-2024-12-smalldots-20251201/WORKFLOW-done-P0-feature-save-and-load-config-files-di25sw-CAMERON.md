## Description

Add ability to save current CLI settings to a config file and reload them later.

Users experimenting with different settings need to remember what worked. Currently they must manually track CLI flags. This feature lets them save successful configurations and replay them.

**Value**: Users can save working configurations, share them with others, and reproduce exact results.

**Target Users**: Anyone running multiple experiments or sharing configurations

---

## Acceptance Criteria

- [x] `--save-config FILE` saves all current settings to YAML file
- [x] `--config FILE` loads settings from file (already exists, enhance it)
- [x] Saved config includes all detection parameters and palette settings
- [x] Config file is human-readable YAML with comments
- [x] Config can be edited manually and reloaded
- [x] Settings from CLI override settings from config file

---

## Implementation Plan

### Overview

Add `--save-config` flag that writes current effective settings to a YAML file. Enhance existing `--config` loading to handle all new flags.

### Implementation Steps

1. **Add `--save-config` CLI flag**:
   ```python
   @click.option('--save-config', type=click.Path(), help='Save current settings to config file')
   ```

2. **Create config serialization**:
   ```python
   def save_config(filepath, settings):
       config = {
           'detection': {
               'min_radius': settings['min_radius'],
               'max_radius': settings['max_radius'],
               'sensitivity': settings['sensitivity'],
               'convex_edge': settings['convex_edge'],
               'palette': settings['palette'],
           },
           'output': {
               'format': settings['format'],
               'extract': str(settings['extract']) if settings['extract'] else None,
           }
       }
       with open(filepath, 'w') as f:
           yaml.dump(config, f, default_flow_style=False)
   ```

3. **Update config_loader.py**:
   - Add support for all new flags (convex_edge, palette, etc.)
   - Add comments to saved config explaining each option

4. **Auto-save config with runs**:
   - When `--extract` is used, optionally save config to run directory
   - Add `--auto-save-config` flag to enable this

### Example Config File

```yaml
# DotMatrix configuration
# Generated: 2025-11-25 14:30:22

detection:
  convex_edge: true
  palette: cmyk
  min_radius: 80
  max_radius: 350
  sensitivity: normal

output:
  format: json
  extract: output/
```

---

## Testing Strategy

### Unit Tests

- [x] Test config serialization includes all settings
- [x] Test config deserialization loads all settings
- [x] Test CLI overrides config file values
- [x] Test config file is valid YAML

### Integration Tests

- [x] Test save config then load produces same results
- [x] Test manual config edit works correctly
