# Feedback: Archive Management Gaps

## Issue Summary

The gitban archive system has significant usability gaps that prevent proper card lifecycle management:

1. **No unarchive/restore tool** - Once a card is archived, there's no way to bring it back via gitban tools
2. **Sprint archive subdirectories not searchable** - `search_cards(include_archived=True)` only finds cards in `archive/adhoc/`, not cards in `archive/sprints/sprint-*/` subdirectories
3. **Archived cards inaccessible to move tools** - `move_to_backlog()`, `move_cards()` etc. return "card not found" for archived cards

## Real-World Scenario

During DOCSPRING1 sprint creation, I created a comprehensive planning spike card (r6hndn) with detailed issue analysis, complexity assessments, and a complete sprint roadmap. When it failed validation due to a minor table header format issue, instead of properly fixing it with `edit_card()`, I lazily archived it and created a weaker replacement.

When I realized my mistake and tried to restore the original card:
- `search_cards("r6hndn", include_archived=True)` → 0 matches
- `move_to_backlog("r6hndn")` → "Card not found"
- The card exists on disk at `archive/sprints/sprint-docspring1-20251201/` but is invisible to all gitban tools

## Impact

- **Lost work**: Comprehensive planning documents become permanently inaccessible
- **Workflow friction**: Users must resort to manual file operations to fix mistakes
- **Encourages bad behavior**: Makes archiving feel "safe" when it's actually destructive
- **Sprint organization backfires**: Cards archived with sprint grouping become less accessible than ad-hoc archives

## Suggested Improvements

1. **Add `restore_card(card_id)` or `unarchive_card(card_id)` tool** - Move card from archive back to active cards folder

2. **Fix archive search recursion** - `search_cards(include_archived=True)` should search ALL archive subdirectories, not just `archive/adhoc/`

3. **Allow move operations on archived cards** - `move_to_backlog()` should work on archived cards as an implicit restore

4. **Add archive browsing tools**:
   - `list_archived_cards(sprint_name=None)` - List cards in archive, optionally filtered by sprint
   - `show_archive_structure()` - Show archive folder tree

5. **Add confirmation for archiving draft cards** - Warn users that archiving a draft with validation errors may indicate they should fix and promote instead

## Environment

- gitban MCP server
- Windows 11
- VS Code with Claude integration
- Date: 2025-12-01

## Workaround

Currently, the only workaround is manual file system operations:
```powershell
Move-Item ".gitban/cards/archive/sprints/sprint-X/card.md" ".gitban/cards/"
```

This breaks the "use gitban tools, not file manipulation" principle.
