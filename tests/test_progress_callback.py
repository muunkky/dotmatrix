"""Tests for progress callback functionality in renderer."""

import pytest
import numpy as np
from unittest.mock import Mock, call

from dotmatrix.circle_renderer import render_flower_global_blend
from dotmatrix.cluster_pixel_counter import ClusterResult


class TestProgressCallback:
    """Tests for progress callback in flower renderer."""

    def test_progress_callback_is_called_during_rendering(self):
        """Progress callback should be invoked during petal optimization phase."""
        # Create test clusters
        clusters = [
            ClusterResult(
                x=50 + i * 20,
                y=50,
                cyan=100,
                magenta=100,
                yellow=100,
                black=50,
                partial=False
            )
            for i in range(10)  # 10 clusters should trigger multiple progress updates
        ]

        # Mock progress callback
        callback = Mock()

        # Render with progress callback
        result = render_flower_global_blend(
            clusters,
            image_shape=(200, 200),
            petal_distance=0.35,
            scale=1,
            progress_callback=callback
        )

        # Verify callback was called
        assert callback.called, "Progress callback should be called during rendering"
        assert callback.call_count > 0, "Progress callback should be called at least once"

        # Verify callback received correct arguments
        # Should be called with (current, total, phase_name, metadata)
        first_call = callback.call_args_list[0]
        assert len(first_call[0]) == 4, "Callback should receive 4 arguments"

        current, total, phase_name, metadata = first_call[0]
        assert isinstance(current, int), "Current should be an integer"
        assert isinstance(total, int), "Total should be an integer"
        assert total == 10, f"Total should be number of clusters (10), got {total}"
        assert phase_name == 'petal_optimization', f"Phase name should be 'petal_optimization', got {phase_name}"
        assert isinstance(metadata, dict), "Metadata should be a dictionary"
        assert 'percentage' in metadata, "Metadata should contain 'percentage' key"

    def test_progress_callback_percentage_increases(self):
        """Progress callback should show increasing percentage values."""
        clusters = [
            ClusterResult(
                x=50 + i * 20,
                y=50,
                cyan=100,
                magenta=100,
                yellow=100,
                black=50,
                partial=False
            )
            for i in range(10)
        ]

        callback = Mock()

        render_flower_global_blend(
            clusters,
            image_shape=(200, 200),
            petal_distance=0.35,
            scale=1,
            progress_callback=callback
        )

        # Extract percentages from all calls
        percentages = []
        for call_args in callback.call_args_list:
            _, _, _, metadata = call_args[0]
            percentages.append(metadata['percentage'])

        # Verify percentages are non-decreasing
        for i in range(len(percentages) - 1):
            assert percentages[i] <= percentages[i + 1], \
                f"Percentages should be non-decreasing, but {percentages[i]} > {percentages[i + 1]}"

        # Verify we reach 100% or close to it
        assert percentages[-1] >= 90, f"Final percentage should be at least 90%, got {percentages[-1]}"

    def test_render_without_callback_still_works(self):
        """Rendering should work normally when no callback is provided."""
        clusters = [
            ClusterResult(
                x=50,
                y=50,
                cyan=100,
                magenta=100,
                yellow=100,
                black=50,
                partial=False
            )
        ]

        # Should not raise any errors
        result = render_flower_global_blend(
            clusters,
            image_shape=(100, 100),
            petal_distance=0.35,
            scale=1,
            progress_callback=None  # Explicitly no callback
        )

        assert result is not None
        assert result.shape == (100, 100, 3)

    def test_progress_callback_with_many_clusters(self):
        """Progress callback should be called at reasonable intervals for many clusters."""
        # Create many clusters to test logging interval
        clusters = [
            ClusterResult(
                x=10 + (i % 20) * 5,
                y=10 + (i // 20) * 5,
                cyan=50,
                magenta=50,
                yellow=50,
                black=25,
                partial=False
            )
            for i in range(100)  # 100 clusters
        ]

        callback = Mock()

        render_flower_global_blend(
            clusters,
            image_shape=(200, 200),
            petal_distance=0.35,
            scale=1,
            progress_callback=callback
        )

        # Should be called approximately every 5% (about 20 times for 100 clusters)
        # But at least some reasonable number of times
        assert 5 <= callback.call_count <= 25, \
            f"For 100 clusters, callback should be called 5-25 times (every 5%), got {callback.call_count}"

    def test_progress_callback_current_and_total_are_consistent(self):
        """Progress callback current values should progress from 1 to total."""
        clusters = [
            ClusterResult(
                x=50 + i * 20,
                y=50,
                cyan=100,
                magenta=100,
                yellow=100,
                black=50,
                partial=False
            )
            for i in range(20)
        ]

        callback = Mock()

        render_flower_global_blend(
            clusters,
            image_shape=(400, 400),
            petal_distance=0.35,
            scale=1,
            progress_callback=callback
        )

        # Verify all calls have same total
        totals = [call_args[0][1] for call_args in callback.call_args_list]
        assert all(t == 20 for t in totals), "All calls should have total=20"

        # Verify current values are reasonable (between 1 and total)
        currents = [call_args[0][0] for call_args in callback.call_args_list]
        for current in currents:
            assert 1 <= current <= 20, f"Current should be between 1 and 20, got {current}"
