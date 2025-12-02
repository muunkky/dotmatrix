## Description

Add real-time progress output during long-running rendering operations so users know what's happening.

Currently, after detection completes and rendering starts (`[192/192] Rendering 15722 clusters...`), there's no further output. The process appears frozen for minutes with no indication of:
- Whether GPU is being used
- Current progress (clusters rendered / total)
- Estimated time remaining
- Whether the process is stuck or working

**Value**: Eliminates user anxiety about hung processes, enables informed decisions about whether to wait or cancel, helps debug performance issues.

**Target Users**: Anyone running large image processing, developers debugging performance.

**Estimated Effort**: 2-4 hours

---

## Acceptance Criteria

- [ ] Show GPU/CPU status at render start: "Rendering with GPU (CUDA)" or "Rendering with CPU"
- [ ] Show progress during flower rendering: "Rendered 1000/15722 clusters (6%)"
- [ ] Update progress every N clusters or every few seconds (not per-cluster spam)
- [ ] Show elapsed time and estimated remaining time
- [ ] Show throughput: "~150 clusters/sec"
- [ ] Works with both single-image and sliding-window modes

---

## Implementation Plan

### Overview

Add a progress callback to the flower renderer that reports status at intervals. Display GPU detection status before rendering starts. Use stderr for progress to not pollute stdout output.

### Implementation Steps

1. **Add GPU status output at render start**:
   ```python
   if use_gpu:
       click.echo(f"Rendering {len(clusters)} clusters with GPU (CUDA)...", err=True)
   else:
       click.echo(f"Rendering {len(clusters)} clusters with CPU...", err=True)
   ```

2. **Add progress callback to render functions**:
   - Add `progress_callback: Optional[Callable[[int, int, float], None]]` parameter
   - Call every 100 clusters or 2 seconds (whichever comes first)
   - Callback receives: (clusters_done, clusters_total, elapsed_seconds)

3. **Implement CLI progress display**:
   ```python
   def render_progress(done, total, elapsed):
       pct = 100 * done / total
       rate = done / elapsed if elapsed > 0 else 0
       eta = (total - done) / rate if rate > 0 else 0
       click.echo(f"\r  Rendered {done}/{total} ({pct:.0f}%) - {rate:.0f}/sec - ETA {eta:.0f}s", err=True, nl=False)
   ```

4. **Add to both CPU and GPU renderers**:
   - `render_flower_global_blend()` in circle_renderer.py
   - `render_flower_global_blend_gpu()` in gpu_renderer.py
   - `process_sliding_window()` in sliding_window.py

### Technical Considerations

- **Performance**: Progress checks should be lightweight (~1μs per cluster)
- **Output**: Use `\r` carriage return for updating same line, stderr to not pollute JSON output
- **Frequency**: Every 100 clusters or 2 seconds, whichever is less frequent
- **Thread safety**: GPU progress may need atomic counter if parallelized

---

## Related Cards (optional)

**Related**: p7f44i - Improve CLI logging (this is a specific instance of that broader need)
**Related**: 6mv3po - Make --blend-overlaps consistent (GPU status output helps debug this)
