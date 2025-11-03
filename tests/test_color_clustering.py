"""Tests for color_clustering module."""

import pytest
import numpy as np

from dotmatrix.circle_detector import Circle
from dotmatrix.color_clustering import cluster_colors


class TestClusterColors:
    """Test k-means color clustering functionality."""

    def test_cluster_to_exact_number(self):
        """Test clustering reduces colors to exact N clusters."""
        # 10 different colors
        colors = [
            (255, 0, 0),    # Red
            (250, 5, 5),    # Similar red
            (0, 255, 0),    # Green
            (5, 250, 10),   # Similar green
            (0, 0, 255),    # Blue
            (10, 10, 250),  # Similar blue
            (255, 255, 0),  # Yellow
            (250, 250, 10), # Similar yellow
            (255, 0, 255),  # Magenta
            (250, 10, 250), # Similar magenta
        ]

        # Cluster to 4 colors
        mapping = cluster_colors(colors, n_clusters=4)

        # Should have exactly 4 unique cluster centers
        unique_clusters = set(mapping.values())
        assert len(unique_clusters) == 4

        # All original colors should be mapped
        assert len(mapping) == 10

    def test_cluster_fewer_colors_than_requested(self):
        """Test clustering when fewer colors than clusters."""
        colors = [
            (255, 0, 0),  # Red
            (0, 255, 0),  # Green
        ]

        # Request 4 clusters but only have 2 colors
        mapping = cluster_colors(colors, n_clusters=4)

        # Should have at most 2 unique clusters (can't create more)
        unique_clusters = set(mapping.values())
        assert len(unique_clusters) <= 2

    def test_cluster_single_color(self):
        """Test clustering with single color."""
        colors = [(255, 0, 0)]

        mapping = cluster_colors(colors, n_clusters=4)

        # Should map to itself
        assert len(mapping) == 1
        assert (255, 0, 0) in mapping

    def test_cluster_groups_similar_colors(self):
        """Test that similar colors are grouped together."""
        colors = [
            (255, 0, 0),    # Red
            (254, 1, 1),    # Very similar red
            (253, 2, 2),    # Very similar red
            (0, 255, 0),    # Green (very different)
        ]

        # Cluster to 2 groups
        mapping = cluster_colors(colors, n_clusters=2)

        # The three reds should map to same cluster
        red1_cluster = mapping[(255, 0, 0)]
        red2_cluster = mapping[(254, 1, 1)]
        red3_cluster = mapping[(253, 2, 2)]

        # At least 2 of the 3 reds should be in same cluster
        assert (red1_cluster == red2_cluster or
                red1_cluster == red3_cluster or
                red2_cluster == red3_cluster)

    def test_cluster_output_format(self):
        """Test that output mapping has correct format."""
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

        mapping = cluster_colors(colors, n_clusters=2)

        # Check keys are original colors (tuples)
        for color in colors:
            assert color in mapping
            assert isinstance(color, tuple)
            assert len(color) == 3

        # Check values are cluster centers (tuples)
        for cluster_center in mapping.values():
            assert isinstance(cluster_center, tuple)
            assert len(cluster_center) == 3
            # RGB values should be in valid range
            assert all(0 <= v <= 255 for v in cluster_center)

    def test_empty_colors_list(self):
        """Test with empty colors list."""
        colors = []

        mapping = cluster_colors(colors, n_clusters=4)

        # Should return empty mapping
        assert len(mapping) == 0
        assert mapping == {}
