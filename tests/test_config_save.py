"""Tests for config save functionality."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from dotmatrix.config_loader import (
    save_config,
    load_config,
    CONFIG_SCHEMA,
    _organize_config_by_category,
    _flatten_config,
)


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_yaml_creates_file(self):
        """Test that save_config creates a YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.yaml"
            settings = {'min_radius': 50, 'convex_edge': True}

            save_config(filepath, settings)

            assert filepath.exists()
            assert filepath.stat().st_size > 0

    def test_save_json_creates_file(self):
        """Test that save_config creates a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.json"
            settings = {'min_radius': 50, 'convex_edge': True}

            save_config(filepath, settings)

            assert filepath.exists()
            # Verify it's valid JSON
            with open(filepath) as f:
                data = json.load(f)
            assert 'detection' in data

    def test_save_invalid_extension_raises(self):
        """Test that invalid file extension raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.txt"

            with pytest.raises(ValueError, match="Unsupported config format"):
                save_config(filepath, {'min_radius': 50})

    def test_saved_yaml_is_valid(self):
        """Test that saved YAML is valid and parseable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.yaml"
            settings = {'min_radius': 50, 'convex_edge': True, 'palette': 'cmyk'}

            save_config(filepath, settings)

            # Should be parseable
            with open(filepath) as f:
                data = yaml.safe_load(f)

            assert data is not None

    def test_yaml_includes_comments(self):
        """Test that YAML includes descriptive comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.yaml"
            settings = {'min_radius': 50}

            save_config(filepath, settings, add_comments=True)

            with open(filepath) as f:
                content = f.read()

            assert "# DotMatrix Configuration" in content
            assert "# Generated:" in content

    def test_non_default_values_saved(self):
        """Test that non-default values are saved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.yaml"
            # min_radius default is 10, so 50 should be saved
            settings = {'min_radius': 50}

            save_config(filepath, settings, include_defaults=False)

            loaded = load_config(filepath)
            assert loaded['min_radius'] == 50

    def test_default_values_excluded_by_default(self):
        """Test that default values are excluded unless include_defaults=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.json"
            # min_radius default is 10
            settings = {'min_radius': 10, 'max_radius': 100}

            save_config(filepath, settings, include_defaults=False)

            with open(filepath) as f:
                data = json.load(f)

            # min_radius (default) should be excluded
            # max_radius (non-default) should be included
            detection = data.get('detection', {})
            assert 'min_radius' not in detection
            assert detection.get('max_radius') == 100

    def test_include_defaults_includes_all(self):
        """Test that include_defaults=True saves all settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.json"
            settings = {'min_radius': 10, 'max_radius': 500}  # Both defaults

            save_config(filepath, settings, include_defaults=True)

            with open(filepath) as f:
                data = json.load(f)

            detection = data.get('detection', {})
            assert detection.get('min_radius') == 10
            assert detection.get('max_radius') == 500


class TestLoadConfigNested:
    """Tests for loading nested (categorized) configs."""

    def test_load_nested_yaml(self):
        """Test that nested YAML config is flattened."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.yaml"

            # Write nested config
            nested = {
                'detection': {'min_radius': 50, 'convex_edge': True},
                'color': {'color_tolerance': 30},
                'output': {'format': 'csv'},
            }
            with open(filepath, 'w') as f:
                yaml.dump(nested, f)

            loaded = load_config(filepath)

            # Should be flattened
            assert loaded['min_radius'] == 50
            assert loaded['convex_edge'] is True
            assert loaded['color_tolerance'] == 30
            assert loaded['format'] == 'csv'

    def test_load_flat_yaml(self):
        """Test that flat YAML config still works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.yaml"

            flat = {'min_radius': 50, 'convex_edge': True}
            with open(filepath, 'w') as f:
                yaml.dump(flat, f)

            loaded = load_config(filepath)

            assert loaded['min_radius'] == 50
            assert loaded['convex_edge'] is True


class TestRoundTrip:
    """Tests for save then load (round-trip)."""

    def test_yaml_round_trip(self):
        """Test save then load produces same settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.yaml"

            # Use non-default values that will be saved
            original = {
                'min_radius': 80,  # Default is 10
                'max_radius': 350,  # Default is 500
                'convex_edge': True,  # Default is False
                'palette': 'rgb',  # Default is cmyk
                'sensitivity': 'relaxed',  # Default is normal
            }

            save_config(filepath, original)
            loaded = load_config(filepath)

            for key, value in original.items():
                assert loaded[key] == value, f"Mismatch for {key}"

    def test_json_round_trip(self):
        """Test save then load produces same settings (JSON)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.json"

            original = {
                'min_radius': 80,
                'convex_edge': True,
                'color_tolerance': 15,
            }

            save_config(filepath, original)
            loaded = load_config(filepath)

            for key, value in original.items():
                assert loaded[key] == value


class TestOrganizeConfig:
    """Tests for config organization helpers."""

    def test_organize_by_category(self):
        """Test flat config is organized by category."""
        flat = {
            'min_radius': 50,
            'color_tolerance': 30,
            'format': 'csv',
        }

        organized = _organize_config_by_category(flat)

        assert organized['detection']['min_radius'] == 50
        assert organized['color']['color_tolerance'] == 30
        assert organized['output']['format'] == 'csv'

    def test_flatten_config(self):
        """Test nested config is flattened."""
        nested = {
            'detection': {'min_radius': 50},
            'color': {'color_tolerance': 30},
            'output': {'format': 'csv'},
        }

        flat = _flatten_config(nested)

        assert flat['min_radius'] == 50
        assert flat['color_tolerance'] == 30
        assert flat['format'] == 'csv'

    def test_flatten_already_flat(self):
        """Test that already-flat config is unchanged."""
        flat = {'min_radius': 50, 'convex_edge': True}

        result = _flatten_config(flat)

        assert result == flat


class TestConfigSchema:
    """Tests for CONFIG_SCHEMA."""

    def test_all_categories_valid(self):
        """Test that all schema entries have valid categories."""
        valid_categories = {'detection', 'color', 'output'}

        for key, schema in CONFIG_SCHEMA.items():
            assert 'category' in schema, f"{key} missing category"
            assert schema['category'] in valid_categories, f"{key} has invalid category"

    def test_all_have_description(self):
        """Test that all schema entries have descriptions."""
        for key, schema in CONFIG_SCHEMA.items():
            assert 'description' in schema, f"{key} missing description"
            assert len(schema['description']) > 0, f"{key} has empty description"

    def test_all_have_default(self):
        """Test that all schema entries have default values."""
        for key, schema in CONFIG_SCHEMA.items():
            assert 'default' in schema, f"{key} missing default"
