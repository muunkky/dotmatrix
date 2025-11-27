"""Tests for image_extractor module."""

import pytest
from pathlib import Path
import tempfile
from PIL import Image

from dotmatrix.circle_detector import Circle
from dotmatrix.image_extractor import (
    group_circles_by_color,
    extract_circles_to_images,
    generate_cmyk_layer_files,
    get_cmyk_layer_name,
)


class TestGroupCirclesByColor:
    """Test color grouping functionality."""

    def test_group_identical_colors(self):
        """Test grouping circles with identical colors."""
        circles = [
            (Circle(100, 100, 50), (255, 0, 0)),
            (Circle(200, 200, 50), (255, 0, 0)),
            (Circle(300, 300, 50), (255, 0, 0)),
        ]

        groups = group_circles_by_color(circles, tolerance=20)

        # Should all be in one group
        assert len(groups) == 1
        assert len(list(groups.values())[0]) == 3

    def test_group_similar_colors(self):
        """Test grouping circles with similar colors."""
        circles = [
            (Circle(100, 100, 50), (255, 0, 0)),
            (Circle(200, 200, 50), (250, 5, 5)),  # Similar red
            (Circle(300, 300, 50), (245, 10, 10)),  # Similar red
        ]

        groups = group_circles_by_color(circles, tolerance=20)

        # Should all be in one group (within tolerance)
        assert len(groups) == 1

    def test_group_different_colors(self):
        """Test grouping circles with different colors."""
        circles = [
            (Circle(100, 100, 50), (255, 0, 0)),    # Red
            (Circle(200, 200, 50), (0, 255, 0)),    # Green
            (Circle(300, 300, 50), (0, 0, 255)),    # Blue
        ]

        groups = group_circles_by_color(circles, tolerance=20)

        # Should be in three separate groups
        assert len(groups) == 3

    def test_empty_list(self):
        """Test with empty circle list."""
        groups = group_circles_by_color([], tolerance=20)
        assert len(groups) == 0

    def test_single_circle(self):
        """Test with single circle."""
        circles = [(Circle(100, 100, 50), (255, 0, 0))]
        groups = group_circles_by_color(circles, tolerance=20)

        assert len(groups) == 1
        assert len(list(groups.values())[0]) == 1

    def test_tolerance_zero_exact_match(self):
        """Test tolerance=0 requires exact color match."""
        circles = [
            (Circle(100, 100, 50), (255, 0, 0)),
            (Circle(200, 200, 50), (255, 0, 0)),  # Exact match
            (Circle(300, 300, 50), (254, 0, 0)),  # Off by 1 - different group
        ]

        groups = group_circles_by_color(circles, tolerance=0)

        # Should be in two groups (exact match only)
        assert len(groups) == 2

    def test_tolerance_high_loose_grouping(self):
        """Test high tolerance groups more loosely."""
        circles = [
            (Circle(100, 100, 50), (255, 0, 0)),      # Red
            (Circle(200, 200, 50), (200, 50, 50)),    # Pinkish red
            (Circle(300, 300, 50), (180, 100, 100)),  # Very light red
        ]

        # Low tolerance: should separate
        groups_strict = group_circles_by_color(circles, tolerance=10)
        assert len(groups_strict) >= 2

        # High tolerance: should group together
        groups_loose = group_circles_by_color(circles, tolerance=50)
        assert len(groups_loose) <= 2


class TestExtractCirclesToImages:
    """Test circle extraction to PNG images."""

    def test_extract_single_color(self):
        """Test extracting circles of single color."""
        with tempfile.TemporaryDirectory() as tmpdir:
            circles = [
                (Circle(100, 100, 50), (255, 0, 0)),
                (Circle(200, 200, 50), (255, 0, 0)),
            ]

            paths = extract_circles_to_images(
                circles,
                image_shape=(400, 400),
                output_dir=Path(tmpdir)
            )

            # Should create one file
            assert len(paths) == 1
            assert paths[0].exists()
            assert paths[0].suffix == '.png'
            assert 'circles_color_255_000_000' in paths[0].name

    def test_extract_multiple_colors(self):
        """Test extracting circles of multiple colors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            circles = [
                (Circle(100, 100, 50), (255, 0, 0)),    # Red
                (Circle(200, 200, 50), (0, 255, 0)),    # Green
                (Circle(300, 300, 50), (0, 0, 255)),    # Blue
            ]

            paths = extract_circles_to_images(
                circles,
                image_shape=(400, 400),
                output_dir=Path(tmpdir)
            )

            # Should create three files
            assert len(paths) == 3
            for path in paths:
                assert path.exists()
                assert path.suffix == '.png'

    def test_transparent_background(self):
        """Test that generated images have transparent backgrounds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            circles = [(Circle(100, 100, 50), (255, 0, 0))]

            paths = extract_circles_to_images(
                circles,
                image_shape=(200, 200),
                output_dir=Path(tmpdir)
            )

            # Load image and check it has alpha channel
            img = Image.open(paths[0])
            assert img.mode == 'RGBA'

            # Check that corners are transparent
            pixels = img.load()
            # Top-left corner should be transparent
            assert pixels[0, 0][3] == 0  # Alpha = 0 (transparent)

    def test_circle_color_correct(self):
        """Test that circles are drawn with correct colors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            red_circle = Circle(100, 100, 30)
            circles = [(red_circle, (255, 0, 0))]

            paths = extract_circles_to_images(
                circles,
                image_shape=(200, 200),
                output_dir=Path(tmpdir)
            )

            # Load image and check center pixel color
            img = Image.open(paths[0])
            pixels = img.load()

            # Center of circle should be red
            center_color = pixels[100, 100]
            assert center_color[0] == 255  # Red channel
            assert center_color[1] == 0    # Green channel
            assert center_color[2] == 0    # Blue channel
            assert center_color[3] == 255  # Fully opaque

    def test_custom_prefix(self):
        """Test custom filename prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            circles = [(Circle(100, 100, 50), (255, 0, 0))]

            paths = extract_circles_to_images(
                circles,
                image_shape=(200, 200),
                output_dir=Path(tmpdir),
                prefix="extracted"
            )

            assert 'extracted_color' in paths[0].name

    def test_output_dir_created(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "output"
            circles = [(Circle(100, 100, 50), (255, 0, 0))]

            paths = extract_circles_to_images(
                circles,
                image_shape=(200, 200),
                output_dir=output_dir
            )

            assert output_dir.exists()
            assert paths[0].exists()

    def test_multiple_circles_same_image(self):
        """Test that multiple circles of same color appear in one image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            circles = [
                (Circle(50, 50, 20), (255, 0, 0)),
                (Circle(150, 150, 20), (255, 0, 0)),
            ]

            paths = extract_circles_to_images(
                circles,
                image_shape=(200, 200),
                output_dir=Path(tmpdir)
            )

            # Should create one file with both circles
            assert len(paths) == 1

            img = Image.open(paths[0])
            pixels = img.load()

            # Both circle centers should be red
            assert pixels[50, 50][0] == 255  # First circle
            assert pixels[150, 150][0] == 255  # Second circle

    def test_empty_circles_list(self):
        """Test with empty circles list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = extract_circles_to_images(
                [],
                image_shape=(200, 200),
                output_dir=Path(tmpdir)
            )

            assert len(paths) == 0

    def test_max_colors_kmeans_clustering(self):
        """Test k-means clustering with max_colors parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 10 circles with different colors
            circles = [
                (Circle(100, 100, 50), (255, 0, 0)),    # Red
                (Circle(120, 100, 50), (250, 5, 5)),    # Similar red
                (Circle(150, 100, 50), (0, 255, 0)),    # Green
                (Circle(180, 100, 50), (5, 250, 10)),   # Similar green
                (Circle(200, 100, 50), (0, 0, 255)),    # Blue
                (Circle(220, 100, 50), (10, 10, 250)),  # Similar blue
                (Circle(250, 100, 50), (255, 255, 0)),  # Yellow
                (Circle(270, 100, 50), (250, 250, 10)), # Similar yellow
                (Circle(290, 100, 50), (255, 0, 255)),  # Magenta
                (Circle(310, 100, 50), (250, 10, 250)), # Similar magenta
            ]
            image_shape = (400, 400)

            # Cluster to 4 colors using k-means
            files = extract_circles_to_images(
                circles, image_shape, Path(tmpdir), max_colors=4
            )

            # Should create exactly 4 files (not 10)
            assert len(files) == 4

            # All files should exist
            for f in files:
                assert f.exists()

    def test_max_colors_overrides_tolerance(self):
        """Test that max_colors overrides tolerance parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            circles = [
                (Circle(100, 100, 50), (255, 0, 0)),
                (Circle(150, 100, 50), (254, 0, 0)),  # Very similar
                (Circle(200, 100, 50), (0, 255, 0)),
                (Circle(250, 100, 50), (0, 254, 0)),  # Very similar
            ]
            image_shape = (300, 300)

            # With max_colors=4, we get up to 4 groups
            files_kmeans = extract_circles_to_images(
                circles, image_shape, Path(tmpdir), max_colors=4
            )

            # K-means should create at most 4 groups (likely 2-4 since 4 unique colors)
            assert len(files_kmeans) <= 4
            assert len(files_kmeans) >= 1


class TestCMYKLayerNameMapping:
    """Test CMYK color to layer name mapping."""

    def test_cyan_detection(self):
        """Test cyan color detection."""
        assert get_cmyk_layer_name((0, 255, 255)) == 'cyan'
        assert get_cmyk_layer_name((0, 200, 200)) == 'cyan'

    def test_magenta_detection(self):
        """Test magenta color detection."""
        assert get_cmyk_layer_name((255, 0, 255)) == 'magenta'
        assert get_cmyk_layer_name((200, 0, 200)) == 'magenta'

    def test_yellow_detection(self):
        """Test yellow color detection."""
        assert get_cmyk_layer_name((255, 255, 0)) == 'yellow'
        assert get_cmyk_layer_name((200, 200, 0)) == 'yellow'

    def test_black_detection(self):
        """Test black color detection."""
        assert get_cmyk_layer_name((0, 0, 0)) == 'black'
        assert get_cmyk_layer_name((30, 30, 30)) == 'black'

    def test_non_cmyk_returns_none(self):
        """Test that non-CMYK colors return None."""
        assert get_cmyk_layer_name((255, 0, 0)) is None  # Red
        assert get_cmyk_layer_name((0, 255, 0)) is None  # Green
        assert get_cmyk_layer_name((0, 0, 255)) is None  # Blue


class TestGenerateCMYKLayerFiles:
    """Test CMYK layer file generation."""

    def test_generates_layer_files(self):
        """Test that layer files are generated with correct names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            circles = [
                (Circle(100, 100, 50), (0, 255, 255)),    # Cyan
                (Circle(200, 100, 50), (255, 0, 255)),    # Magenta
                (Circle(100, 200, 50), (255, 255, 0)),    # Yellow
                (Circle(200, 200, 50), (0, 0, 0)),        # Black
            ]

            layer_files = generate_cmyk_layer_files(
                circles,
                image_shape=(300, 300),
                output_dir=Path(tmpdir)
            )

            # Should create 4 layer files
            assert len(layer_files) == 4
            assert 'cyan' in layer_files
            assert 'magenta' in layer_files
            assert 'yellow' in layer_files
            assert 'black' in layer_files

            # Each file should exist with correct name
            for name, path in layer_files.items():
                assert path.exists()
                assert path.name == f"{name}.png"

    def test_partial_cmyk(self):
        """Test with only some CMYK colors present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            circles = [
                (Circle(100, 100, 50), (0, 255, 255)),    # Cyan
                (Circle(200, 100, 50), (255, 255, 0)),    # Yellow
            ]

            layer_files = generate_cmyk_layer_files(
                circles,
                image_shape=(300, 300),
                output_dir=Path(tmpdir)
            )

            # Should only create 2 layer files
            assert len(layer_files) == 2
            assert 'cyan' in layer_files
            assert 'yellow' in layer_files
            assert 'magenta' not in layer_files
            assert 'black' not in layer_files

    def test_multiple_circles_per_layer(self):
        """Test multiple circles of same color in one layer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            circles = [
                (Circle(50, 50, 20), (0, 255, 255)),    # Cyan
                (Circle(100, 50, 20), (0, 255, 255)),   # Cyan
                (Circle(150, 50, 20), (0, 255, 255)),   # Cyan
            ]

            layer_files = generate_cmyk_layer_files(
                circles,
                image_shape=(200, 200),
                output_dir=Path(tmpdir)
            )

            # Should create 1 layer file with all circles
            assert len(layer_files) == 1
            assert 'cyan' in layer_files

            # Load image and verify circles are present
            img = Image.open(layer_files['cyan'])
            pixels = img.load()

            # Check each circle center is filled
            assert pixels[50, 50][3] == 255  # First circle opaque
            assert pixels[100, 50][3] == 255  # Second circle opaque
            assert pixels[150, 50][3] == 255  # Third circle opaque

    def test_transparent_background(self):
        """Test that layer images have transparent backgrounds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            circles = [(Circle(100, 100, 30), (0, 255, 255))]  # Cyan

            layer_files = generate_cmyk_layer_files(
                circles,
                image_shape=(200, 200),
                output_dir=Path(tmpdir)
            )

            img = Image.open(layer_files['cyan'])
            assert img.mode == 'RGBA'

            pixels = img.load()
            # Corner should be transparent
            assert pixels[0, 0][3] == 0

    def test_empty_circles_list(self):
        """Test with empty circles list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            layer_files = generate_cmyk_layer_files(
                [],
                image_shape=(200, 200),
                output_dir=Path(tmpdir)
            )

            assert len(layer_files) == 0
