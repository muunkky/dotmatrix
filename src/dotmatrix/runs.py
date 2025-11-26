"""Run discovery and management for DotMatrix."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .manifest import read_manifest, get_manifest_summary


def find_runs(base_dir: Path) -> List[Path]:
    """Find all run directories containing manifest.json files.

    Args:
        base_dir: Base output directory to search

    Returns:
        List of paths to directories containing manifest.json
    """
    if not base_dir.exists():
        return []

    runs = []
    # Look for manifest.json in immediate subdirectories
    for subdir in base_dir.iterdir():
        if subdir.is_dir():
            manifest_path = subdir / "manifest.json"
            if manifest_path.exists():
                runs.append(subdir)

    # Sort by modification time, most recent first
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs


def get_run_info(run_dir: Path) -> Optional[Dict[str, Any]]:
    """Get summary information about a run.

    Args:
        run_dir: Path to run directory

    Returns:
        Dictionary with run info, or None if manifest missing/invalid
    """
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return None

    try:
        manifest = read_manifest(manifest_path)
    except Exception:
        return None

    # Extract key info
    timestamp_str = manifest.get("timestamp", "")
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        date_str = timestamp.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        date_str = timestamp_str[:16] if timestamp_str else "Unknown"

    source_file = manifest.get("source_file", {})
    source_name = source_file.get("name", "Unknown") if isinstance(source_file, dict) else str(source_file)

    results = manifest.get("results", {})
    total_circles = results.get("total_circles", 0)

    return {
        "name": run_dir.name,
        "path": run_dir,
        "date": date_str,
        "timestamp": timestamp_str,
        "source": source_name,
        "circles": total_circles,
        "manifest": manifest,
    }


def list_runs(
    base_dir: Path,
    source_filter: Optional[str] = None,
    after_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List runs with optional filtering.

    Args:
        base_dir: Base output directory to search
        source_filter: Filter by source filename (substring match)
        after_date: Filter runs after this date (YYYY-MM-DD format)

    Returns:
        List of run info dictionaries
    """
    runs = find_runs(base_dir)
    results = []

    # Parse after_date if provided
    filter_date = None
    if after_date:
        try:
            filter_date = datetime.strptime(after_date, "%Y-%m-%d")
        except ValueError:
            pass  # Invalid date format, skip filter

    for run_dir in runs:
        info = get_run_info(run_dir)
        if info is None:
            continue

        # Apply source filter
        if source_filter:
            if source_filter.lower() not in info["source"].lower():
                continue

        # Apply date filter
        if filter_date:
            try:
                run_date = datetime.fromisoformat(info["timestamp"])
                if run_date < filter_date:
                    continue
            except (ValueError, TypeError):
                continue

        results.append(info)

    return results


def find_run_by_name(base_dir: Path, run_name: str) -> Optional[Path]:
    """Find a run directory by name.

    Args:
        base_dir: Base output directory
        run_name: Run name (directory name) to find

    Returns:
        Path to run directory if found, None otherwise
    """
    run_dir = base_dir / run_name
    if run_dir.is_dir() and (run_dir / "manifest.json").exists():
        return run_dir
    return None


def get_replay_settings(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Extract settings from manifest for replay.

    Args:
        manifest: Manifest dictionary

    Returns:
        Dictionary of settings suitable for CLI replay
    """
    settings = manifest.get("settings", {})
    source_file = manifest.get("source_file", {})

    # Build replay config
    replay = {
        "source": source_file.get("path") if isinstance(source_file, dict) else str(source_file),
    }

    # Copy all settings that have values
    for key, value in settings.items():
        if value is not None:
            replay[key] = value

    return replay


def format_runs_table(runs: List[Dict[str, Any]], verbose: bool = False) -> str:
    """Format runs as a table for display.

    Args:
        runs: List of run info dictionaries
        verbose: Include more columns if True

    Returns:
        Formatted table string
    """
    if not runs:
        return "No runs found."

    # Column widths
    name_width = max(len(r["name"]) for r in runs)
    name_width = max(name_width, 4)  # Minimum "NAME"
    name_width = min(name_width, 40)  # Maximum

    source_width = max(len(r["source"]) for r in runs)
    source_width = max(source_width, 6)  # Minimum "SOURCE"
    source_width = min(source_width, 30)  # Maximum

    # Header
    header = f"{'NAME':<{name_width}}  {'DATE':<16}  {'SOURCE':<{source_width}}  {'CIRCLES':>7}"
    separator = "-" * len(header)

    lines = [header, separator]

    for run in runs:
        name = run["name"][:name_width]
        date = run["date"][:16]
        source = run["source"][:source_width]
        circles = run["circles"]

        line = f"{name:<{name_width}}  {date:<16}  {source:<{source_width}}  {circles:>7}"
        lines.append(line)

    return "\n".join(lines)
