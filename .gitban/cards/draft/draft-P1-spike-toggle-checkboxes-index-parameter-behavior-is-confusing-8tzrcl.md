# Feedback: toggle_checkboxes index parameter behavior

## Issue Description

When using `toggle_checkboxes` with index-based checkbox selection, the behavior is confusing and can accidentally toggle the wrong checkboxes.

## What Happened

I had a card with 33 checkboxes across multiple sections. After toggling 23 by text match, I needed to toggle the remaining 10. Several of these had duplicate text (e.g., "Run tests" appeared 5 times in different sections).

When I tried to toggle by index within a section:
```python
toggle_checkboxes("nc3stt", [
    {"index": 0, "section": "Phase 2: Incremental Refactoring"},
    {"index": 1, "section": "Phase 2: Incremental Refactoring"},
    ...
])
```

The result was unexpected:
- Some checkboxes that were already checked got toggled OFF
- The index didn't seem to map to the unchecked items, but rather to ALL items in the section

## Expected Behavior

When specifying `{"index": N, "section": "..."}`, I expected:
1. Index N to refer to the Nth checkbox in that section (0-indexed)
2. OR index N to refer to the Nth UNCHECKED checkbox in that section

## Actual Behavior

The index appeared to match against ALL checkboxes in the section, not just unchecked ones. This caused already-checked items to be toggled back to unchecked.

## Workaround Used

Used `edit_card` with `replace_all=True` to change all `- [ ]` to `- [x]`:
```python
edit_card("nc3stt", "- [ ]", "- [x]", replace_all=True)
```

This worked but bypasses the checkbox validation logic.

## Suggestions

1. Make index-based selection only target unchecked checkboxes when toggling ON
2. Add clearer documentation about how indices work with sections
3. Consider adding an `only_unchecked=True` parameter for batch operations
4. The results message says "Toggled X in section: [x] → [x]" which is confusing - it shows the same state twice

## Context

- Card had many duplicate checkbox texts ("Run tests" x5)
- Using batch toggle with index is the only way to target specific duplicates
- Session was a continuation where I needed to mark all tasks complete before completing the card
