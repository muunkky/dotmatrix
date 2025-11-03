"""Tests for image_loader module."""

import pytest
import numpy as np
from pathlib import Path
from PIL import Image
import tempfile

from dotmatrix.image_loader import load_image, ImageLoadError, ImageFormatError


class TestImageLoader:
    """Test image loading and validation."""

    @pytest.fixture
    def temp_png_image(self):
        """Create a temporary PNG image for testing."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (100, 100), color='red')
            img.save(f.name)
            yield Path(f.name)
            Path(f.name).unlink()

    @pytest.fixture
    def temp_jpg_image(self):
        """Create a temporary JPG image for testing."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(f.name)
            yield Path(f.name)
            Path(f.name).unlink()

    @pytest.fixture
    def temp_invalid_file(self):
        """Create a temporary text file pretending to be an image."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'This is not an image')
            yield Path(f.name)
            Path(f.name).unlink()

    def test_load_valid_png(self, temp_png_image):
        """Test loading a valid PNG image."""
        image = load_image(temp_png_image)

        # Should return numpy array
        assert isinstance(image, np.ndarray)

        # Should have correct shape (height, width, channels)
        assert len(image.shape) == 3
        assert image.shape[2] == 3  # BGR format

        # Should have correct dimensions
        assert image.shape[0] == 100
        assert image.shape[1] == 100

    def test_load_valid_jpg(self, temp_jpg_image):
        """Test loading a valid JPG image."""
        image = load_image(temp_jpg_image)

        assert isinstance(image, np.ndarray)
        assert len(image.shape) == 3
        assert image.shape[2] == 3

    def test_load_nonexistent_file(self):
        """Test error handling for non-existent file."""
        with pytest.raises(ImageLoadError) as exc_info:
            load_image(Path('/nonexistent/path/image.png'))

        assert 'does not exist' in str(exc_info.value).lower()

    def test_load_invalid_format(self):
        """Test error handling for unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as f:
            path = Path(f.name)

        try:
            with pytest.raises(ImageFormatError) as exc_info:
                load_image(path)

            assert 'format' in str(exc_info.value).lower()
        finally:
            path.unlink()

    def test_load_corrupted_image(self, temp_invalid_file):
        """Test error handling for corrupted image file."""
        with pytest.raises(ImageLoadError) as exc_info:
            load_image(temp_invalid_file)

        assert 'load' in str(exc_info.value).lower() or 'invalid' in str(exc_info.value).lower()

    def test_returns_bgr_format(self, temp_png_image):
        """Test that image is returned in BGR format (OpenCV standard)."""
        # Create a red image
        img = Image.new('RGB', (10, 10), color=(255, 0, 0))
        img.save(temp_png_image)

        image = load_image(temp_png_image)

        # In BGR format, red image should have high values in B channel (index 2)
        # This test verifies the color channel order
        mean_b = np.mean(image[:, :, 0])  # Blue channel
        mean_g = np.mean(image[:, :, 1])  # Green channel
        mean_r = np.mean(image[:, :, 2])  # Red channel

        # For a red image in BGR format, R channel should be highest
        assert mean_r > mean_b
        assert mean_r > mean_g

    def test_load_with_string_path(self, temp_png_image):
        """Test loading with string path instead of Path object."""
        image = load_image(str(temp_png_image))
        assert isinstance(image, np.ndarray)

    def test_image_data_range(self, temp_png_image):
        """Test that pixel values are in expected range (0-255)."""
        image = load_image(temp_png_image)

        assert image.min() >= 0
        assert image.max() <= 255
        assert image.dtype == np.uint8
