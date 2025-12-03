

# Make --blend-overlaps Consistent

## Idea
The `--blend-overlaps` flag behavior is inconsistent:
- For flower renderer: required to enable GPU
- For sliding-window: GPU auto-enables without it

Should be consistent - either always require it or never require it for GPU.

## Notes
Confusing UX when GPU requires different flags in different modes.