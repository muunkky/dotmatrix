"""Tests for block_renderer module.

Tests the block-based reconstitution approach that achieves 100% pixel accuracy
by rendering clusters as horizontally stacked color bars.
"""

import pytest
import numpy as np

from dotmatrix.block_renderer import (
    calculate_bar_dimensions,
    render_single_block,
    render_blocks,
    COLORS,
    LAYER_ORDER,
)
from dotmatrix.cluster_pixel_counter import ClusterResult


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def simple_cluster():
    """Cluster with known pixel counts for all 7 colors."""
    return ClusterResult(
        x=100, y=100,
        cyan=100, magenta=80, yellow=60, black=200,
        red=40, green=30, blue=20,
        partial=False
    )


@pytest.fixture
def cluster_all_equal():
    """Cluster with equal counts for all colors."""
    return ClusterResult(
        x=150, y=150,
        cyan=50, magenta=50, yellow=50, black=50,
        red=50, green=50, blue=50,
        partial=False
    )


@pytest.fixture
def cluster_single_color():
    """Cluster with only black pixels."""
    return ClusterResult(
        x=50, y=50,
        cyan=0, magenta=0, yellow=0, black=100,
        red=0, green=0, blue=0,
        partial=False
    )


@pytest.fixture
def partial_cluster():
    """Cluster marked as partial (at edge)."""
    return ClusterResult(
        x=10, y=10,
        cyan=50, magenta=50, yellow=50, black=50,
        red=50, green=50, blue=50,
        partial=True
    )


# ============================================================================
# Helper Functions
# ============================================================================

def count_pixels_by_color(image: np.ndarray, color_bgr: tuple) -> int:
    """Count pixels matching a specific BGR color."""
    mask = np.all(image == color_bgr, axis=-1)
    return np.sum(mask)


# ============================================================================
# TestColors - Verify color definitions
# ============================================================================

class TestColors:
    """Test COLORS dict is properly defined in BGR format."""

    def test_all_seven_colors_defined(self):
        """All 7 colors must be in COLORS dict."""
        expected = ['cyan', 'magenta', 'yellow', 'black', 'red', 'green', 'blue']
        for color in expected:
            assert color in COLORS, f"Missing color: {color}"

    def test_cyan_is_bgr(self):
        """Cyan should be BGR (255, 255, 0)."""
        assert COLORS['cyan'] == (255, 255, 0)

    def test_magenta_is_bgr(self):
        """Magenta should be BGR (255, 0, 255)."""
        assert COLORS['magenta'] == (255, 0, 255)

    def test_yellow_is_bgr(self):
        """Yellow should be BGR (0, 255, 255)."""
        assert COLORS['yellow'] == (0, 255, 255)

    def test_black_is_bgr(self):
        """Black should be BGR (0, 0, 0)."""
        assert COLORS['black'] == (0, 0, 0)

    def test_red_is_bgr(self):
        """Red should be BGR (0, 0, 255)."""
        assert COLORS['red'] == (0, 0, 255)

    def test_green_is_bgr(self):
        """Green should be BGR (0, 255, 0)."""
        assert COLORS['green'] == (0, 255, 0)

    def test_blue_is_bgr(self):
        """Blue should be BGR (255, 0, 0)."""
        assert COLORS['blue'] == (255, 0, 0)


class TestLayerOrder:
    """Test LAYER_ORDER is properly defined."""

    def test_has_all_seven_colors(self):
        """LAYER_ORDER should have all 7 colors."""
        assert len(LAYER_ORDER) == 7
        for color in ['cyan', 'magenta', 'yellow', 'black', 'red', 'green', 'blue']:
            assert color in LAYER_ORDER


# ============================================================================
# TestCalculateBarDimensions
# ============================================================================

class TestCalculateBarDimensions:
    """Test calculate_bar_dimensions function."""

    def test_returns_dict_with_all_colors(self, simple_cluster):
        """Should return dict with all 7 color keys."""
        result = calculate_bar_dimensions(simple_cluster, segment_height=10)
        assert isinstance(result, dict)
        for color in LAYER_ORDER:
            assert color in result, f"Missing color in result: {color}"

    def test_each_color_has_bounds_tuple(self, simple_cluster):
        """Each color should map to (x1, y1, x2, y2) tuple."""
        result = calculate_bar_dimensions(simple_cluster, segment_height=10)
        for color, bounds in result.items():
            assert isinstance(bounds, tuple), f"{color} bounds not tuple"
            assert len(bounds) == 4, f"{color} bounds should have 4 elements"

    def test_segment_width_matches_pixel_count(self, simple_cluster):
        """Width should be pixel_count / segment_height."""
        segment_height = 10
        result = calculate_bar_dimensions(simple_cluster, segment_height=segment_height)

        # Black has 200 pixels, so width should be 200/10 = 20
        # cv2.rectangle uses inclusive bounds, so actual width = x2 - x1 + 1
        x1, y1, x2, y2 = result['black']
        width = x2 - x1 + 1
        assert width == simple_cluster.black // segment_height

    def test_zero_count_has_zero_width(self, cluster_single_color):
        """Colors with 0 pixels should have 0 width."""
        result = calculate_bar_dimensions(cluster_single_color, segment_height=10)

        # Cyan has 0 pixels
        x1, y1, x2, y2 = result['cyan']
        assert x2 - x1 == 0

    def test_rows_are_segment_height_tall(self, simple_cluster):
        """Each row should be segment_height pixels tall."""
        segment_height = 10
        result = calculate_bar_dimensions(simple_cluster, segment_height=segment_height)

        for color, bounds in result.items():
            x1, y1, x2, y2 = bounds
            # cv2.rectangle uses inclusive bounds, so actual height = y2 - y1 + 1
            height = y2 - y1 + 1
            # Zero-width segments may have zero height
            if x2 - x1 + 1 > 0 and x1 != x2:
                assert height == segment_height, f"{color} height should be {segment_height}, got {height}"


# ============================================================================
# TestRenderSingleBlock
# ============================================================================

class TestRenderSingleBlock:
    """Test render_single_block function."""

    def test_renders_on_white_background(self, simple_cluster):
        """Should render on white background."""
        image = np.full((300, 300, 3), 255, dtype=np.uint8)
        result = render_single_block(simple_cluster, image, segment_height=10)

        # Should have some non-white pixels
        non_white = np.sum(np.any(result != 255, axis=-1))
        assert non_white > 0

    def test_renders_all_nonzero_colors(self, simple_cluster):
        """Should render all colors with non-zero counts."""
        image = np.full((300, 300, 3), 255, dtype=np.uint8)
        result = render_single_block(simple_cluster, image, segment_height=10)

        # Check each color is present
        for color in LAYER_ORDER:
            count = getattr(simple_cluster, color)
            if count > 0:
                pixel_count = count_pixels_by_color(result, COLORS[color])
                assert pixel_count > 0, f"Color {color} not rendered"

    def test_black_is_rendered(self, simple_cluster):
        """Black should be rendered (innermost/last)."""
        image = np.full((300, 300, 3), 255, dtype=np.uint8)
        result = render_single_block(simple_cluster, image, segment_height=10)

        black_pixels = count_pixels_by_color(result, COLORS['black'])
        assert black_pixels > 0


# ============================================================================
# TestRenderBlocks
# ============================================================================

class TestRenderBlocks:
    """Test render_blocks main entry point."""

    def test_empty_list_returns_white_image(self):
        """Empty cluster list should return white image."""
        result = render_blocks([], (200, 200), segment_height=10)

        assert result.shape == (200, 200, 3)
        assert np.all(result == 255)

    def test_renders_single_cluster(self, simple_cluster):
        """Should render a single cluster."""
        result = render_blocks([simple_cluster], (300, 300), segment_height=10)

        # Should have some colored pixels
        non_white = np.sum(np.any(result != 255, axis=-1))
        assert non_white > 0

    def test_renders_multiple_clusters(self, simple_cluster, cluster_all_equal):
        """Should render multiple clusters."""
        clusters = [simple_cluster, cluster_all_equal]
        result = render_blocks(clusters, (300, 300), segment_height=10)

        # Should have colored pixels
        non_white = np.sum(np.any(result != 255, axis=-1))
        assert non_white > 0

    def test_skip_partial_excludes_partial_clusters(self, simple_cluster, partial_cluster):
        """skip_partial=True should skip partial clusters."""
        clusters = [simple_cluster, partial_cluster]

        # With skip_partial=False
        result_with_partial = render_blocks(clusters, (300, 300), segment_height=10, skip_partial=False)

        # With skip_partial=True
        result_without_partial = render_blocks(clusters, (300, 300), segment_height=10, skip_partial=True)

        # Should render fewer pixels when skipping partial
        pixels_with = np.sum(np.any(result_with_partial != 255, axis=-1))
        pixels_without = np.sum(np.any(result_without_partial != 255, axis=-1))
        assert pixels_without < pixels_with

    def test_returns_bgr_image(self, simple_cluster):
        """Should return BGR image (3 channels)."""
        result = render_blocks([simple_cluster], (300, 300), segment_height=10)

        assert result.ndim == 3
        assert result.shape[2] == 3
        assert result.dtype == np.uint8


# ============================================================================
# TestHeightModes
# ============================================================================

class TestHeightModes:
    """Test fixed-segment height mode (primary implementation)."""

    def test_fixed_segment_all_rows_same_height(self, cluster_all_equal):
        """In fixed-segment mode, all rows should have same height."""
        segment_height = 10
        result = calculate_bar_dimensions(cluster_all_equal, segment_height=segment_height)

        heights = []
        for color, bounds in result.items():
            x1, y1, x2, y2 = bounds
            # cv2.rectangle uses inclusive bounds
            if x2 - x1 + 1 > 0 and x1 != x2:  # Only check non-zero width rows
                heights.append(y2 - y1 + 1)

        # All heights should be equal
        assert len(set(heights)) == 1, "All rows should have same height"
        assert heights[0] == segment_height

    def test_segment_height_parameter_affects_row_height(self, simple_cluster):
        """Different segment_height should produce different row heights."""
        result_10 = calculate_bar_dimensions(simple_cluster, segment_height=10)
        result_20 = calculate_bar_dimensions(simple_cluster, segment_height=20)

        # Check black row height differs (inclusive bounds: height = y2 - y1 + 1)
        _, y1_10, _, y2_10 = result_10['black']
        _, y1_20, _, y2_20 = result_20['black']

        assert y2_10 - y1_10 + 1 == 10
        assert y2_20 - y1_20 + 1 == 20


# ============================================================================
# TestPixelAccuracy
# ============================================================================

class TestPixelAccuracy:
    """Test pixel count accuracy."""

    def test_accuracy_for_divisible_counts(self):
        """When pixel_count is divisible by segment_height, accuracy should be 100%."""
        # Create cluster where all counts are divisible by 10
        cluster = ClusterResult(
            x=150, y=150,
            cyan=100, magenta=100, yellow=100, black=100,
            red=100, green=100, blue=100,
            partial=False
        )
        segment_height = 10

        result = render_blocks([cluster], (400, 400), segment_height=segment_height)

        # Each color should have exactly 100 pixels (width=10, height=10)
        for color in LAYER_ORDER:
            expected = 100  # 100 / 10 * 10 = 100
            actual = count_pixels_by_color(result, COLORS[color])
            assert actual == expected, f"{color}: expected {expected}, got {actual}"

    def test_total_colored_pixels_reasonable(self, simple_cluster):
        """Total colored pixels should be close to sum of counts."""
        segment_height = 10
        result = render_blocks([simple_cluster], (300, 300), segment_height=segment_height)

        total_input = (simple_cluster.cyan + simple_cluster.magenta +
                      simple_cluster.yellow + simple_cluster.black +
                      simple_cluster.red + simple_cluster.green + simple_cluster.blue)

        total_rendered = 0
        for color in LAYER_ORDER:
            total_rendered += count_pixels_by_color(result, COLORS[color])

        # Allow for integer division error (up to segment_height per color)
        max_error = segment_height * 7
        assert abs(total_rendered - total_input) <= max_error
