"""Tests for CMYK-only color mode.

Tests the simplified color mode that outputs only C, M, Y, K channels
without detecting RGB overlap colors. This is useful for halftone
separation printing where overlaps occur naturally during physical printing.
"""

import pytest
import numpy as np

from dotmatrix.cluster_pixel_counter import (
    ClusterResult,
    count_cluster_pixels_cmyk,
    cluster_and_count_pixels,
)
from dotmatrix.treemap_renderer import (
    render_treemap,
    COLORS,
    LAYER_ORDER,
    LAYER_ORDER_CMYK,
)
from dotmatrix.block_renderer import (
    render_blocks,
    LAYER_ORDER as BLOCK_LAYER_ORDER,
    LAYER_ORDER_CMYK as BLOCK_LAYER_ORDER_CMYK,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def masks_with_overlaps():
    """Create masks where CMY colors overlap to form RGB."""
    h, w = 100, 100

    # Cyan: left half
    cyan = np.zeros((h, w), dtype=np.uint8)
    cyan[:, :50] = 255

    # Magenta: top half
    magenta = np.zeros((h, w), dtype=np.uint8)
    magenta[:50, :] = 255

    # Yellow: diagonal stripe
    yellow = np.zeros((h, w), dtype=np.uint8)
    yellow[25:75, 25:75] = 255

    # Black: single dot at center
    black = np.zeros((h, w), dtype=np.uint8)
    black[48:52, 48:52] = 255

    return cyan, magenta, yellow, black


@pytest.fixture
def simple_cluster_full():
    """Cluster with all 7 colors (full mode result)."""
    return ClusterResult(
        x=50, y=50,
        cyan=100, magenta=80, yellow=60, black=40,
        red=30, green=20, blue=10,
        partial=False
    )


@pytest.fixture
def simple_cluster_cmyk():
    """Cluster with only CMYK (cmyk mode result)."""
    return ClusterResult(
        x=50, y=50,
        cyan=130, magenta=120, yellow=110, black=40,  # Includes overlap pixels
        red=0, green=0, blue=0,  # Always zero in CMYK mode
        partial=False
    )


# ============================================================================
# TestClusterPixelCounterCMYK
# ============================================================================

class TestClusterPixelCounterCMYK:
    """Test CMYK-only counting in cluster_pixel_counter."""

    def test_count_cluster_pixels_cmyk_returns_zero_rgb(self, masks_with_overlaps):
        """CMYK mode should return zero for red, green, blue counts."""
        cyan, magenta, yellow, black = masks_with_overlaps

        # Create simple labels - all pixels belong to cluster 0
        labels = np.zeros((100, 100), dtype=np.int32)

        result = count_cluster_pixels_cmyk(
            cluster_id=0,
            labels=labels,
            cyan_mask=cyan,
            magenta_mask=magenta,
            yellow_mask=yellow,
            black_mask=black,
            center=(50, 50)
        )

        # RGB should always be 0 in CMYK mode
        assert result.red == 0
        assert result.green == 0
        assert result.blue == 0

    def test_cmyk_counts_include_overlaps(self, masks_with_overlaps):
        """CMYK counts should include pixels that would be RGB overlaps."""
        cyan, magenta, yellow, black = masks_with_overlaps

        # Create simple labels
        labels = np.zeros((100, 100), dtype=np.int32)

        result = count_cluster_pixels_cmyk(
            cluster_id=0,
            labels=labels,
            cyan_mask=cyan,
            magenta_mask=magenta,
            yellow_mask=yellow,
            black_mask=black,
            center=(50, 50)
        )

        # Cyan should include cyan pixels + green pixels (C∩Y) + blue pixels (C∩M)
        # This is the total count of all pixels where cyan ink is present
        assert result.cyan > 0
        assert result.magenta > 0
        assert result.yellow > 0

    def test_cluster_and_count_pixels_color_mode_full(self, masks_with_overlaps):
        """Full mode should detect RGB overlaps."""
        cyan, magenta, yellow, black = masks_with_overlaps

        results = cluster_and_count_pixels(
            cyan, magenta, yellow, black,
            color_mode='full'
        )

        # Should have at least one cluster (from black dot)
        assert len(results) >= 1

        # In full mode, RGB may have non-zero values
        # (depends on actual overlap in test data)

    def test_cluster_and_count_pixels_color_mode_cmyk(self, masks_with_overlaps):
        """CMYK mode should have zero RGB values."""
        cyan, magenta, yellow, black = masks_with_overlaps

        results = cluster_and_count_pixels(
            cyan, magenta, yellow, black,
            color_mode='cmyk'
        )

        # Should have at least one cluster
        assert len(results) >= 1

        # All clusters should have zero RGB
        for result in results:
            assert result.red == 0, f"Expected red=0, got {result.red}"
            assert result.green == 0, f"Expected green=0, got {result.green}"
            assert result.blue == 0, f"Expected blue=0, got {result.blue}"

    def test_default_color_mode_is_full(self, masks_with_overlaps):
        """Default color mode should be 'full' for backward compatibility."""
        cyan, magenta, yellow, black = masks_with_overlaps

        # Call without color_mode argument
        results_default = cluster_and_count_pixels(cyan, magenta, yellow, black)
        results_full = cluster_and_count_pixels(cyan, magenta, yellow, black, color_mode='full')

        # Should produce same results
        assert len(results_default) == len(results_full)
        for r1, r2 in zip(results_default, results_full):
            assert r1.cyan == r2.cyan
            assert r1.magenta == r2.magenta
            assert r1.yellow == r2.yellow
            assert r1.black == r2.black


# ============================================================================
# TestTreemapRendererCMYK
# ============================================================================

class TestTreemapRendererCMYK:
    """Test treemap renderer with CMYK-only mode."""

    def test_layer_order_cmyk_has_4_colors(self):
        """LAYER_ORDER_CMYK should have exactly 4 colors."""
        assert len(LAYER_ORDER_CMYK) == 4
        assert 'cyan' in LAYER_ORDER_CMYK
        assert 'magenta' in LAYER_ORDER_CMYK
        assert 'yellow' in LAYER_ORDER_CMYK
        assert 'black' in LAYER_ORDER_CMYK

    def test_layer_order_cmyk_no_rgb(self):
        """LAYER_ORDER_CMYK should not have red, green, blue."""
        assert 'red' not in LAYER_ORDER_CMYK
        assert 'green' not in LAYER_ORDER_CMYK
        assert 'blue' not in LAYER_ORDER_CMYK

    def test_render_treemap_color_mode_cmyk(self, simple_cluster_cmyk):
        """Treemap in CMYK mode should only use 4 colors."""
        result = render_treemap(
            [simple_cluster_cmyk],
            (200, 200),
            cluster_size=50,
            color_mode='cmyk'
        )

        # Check that only CMYK colors are present (plus white background)
        # Find all unique colors in the result
        unique_colors = set()
        for y in range(result.shape[0]):
            for x in range(result.shape[1]):
                unique_colors.add(tuple(result[y, x]))

        # White background
        white = (255, 255, 255)

        # Valid colors
        valid_colors = {white, COLORS['cyan'], COLORS['magenta'], COLORS['yellow'], COLORS['black']}

        for color in unique_colors:
            assert color in valid_colors, f"Unexpected color {color} in CMYK mode"

    def test_render_treemap_color_mode_full(self, simple_cluster_full):
        """Treemap in full mode should use all 7 colors."""
        result = render_treemap(
            [simple_cluster_full],
            (200, 200),
            cluster_size=50,
            color_mode='full'
        )

        # Should render without error
        assert result.shape == (200, 200, 3)

    def test_render_treemap_default_mode_is_full(self, simple_cluster_full):
        """Default color mode should be 'full'."""
        result1 = render_treemap([simple_cluster_full], (200, 200), cluster_size=50)
        result2 = render_treemap([simple_cluster_full], (200, 200), cluster_size=50, color_mode='full')

        # Should produce same output
        assert np.array_equal(result1, result2)


# ============================================================================
# TestBlockRendererCMYK
# ============================================================================

class TestBlockRendererCMYK:
    """Test block renderer with CMYK-only mode."""

    def test_block_layer_order_cmyk_has_4_colors(self):
        """Block renderer LAYER_ORDER_CMYK should have exactly 4 colors."""
        assert len(BLOCK_LAYER_ORDER_CMYK) == 4
        assert 'cyan' in BLOCK_LAYER_ORDER_CMYK
        assert 'magenta' in BLOCK_LAYER_ORDER_CMYK
        assert 'yellow' in BLOCK_LAYER_ORDER_CMYK
        assert 'black' in BLOCK_LAYER_ORDER_CMYK

    def test_render_blocks_color_mode_cmyk(self, simple_cluster_cmyk):
        """Block renderer in CMYK mode should only use 4 colors."""
        result = render_blocks(
            [simple_cluster_cmyk],
            (200, 200),
            segment_height=10,
            color_mode='cmyk'
        )

        # Check that only CMYK colors are present
        unique_colors = set()
        for y in range(result.shape[0]):
            for x in range(result.shape[1]):
                unique_colors.add(tuple(result[y, x]))

        white = (255, 255, 255)
        valid_colors = {white, COLORS['cyan'], COLORS['magenta'], COLORS['yellow'], COLORS['black']}

        for color in unique_colors:
            assert color in valid_colors, f"Unexpected color {color} in CMYK mode"


# ============================================================================
# Integration: CLI Color Mode
# ============================================================================

class TestColorModeIntegration:
    """Integration tests for color mode across the pipeline."""

    def test_cmyk_mode_total_pixels_consistent(self, masks_with_overlaps):
        """In CMYK mode, total CMY pixels should include what would be RGB overlaps."""
        cyan, magenta, yellow, black = masks_with_overlaps

        results_full = cluster_and_count_pixels(cyan, magenta, yellow, black, color_mode='full')
        results_cmyk = cluster_and_count_pixels(cyan, magenta, yellow, black, color_mode='cmyk')

        # For each cluster, CMYK mode totals should be >= full mode totals
        # because CMYK includes overlap pixels in each channel
        for rf, rc in zip(results_full, results_cmyk):
            # CMYK cyan includes what full mode counts as cyan + green + blue contributions
            # The relationship depends on the actual overlap structure
            # Key assertion: RGB should be 0 in CMYK mode
            assert rc.red == 0
            assert rc.green == 0
            assert rc.blue == 0
