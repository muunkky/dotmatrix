# Documentation Card

## Overview

Create comprehensive configuration reference documentation for all dotmatrix CLI options, configuration files, and environment settings.

**Documentation Type:** Reference
**Target Audience:** Users, Developers
**Estimated Effort:** 1 day

## Scope

### What Will Be Documented

* [ ] All CLI options with descriptions and examples
* [ ] Configuration file format (JSON configs in configs/)
* [ ] Environment variables that affect behavior
* [ ] Default values and valid ranges for all options
* [ ] Option interactions and dependencies
* [ ] Preset configurations for common use cases

### Success Criteria

| Criterion | How to Verify |
| :--- | :--- |
| All CLI options documented | Cross-reference with argparse definitions in cli.py |
| Examples provided | Each major option has at least one example |
| Config file format documented | JSON schema or detailed format spec |
| Defaults listed | All default values documented |

### Dependencies

| Dependency | Status | Blocker? |
| :--- | :--- | :---: |
| Architecture Deep Dive spike (4ftn9c) | Must be complete | Yes |
| cli.py option analysis | Included in spike | No |

## Implementation Plan

### Tasks

* [ ] Extract all argparse options from cli.py
* [ ] Categorize options by function (input, output, processing, GPU, etc.)
* [ ] Document each option with: name, type, default, description, example
* [ ] Document configuration file format from configs/README.md
* [ ] Add cross-references to related options
* [ ] Create common configuration presets section
* [ ] Add troubleshooting section for configuration issues

### Documentation Structure

```
docs/configuration-reference.md
├── CLI Options
│   ├── Input Options
│   ├── Output Options
│   ├── Processing Options
│   ├── GPU Options
│   └── Advanced Options
├── Configuration Files
│   ├── JSON Format
│   └── Example Configs
├── Environment Variables
├── Presets
└── Troubleshooting
```

## Notes

This is a P2 card - important for comprehensive documentation but not required for initial handoff. The Architecture Deep Dive spike will provide most of the information needed. This card is about organizing that information into a user-friendly reference format.

Consider auto-generating portions from argparse help text.
