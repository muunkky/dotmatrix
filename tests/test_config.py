"""Tests for DetectionConfig dataclass."""

import pytest
from pathlib import Path

from dotmatrix.config import (
    DetectionConfig,
    DetectionParams,
    DetectionMethodParams,
    ColorParams,
    EdgeSamplingParams,
    OutputParams,
    PerformanceParams,
    CalibrationParams,
)


class TestDetectionParams:
    """Test DetectionParams dataclass."""

    def test_defaults(self):
        """Test default values."""
        params = DetectionParams()
        assert params.min_radius == 10
        assert params.max_radius == 500
        assert params.min_distance == 20
        assert params.sensitivity == 'normal'
        assert params.min_confidence is None

    def test_custom_values(self):
        """Test custom values."""
        params = DetectionParams(
            min_radius=15,
            max_radius=100,
            min_distance=30,
            sensitivity='strict',
            min_confidence=80,
        )
        assert params.min_radius == 15
        assert params.max_radius == 100
        assert params.min_distance == 30
        assert params.sensitivity == 'strict'
        assert params.min_confidence == 80


class TestDetectionMethodParams:
    """Test DetectionMethodParams dataclass."""

    def test_defaults(self):
        """Test default values (all False)."""
        params = DetectionMethodParams()
        assert params.convex_edge is False
        assert params.color_separation is False
        assert params.use_histogram is False
        assert params.sensitive_occlusion is False
        assert params.morph_enhance is False

    def test_halftone_settings(self):
        """Test typical halftone detection settings."""
        params = DetectionMethodParams(
            convex_edge=True,
            sensitive_occlusion=True,
            morph_enhance=True,
        )
        assert params.convex_edge is True
        assert params.sensitive_occlusion is True
        assert params.morph_enhance is True


class TestColorParams:
    """Test ColorParams dataclass."""

    def test_defaults(self):
        """Test default values."""
        params = ColorParams()
        assert params.palette == 'cmyk'
        assert params.num_colors == 6
        assert params.color_tolerance == 20
        assert params.max_colors is None
        assert params.exclude_background is False

    def test_cmyk_sep_settings(self):
        """Test typical CMYK separation settings."""
        params = ColorParams(
            palette='cmyk-sep',
            exclude_background=True,
        )
        assert params.palette == 'cmyk-sep'
        assert params.exclude_background is True


class TestEdgeSamplingParams:
    """Test EdgeSamplingParams dataclass."""

    def test_defaults(self):
        """Test default values."""
        params = EdgeSamplingParams()
        assert params.enabled is False
        assert params.samples == 36
        assert params.method == 'circumference'

    def test_enabled_with_custom_method(self):
        """Test enabled edge sampling with custom method."""
        params = EdgeSamplingParams(
            enabled=True,
            samples=48,
            method='canny',
        )
        assert params.enabled is True
        assert params.samples == 48
        assert params.method == 'canny'


class TestOutputParams:
    """Test OutputParams dataclass."""

    def test_defaults(self):
        """Test default values."""
        params = OutputParams()
        assert params.format == 'json'
        assert params.output_path is None
        assert params.extract_dir is None
        assert params.run_name is None
        assert params.no_organize is False
        assert params.no_manifest is False

    def test_extraction_settings(self):
        """Test typical extraction settings."""
        params = OutputParams(
            format='json',
            extract_dir=Path('output'),
            run_name='test-run',
        )
        assert params.extract_dir == Path('output')
        assert params.run_name == 'test-run'


class TestDetectionConfig:
    """Test main DetectionConfig dataclass."""

    def test_defaults(self):
        """Test default configuration."""
        config = DetectionConfig()
        assert config.input_path is None
        assert config.config_file is None
        assert config.mode is None
        assert config.debug is False
        assert isinstance(config.detection, DetectionParams)
        assert isinstance(config.methods, DetectionMethodParams)
        assert isinstance(config.color, ColorParams)
        assert isinstance(config.edge_sampling, EdgeSamplingParams)
        assert isinstance(config.output, OutputParams)
        assert isinstance(config.performance, PerformanceParams)
        assert isinstance(config.calibration, CalibrationParams)

    def test_nested_access(self):
        """Test accessing nested parameters."""
        config = DetectionConfig(
            detection=DetectionParams(min_radius=20),
            color=ColorParams(palette='cmyk-sep'),
        )
        assert config.detection.min_radius == 20
        assert config.color.palette == 'cmyk-sep'

    def test_from_cli_args(self):
        """Test creating config from CLI arguments."""
        config = DetectionConfig.from_cli_args(
            input=Path('test.png'),
            config=None,
            mode='halftone',
            debug=True,
            min_radius=15,
            max_radius=100,
            min_distance=25,
            sensitivity='normal',
            min_confidence=None,
            convex_edge=True,
            color_separation=False,
            use_histogram=False,
            sensitive_occlusion=True,
            morph_enhance=True,
            palette='cmyk',
            num_colors=6,
            color_tolerance=20,
            max_colors=None,
            exclude_background=False,
            edge_sampling=False,
            edge_samples=36,
            edge_method='circumference',
            format='json',
            output=None,
            extract=Path('output'),
            run_name='test',
            no_organize=False,
            no_manifest=False,
            quantize_output=None,
            save_config=None,
            chunk_size='auto',
            auto_calibrate=False,
            calibrate_from=None,
        )

        assert config.input_path == Path('test.png')
        assert config.mode == 'halftone'
        assert config.debug is True
        assert config.detection.min_radius == 15
        assert config.detection.max_radius == 100
        assert config.methods.convex_edge is True
        assert config.methods.sensitive_occlusion is True
        assert config.color.palette == 'cmyk'
        assert config.output.extract_dir == Path('output')

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = DetectionConfig(
            input_path=Path('test.png'),
            detection=DetectionParams(min_radius=20),
        )
        d = config.to_dict()

        assert d['input_path'] == 'test.png'
        assert d['detection']['min_radius'] == 20
        assert d['detection']['max_radius'] == 500  # default

    def test_to_dict_none_paths(self):
        """Test serialization handles None paths."""
        config = DetectionConfig()
        d = config.to_dict()

        assert d['input_path'] is None
        assert d['output']['output_path'] is None
        assert d['output']['extract_dir'] is None
