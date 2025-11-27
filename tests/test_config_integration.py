"""Integration tests for config save/load via CLI."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml


# Path to test image
TEST_IMAGE = Path(__file__).parent.parent / "test_dotmatrix.png"


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestSaveConfigCLI:
    """Integration tests for --save-config flag."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_save_config_creates_file(self, temp_output_dir):
        """Test that --save-config creates a config file."""
        config_path = temp_output_dir / "my_config.yaml"

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--save-config", str(config_path)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert config_path.exists(), "Config file not created"

        # Verify it's valid YAML
        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config is not None

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_save_config_contains_settings(self, temp_output_dir):
        """Test that saved config contains the specified settings."""
        config_path = temp_output_dir / "config.yaml"

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "rgb",
                "--min-radius", "100",
                "--sensitivity", "relaxed",
                "--save-config", str(config_path)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        with open(config_path) as f:
            content = f.read()

        # Check key settings are in the file
        assert "convex_edge" in content
        assert "min_radius" in content
        assert "100" in content
        assert "relaxed" in content

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_save_config_json_format(self, temp_output_dir):
        """Test that --save-config works with JSON extension."""
        config_path = temp_output_dir / "config.json"

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--min-radius", "50",
                "--save-config", str(config_path)
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert config_path.exists()

        # Verify it's valid JSON
        with open(config_path) as f:
            config = json.load(f)

        assert 'detection' in config


class TestLoadSavedConfig:
    """Integration tests for loading saved configs."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_load_saved_config_produces_same_results(self, temp_output_dir):
        """Test that loading a saved config produces the same results."""
        config_path = temp_output_dir / "config.yaml"
        output1 = temp_output_dir / "output1"
        output2 = temp_output_dir / "output2"

        # Run 1: Save config and extract
        result1 = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--convex-edge",
                "--palette", "cmyk",
                "--min-radius", "80",
                "--output-dir", str(output1),
                "--no-organize",
                "--save-config", str(config_path)
            ],
            capture_output=True,
            text=True
        )
        assert result1.returncode == 0

        # Run 2: Load config and extract
        result2 = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--config", str(config_path),
                "--output-dir", str(output2),
                "--no-organize"
            ],
            capture_output=True,
            text=True
        )
        assert result2.returncode == 0

        # Both should produce same number of files
        files1 = list(output1.glob("*.png"))
        files2 = list(output2.glob("*.png"))

        assert len(files1) == len(files2), f"File count mismatch: {len(files1)} vs {len(files2)}"

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_cli_overrides_config(self, temp_output_dir):
        """Test that CLI args override config file values."""
        config_path = temp_output_dir / "config.yaml"

        # Create config with min_radius=80
        config_content = """
detection:
  min_radius: 80
  convex_edge: true
  palette: "cmyk"
"""
        with open(config_path, 'w') as f:
            f.write(config_content)

        # Run with --min-radius 150 (should override config)
        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--config", str(config_path),
                "--min-radius", "150",  # Override config
                "--format", "json",
                "--no-extract"  # JSON to stdout
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # All circles should have radius >= 150
        circles = json.loads(result.stdout)
        for circle in circles:
            assert circle['radius'] >= 150, f"Found circle with radius {circle['radius']} < 150"


class TestManualConfigEdit:
    """Tests for manually created/edited config files."""

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_manually_created_config(self, temp_output_dir):
        """Test that manually created config files work."""
        config_path = temp_output_dir / "manual.yaml"

        # Create a manual config file
        config_content = """
# My custom configuration
detection:
  convex_edge: true
  palette: "cmyk"
  min_radius: 80
  max_radius: 350

output:
  format: "json"
"""
        with open(config_path, 'w') as f:
            f.write(config_content)

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--config", str(config_path),
                "--no-extract"  # JSON to stdout
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        circles = json.loads(result.stdout)
        assert len(circles) == 16  # Expected for test image with these settings

    @pytest.mark.skipif(not TEST_IMAGE.exists(), reason="Test image not found")
    def test_flat_config_format(self, temp_output_dir):
        """Test that flat (non-nested) config format works."""
        config_path = temp_output_dir / "flat.yaml"

        # Create flat config (not nested by category)
        config_content = """
convex_edge: true
palette: "cmyk"
min_radius: 80
format: "json"
"""
        with open(config_path, 'w') as f:
            f.write(config_content)

        result = subprocess.run(
            [
                "python3", "-m", "dotmatrix",
                "-i", str(TEST_IMAGE),
                "--config", str(config_path),
                "--no-extract"  # JSON to stdout
            ],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        circles = json.loads(result.stdout)
        assert len(circles) == 16
