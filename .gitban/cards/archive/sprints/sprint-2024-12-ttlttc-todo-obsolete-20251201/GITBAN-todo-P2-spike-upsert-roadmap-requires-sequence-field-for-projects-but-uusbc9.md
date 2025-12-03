# Feedback: upsert_roadmap sequence field requirement

## Problem Statement

When using `upsert_roadmap` to create projects, the `sequence` field is required but this is not documented in the tool description or easily discoverable.

## Steps to Reproduce

1. Call upsert_roadmap with scope="project" 
2. Provide content without `sequence` field:
```python
upsert_roadmap(
    content={"id": "my-project", "title": "My Project", "status": "todo"},
    scope="project",
    version_id="v1",
    milestone_id="m1", 
    feature_id="my-feature",
    project_id="my-project"
)
```

## Actual Result

Error: `"Missing required field for project: sequence"`

## Expected Result

Either:
1. Auto-generate sequence number (append to end = max sequence + 1)
2. Document required fields clearly in tool description
3. Provide example in tool description showing all required fields

## Impact

- Medium friction for AI agents using the tool
- Multiple trial-and-error iterations to discover requirements
- Tool description says nothing about required fields per scope

## Suggested Improvements

1. Add required fields documentation per scope level
2. Consider auto-generating sequence when not provided (same as position="end" behavior)
3. Better error messages with examples of correct usage

## Environment

- gitban-mcp version: unknown
- Context: Creating GPU sprint roadmap projects

## Research Question

How can tool discoverability be improved for complex schema requirements?

## Time Box

N/A - feedback submission

## Success Criteria

- [ ] Feedback received by gitban team

## Acceptance Criteria

- [ ] Feedback submitted successfully

## Test Plan

N/A - feedback card

## Context

When creating a sprint roadmap for GPU acceleration work, I needed to add projects under features. The upsert_roadmap tool required a `sequence` field that was not documented in the tool description. This caused multiple failed attempts before discovering the requirement through error messages.

The same session also encountered issues with:
1. features array being rejected when creating milestones (had to use empty {} object workaround)  
2. Priority values P0/P1 rejected (had to use critical/high)

These are separate issues but contribute to overall roadmap tool usability friction.