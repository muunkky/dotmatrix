"""Tests for manifest module."""

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest

from dotmatrix.manifest import (
    compute_file_hash,
    count_circles_by_color,
    generate_manifest,
    write_manifest,
    read_manifest,
    get_manifest_summary,
)


@dataclass
class MockCircle:
    """Mock circle for testing."""
    center_x: int
    center_y: int
    radius: int


class TestComputeFileHash:
    """Tests for compute_file_hash function."""

    def test_hash_format(self):
        """Test that hash has correct format."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            f.flush()
            filepath = Path(f.name)

        try:
            hash_result = compute_file_hash(filepath)
            assert hash_result.startswith("sha256:")
            # SHA256 hex is 64 characters
            assert len(hash_result) == 7 + 64  # "sha256:" + 64 hex chars
        finally:
            filepath.unlink()

    def test_same_content_same_hash(self):
        """Test that same content produces same hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"

            file1.write_bytes(b"identical content")
            file2.write_bytes(b"identical content")

            assert compute_file_hash(file1) == compute_file_hash(file2)

    def test_different_content_different_hash(self):
        """Test that different content produces different hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"

            file1.write_bytes(b"content A")
            file2.write_bytes(b"content B")

            assert compute_file_hash(file1) != compute_file_hash(file2)


class TestCountCirclesByColor:
    """Tests for count_circles_by_color function."""

    def test_basic_count(self):
        """Test basic color counting."""
        results = [
            (MockCircle(0, 0, 10), (255, 0, 0)),
            (MockCircle(10, 10, 10), (255, 0, 0)),
            (MockCircle(20, 20, 10), (0, 255, 0)),
        ]

        counts = count_circles_by_color(results)

        assert counts["rgb(255,0,0)"] == 2
        assert counts["rgb(0,255,0)"] == 1

    def test_with_color_names(self):
        """Test counting with color name mapping."""
        results = [
            (MockCircle(0, 0, 10), (255, 0, 0)),
            (MockCircle(10, 10, 10), (255, 0, 0)),
            (MockCircle(20, 20, 10), (0, 255, 0)),
        ]

        color_names = {
            (255, 0, 0): "Red",
            (0, 255, 0): "Green",
        }

        counts = count_circles_by_color(results, color_names)

        assert counts["Red"] == 2
        assert counts["Green"] == 1

    def test_empty_results(self):
        """Test with empty results."""
        counts = count_circles_by_color([])
        assert counts == {}


class TestGenerateManifest:
    """Tests for generate_manifest function."""

    def test_manifest_structure(self):
        """Test that manifest has required fields."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
            f.write(b"fake image content")
            source_file = Path(f.name)

        try:
            results = [
                (MockCircle(100, 100, 50), (255, 0, 0)),
            ]
            settings = {"min_radius": 10, "convex_edge": True}

            manifest = generate_manifest(
                source_file=source_file,
                settings=settings,
                results=results,
                output_files=[Path("output.png")],
            )

            assert "dotmatrix_version" in manifest
            assert "timestamp" in manifest
            assert "source_file" in manifest
            assert "settings" in manifest
            assert "results" in manifest
            assert "output_files" in manifest
        finally:
            source_file.unlink()

    def test_manifest_source_file_info(self):
        """Test that source file info is correct."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
            f.write(b"fake image content")
            source_file = Path(f.name)

        try:
            manifest = generate_manifest(
                source_file=source_file,
                settings={},
                results=[],
                output_files=[],
            )

            assert manifest["source_file"]["name"] == source_file.name
            assert manifest["source_file"]["hash"].startswith("sha256:")
        finally:
            source_file.unlink()

    def test_manifest_results_summary(self):
        """Test that results summary is accurate."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
            f.write(b"fake image")
            source_file = Path(f.name)

        try:
            results = [
                (MockCircle(0, 0, 10), (255, 0, 0)),
                (MockCircle(10, 10, 10), (255, 0, 0)),
                (MockCircle(20, 20, 10), (0, 255, 0)),
                (MockCircle(30, 30, 10), (0, 0, 255)),
            ]

            manifest = generate_manifest(
                source_file=source_file,
                settings={},
                results=results,
                output_files=[],
            )

            assert manifest["results"]["total_circles"] == 4
            assert len(manifest["results"]["circles_by_color"]) == 3
        finally:
            source_file.unlink()

    def test_manifest_output_files_list(self):
        """Test that output files are listed correctly."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
            f.write(b"fake")
            source_file = Path(f.name)

        try:
            output_files = [
                Path("/output/circles_red.png"),
                Path("/output/circles_blue.png"),
            ]

            manifest = generate_manifest(
                source_file=source_file,
                settings={},
                results=[],
                output_files=output_files,
            )

            assert manifest["output_files"] == ["circles_red.png", "circles_blue.png"]
        finally:
            source_file.unlink()


class TestWriteReadManifest:
    """Tests for write_manifest and read_manifest functions."""

    def test_write_creates_file(self):
        """Test that write_manifest creates a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            manifest = {"test": "data"}

            manifest_path = write_manifest(run_dir, manifest)

            assert manifest_path.exists()
            assert manifest_path.name == "manifest.json"

    def test_write_custom_filename(self):
        """Test writing with custom filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            manifest = {"test": "data"}

            manifest_path = write_manifest(run_dir, manifest, filename="custom.json")

            assert manifest_path.exists()
            assert manifest_path.name == "custom.json"

    def test_read_written_manifest(self):
        """Test that read_manifest reads what was written."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            original = {"version": "1.0", "data": [1, 2, 3]}

            manifest_path = write_manifest(run_dir, original)
            loaded = read_manifest(manifest_path)

            assert loaded == original

    def test_manifest_is_valid_json(self):
        """Test that written manifest is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            manifest = {"nested": {"data": "value"}, "list": [1, 2, 3]}

            manifest_path = write_manifest(run_dir, manifest)

            # Should be parseable as JSON
            with open(manifest_path) as f:
                loaded = json.load(f)

            assert loaded == manifest


class TestGetManifestSummary:
    """Tests for get_manifest_summary function."""

    def test_summary_format(self):
        """Test that summary is formatted correctly."""
        manifest = {
            "source_file": {"name": "test.png"},
            "timestamp": "2025-11-25T14:30:22.123456",
            "results": {
                "total_circles": 16,
                "circles_by_color": {"black": 4, "cyan": 4, "magenta": 4, "yellow": 4},
            },
        }

        summary = get_manifest_summary(manifest)

        assert "test.png" in summary
        assert "16" in summary
        assert "black=4" in summary

    def test_summary_without_color_breakdown(self):
        """Test summary when no color breakdown present."""
        manifest = {
            "source_file": {"name": "test.png"},
            "timestamp": "2025-11-25T14:30:22",
            "results": {"total_circles": 5},
        }

        summary = get_manifest_summary(manifest)

        assert "test.png" in summary
        assert "5" in summary
