"""Pytest configuration and fixtures."""

import pytest
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
import tempfile
import json


@pytest.fixture
def test_image_single_circle():
    """Create a test image with a single red circle."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        # Create white background
        img = Image.new('RGB', (200, 200), color='white')
        draw = ImageDraw.Draw(img)

        # Draw a red circle at center (100, 100) with radius 40
        draw.ellipse([60, 60, 140, 140], fill='red', outline='red')

        img.save(f.name)

        # Ground truth data
        ground_truth = [
            {
                'center': [100, 100],
                'radius': 40,
                'color': [255, 0, 0]  # Red in RGB
            }
        ]

        yield Path(f.name), ground_truth
        Path(f.name).unlink()


@pytest.fixture
def test_image_multiple_circles():
    """Create a test image with multiple circles."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        # Create white background
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)

        # Red circle
        draw.ellipse([50, 50, 130, 130], fill='red', outline='red')

        # Blue circle
        draw.ellipse([200, 100, 300, 200], fill='blue', outline='blue')

        # Green circle
        draw.ellipse([280, 30, 360, 110], fill='green', outline='green')

        img.save(f.name)

        # Ground truth data
        ground_truth = [
            {'center': [90, 90], 'radius': 40, 'color': [255, 0, 0]},  # Red
            {'center': [250, 150], 'radius': 50, 'color': [0, 0, 255]},  # Blue
            {'center': [320, 70], 'radius': 40, 'color': [0, 128, 0]},  # Green
        ]

        yield Path(f.name), ground_truth
        Path(f.name).unlink()


@pytest.fixture
def test_image_no_circles():
    """Create a test image with no circles."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        # Just a white background
        img = Image.new('RGB', (200, 200), color='white')
        img.save(f.name)

        yield Path(f.name), []
        Path(f.name).unlink()


@pytest.fixture
def test_image_various_sizes():
    """Create a test image with circles of various sizes."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img = Image.new('RGB', (500, 400), color='white')
        draw = ImageDraw.Draw(img)

        # Small circle (radius ~15)
        draw.ellipse([50, 50, 80, 80], fill='red', outline='red')

        # Medium circle (radius ~50)
        draw.ellipse([150, 150, 250, 250], fill='blue', outline='blue')

        # Large circle (radius ~100)
        draw.ellipse([300, 100, 500, 300], fill='green', outline='green')

        img.save(f.name)

        ground_truth = [
            {'center': [65, 65], 'radius': 15, 'color': [255, 0, 0]},
            {'center': [200, 200], 'radius': 50, 'color': [0, 0, 255]},
            {'center': [400, 200], 'radius': 100, 'color': [0, 128, 0]},
        ]

        yield Path(f.name), ground_truth
        Path(f.name).unlink()
