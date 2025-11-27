"""Tests for CLI mode presets (--mode option)."""

import pytest
import subprocess
import json
from pathlib import Path


class TestModePresets:
    """Test --mode preset option behavior."""

    def test_apply_mode_presets_standard(self):
        """Test standard mode preset returns correct settings."""
        from dotmatrix.cli import _apply_mode_presets

        convex_edge, palette, sensitive_occlusion, morph_enhance = _apply_mode_presets(
            mode='standard',
            convex_edge=None,
            palette='cmyk',
            sensitive_occlusion=False,
            morph_enhance=False,
            debug=False
        )

        assert convex_edge is False
        assert palette == 'cmyk'  # Unchanged
        assert sensitive_occlusion is False  # Unchanged
        assert morph_enhance is False  # Unchanged

    def test_apply_mode_presets_halftone(self):
        """Test halftone mode preset enables convex edge detection."""
        from dotmatrix.cli import _apply_mode_presets

        convex_edge, palette, sensitive_occlusion, morph_enhance = _apply_mode_presets(
            mode='halftone',
            convex_edge=False,
            palette='cmyk',
            sensitive_occlusion=False,
            morph_enhance=False,
            debug=False
        )

        assert convex_edge is True
        assert palette == 'cmyk'
        assert sensitive_occlusion is True
        assert morph_enhance is True

    def test_apply_mode_presets_cmyk_sep(self):
        """Test cmyk-sep mode preset enables ink separation."""
        from dotmatrix.cli import _apply_mode_presets

        convex_edge, palette, sensitive_occlusion, morph_enhance = _apply_mode_presets(
            mode='cmyk-sep',
            convex_edge=False,
            palette='cmyk',
            sensitive_occlusion=False,
            morph_enhance=False,
            debug=False
        )

        assert convex_edge is True
        assert palette == 'cmyk-sep'
        assert sensitive_occlusion is True
        assert morph_enhance is True

    def test_apply_mode_presets_none(self):
        """Test no mode preset returns original values."""
        from dotmatrix.cli import _apply_mode_presets

        convex_edge, palette, sensitive_occlusion, morph_enhance = _apply_mode_presets(
            mode=None,
            convex_edge=True,
            palette='rgb',
            sensitive_occlusion=True,
            morph_enhance=False,
            debug=False
        )

        assert convex_edge is True  # Unchanged
        assert palette == 'rgb'  # Unchanged
        assert sensitive_occlusion is True  # Unchanged
        assert morph_enhance is False  # Unchanged

    def test_apply_mode_presets_case_insensitive(self):
        """Test mode preset is case-insensitive."""
        from dotmatrix.cli import _apply_mode_presets

        # Test uppercase
        convex_edge, palette, _, _ = _apply_mode_presets(
            mode='HALFTONE',
            convex_edge=False,
            palette='cmyk',
            sensitive_occlusion=False,
            morph_enhance=False,
            debug=False
        )
        assert convex_edge is True

        # Test mixed case
        convex_edge, palette, _, _ = _apply_mode_presets(
            mode='Cmyk-Sep',
            convex_edge=False,
            palette='cmyk',
            sensitive_occlusion=False,
            morph_enhance=False,
            debug=False
        )
        assert palette == 'cmyk-sep'


class TestCLIModeIntegration:
    """Test --mode option via CLI subprocess."""

    def test_cli_mode_standard(self, test_image_single_circle):
        """Test CLI with --mode standard."""
        image_path, _ = test_image_single_circle

        result = subprocess.run(
            ['dotmatrix', '-i', str(image_path), '--mode', 'standard', '-f', 'json'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_cli_mode_halftone(self, test_image_single_circle):
        """Test CLI with --mode halftone."""
        image_path, _ = test_image_single_circle

        result = subprocess.run(
            ['dotmatrix', '-i', str(image_path), '--mode', 'halftone', '-f', 'json'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_cli_mode_cmyk_sep(self, test_image_single_circle):
        """Test CLI with --mode cmyk-sep."""
        image_path, _ = test_image_single_circle

        result = subprocess.run(
            ['dotmatrix', '-i', str(image_path), '--mode', 'cmyk-sep', '-f', 'json'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_cli_mode_with_debug(self, test_image_single_circle):
        """Test mode preset applies and debug shows it."""
        image_path, _ = test_image_single_circle

        result = subprocess.run(
            ['dotmatrix', '-i', str(image_path), '--mode', 'halftone', '--debug', '-f', 'json'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Mode 'halftone' preset applied" in result.stderr

    def test_cli_mode_invalid(self, test_image_single_circle):
        """Test CLI rejects invalid mode."""
        image_path, _ = test_image_single_circle

        result = subprocess.run(
            ['dotmatrix', '-i', str(image_path), '--mode', 'invalid'],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert 'invalid' in result.stderr.lower() or 'choice' in result.stderr.lower()
