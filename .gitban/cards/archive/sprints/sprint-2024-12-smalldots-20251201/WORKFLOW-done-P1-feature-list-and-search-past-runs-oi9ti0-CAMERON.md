## Description

Add CLI commands to list and search through past runs based on their manifests.

When users have many run directories, they need to find specific runs by source file, date, settings, or results. This feature provides CLI commands to query past runs.

**Value**: Users can quickly find previous runs without manually browsing directories.

**Target Users**: Anyone with multiple saved runs who needs to find specific results

---

## Acceptance Criteria

- [x] `dotmatrix runs list` shows all runs in output directory
- [x] `dotmatrix runs list --source FILE` filters by source image
- [x] `dotmatrix runs list --after DATE` filters by date
- [x] `dotmatrix runs show RUN_NAME` displays full manifest
- [x] `dotmatrix runs replay RUN_NAME` re-runs with same settings
- [x] Output includes run name, date, source file, circle count

---

## Implementation Plan

### Overview

Add a `runs` subcommand group with list, show, and replay commands that operate on manifest files in the output directory.

### Implementation Steps

1. **Add Click command group**:
   ```python
   @click.group()
   def runs():
       '''Manage and query past runs'''
       pass
   
   @runs.command()
   @click.option('--source', help='Filter by source file')
   @click.option('--after', help='Filter runs after date')
   def list(source, after):
       '''List all runs'''
       pass
   ```

2. **Implement runs list**:
   - Scan output directory for manifest.json files
   - Parse each manifest
   - Apply filters (source, date)
   - Display table of results

3. **Implement runs show**:
   - Load specific manifest by run name
   - Pretty-print all metadata

4. **Implement runs replay**:
   - Load manifest settings
   - Construct CLI command
   - Execute with same parameters

### Example Output

```
$ dotmatrix runs list
NAME                    DATE        SOURCE              CIRCLES
run_20251125_143022     Nov 25      test_dotmatrix.png  16
my-cmyk-test            Nov 25      halftone.png        24
rgb-experiment          Nov 24      logo.png            8

$ dotmatrix runs show my-cmyk-test
Run: my-cmyk-test
Date: 2025-11-25 14:30:22
Source: halftone.png
Settings:
  convex_edge: true
  palette: cmyk
  min_radius: 80
Results:
  Total circles: 24
  By color: black=6, cyan=6, magenta=6, yellow=6
```

---

## Testing Strategy

### Unit Tests

- [x] Test manifest scanning finds all runs
- [x] Test source filter works correctly
- [x] Test date filter works correctly
- [x] Test replay constructs correct command

### Integration Tests

- [x] Test list command shows created runs
- [x] Test show command displays manifest
- [x] Test replay produces same results
