# Prototype: ASCII Output Mode

## Objective

Build working prototype of ASCII art output to validate character mapping, layout, and terminal compatibility before full implementation.

## Time Box

**Estimated effort**: 4-6 hours
**Deadline**: 2026-01-15

## Prototype Scope

Create minimal CLI flag `--format ascii` that outputs detected circles as ASCII art:
- Map circle size to character choice (blocks, outlines, shades)
- Handle terminal width constraints (default 80 columns)
- Support grayscale or ANSI color output

## Success Criteria

- [ ] Working `--format ascii` CLI flag
- [ ] Generated 5+ ASCII samples from test images
- [ ] Tested on multiple terminals (cmd, PowerShell, bash)
- [ ] Measured rendering quality vs. PNG output
- [ ] Technical decisions documented

## Deliverables

1. Prototype code (can be throwaway quality)
2. ASCII art samples (text files)
3. Terminal compatibility matrix
4. ADR documenting prototype learnings

## Dependencies

- Requires completion of "Research ASCII/Text-based cluster rendering" (wmhy58)