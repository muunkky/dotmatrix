# Spike: Roadmap Upsert Usability Issues

## Problem Statement
The `upsert_roadmap` tool requires all mandatory fields (like `title`) even when performing a partial update (e.g., changing `status`). This makes it difficult to use for quick status updates without first reading the full item to get its title.

## Observations
- Calling `upsert_roadmap` with just `id` and `status` fails with `MISSING_REQUIRED_FIELD` for `title`.
- This forces a read-modify-write cycle which consumes more tokens and is error-prone.

## Proposed Solution
- `upsert_roadmap` should support PATCH semantics: if `id` exists, update only provided fields.
- Validation should only check for required fields on *creation*, not *update*.

## Reproduction
```python
upsert_roadmap(
    content={"id": "v1", "status": "in_progress"},
    scope="version",
    version_id="v1"
)
# Fails with: Missing required field for version: title
```
