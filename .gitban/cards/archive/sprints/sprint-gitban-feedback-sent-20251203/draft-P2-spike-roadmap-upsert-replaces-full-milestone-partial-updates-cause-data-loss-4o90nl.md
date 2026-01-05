# Roadmap Upsert Behavior Causes Accidental Data Loss

## Description
`upsert_roadmap(scope="milestone")` requires a full milestone payload. Partial updates are rejected with sequential "Missing required field" errors. Supplying a minimal payload that includes `features: {}` succeeds but replaces the entire `features` subtree, erasing existing content.

## Context
I attempted to mark `v1 > m1` as done. Initially I tried a minimal payload with just `status: done` and the API returned validation errors requiring `title`, `description`, `success_criteria`, and finally `features`.

When I supplied `features: {}` to satisfy the schema, the call succeeded but wiped the original `features` content for the milestone (deep replace rather than merge).

## Expected Behavior
- Allow partial/patch semantics that merge into existing milestone content without requiring the full object, OR
- Require an explicit `replace=true` flag to perform destructive replacements, OR
- Provide a separate `patch_roadmap` endpoint that deep-merges without losing unspecified fields.

## Actual Behavior
- `upsert_roadmap` behaves like a full replace, not an upsert/merge.
- Required fields include `features`, so naïve updates require sending `features: {}` which deletes existing subtrees.

## Reproduction Steps
1. Read milestone:
   - `read_roadmap(scope="milestone", version_id="v1", milestone_id="m1")`
2. Try minimal update:
   - `upsert_roadmap(scope="milestone", version_id="v1", milestone_id="m1", content={"id":"m1","status":"done"})`
   - Error: Missing required field for milestone: title
3. Add title, description:
   - Error: Missing required field for milestone: success_criteria
4. Add success_criteria:
   - Error: Missing required field for milestone: features
5. Add `features: {}`:
   - Success, but milestone now has `features: {}` and all prior nested content is gone.

## Captured Errors
- `{"error_code":"MISSING_REQUIRED_FIELD","error":"Missing required field for milestone: title"}`
- `{"error_code":"MISSING_REQUIRED_FIELD","error":"Missing required field for milestone: description"}`
- `{"error_code":"MISSING_REQUIRED_FIELD","error":"Missing required field for milestone: success_criteria"}`
- `{"error_code":"MISSING_REQUIRED_FIELD","error":"Missing required field for milestone: features"}`

## Impact
- High risk of accidental data loss when performing small updates.
- Forces clients to reconstruct and resend the full milestone object for trivial changes (e.g., status), which is error-prone and heavy.

## Suggested Solutions
- Support deep-merge upserts (treat unspecified fields as unchanged).
- Add `mode` parameter: `mode="merge"|"replace"` with default `merge` for safety.
- Provide a dedicated `update_field` or `patch_roadmap` for targeted changes.
- If keeping replace semantics, require an explicit `allowDestructive=true` to accept `features: {}`.

## Workaround
- Read the full milestone, then re-upsert the complete object with only the desired fields changed (e.g., `status`). This avoids data loss but is cumbersome.

## Environment
- Date: 2025-12-02
- OS: Windows (PowerShell)
- Repo: muunkky/dotmatrix
- Actioned via Gitban MCP tools in VS Code

## Attachments
- Milestone path: `v1 > m1`
- Successful corrective upsert: re-sent the full original milestone content with `status: done` to restore features.
