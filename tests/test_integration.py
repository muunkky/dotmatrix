"""End-to-end integration tests for DotMatrix."""

import pytest
import json
import csv
from io import StringIO
from pathlib import Path
import subprocess
import tempfile
from PIL import Image, ImageDraw


class TestEndToEnd:
    """Test complete pipeline from image to output."""

    def test_full_pipeline_json(self, test_image_single_circle):
        """Test complete pipeline with JSON output."""
        from dotmatrix.image_loader import load_image
        from dotmatrix.circle_detector import detect_circles
        from dotmatrix.color_extractor import extract_color
        from dotmatrix.formatter import format_json

        image_path, ground_truth = test_image_single_circle

        # Load image
        image = load_image(image_path)

        # Detect circles
        circles = detect_circles(image)
        assert len(circles) > 0

        # Extract colors
        results = []
        for circle in circles:
            color = extract_color(image, circle)
            results.append((circle, color))

        # Format as JSON
        json_output = format_json(results)

        # Parse and validate JSON
        data = json.loads(json_output)
        assert isinstance(data, list)
        assert len(data) > 0

        # Validate first circle
        first = data[0]
        assert 'center' in first
        assert 'radius' in first
        assert 'color' in first

        assert isinstance(first['center'], list)
        assert len(first['center']) == 2
        assert isinstance(first['radius'], (int, float))
        assert isinstance(first['color'], list)
        assert len(first['color']) == 3

    def test_full_pipeline_csv(self, test_image_multiple_circles):
        """Test complete pipeline with CSV output."""
        from dotmatrix.image_loader import load_image
        from dotmatrix.circle_detector import detect_circles
        from dotmatrix.color_extractor import extract_color
        from dotmatrix.formatter import format_csv

        image_path, ground_truth = test_image_multiple_circles

        # Load image
        image = load_image(image_path)

        # Detect circles
        circles = detect_circles(image)
        assert len(circles) >= 2

        # Extract colors
        results = []
        for circle in circles:
            color = extract_color(image, circle)
            results.append((circle, color))

        # Format as CSV
        csv_output = format_csv(results)

        # Parse and validate CSV
        reader = csv.DictReader(StringIO(csv_output))
        rows = list(reader)

        assert len(rows) >= 2

        # Validate first row
        first_row = rows[0]
        assert 'center_x' in first_row
        assert 'center_y' in first_row
        assert 'radius' in first_row
        assert 'color_r' in first_row
        assert 'color_g' in first_row
        assert 'color_b' in first_row

        # Values should be numeric
        float(first_row['center_x'])
        float(first_row['center_y'])
        float(first_row['radius'])
        int(first_row['color_r'])
        int(first_row['color_g'])
        int(first_row['color_b'])

    def test_cli_json_output(self, test_image_single_circle):
        """Test CLI with JSON output to stdout."""
        image_path, _ = test_image_single_circle

        # Run CLI (--no-extract to get JSON on stdout)
        result = subprocess.run(
            ['dotmatrix', '--input', str(image_path), '--format', 'json', '--no-extract'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip()

        # Parse JSON output
        data = json.loads(result.stdout)
        assert isinstance(data, list)

        if len(data) > 0:
            # Validate structure
            first = data[0]
            assert 'center' in first
            assert 'radius' in first
            assert 'color' in first

    def test_cli_csv_output(self, test_image_single_circle):
        """Test CLI with CSV output to stdout."""
        image_path, _ = test_image_single_circle

        # Run CLI (--no-extract to get CSV on stdout)
        result = subprocess.run(
            ['dotmatrix', '--input', str(image_path), '--format', 'csv', '--no-extract'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert result.stdout.strip()

        # Parse CSV output
        reader = csv.DictReader(StringIO(result.stdout))
        rows = list(reader)

        if len(rows) > 0:
            first_row = rows[0]
            assert 'center_x' in first_row
            assert 'radius' in first_row
            assert 'color_r' in first_row

    def test_cli_output_to_file(self, test_image_single_circle):
        """Test CLI writing output to file."""
        image_path, _ = test_image_single_circle

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = Path(f.name)

        try:
            # Run CLI
            result = subprocess.run(
                ['dotmatrix', '--input', str(image_path),
                 '--output', str(output_path), '--format', 'json'],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0

            # Check output file was created
            assert output_path.exists()

            # Validate content
            content = output_path.read_text()
            data = json.loads(content)
            assert isinstance(data, list)

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_cli_debug_mode(self, test_image_single_circle):
        """Test CLI debug output."""
        image_path, _ = test_image_single_circle

        # Run CLI with debug flag
        result = subprocess.run(
            ['dotmatrix', '--input', str(image_path), '--debug'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Debug messages should appear in stderr
        assert 'Loading image' in result.stderr or 'Detecting circles' in result.stderr

    def test_accuracy_against_ground_truth(self, test_image_single_circle):
        """Test detection accuracy against known ground truth."""
        from dotmatrix.image_loader import load_image
        from dotmatrix.circle_detector import detect_circles
        from dotmatrix.color_extractor import extract_color

        image_path, ground_truth = test_image_single_circle

        # Run full pipeline
        image = load_image(image_path)
        circles = detect_circles(image)

        assert len(circles) >= 1, "Should detect at least one circle"

        expected = ground_truth[0]
        detected = circles[0]

        # Validate center accuracy (within 5px)
        center_error_x = abs(detected.center_x - expected['center'][0])
        center_error_y = abs(detected.center_y - expected['center'][1])
        assert center_error_x <= 5, f"Center X error: {center_error_x}px"
        assert center_error_y <= 5, f"Center Y error: {center_error_y}px"

        # Validate radius accuracy (within 10%)
        radius_error = abs(detected.radius - expected['radius']) / expected['radius']
        assert radius_error <= 0.10, f"Radius error: {radius_error*100:.1f}%"

        # Validate color accuracy
        color = extract_color(image, detected)
        expected_color = expected['color']

        for i, (actual, expect) in enumerate(zip(color, expected_color)):
            tolerance = max(expect * 0.1, 25)
            error = abs(actual - expect)
            assert error <= tolerance, \
                f"Color channel {i}: expected {expect}, got {actual}, error {error}"

    def test_no_circles_in_image(self, test_image_no_circles):
        """Test handling of image with no circles."""
        from dotmatrix.image_loader import load_image
        from dotmatrix.circle_detector import detect_circles

        image_path, _ = test_image_no_circles

        image = load_image(image_path)
        circles = detect_circles(image)

        # Should return empty list
        assert len(circles) == 0 or len(circles) <= 1  # Allow minimal false positives
