"""Tests for color_extractor module."""

import pytest
import numpy as np
from PIL import Image, ImageDraw
import tempfile
from pathlib import Path

from dotmatrix.image_loader import load_image
from dotmatrix.circle_detector import Circle
from dotmatrix.color_extractor import extract_color


class TestExtractColor:
    """Test color extraction from circles."""

    def test_extract_solid_color(self):
        """Test extracting color from a solid color circle."""
        # Create a red circle on white background
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([25, 25, 75, 75], fill='red', outline='red')

        # Save and load as BGR
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        # Circle at center (50, 50) with radius 25
        circle = Circle(center_x=50, center_y=50, radius=25)

        color = extract_color(image, circle)

        # Should be close to red (255, 0, 0)
        assert isinstance(color, tuple)
        assert len(color) == 3

        # Red channel should be dominant
        r, g, b = color
        assert r > 200  # Strong red
        assert g < 50   # Minimal green
        assert b < 50   # Minimal blue

    def test_extract_blue_color(self):
        """Test extracting blue color."""
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([25, 25, 75, 75], fill='blue', outline='blue')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        circle = Circle(center_x=50, center_y=50, radius=25)
        color = extract_color(image, circle)

        r, g, b = color
        assert b > 200  # Strong blue
        assert r < 50
        assert g < 50

    def test_extract_green_color(self):
        """Test extracting green color."""
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([25, 25, 75, 75], fill='green', outline='green')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        circle = Circle(center_x=50, center_y=50, radius=25)
        color = extract_color(image, circle)

        r, g, b = color
        assert g > 100  # Strong green
        # Note: 'green' in PIL is (0, 128, 0), not pure green

    def test_color_values_in_range(self):
        """Test that color values are in valid range 0-255."""
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([25, 25, 75, 75], fill='purple', outline='purple')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        circle = Circle(center_x=50, center_y=50, radius=25)
        color = extract_color(image, circle)

        r, g, b = color
        assert 0 <= r <= 255
        assert 0 <= g <= 255
        assert 0 <= b <= 255

        # Should be integers
        assert isinstance(r, int)
        assert isinstance(g, int)
        assert isinstance(b, int)

    def test_circle_at_edge(self):
        """Test extracting color from circle at image edge."""
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        # Circle near edge
        draw.ellipse([0, 0, 40, 40], fill='red', outline='red')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        circle = Circle(center_x=20, center_y=20, radius=20)
        color = extract_color(image, circle)

        # Should still work, extracting partial circle
        assert color is not None
        assert len(color) == 3

    def test_small_circle(self):
        """Test extracting color from very small circle."""
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([45, 45, 55, 55], fill='red', outline='red')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        circle = Circle(center_x=50, center_y=50, radius=5)
        color = extract_color(image, circle)

        # Should work even for small circles
        assert color is not None
        r, g, b = color
        assert r > 100  # Should detect reddish color

    def test_color_accuracy_tolerance(self, test_image_single_circle):
        """Test color extraction accuracy against ground truth."""
        image_path, ground_truth = test_image_single_circle
        image = load_image(image_path)

        expected = ground_truth[0]
        circle = Circle(
            center_x=expected['center'][0],
            center_y=expected['center'][1],
            radius=expected['radius']
        )

        color = extract_color(image, circle)

        expected_color = expected['color']

        # Each channel should be within 10% tolerance
        for i, (actual, expect) in enumerate(zip(color, expected_color)):
            tolerance = max(expect * 0.1, 25)  # At least 25 for low values
            assert abs(actual - expect) <= tolerance, \
                f"Channel {i}: expected {expect}, got {actual}"

    def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        # Create a valid image
        img = Image.new('RGB', (100, 100), color='white')
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        # Invalid circle (negative radius)
        with pytest.raises(ValueError):
            circle = Circle(center_x=50, center_y=50, radius=-10)
            extract_color(image, circle)

        # Empty image
        with pytest.raises(ValueError):
            extract_color(np.array([]), Circle(50, 50, 10))


class TestEdgeSampling:
    """Test edge-based color sampling for overlapping circles."""

    def test_edge_sampling_parameter_exists(self):
        """Test that extract_color accepts use_edge_sampling parameter."""
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([25, 25, 75, 75], fill='red', outline='red')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        circle = Circle(center_x=50, center_y=50, radius=25)

        # Should accept use_edge_sampling parameter without error
        color = extract_color(image, circle, use_edge_sampling=True)
        assert isinstance(color, tuple)
        assert len(color) == 3

    def test_edge_sampling_num_samples_parameter(self):
        """Test that extract_color accepts num_samples parameter."""
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([25, 25, 75, 75], fill='blue', outline='blue')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        circle = Circle(center_x=50, center_y=50, radius=25)

        # Should accept num_samples parameter
        color = extract_color(image, circle, use_edge_sampling=True, num_samples=36)
        assert isinstance(color, tuple)
        assert len(color) == 3

    def test_edge_sampling_differs_from_area_sampling(self):
        """Test that edge sampling gives different results than area sampling for overlapping circles."""
        # Create image with blue circle partially covered by black circle
        img = Image.new('RGB', (200, 200), color='white')
        draw = ImageDraw.Draw(img)

        # Draw blue circle
        draw.ellipse([50, 50, 150, 150], fill='blue', outline='blue')

        # Draw black circle overlapping the blue one
        draw.ellipse([75, 75, 175, 175], fill='black', outline='black')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        # Test the blue circle (partially covered by black)
        blue_circle = Circle(center_x=100, center_y=100, radius=50)

        # Area sampling should include lots of black pixels
        area_color = extract_color(image, blue_circle, use_edge_sampling=False)

        # Edge sampling should detect more blue at the exposed edges
        edge_color = extract_color(image, blue_circle, use_edge_sampling=True)

        # Edge sampling should have more blue than area sampling
        # (blue channel should be higher, or red/green should be lower)
        # Area sampling will have averaged in black pixels
        assert edge_color != area_color, "Edge and area sampling should give different results"

    def test_edge_sampling_with_solid_circle(self):
        """Test that edge sampling works correctly on a solid color circle."""
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([25, 25, 75, 75], fill='green', outline='green')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        circle = Circle(center_x=50, center_y=50, radius=25)

        # Edge sampling should still work on solid circles
        color = extract_color(image, circle, use_edge_sampling=True)

        r, g, b = color
        # Should detect green
        assert g > 100

    def test_edge_sampling_default_is_false(self):
        """Test that use_edge_sampling defaults to False (area sampling)."""
        img = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([25, 25, 75, 75], fill='red', outline='red')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            image = load_image(f.name)
            Path(f.name).unlink()

        circle = Circle(center_x=50, center_y=50, radius=25)

        # Default behavior (no parameter)
        default_color = extract_color(image, circle)

        # Explicit False
        area_color = extract_color(image, circle, use_edge_sampling=False)

        # Should be the same
        assert default_color == area_color
