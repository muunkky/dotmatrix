"""Configuration file loader for DotMatrix."""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


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
