# Bug Report: spike-planning template validation fails on its own required sections

## Summary

When using `create_card()` with `template='spike-planning'`, the card is created as draft with validation errors for sections that don't exist in the template itself.

## Steps to Reproduce

1. Call `list_templates()` to find `spike-planning` template
2. Call `read_template('spike-planning')` to see its structure
3. Create a card following the template structure exactly:
```python
create_card(
    title="My Planning Session",
    card_type="spike",
    template="spike-planning",
    content="... content following spike-planning template structure ..."
)
```
4. Card is created as `draft` status with validation errors

## Expected Behavior

Card should be created with `todo` or `backlog` status since content follows the template structure.

## Actual Behavior

Card is created as `draft` with validation errors:
- `missing_tables`: Looking for table header `Issue #|Issue Summary|Type (feature/bug/spike/chore/docs/refactor)|Complexity (small/medium/large)|Priority (P0/P1/P2)|Notes & Dependencies` - even when table exists with slightly different header format

## Additional Context

When I later tried creating a spike without specifying `template='spike-planning'`, it failed validation looking for `Research Question` and `Context` sections - which are from the base `spike.md` template, not `spike-planning.md`.

This suggests:
1. Template variant selection may not be working correctly
2. Validation is too strict on table header exact matching
3. The `parsed.sections` in template metadata doesn't match what validation expects

## Environment

- gitban MCP server
- Creating cards via Claude agent

## Suggested Fix

1. Template validation should use the actual template file's structure, not a hardcoded set of required sections
2. Table header matching should be more flexible (ignore extra spaces, allow column name variations)
3. When `template='spike-planning'` is specified, only validate against that template's requirements
