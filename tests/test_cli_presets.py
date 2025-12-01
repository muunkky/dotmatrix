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

        convex_edge, palette, sensitive_occlusion, morph_enhance, reconstitute = _apply_mode_presets(
            mode='standard',
            convex_edge=None,
            palette='cmyk',
            sensitive_occlusion=False,
            morph_enhance=False,
            reconstitute=True,  # Default is now True
            debug=False
        )

        assert convex_edge is False
        assert palette == 'cmyk'  # Unchanged
        assert sensitive_occlusion is False  # Unchanged
        assert morph_enhance is False  # Unchanged
        assert reconstitute is False  # Standard mode disables reconstitute

    def test_apply_mode_presets_halftone(self):
        """Test halftone mode preset enables convex edge detection."""
        from dotmatrix.cli import _apply_mode_presets

        convex_edge, palette, sensitive_occlusion, morph_enhance, reconstitute = _apply_mode_presets(
            mode='halftone',
            convex_edge=False,
            palette='cmyk',
            sensitive_occlusion=False,
            morph_enhance=False,
            reconstitute=True,
            debug=False
        )

        assert convex_edge is True
        assert palette == 'cmyk'
        assert sensitive_occlusion is True
        assert morph_enhance is True
        assert reconstitute is True  # Halftone mode keeps reconstitute enabled

    def test_apply_mode_presets_cmyk_sep(self):
        """Test cmyk-sep mode preset enables ink separation."""
        from dotmatrix.cli import _apply_mode_presets

        convex_edge, palette, sensitive_occlusion, morph_enhance, reconstitute = _apply_mode_presets(
            mode='cmyk-sep',
            convex_edge=False,
            palette='cmyk',
            sensitive_occlusion=False,
            morph_enhance=False,
            reconstitute=True,
            debug=False
        )

        assert convex_edge is True
        assert palette == 'cmyk-sep'
        assert sensitive_occlusion is True
        assert morph_enhance is True
        assert reconstitute is True  # CMYK-sep mode keeps reconstitute enabled

    def test_apply_mode_presets_none(self):
        """Test no mode preset returns original values."""
        from dotmatrix.cli import _apply_mode_presets

        convex_edge, palette, sensitive_occlusion, morph_enhance, reconstitute = _apply_mode_presets(
            mode=None,
            convex_edge=True,
            palette='rgb',
            sensitive_occlusion=True,
            morph_enhance=False,
            reconstitute=True,
            debug=False
        )

        assert convex_edge is True  # Unchanged
        assert palette == 'rgb'  # Unchanged
        assert sensitive_occlusion is True  # Unchanged
        assert morph_enhance is False  # Unchanged
        assert reconstitute is True  # Unchanged

    def test_apply_mode_presets_case_insensitive(self):
        """Test mode preset is case-insensitive."""
        from dotmatrix.cli import _apply_mode_presets

        # Test uppercase
        convex_edge, palette, _, _, _ = _apply_mode_presets(
            mode='HALFTONE',
            convex_edge=False,
            palette='cmyk',
            sensitive_occlusion=False,
            morph_enhance=False,
            reconstitute=True,
            debug=False
        )
        assert convex_edge is True

        # Test mixed case
        convex_edge, palette, _, _, _ = _apply_mode_presets(
            mode='Cmyk-Sep',
            convex_edge=False,
            palette='cmyk',
            sensitive_occlusion=False,
            morph_enhance=False,
            reconstitute=True,
            debug=False
        )
        assert palette == 'cmyk-sep'


class TestCLIModeIntegration:
    """Test --mode option via CLI subprocess."""

    def test_cli_mode_standard(self, test_image_single_circle):
        """Test CLI with --mode standard."""
        image_path, _ = test_image_single_circle

        result = subprocess.run(
            ['dotmatrix', '-i', str(image_path), '--mode', 'standard', '-f', 'json', '--no-extract'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_cli_mode_halftone(self, test_image_single_circle):
        """Test CLI with --mode halftone (JSON output with --no-reconstitute)."""
        image_path, _ = test_image_single_circle

        # halftone mode enables reconstitute by default, use --no-reconstitute for JSON output
        result = subprocess.run(
            ['dotmatrix', '-i', str(image_path), '--mode', 'halftone', '--no-reconstitute', '-f', 'json', '--no-extract'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_cli_mode_cmyk_sep(self, test_image_single_circle):
        """Test CLI with --mode cmyk-sep (JSON output with --no-reconstitute)."""
        image_path, _ = test_image_single_circle

        # cmyk-sep mode enables reconstitute by default, use --no-reconstitute for JSON output
        result = subprocess.run(
            ['dotmatrix', '-i', str(image_path), '--mode', 'cmyk-sep', '--no-reconstitute', '-f', 'json', '--no-extract'],
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
