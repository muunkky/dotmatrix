"""Tests for runs module."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from dotmatrix.runs import (
    find_runs,
    get_run_info,
    list_runs,
    find_run_by_name,
    get_replay_settings,
    format_runs_table,
)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory structure with runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create run1 with manifest
        run1 = base / "run_20251125_100000"
        run1.mkdir()
        manifest1 = {
            "dotmatrix_version": "0.1.0",
            "timestamp": "2025-11-25T10:00:00",
            "source_file": {"name": "image1.png", "path": "/path/to/image1.png"},
            "settings": {"min_radius": 80, "convex_edge": True},
            "results": {"total_circles": 16},
        }
        (run1 / "manifest.json").write_text(json.dumps(manifest1))

        # Create run2 with manifest
        run2 = base / "run_20251124_090000"
        run2.mkdir()
        manifest2 = {
            "dotmatrix_version": "0.1.0",
            "timestamp": "2025-11-24T09:00:00",
            "source_file": {"name": "image2.png", "path": "/path/to/image2.png"},
            "settings": {"min_radius": 50},
            "results": {"total_circles": 8},
        }
        (run2 / "manifest.json").write_text(json.dumps(manifest2))

        # Create run3 with same source as run1
        run3 = base / "test_experiment"
        run3.mkdir()
        manifest3 = {
            "dotmatrix_version": "0.1.0",
            "timestamp": "2025-11-23T15:30:00",
            "source_file": {"name": "image1.png", "path": "/path/to/image1.png"},
            "settings": {"min_radius": 100, "palette": "rgb"},
            "results": {"total_circles": 12},
        }
        (run3 / "manifest.json").write_text(json.dumps(manifest3))

        # Create directory without manifest (should be ignored)
        no_manifest = base / "empty_dir"
        no_manifest.mkdir()

        yield base


class TestFindRuns:
    """Tests for find_runs function."""

    def test_finds_runs_with_manifests(self, temp_output_dir):
        """Test that find_runs finds directories with manifest.json."""
        runs = find_runs(temp_output_dir)
        assert len(runs) == 3

    def test_ignores_dirs_without_manifest(self, temp_output_dir):
        """Test that directories without manifest.json are ignored."""
        runs = find_runs(temp_output_dir)
        names = [r.name for r in runs]
        assert "empty_dir" not in names

    def test_returns_empty_for_nonexistent_dir(self):
        """Test that nonexistent directory returns empty list."""
        runs = find_runs(Path("/nonexistent/path"))
        assert runs == []

    def test_returns_sorted_by_mtime(self, temp_output_dir):
        """Test that runs are sorted by modification time."""
        runs = find_runs(temp_output_dir)
        # First run should be most recently modified
        assert len(runs) == 3


class TestGetRunInfo:
    """Tests for get_run_info function."""

    def test_extracts_basic_info(self, temp_output_dir):
        """Test that basic info is extracted from manifest."""
        run_dir = temp_output_dir / "run_20251125_100000"
        info = get_run_info(run_dir)

        assert info is not None
        assert info["name"] == "run_20251125_100000"
        assert info["source"] == "image1.png"
        assert info["circles"] == 16

    def test_returns_none_for_missing_manifest(self, temp_output_dir):
        """Test that missing manifest returns None."""
        info = get_run_info(temp_output_dir / "empty_dir")
        assert info is None

    def test_includes_formatted_date(self, temp_output_dir):
        """Test that date is formatted nicely."""
        run_dir = temp_output_dir / "run_20251125_100000"
        info = get_run_info(run_dir)

        assert "2025-11-25" in info["date"]

    def test_includes_full_manifest(self, temp_output_dir):
        """Test that full manifest is included in info."""
        run_dir = temp_output_dir / "run_20251125_100000"
        info = get_run_info(run_dir)

        assert "manifest" in info
        assert info["manifest"]["dotmatrix_version"] == "0.1.0"


class TestListRuns:
    """Tests for list_runs function."""

    def test_lists_all_runs(self, temp_output_dir):
        """Test that all runs are listed without filters."""
        runs = list_runs(temp_output_dir)
        assert len(runs) == 3

    def test_filter_by_source(self, temp_output_dir):
        """Test filtering by source filename."""
        runs = list_runs(temp_output_dir, source_filter="image1")
        assert len(runs) == 2
        assert all(r["source"] == "image1.png" for r in runs)

    def test_filter_by_source_case_insensitive(self, temp_output_dir):
        """Test source filter is case-insensitive."""
        runs = list_runs(temp_output_dir, source_filter="IMAGE1")
        assert len(runs) == 2

    def test_filter_by_date(self, temp_output_dir):
        """Test filtering by date."""
        runs = list_runs(temp_output_dir, after_date="2025-11-25")
        assert len(runs) == 1
        assert runs[0]["name"] == "run_20251125_100000"

    def test_filter_by_date_excludes_older(self, temp_output_dir):
        """Test that older runs are excluded by date filter."""
        runs = list_runs(temp_output_dir, after_date="2025-11-24")
        assert len(runs) == 2

    def test_combined_filters(self, temp_output_dir):
        """Test combining source and date filters."""
        runs = list_runs(temp_output_dir, source_filter="image1", after_date="2025-11-25")
        assert len(runs) == 1


class TestFindRunByName:
    """Tests for find_run_by_name function."""

    def test_finds_existing_run(self, temp_output_dir):
        """Test finding an existing run by name."""
        result = find_run_by_name(temp_output_dir, "run_20251125_100000")
        assert result is not None
        assert result.name == "run_20251125_100000"

    def test_returns_none_for_nonexistent(self, temp_output_dir):
        """Test that nonexistent run returns None."""
        result = find_run_by_name(temp_output_dir, "nonexistent_run")
        assert result is None

    def test_returns_none_for_dir_without_manifest(self, temp_output_dir):
        """Test that directory without manifest returns None."""
        result = find_run_by_name(temp_output_dir, "empty_dir")
        assert result is None


class TestGetReplaySettings:
    """Tests for get_replay_settings function."""

    def test_extracts_source_path(self):
        """Test that source path is extracted."""
        manifest = {
            "source_file": {"path": "/path/to/image.png"},
            "settings": {},
        }
        settings = get_replay_settings(manifest)
        assert settings["source"] == "/path/to/image.png"

    def test_extracts_settings(self):
        """Test that settings are extracted."""
        manifest = {
            "source_file": {"path": "/path/to/image.png"},
            "settings": {"min_radius": 80, "convex_edge": True},
        }
        settings = get_replay_settings(manifest)
        assert settings["min_radius"] == 80
        assert settings["convex_edge"] is True

    def test_excludes_none_values(self):
        """Test that None values are excluded."""
        manifest = {
            "source_file": {"path": "/path/to/image.png"},
            "settings": {"min_radius": 80, "max_colors": None},
        }
        settings = get_replay_settings(manifest)
        assert "max_colors" not in settings


class TestFormatRunsTable:
    """Tests for format_runs_table function."""

    def test_formats_empty_list(self):
        """Test formatting empty run list."""
        result = format_runs_table([])
        assert "No runs found" in result

    def test_includes_header(self, temp_output_dir):
        """Test that table includes header."""
        runs = list_runs(temp_output_dir)
        result = format_runs_table(runs)

        assert "NAME" in result
        assert "DATE" in result
        assert "SOURCE" in result
        assert "CIRCLES" in result

    def test_includes_run_data(self, temp_output_dir):
        """Test that table includes run data."""
        runs = list_runs(temp_output_dir)
        result = format_runs_table(runs)

        assert "run_20251125_100000" in result
        assert "image1.png" in result
        assert "16" in result

    def test_aligns_columns(self, temp_output_dir):
        """Test that columns are aligned."""
        runs = list_runs(temp_output_dir)
        result = format_runs_table(runs)
        lines = result.split("\n")

        # Header and separator should be same length
        assert len(lines[0]) == len(lines[1])
