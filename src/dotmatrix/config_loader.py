"""Configuration file loader and saver for DotMatrix."""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from JSON or YAML file.

    Args:
        config_path: Path to configuration file (.json or .yaml/.yml)

    Returns:
        Dictionary of configuration parameters

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If file format is not supported or invalid
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Determine file format
    suffix = config_path.suffix.lower()

    if suffix == '.json':
        with open(config_path, 'r') as f:
            config = json.load(f)
    elif suffix in ['.yaml', '.yml']:
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except ImportError:
            raise ValueError(
                "PyYAML is required for YAML configs. Install with: pip install pyyaml"
            )
    else:
        raise ValueError(
            f"Unsupported config format: {suffix}. Use .json, .yaml, or .yml"
        )

    # Validate config structure
    if not isinstance(config, dict):
        raise ValueError("Config file must contain a dictionary/object at root level")

    return config


def merge_config_with_cli_args(config: Dict[str, Any], cli_args: Dict[str, Any]) -> Dict[str, Any]:
    """Merge configuration file with CLI arguments.

    CLI arguments take precedence over config file values.

    Args:
        config: Configuration from file
        cli_args: Arguments from command line (only non-None values)

    Returns:
        Merged configuration dictionary
    """
    # Start with config file values
    merged = config.copy()

    # Override with CLI arguments (only if explicitly provided)
    for key, value in cli_args.items():
        if value is not None:
            merged[key] = value

    return merged


def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration parameters.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValueError: If configuration has invalid values
    """
    # Validate sensitivity
    if 'sensitivity' in config:
        valid_sensitivities = ['strict', 'normal', 'relaxed']
        if config['sensitivity'] not in valid_sensitivities:
            raise ValueError(
                f"Invalid sensitivity: {config['sensitivity']}. "
                f"Must be one of: {', '.join(valid_sensitivities)}"
            )

    # Validate edge_method
    if 'edge_method' in config:
        valid_methods = ['circumference', 'canny', 'exposed', 'band']
        if config['edge_method'] not in valid_methods:
            raise ValueError(
                f"Invalid edge_method: {config['edge_method']}. "
                f"Must be one of: {', '.join(valid_methods)}"
            )

    # Validate numeric ranges
    if 'min_radius' in config and config['min_radius'] < 0:
        raise ValueError("min_radius must be non-negative")

    if 'max_radius' in config and config['max_radius'] < 0:
        raise ValueError("max_radius must be non-negative")

    if 'min_distance' in config and config['min_distance'] < 0:
        raise ValueError("min_distance must be non-negative")

    if 'color_tolerance' in config:
        if not 0 <= config['color_tolerance'] <= 255:
            raise ValueError("color_tolerance must be between 0 and 255")

    if 'max_colors' in config and config['max_colors'] < 1:
        raise ValueError("max_colors must be positive")


# All configurable parameters with their defaults and descriptions
CONFIG_SCHEMA = {
    # Detection parameters
    'min_radius': {
        'default': 10,
        'type': int,
        'description': 'Minimum circle radius in pixels',
        'category': 'detection'
    },
    'max_radius': {
        'default': 500,
        'type': int,
        'description': 'Maximum circle radius in pixels',
        'category': 'detection'
    },
    'min_distance': {
        'default': 20,
        'type': int,
        'description': 'Minimum distance between circle centers',
        'category': 'detection'
    },
    'sensitivity': {
        'default': 'normal',
        'type': str,
        'description': 'Detection sensitivity: strict, normal, relaxed',
        'category': 'detection'
    },
    'min_confidence': {
        'default': None,
        'type': int,
        'description': 'Minimum confidence score (0-100)',
        'category': 'detection'
    },
    'convex_edge': {
        'default': False,
        'type': bool,
        'description': 'Use convex edge detection for overlapping circles',
        'category': 'detection'
    },
    'palette': {
        'default': 'cmyk',
        'type': str,
        'description': 'Color palette for convex-edge mode: cmyk, rgb, or custom RGB values',
        'category': 'detection'
    },
    # Color extraction parameters
    'color_tolerance': {
        'default': 20,
        'type': int,
        'description': 'RGB distance threshold for color grouping (0-100)',
        'category': 'color'
    },
    'max_colors': {
        'default': None,
        'type': int,
        'description': 'Maximum color groups using k-means clustering',
        'category': 'color'
    },
    'edge_sampling': {
        'default': False,
        'type': bool,
        'description': 'Use edge-based color sampling',
        'category': 'color'
    },
    'edge_samples': {
        'default': 36,
        'type': int,
        'description': 'Number of sample points around circle edge',
        'category': 'color'
    },
    'edge_method': {
        'default': 'circumference',
        'type': str,
        'description': 'Edge sampling method: circumference, canny, exposed, band',
        'category': 'color'
    },
    'exclude_background': {
        'default': False,
        'type': bool,
        'description': 'Exclude near-white background colors',
        'category': 'color'
    },
    'use_histogram': {
        'default': False,
        'type': bool,
        'description': 'Use histogram-based color palette extraction',
        'category': 'color'
    },
    # Output parameters
    'format': {
        'default': 'json',
        'type': str,
        'description': 'Output format: json or csv',
        'category': 'output'
    },
    'run_name': {
        'default': None,
        'type': str,
        'description': 'Custom name for this run',
        'category': 'output'
    },
    'no_organize': {
        'default': False,
        'type': bool,
        'description': 'Disable automatic subdirectory creation',
        'category': 'output'
    },
}


def save_config(
    filepath: Path,
    settings: Dict[str, Any],
    include_defaults: bool = False,
    add_comments: bool = True
) -> None:
    """Save configuration settings to a YAML or JSON file.

    Args:
        filepath: Path to save configuration to (.yaml, .yml, or .json)
        settings: Dictionary of settings to save
        include_defaults: If True, include settings that match defaults
        add_comments: If True, add descriptive comments (YAML only)

    Raises:
        ValueError: If file format is not supported
    """
    filepath = Path(filepath)
    suffix = filepath.suffix.lower()

    if suffix not in ['.yaml', '.yml', '.json']:
        raise ValueError(
            f"Unsupported config format: {suffix}. Use .yaml, .yml, or .json"
        )

    # Filter settings - only include non-default values unless requested
    config_to_save = {}
    for key, value in settings.items():
        if key not in CONFIG_SCHEMA:
            # Include unknown keys as-is
            config_to_save[key] = value
            continue

        schema = CONFIG_SCHEMA[key]
        default = schema['default']

        # Include if different from default or if include_defaults is True
        if include_defaults or value != default:
            if value is not None:  # Skip None values
                config_to_save[key] = value

    # Organize by category for readability
    organized = _organize_config_by_category(config_to_save)

    if suffix == '.json':
        with open(filepath, 'w') as f:
            json.dump(organized, f, indent=2, default=str)
    else:  # YAML
        if add_comments:
            content = _generate_yaml_with_comments(organized)
            with open(filepath, 'w') as f:
                f.write(content)
        else:
            with open(filepath, 'w') as f:
                yaml.dump(organized, f, default_flow_style=False, sort_keys=False)


def _organize_config_by_category(config: Dict[str, Any]) -> Dict[str, Any]:
    """Organize flat config into nested structure by category."""
    organized = {
        'detection': {},
        'color': {},
        'output': {},
    }

    for key, value in config.items():
        if key in CONFIG_SCHEMA:
            category = CONFIG_SCHEMA[key]['category']
            organized[category][key] = value
        else:
            # Unknown keys go to root
            organized[key] = value

    # Remove empty categories
    return {k: v for k, v in organized.items() if v}


def _flatten_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten nested config back to flat structure."""
    flat = {}

    for key, value in config.items():
        if isinstance(value, dict) and key in ['detection', 'color', 'output']:
            # Nested category - flatten it
            flat.update(value)
        else:
            flat[key] = value

    return flat


def _generate_yaml_with_comments(config: Dict[str, Any]) -> str:
    """Generate YAML content with descriptive comments."""
    lines = [
        "# DotMatrix Configuration",
        f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "#",
        "# Load with: dotmatrix --config this_file.yaml --input image.png",
        "",
    ]

    category_descriptions = {
        'detection': 'Circle Detection Settings',
        'color': 'Color Extraction Settings',
        'output': 'Output Settings',
    }

    for category, settings in config.items():
        if category in category_descriptions:
            lines.append(f"# {category_descriptions[category]}")
            lines.append(f"{category}:")

            for key, value in settings.items():
                # Add comment with description
                if key in CONFIG_SCHEMA:
                    desc = CONFIG_SCHEMA[key]['description']
                    lines.append(f"  # {desc}")

                # Format value
                if isinstance(value, bool):
                    lines.append(f"  {key}: {str(value).lower()}")
                elif isinstance(value, str):
                    lines.append(f"  {key}: \"{value}\"")
                elif value is None:
                    lines.append(f"  {key}: null")
                else:
                    lines.append(f"  {key}: {value}")

            lines.append("")
        else:
            # Non-category key at root level
            if isinstance(config[category], dict):
                lines.append(f"{category}:")
                for k, v in config[category].items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{category}: {config[category]}")

    return "\n".join(lines)


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from JSON or YAML file.

    Supports both flat and nested (categorized) config formats.
    Nested configs are flattened for use with CLI.

    Args:
        config_path: Path to configuration file (.json or .yaml/.yml)

    Returns:
        Dictionary of configuration parameters (flattened)

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If file format is not supported or invalid
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Determine file format
    suffix = config_path.suffix.lower()

    if suffix == '.json':
        with open(config_path, 'r') as f:
            config = json.load(f)
    elif suffix in ['.yaml', '.yml']:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        raise ValueError(
            f"Unsupported config format: {suffix}. Use .json, .yaml, or .yml"
        )

    # Validate config structure
    if not isinstance(config, dict):
        raise ValueError("Config file must contain a dictionary/object at root level")

    # Flatten nested config if needed
    config = _flatten_config(config)

    return config
