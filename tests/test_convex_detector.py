"""Unit tests for convex_detector module."""

import numpy as np
import pytest
import cv2

from dotmatrix.convex_detector import (
    parse_palette,
    quantize_to_palette,
    filter_by_color,
    detect_circles_from_convex_edges,
    detect_all_circles,
    get_color_name,
    DetectedCircle,
    PALETTES,
)


class TestParsePalette:
    """Tests for parse_palette function."""

    def test_preset_cmyk(self):
        """Test parsing CMYK preset."""
        palette = parse_palette('cmyk')
        assert len(palette) == 5
        assert (255, 255, 255) in palette  # White
        assert (0, 0, 0) in palette  # Black
        assert (118, 193, 241) in palette  # Cyan
        assert (217, 93, 155) in palette  # Magenta
        assert (238, 206, 94) in palette  # Yellow

    def test_preset_rgb(self):
        """Test parsing RGB preset."""
        palette = parse_palette('rgb')
        assert len(palette) == 5
        assert (255, 0, 0) in palette  # Red
        assert (0, 255, 0) in palette  # Green
        assert (0, 0, 255) in palette  # Blue

    def test_preset_case_insensitive(self):
        """Test preset names are case insensitive."""
        assert parse_palette('CMYK') == parse_palette('cmyk')
        assert parse_palette('RGB') == parse_palette('rgb')

    def test_custom_palette(self):
        """Test parsing custom RGB values."""
        palette = parse_palette('255,0,0;0,255,0;0,0,255')
        assert len(palette) == 4  # White + 3 custom
        assert (255, 255, 255) in palette  # Auto-added white
        assert (255, 0, 0) in palette
        assert (0, 255, 0) in palette
        assert (0, 0, 255) in palette

    def test_custom_single_color(self):
        """Test parsing single custom color."""
        palette = parse_palette('128,128,128')
        assert len(palette) == 2
        assert (255, 255, 255) in palette
        assert (128, 128, 128) in palette

    def test_invalid_format_raises(self):
        """Test invalid format raises ValueError."""
        with pytest.raises(ValueError):
            parse_palette('invalid')

    def test_invalid_rgb_values_raises(self):
        """Test out-of-range RGB values raise ValueError."""
        with pytest.raises(ValueError):
            parse_palette('256,0,0')

    def test_invalid_negative_values_raises(self):
        """Test negative RGB values raise ValueError."""
        with pytest.raises(ValueError):
            parse_palette('-1,0,0')


class TestQuantizeToPalette:
    """Tests for quantize_to_palette function."""

    def test_exact_match_unchanged(self):
        """Test that exact palette colors remain unchanged."""
        palette = [(255, 255, 255), (0, 0, 0), (255, 0, 0)]
        image = np.array([[[255, 0, 0], [0, 0, 0]]], dtype=np.uint8)

        result = quantize_to_palette(image, palette)

        np.testing.assert_array_equal(result[0, 0], [255, 0, 0])
        np.testing.assert_array_equal(result[0, 1], [0, 0, 0])

    def test_near_color_quantized(self):
        """Test that near-palette colors are quantized."""
        palette = [(255, 255, 255), (0, 0, 0)]
        # Light gray should map to white, dark gray to black
        image = np.array([[[200, 200, 200], [50, 50, 50]]], dtype=np.uint8)

        result = quantize_to_palette(image, palette)

        np.testing.assert_array_equal(result[0, 0], [255, 255, 255])
        np.testing.assert_array_equal(result[0, 1], [0, 0, 0])

    def test_preserves_shape(self):
        """Test output has same shape as input."""
        palette = [(255, 255, 255), (0, 0, 0)]
        image = np.zeros((100, 200, 3), dtype=np.uint8)

        result = quantize_to_palette(image, palette)

        assert result.shape == image.shape

    def test_cmyk_quantization(self):
        """Test quantization with CMYK palette."""
        palette = PALETTES['cmyk']
        # Create image with colors close to CMYK
        image = np.array([
            [[120, 190, 240]],  # Near cyan
            [[215, 95, 160]],   # Near magenta
            [[240, 205, 95]],   # Near yellow
        ], dtype=np.uint8)

        result = quantize_to_palette(image, palette)

        # Check each maps to correct palette color
        np.testing.assert_array_equal(result[0, 0], [118, 193, 241])  # Cyan
        np.testing.assert_array_equal(result[1, 0], [217, 93, 155])   # Magenta
        np.testing.assert_array_equal(result[2, 0], [238, 206, 94])   # Yellow


class TestFilterByColor:
    """Tests for filter_by_color function."""

    def test_exact_match_returns_255(self):
        """Test exact color match returns 255."""
        image = np.array([[[255, 0, 0], [0, 255, 0]]], dtype=np.uint8)

        result = filter_by_color(image, (255, 0, 0))

        assert result[0, 0] == 255
        assert result[0, 1] == 0

    def test_no_match_returns_zeros(self):
        """Test non-matching pixels return 0."""
        image = np.array([[[255, 0, 0], [255, 0, 0]]], dtype=np.uint8)

        result = filter_by_color(image, (0, 0, 255))

        assert result[0, 0] == 0
        assert result[0, 1] == 0

    def test_output_is_binary(self):
        """Test output only contains 0 and 255."""
        palette = [(255, 255, 255), (0, 0, 0), (255, 0, 0)]
        image = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
        quantized = quantize_to_palette(image, palette)

        result = filter_by_color(quantized, (255, 0, 0))

        unique = np.unique(result)
        assert all(v in [0, 255] for v in unique)


class TestDetectCirclesFromConvexEdges:
    """Tests for detect_circles_from_convex_edges function."""

    def test_single_circle(self):
        """Test detection of a single complete circle."""
        # Create 200x200 image with a circle
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(mask, (100, 100), 50, 255, -1)

        circles = detect_circles_from_convex_edges(
            mask, (255, 0, 0),
            min_radius=30, max_radius=70
        )

        assert len(circles) == 1
        circle = circles[0]
        assert abs(circle.x - 100) < 10
        assert abs(circle.y - 100) < 10
        assert abs(circle.radius - 50) < 10
        assert circle.color == (255, 0, 0)

    def test_no_circles_in_empty_mask(self):
        """Test no circles detected in empty mask."""
        mask = np.zeros((200, 200), dtype=np.uint8)

        circles = detect_circles_from_convex_edges(mask, (255, 0, 0))

        assert len(circles) == 0

    def test_small_blobs_filtered(self):
        """Test small blobs below min_blob_area are filtered."""
        mask = np.zeros((200, 200), dtype=np.uint8)
        # Draw a tiny blob
        cv2.circle(mask, (100, 100), 5, 255, -1)

        circles = detect_circles_from_convex_edges(
            mask, (255, 0, 0),
            min_blob_area=1000  # Larger than the blob
        )

        assert len(circles) == 0

    def test_deduplication(self):
        """Test circles at same location are deduplicated."""
        # Create mask with single circle
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(mask, (100, 100), 50, 255, -1)

        circles = detect_circles_from_convex_edges(
            mask, (255, 0, 0),
            min_radius=30, max_radius=70,
            dedup_distance=50  # Large dedup distance
        )

        # Should only get one circle even if Hough finds multiple
        assert len(circles) <= 1


class TestDetectAllCircles:
    """Tests for detect_all_circles function."""

    def test_multiple_colors(self):
        """Test detection across multiple colors."""
        # Create 300x300 image with circles of different colors
        image = np.full((300, 300, 3), 255, dtype=np.uint8)  # White background

        # Draw red circle
        cv2.circle(image, (75, 75), 40, (255, 0, 0), -1)
        # Draw green circle
        cv2.circle(image, (225, 75), 40, (0, 255, 0), -1)
        # Draw blue circle
        cv2.circle(image, (150, 225), 40, (0, 0, 255), -1)

        palette = [
            (255, 255, 255),  # White background
            (255, 0, 0),      # Red
            (0, 255, 0),      # Green
            (0, 0, 255),      # Blue
        ]

        circles, quantized = detect_all_circles(
            image, palette,
            min_radius=30, max_radius=60
        )

        # Should detect 3 circles
        assert len(circles) == 3

        # Check each color is represented
        colors = [c.color for c in circles]
        assert (255, 0, 0) in colors
        assert (0, 255, 0) in colors
        assert (0, 0, 255) in colors

    def test_exclude_background(self):
        """Test background color is excluded."""
        image = np.full((200, 200, 3), 255, dtype=np.uint8)
        palette = [(255, 255, 255), (0, 0, 0)]

        circles, _ = detect_all_circles(image, palette, exclude_background=True)

        # No circles should be detected (all white)
        colors = [c.color for c in circles]
        assert (255, 255, 255) not in colors

    def test_returns_quantized_image(self):
        """Test function returns the quantized image."""
        image = np.full((100, 100, 3), 128, dtype=np.uint8)  # Gray
        palette = [(255, 255, 255), (0, 0, 0)]

        circles, quantized = detect_all_circles(image, palette)

        assert quantized.shape == image.shape
        # Gray should map to one of the palette colors
        unique = np.unique(quantized.reshape(-1, 3), axis=0)
        assert len(unique) == 1


class TestGetColorName:
    """Tests for get_color_name function."""

    def test_known_colors(self):
        """Test known colors return correct names."""
        assert get_color_name((0, 0, 0)) == 'black'
        assert get_color_name((255, 255, 255)) == 'white'
        assert get_color_name((255, 0, 0)) == 'red'
        assert get_color_name((118, 193, 241)) == 'cyan'
        assert get_color_name((217, 93, 155)) == 'magenta'
        assert get_color_name((238, 206, 94)) == 'yellow'

    def test_unknown_color_returns_rgb_string(self):
        """Test unknown colors return RGB string."""
        result = get_color_name((123, 45, 67))
        assert result == 'rgb_123_45_67'


class TestDetectedCircle:
    """Tests for DetectedCircle dataclass."""

    def test_unpacking(self):
        """Test DetectedCircle can be unpacked as (x, y, radius)."""
        circle = DetectedCircle(100, 200, 50, (255, 0, 0))
        x, y, r = circle

        assert x == 100
        assert y == 200
        assert r == 50

    def test_attributes(self):
        """Test DetectedCircle attributes."""
        circle = DetectedCircle(100, 200, 50, (255, 0, 0), confidence=95.5)

        assert circle.x == 100
        assert circle.y == 200
        assert circle.radius == 50
        assert circle.color == (255, 0, 0)
        assert circle.confidence == 95.5

    def test_default_confidence(self):
        """Test default confidence is 100."""
        circle = DetectedCircle(0, 0, 10, (0, 0, 0))
        assert circle.confidence == 100.0


class TestMorphologicalEnhancement:
    """Tests for morphological enhancement feature."""

    def test_morphological_enhancement_applied(self):
        """Test that morphological enhancement can be enabled."""
        from dotmatrix.convex_detector import apply_morphological_enhancement

        # Create fragmented mask
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(mask, (100, 100), 45, 255, 3)  # Just the edge, not filled

        # Apply enhancement
        enhanced = apply_morphological_enhancement(mask, dilation_size=5, erosion_size=2)

        # Enhanced mask should have more white pixels
        assert enhanced.shape == mask.shape

    def test_detect_with_morphological_enhance(self):
        """Test detection with morphological_enhance flag."""
        # Create image with a circle
        image = np.full((300, 300, 3), 255, dtype=np.uint8)
        cv2.circle(image, (150, 150), 60, (255, 0, 0), -1)

        palette = [(255, 255, 255), (255, 0, 0)]

        circles, _ = detect_all_circles(
            image, palette,
            min_radius=40, max_radius=80,
            morphological_enhance=True
        )

        # Should detect circle with morph enhancement
        assert len(circles) >= 1

    def test_detect_with_sensitive_mode(self):
        """Test detection with sensitive_mode flag."""
        # Create image with a circle
        image = np.full((300, 300, 3), 255, dtype=np.uint8)
        cv2.circle(image, (150, 150), 60, (0, 255, 0), -1)

        palette = [(255, 255, 255), (0, 255, 0)]

        circles, _ = detect_all_circles(
            image, palette,
            min_radius=40, max_radius=80,
            sensitive_mode=True
        )

        # Should detect circle with sensitive mode
        assert len(circles) >= 1

    def test_detect_circles_from_convex_edges_with_flags(self):
        """Test detect_circles_from_convex_edges with new flags."""
        # Create a solid circle mask
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(mask, (100, 100), 50, 255, -1)

        # Test with sensitive mode
        circles_sensitive = detect_circles_from_convex_edges(
            mask, (255, 0, 0),
            min_radius=30, max_radius=70,
            sensitive_mode=True,
            morphological_enhance=False
        )

        # Test with morphological enhance
        circles_morph = detect_circles_from_convex_edges(
            mask, (255, 0, 0),
            min_radius=30, max_radius=70,
            sensitive_mode=False,
            morphological_enhance=True
        )

        # Both should detect the circle
        assert len(circles_sensitive) >= 1
        assert len(circles_morph) >= 1
