"""Run manifest generator for DotMatrix."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from . import __version__


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file.

    Args:
        filepath: Path to the file

    Returns:
        Hex-encoded SHA256 hash prefixed with 'sha256:'
    """
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def count_circles_by_color(
    results: List[Tuple[Any, Tuple[int, int, int]]],
    color_names: Optional[Dict[Tuple[int, int, int], str]] = None
) -> Dict[str, int]:
    """Count detected circles grouped by color.

    Args:
        results: List of (circle, color) tuples
        color_names: Optional mapping of RGB tuples to color names

    Returns:
        Dictionary of color (name or RGB) to count
    """
    counts: Dict[str, int] = {}

    for _, color in results:
        if color_names and color in color_names:
            color_key = color_names[color]
        else:
            color_key = f"rgb({color[0]},{color[1]},{color[2]})"

        counts[color_key] = counts.get(color_key, 0) + 1

    return counts


def generate_manifest(
    source_file: Path,
    settings: Dict[str, Any],
    results: List[Tuple[Any, Tuple[int, int, int]]],
    output_files: List[Path],
    color_names: Optional[Dict[Tuple[int, int, int], str]] = None,
) -> Dict[str, Any]:
    """Generate a manifest dictionary for a detection run.

    Args:
        source_file: Path to the source image
        settings: Dictionary of detection settings used
        results: List of (circle, color) detection results
        output_files: List of generated output file paths
        color_names: Optional mapping of RGB tuples to color names

    Returns:
        Manifest dictionary ready to be serialized to JSON
    """
    # Count circles by color
    circles_by_color = count_circles_by_color(results, color_names)

    manifest = {
        "dotmatrix_version": __version__,
        "timestamp": datetime.now().isoformat(),
        "source_file": {
            "path": str(source_file.resolve()),
            "name": source_file.name,
            "hash": compute_file_hash(source_file),
        },
        "settings": _clean_settings(settings),
        "results": {
            "total_circles": len(results),
            "circles_by_color": circles_by_color,
        },
        "output_files": [f.name for f in output_files],
    }

    return manifest


def _clean_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Clean settings for manifest - convert Paths to strings, remove None values."""
    cleaned = {}
    for key, value in settings.items():
        if value is None:
            continue
        if isinstance(value, Path):
            cleaned[key] = str(value)
        else:
            cleaned[key] = value
    return cleaned


def write_manifest(
    run_dir: Path,
    manifest: Dict[str, Any],
    filename: str = "manifest.json"
) -> Path:
    """Write manifest to a JSON file in the run directory.

    Args:
        run_dir: Directory to write manifest to
        manifest: Manifest dictionary
        filename: Name of the manifest file

    Returns:
        Path to the written manifest file
    """
    manifest_path = run_dir / filename

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2, default=str)

    return manifest_path


def read_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Read a manifest file.

    Args:
        manifest_path: Path to manifest.json

    Returns:
        Parsed manifest dictionary

    Raises:
        FileNotFoundError: If manifest doesn't exist
        json.JSONDecodeError: If manifest is invalid JSON
    """
    with open(manifest_path, 'r') as f:
        return json.load(f)


def get_manifest_summary(manifest: Dict[str, Any]) -> str:
    """Generate a human-readable summary of a manifest.

    Args:
        manifest: Manifest dictionary

    Returns:
        Formatted summary string
    """
    lines = [
        f"Source: {manifest['source_file']['name']}",
        f"Date: {manifest['timestamp'][:19].replace('T', ' ')}",
        f"Circles: {manifest['results']['total_circles']}",
    ]

    # Add color breakdown
    by_color = manifest['results'].get('circles_by_color', {})
    if by_color:
        color_str = ", ".join(f"{name}={count}" for name, count in by_color.items())
        lines.append(f"By color: {color_str}")

    return "\n".join(lines)
