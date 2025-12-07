"""
Tests for run directory management and organization.

Following TDD methodology for organized output directories feature.
Tests verify timestamped directory creation, custom run naming, and manifest generation.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dotmatrix.cli import cli


@pytest.fixture
def runner():
    """Create Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_image(tmp_path):
    """Create a minimal test image."""
    import numpy as np
    from PIL import Image
    
    # Create 100x100 white image with a black circle
    img = Image.new('RGB', (100, 100), color='white')
    img_array = np.array(img)
    
    # Draw a simple black circle in center
    center_x, center_y = 50, 50
    radius = 20
    for y in range(100):
        for x in range(100):
            if (x - center_x)**2 + (y - center_y)**2 <= radius**2:
                img_array[y, x] = [0, 0, 0]
    
    img = Image.fromarray(img_array)
    img_path = tmp_path / "test_input.png"
    img.save(img_path)
    return str(img_path)


class TestRunDirectoryCreation:
    """Test automated run directory creation with timestamps."""
    
    def test_creates_timestamped_run_directory(self, runner, sample_image, tmp_path):
        """Test that CLI creates output/run_YYYY-MM-DD_HHMMSS/ directory."""
        fixed_time = datetime(2025, 12, 6, 14, 30, 22)
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            with patch('dotmatrix.run_manager.datetime') as mock_datetime:
                mock_datetime.now.return_value = fixed_time
                
                result = runner.invoke(cli, ['-i', sample_image])
                
                # Should create timestamped directory
                expected_dir = Path('output') / 'run_2025-12-06_143022'
                assert expected_dir.exists(), f"Expected directory {expected_dir} was not created"
                assert expected_dir.is_dir()
    
    def test_default_behavior_without_run_name_flag(self, runner, sample_image, tmp_path):
        """Test default behavior creates timestamp-only directory."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['-i', sample_image])
            
            # Should have at least one run_* directory
            output_dir = Path('output')
            run_dirs = list(output_dir.glob('run_*'))
            assert len(run_dirs) >= 1, "No run directories created"
            
            # Verify timestamp format (run_YYYY-MM-DD_HHMMSS)
            run_dir_name = run_dirs[0].name
            assert run_dir_name.startswith('run_')
            timestamp_part = run_dir_name[4:]  # Remove 'run_' prefix
            
            # Should be parseable as datetime
            try:
                datetime.strptime(timestamp_part, '%Y-%m-%d_%H%M%S')
            except ValueError:
                pytest.fail(f"Directory name {run_dir_name} does not follow timestamp format")
    
    def test_outputs_placed_in_run_directory(self, runner, sample_image, tmp_path):
        """Test that all outputs (PNGs, JSON) are placed in run directory."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['-i', sample_image])
            
            output_dir = Path('output')
            run_dirs = list(output_dir.glob('run_*'))
            assert len(run_dirs) == 1
            
            run_dir = run_dirs[0]
            
            # Check for expected output files
            expected_files = [
                'composite.png',  # Composite visualization
                'results.json',   # Detection results
            ]
            
            for expected_file in expected_files:
                file_path = run_dir / expected_file
                assert file_path.exists(), f"Expected output file {expected_file} not found in {run_dir}"


class TestCustomRunNaming:
    """Test custom run name functionality."""
    
    def test_custom_run_name_appended_to_timestamp(self, runner, sample_image, tmp_path):
        """Test --run-name flag appends custom name to timestamp."""
        fixed_time = datetime(2025, 12, 6, 14, 30, 22)
        
        with runner.isolated_filesystem(temp_dir=tmp_path):
            with patch('dotmatrix.run_manager.datetime') as mock_datetime:
                mock_datetime.now.return_value = fixed_time
                
                result = runner.invoke(cli, [
                    '-i', sample_image,
                    '--run-name', 'calibration_test'
                ])
                
                expected_dir = Path('output') / 'run_2025-12-06_143022_calibration_test'
                assert expected_dir.exists(), f"Expected directory with custom name {expected_dir} was not created"
    
    def test_run_name_sanitization(self, runner, sample_image, tmp_path):
        """Test that run names with special characters are sanitized."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, [
                '-i', sample_image,
                '--run-name', 'test/with:special*chars'
            ])
            
            # Should sanitize to safe filename characters
            output_dir = Path('output')
            run_dirs = list(output_dir.glob('run_*'))
            assert len(run_dirs) == 1
            
            run_dir_name = run_dirs[0].name
            # Should not contain problematic characters
            problematic_chars = ['/', ':', '*', '?', '"', '<', '>', '|']
            for char in problematic_chars:
                assert char not in run_dir_name, f"Run directory name contains unsanitized character: {char}"
    
    def test_empty_run_name_ignored(self, runner, sample_image, tmp_path):
        """Test that empty --run-name is ignored and only timestamp is used."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, [
                '-i', sample_image,
                '--run-name', ''
            ])
            
            output_dir = Path('output')
            run_dirs = list(output_dir.glob('run_*'))
            assert len(run_dirs) == 1
            
            run_dir_name = run_dirs[0].name
            # Should not end with trailing underscore
            assert not run_dir_name.endswith('_'), "Empty run name left trailing underscore"


class TestRunManifest:
    """Test run manifest.json generation."""
    
    def test_manifest_created_in_run_directory(self, runner, sample_image, tmp_path):
        """Test that manifest.json is created in each run directory."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['-i', sample_image])
            
            output_dir = Path('output')
            run_dirs = list(output_dir.glob('run_*'))
            assert len(run_dirs) == 1
            
            manifest_path = run_dirs[0] / 'manifest.json'
            assert manifest_path.exists(), "manifest.json not found in run directory"
    
    def test_manifest_contains_required_metadata(self, runner, sample_image, tmp_path):
        """Test that manifest contains timestamp, input file, and CLI args."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, [
                '-i', sample_image,
                '--min-radius', '10',
                '--max-radius', '50'
            ])
            
            output_dir = Path('output')
            run_dirs = list(output_dir.glob('run_*'))
            manifest_path = run_dirs[0] / 'manifest.json'
            
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            # Verify required fields
            assert 'timestamp' in manifest, "manifest missing timestamp"
            assert 'input_file' in manifest, "manifest missing input_file"
            assert 'cli_args' in manifest, "manifest missing cli_args"
            
            # Verify CLI args captured
            assert '--min-radius' in str(manifest['cli_args'])
            assert '10' in str(manifest['cli_args'])
    
    def test_manifest_timestamp_format(self, runner, sample_image, tmp_path):
        """Test that manifest timestamp is ISO 8601 format."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['-i', sample_image])
            
            output_dir = Path('output')
            run_dirs = list(output_dir.glob('run_*'))
            manifest_path = run_dirs[0] / 'manifest.json'
            
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            # Should be parseable as ISO 8601
            try:
                datetime.fromisoformat(manifest['timestamp'])
            except ValueError:
                pytest.fail(f"Manifest timestamp {manifest['timestamp']} is not valid ISO 8601 format")


class TestBackwardCompatibility:
    """Test backward compatibility with existing behavior."""
    
    def test_explicit_output_dir_still_works(self, runner, sample_image, tmp_path):
        """Test that explicit --output-dir overrides run directory logic."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            custom_output = tmp_path / 'custom_output'
            result = runner.invoke(cli, [
                '-i', sample_image,
                '--output-dir', str(custom_output)
            ])
            
            # Should use custom directory directly, not create run_* subdirectory
            assert custom_output.exists()
            # Should not create run_* subdirectory inside custom_output
            run_dirs = list(custom_output.glob('run_*'))
            assert len(run_dirs) == 0, "Run directory created even with explicit --output-dir"
    
    def test_no_breaking_changes_to_cli_flags(self, runner, sample_image, tmp_path):
        """Test that all existing CLI flags still work."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Run with various existing flags
            result = runner.invoke(cli, [
                '-i', sample_image,
                '--min-radius', '5',
                '--max-radius', '30',
                '--palette', 'auto'
            ])
            
            # Should succeed without errors
            assert result.exit_code == 0, f"CLI failed with existing flags: {result.output}"
