# upsert_roadmap validation error for nested milestone with features

## Bug Report

When using `upsert_roadmap()` to create a new milestone with nested features and projects, the validation fails with:

```
Schema validation failed: Invalid type for features: [...] is not of type 'object'
```

## Steps to Reproduce

1. Call `upsert_roadmap()` with `scope="milestone"` 
2. Include a `features` array in the content with nested `projects` arrays
3. Get validation error about features not being of type 'object'

## Expected Behavior

The roadmap schema should accept an array of features when upserting a milestone, as the roadmap structure is hierarchical:
- version → milestones (array)
- milestone → features (array)
- feature → projects (array)

## Actual Behavior

Validation fails claiming features must be type 'object' when it's actually a list of feature objects.

## Environment

- gitban-mcp version: latest
- Using MCP tools from Claude Code

## Suggested Fix

Check the JSON schema validation for upsert_roadmap - the `features` field at milestone level should accept an array of feature objects, not require a single object.

## Workaround

Create milestone first without features, then upsert features one-by-one, then upsert projects one-by-one. This is tedious but functional.
