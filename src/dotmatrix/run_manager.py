"""Run management for DotMatrix - organized output directories."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """Sanitize a string for use as a directory/file name.

    Args:
        name: The name to sanitize
        max_length: Maximum length for the result

    Returns:
        Filesystem-safe string
    """
    # Replace spaces with underscores
    sanitized = name.replace(' ', '_')

    # Remove or replace special characters
    # Allow only alphanumeric, underscore, hyphen, and dot
    sanitized = re.sub(r'[^\w\-.]', '', sanitized)

    # Remove consecutive underscores/hyphens
    sanitized = re.sub(r'[-_]+', '_', sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_-.')

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_-.')

    # Ensure we have something
    if not sanitized:
        sanitized = "unnamed"

    return sanitized


def generate_timestamp() -> str:
    """Generate a timestamp string for run naming.

    Returns:
        Timestamp in format YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def create_run_directory(
    base_dir: Path,
    run_name: Optional[str] = None,
    organize: bool = True
) -> Path:
    """Create an organized run directory for output files.

    Args:
        base_dir: Base output directory (e.g., from --extract)
        run_name: Optional custom name for this run
        organize: If True, create timestamped subdirectory. If False, use base_dir directly.

    Returns:
        Path to the directory where output files should be written
    """
    base_dir = Path(base_dir)

    if not organize:
        # Flat output - use base_dir directly
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    # Create organized subdirectory
    if run_name:
        # Use custom name with timestamp suffix for uniqueness
        safe_name = sanitize_filename(run_name)
        subdir_name = f"{safe_name}_{generate_timestamp()}"
    else:
        # Default: just timestamp
        subdir_name = f"run_{generate_timestamp()}"

    run_dir = base_dir / subdir_name
    run_dir.mkdir(parents=True, exist_ok=True)

    return run_dir


def get_run_info(run_dir: Path) -> dict:
    """Get information about a run directory.

    Args:
        run_dir: Path to a run directory

    Returns:
        Dictionary with run information
    """
    return {
        'path': str(run_dir),
        'name': run_dir.name,
        'created': datetime.fromtimestamp(run_dir.stat().st_ctime).isoformat(),
    }
