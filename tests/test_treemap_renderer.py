"""Tests for treemap_renderer module.

Tests the treemap-based reconstitution approach that fills bounded rectangles
with proportional color areas using slice-and-dice algorithm.
"""

import pytest
import numpy as np

from dotmatrix.treemap_renderer import (
    Rectangle,
    slice_and_dice,
    get_cluster_bounds,
    render_single_treemap,
    render_treemap,
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
        cyan=100, magenta=100, yellow=100, black=100,
        red=100, green=100, blue=100,
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
# TestRectangle
# ============================================================================

class TestRectangle:
    """Test Rectangle dataclass."""

    def test_area_calculation(self):
        """Area should be width * height."""
        rect = Rectangle(x=0, y=0, width=10, height=20)
        assert rect.area == 200

    def test_x2_calculation(self):
        """x2 should be x + width."""
        rect = Rectangle(x=5, y=0, width=10, height=20)
        assert rect.x2 == 15

    def test_y2_calculation(self):
        """y2 should be y + height."""
        rect = Rectangle(x=0, y=3, width=10, height=20)
        assert rect.y2 == 23


# ============================================================================
# TestSliceAndDice
# ============================================================================

class TestSliceAndDice:
    """Test slice_and_dice algorithm."""

    def test_empty_values_returns_empty(self):
        """Empty values should return empty dict."""
        rect = Rectangle(0, 0, 100, 100)
        result = slice_and_dice(rect, [])
        assert result == {}

    def test_single_value_fills_entire_rect(self):
        """Single value should fill the entire rectangle."""
        rect = Rectangle(0, 0, 100, 100)
        result = slice_and_dice(rect, [('black', 100)])

        assert 'black' in result
        assert result['black'].x == 0
        assert result['black'].y == 0
        assert result['black'].width == 100
        assert result['black'].height == 100

    def test_two_equal_values_split_evenly_horizontal(self):
        """Two equal values should split rectangle in half horizontally."""
        rect = Rectangle(0, 0, 100, 100)
        result = slice_and_dice(rect, [('a', 50), ('b', 50)], horizontal=True)

        # Horizontal split: top to bottom
        assert result['a'].height == 50
        assert result['b'].height == 50
        assert result['a'].y == 0
        assert result['b'].y == 50

    def test_two_equal_values_split_evenly_vertical(self):
        """Two equal values should split rectangle in half vertically."""
        rect = Rectangle(0, 0, 100, 100)
        result = slice_and_dice(rect, [('a', 50), ('b', 50)], horizontal=False)

        # Vertical split: left to right
        assert result['a'].width == 50
        assert result['b'].width == 50
        assert result['a'].x == 0
        assert result['b'].x == 50

    def test_proportional_split(self):
        """Values should get proportional areas."""
        rect = Rectangle(0, 0, 100, 100)
        # 75% + 25% = 100%
        result = slice_and_dice(rect, [('a', 75), ('b', 25)], horizontal=True)

        # 'a' should get ~75% of height
        assert result['a'].height >= 70  # Allow some rounding
        assert result['a'].height <= 80
        # 'b' should get the rest
        assert result['b'].height == 100 - result['a'].height

    def test_zero_values_get_zero_size_rectangles(self):
        """Zero values should get zero-sized rectangles."""
        rect = Rectangle(0, 0, 100, 100)
        result = slice_and_dice(rect, [('a', 100), ('b', 0)])

        assert result['a'].width > 0
        assert result['b'].width == 0 or result['b'].height == 0

    def test_no_gaps_horizontal(self):
        """Subdivisions should fill the rectangle with no gaps (horizontal)."""
        rect = Rectangle(0, 0, 100, 100)
        result = slice_and_dice(rect, [('a', 33), ('b', 33), ('c', 34)], horizontal=True)

        # Total height should equal original
        total_height = sum(r.height for r in result.values())
        assert total_height == 100

    def test_no_gaps_vertical(self):
        """Subdivisions should fill the rectangle with no gaps (vertical)."""
        rect = Rectangle(0, 0, 100, 100)
        result = slice_and_dice(rect, [('a', 33), ('b', 33), ('c', 34)], horizontal=False)

        # Total width should equal original
        total_width = sum(r.width for r in result.values())
        assert total_width == 100

    def test_all_seven_colors(self):
        """Should handle all 7 colors correctly."""
        rect = Rectangle(0, 0, 100, 100)
        values = [
            ('yellow', 100),
            ('red', 50),
            ('green', 50),
            ('magenta', 80),
            ('blue', 30),
            ('cyan', 60),
            ('black', 40),
        ]
        result = slice_and_dice(rect, values, horizontal=True)

        # All colors should have rectangles
        for color, _ in values:
            assert color in result


# ============================================================================
# TestGetClusterBounds
# ============================================================================

class TestGetClusterBounds:
    """Test get_cluster_bounds function."""

    def test_centered_at_cluster_position(self):
        """Bounds should be centered at cluster.x, cluster.y."""
        cluster = ClusterResult(
            x=100, y=100,
            cyan=0, magenta=0, yellow=0, black=0,
            red=0, green=0, blue=0
        )
        bounds = get_cluster_bounds(cluster, cluster_size=20)

        # Center should be at (100, 100)
        center_x = bounds.x + bounds.width // 2
        center_y = bounds.y + bounds.height // 2
        assert center_x == 100
        assert center_y == 100

    def test_correct_size(self):
        """Bounds should have the specified size."""
        cluster = ClusterResult(x=50, y=50, cyan=0, magenta=0, yellow=0, black=0, red=0, green=0, blue=0)
        bounds = get_cluster_bounds(cluster, cluster_size=30)

        assert bounds.width == 30
        assert bounds.height == 30


# ============================================================================
# TestRenderSingleTreemap
# ============================================================================

class TestRenderSingleTreemap:
    """Test render_single_treemap function."""

    def test_renders_on_white_background(self, simple_cluster):
        """Should render on white background."""
        image = np.full((300, 300, 3), 255, dtype=np.uint8)
        result = render_single_treemap(simple_cluster, image, cluster_size=50)

        # Should have some non-white pixels
        non_white = np.sum(np.any(result != 255, axis=-1))
        assert non_white > 0

    def test_renders_all_nonzero_colors(self, simple_cluster):
        """Should render all colors with non-zero counts."""
        image = np.full((300, 300, 3), 255, dtype=np.uint8)
        result = render_single_treemap(simple_cluster, image, cluster_size=50)

        # Check each color is present
        for color in LAYER_ORDER:
            count = getattr(simple_cluster, color)
            if count > 0:
                pixel_count = count_pixels_by_color(result, COLORS[color])
                assert pixel_count > 0, f"Color {color} not rendered"

    def test_stays_within_cluster_bounds(self, simple_cluster):
        """All rendering should stay within cluster bounds."""
        image = np.full((300, 300, 3), 255, dtype=np.uint8)
        cluster_size = 50
        result = render_single_treemap(simple_cluster, image, cluster_size=cluster_size)

        # Calculate expected bounds
        half = cluster_size // 2
        min_x = simple_cluster.x - half
        max_x = simple_cluster.x + half
        min_y = simple_cluster.y - half
        max_y = simple_cluster.y + half

        # Find all non-white pixels
        non_white_mask = np.any(result != 255, axis=-1)
        non_white_coords = np.argwhere(non_white_mask)  # (y, x)

        if len(non_white_coords) > 0:
            ys, xs = non_white_coords[:, 0], non_white_coords[:, 1]
            assert xs.min() >= min_x, f"Pixels outside left bound: {xs.min()} < {min_x}"
            assert xs.max() < max_x, f"Pixels outside right bound: {xs.max()} >= {max_x}"
            assert ys.min() >= min_y, f"Pixels outside top bound: {ys.min()} < {min_y}"
            assert ys.max() < max_y, f"Pixels outside bottom bound: {ys.max()} >= {max_y}"


# ============================================================================
# TestRenderTreemap
# ============================================================================

class TestRenderTreemap:
    """Test render_treemap main entry point."""

    def test_empty_list_returns_white_image(self):
        """Empty cluster list should return white image."""
        result = render_treemap([], (200, 200), cluster_size=20)

        assert result.shape == (200, 200, 3)
        assert np.all(result == 255)

    def test_renders_single_cluster(self, simple_cluster):
        """Should render a single cluster."""
        result = render_treemap([simple_cluster], (300, 300), cluster_size=50)

        # Should have some colored pixels
        non_white = np.sum(np.any(result != 255, axis=-1))
        assert non_white > 0

    def test_renders_multiple_clusters(self, simple_cluster, cluster_all_equal):
        """Should render multiple clusters."""
        # Move clusters apart to avoid overlap
        simple_cluster.x, simple_cluster.y = 50, 50
        cluster_all_equal.x, cluster_all_equal.y = 150, 150

        clusters = [simple_cluster, cluster_all_equal]
        result = render_treemap(clusters, (300, 300), cluster_size=30)

        # Should have colored pixels
        non_white = np.sum(np.any(result != 255, axis=-1))
        assert non_white > 0

    def test_skip_partial_excludes_partial_clusters(self, simple_cluster, partial_cluster):
        """skip_partial=True should skip partial clusters."""
        simple_cluster.x, simple_cluster.y = 100, 100
        partial_cluster.x, partial_cluster.y = 200, 200

        clusters = [simple_cluster, partial_cluster]

        # With skip_partial=False
        result_with_partial = render_treemap(clusters, (300, 300), cluster_size=30, skip_partial=False)

        # With skip_partial=True
        result_without_partial = render_treemap(clusters, (300, 300), cluster_size=30, skip_partial=True)

        # Should render fewer pixels when skipping partial
        pixels_with = np.sum(np.any(result_with_partial != 255, axis=-1))
        pixels_without = np.sum(np.any(result_without_partial != 255, axis=-1))
        assert pixels_without < pixels_with

    def test_returns_bgr_image(self, simple_cluster):
        """Should return BGR image (3 channels)."""
        result = render_treemap([simple_cluster], (300, 300), cluster_size=50)

        assert result.ndim == 3
        assert result.shape[2] == 3
        assert result.dtype == np.uint8

    def test_no_overflow_with_large_counts(self):
        """Clusters with large counts should not overflow bounds."""
        # Create cluster with very large counts
        cluster = ClusterResult(
            x=100, y=100,
            cyan=10000, magenta=10000, yellow=10000, black=10000,
            red=10000, green=10000, blue=10000,
            partial=False
        )

        cluster_size = 50
        result = render_treemap([cluster], (200, 200), cluster_size=cluster_size)

        # Calculate expected bounds
        half = cluster_size // 2
        min_x = max(0, cluster.x - half)
        max_x = min(200, cluster.x + half)
        min_y = max(0, cluster.y - half)
        max_y = min(200, cluster.y + half)

        # Find all non-white pixels
        non_white_mask = np.any(result != 255, axis=-1)
        non_white_coords = np.argwhere(non_white_mask)

        if len(non_white_coords) > 0:
            ys, xs = non_white_coords[:, 0], non_white_coords[:, 1]
            assert xs.min() >= min_x
            assert xs.max() < max_x
            assert ys.min() >= min_y
            assert ys.max() < max_y


# ============================================================================
# TestColors
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


class TestLayerOrder:
    """Test LAYER_ORDER is properly defined."""

    def test_has_all_seven_colors(self):
        """LAYER_ORDER should have all 7 colors."""
        assert len(LAYER_ORDER) == 7
        for color in ['cyan', 'magenta', 'yellow', 'black', 'red', 'green', 'blue']:
            assert color in LAYER_ORDER
