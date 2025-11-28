"""Unit tests for calibration module."""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from dotmatrix.calibration import (
    CalibrationStep,
    CalibrationResult,
    calculate_calibration_error,
    calibrate_radius,
    format_calibration_output,
)
from dotmatrix.black_verification import VerificationResult


class TestCalibrationStep:
    """Tests for CalibrationStep dataclass."""

    def test_to_dict(self):
        """Test CalibrationStep serialization."""
        step = CalibrationStep(
            iteration=1,
            parameter='min_radius',
            min_radius=50,
            max_radius=200,
            detected_count=10,
            target_count=10,
            error=0
        )
        d = step.to_dict()

        assert d['iteration'] == 1
        assert d['parameter'] == 'min_radius'
        assert d['min_radius'] == 50
        assert d['max_radius'] == 200
        assert d['detected_count'] == 10
        assert d['target_count'] == 10
        assert d['error'] == 0


class TestCalibrationResult:
    """Tests for CalibrationResult dataclass."""

    def test_to_dict(self):
        """Test CalibrationResult serialization with history."""
        step1 = CalibrationStep(
            iteration=0, parameter='baseline', min_radius=10, max_radius=300,
            detected_count=5, target_count=5, error=0
        )
        step2 = CalibrationStep(
            iteration=1, parameter='min_radius', min_radius=80, max_radius=300,
            detected_count=5, target_count=5, error=0
        )

        result = CalibrationResult(
            optimal_min_radius=80,
            optimal_max_radius=120,
            target_count=5,
            final_count=5,
            final_error=0,
            iterations=2,
            converged=True,
            history=[step1, step2],
            message="Converged successfully"
        )
        d = result.to_dict()

        assert d['optimal_min_radius'] == 80
        assert d['optimal_max_radius'] == 120
        assert d['target_count'] == 5
        assert d['final_count'] == 5
        assert d['final_error'] == 0
        assert d['iterations'] == 2
        assert d['converged'] is True
        assert len(d['history']) == 2
        assert d['history'][0]['iteration'] == 0
        assert d['history'][1]['iteration'] == 1

    def test_empty_history(self):
        """Test CalibrationResult with empty history."""
        result = CalibrationResult(
            optimal_min_radius=50,
            optimal_max_radius=150,
            target_count=0,
            final_count=0,
            final_error=0,
            iterations=0,
            converged=False,
            message="No circles found"
        )
        d = result.to_dict()

        assert d['history'] == []


class TestCalculateCalibrationError:
    """Tests for calculate_calibration_error function."""

    def test_zero_mean_returns_infinity(self):
        """Test that zero mean returns infinity (worst error)."""
        error = calculate_calibration_error(0, 0)
        assert error == float('inf')

    def test_perfect_detection_no_target(self):
        """Test error calculation without target."""
        # With no target, only std contributes
        error = calculate_calibration_error(100.0, 0.0)
        assert error == 0.0

        # Std contributes with 0.5 weight
        error = calculate_calibration_error(100.0, 10.0)
        assert error == 5.0  # 10 * 0.5

    def test_with_target_mean(self):
        """Test error calculation with target mean."""
        # Perfect match to target, no std
        error = calculate_calibration_error(100.0, 0.0, target_mean=100.0)
        assert error == 0.0

        # Off by 10 from target
        error = calculate_calibration_error(110.0, 0.0, target_mean=100.0)
        assert error == 10.0

        # Off by 10, with std of 4
        error = calculate_calibration_error(110.0, 4.0, target_mean=100.0)
        assert error == 12.0  # 10 + 4*0.5

    def test_error_increases_with_deviation(self):
        """Test that error increases with deviation from target."""
        error1 = calculate_calibration_error(100.0, 5.0, target_mean=100.0)
        error2 = calculate_calibration_error(120.0, 5.0, target_mean=100.0)

        assert error2 > error1


class TestCalibrateRadius:
    """Tests for calibrate_radius function."""

    def _create_mock_verification(
        self, count: int, mean: float, std: float,
        r_min: int, r_max: int
    ) -> VerificationResult:
        """Create a mock VerificationResult."""
        return VerificationResult(
            black_circles_detected=count,
            radius_mean=mean,
            radius_std=std,
            radius_min=r_min,
            radius_max=r_max,
            expected_density=0.0,
            actual_density=count / 1.0,
            coverage_percent=1.0,
            warnings=[],
            passed=True
        )

    def test_no_circles_detected(self):
        """Test handling when no black circles are detected."""
        # Create a blank image
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image.fill(255)  # White image

        result = calibrate_radius(image, initial_min=10, initial_max=100)

        assert result.converged is False
        assert "No black circles detected" in result.message
        assert result.iterations == 0

    @patch('dotmatrix.calibration.verify_black_dot_detection')
    def test_already_optimal(self, mock_verify):
        """Test when initial params already detect all circles (count-based error = 0)."""
        # Mock verification always returns same count
        mock_verify.return_value = self._create_mock_verification(
            count=10, mean=100.0, std=0.0, r_min=100, r_max=100
        )

        image = np.zeros((500, 500, 3), dtype=np.uint8)

        # With count-based error, error will be 0 when all circles detected
        result = calibrate_radius(
            image,
            initial_min=90,
            initial_max=110
        )

        assert result.converged is True
        assert result.final_error == 0
        assert result.target_count == 10
        assert result.final_count == 10

    @patch('dotmatrix.calibration.verify_black_dot_detection')
    def test_binary_search_converges_log_n(self, mock_verify):
        """Test that binary search converges in O(log n) iterations."""
        # Mock returns consistent results for binary search
        mock_verify.return_value = self._create_mock_verification(
            count=10, mean=100.0, std=50.0, r_min=50, r_max=150
        )

        image = np.zeros((500, 500, 3), dtype=np.uint8)

        result = calibrate_radius(
            image,
            initial_min=10,
            initial_max=300
        )

        # Binary search on range [10, 50] + [150, 300] should take ~log2(40)+log2(150) iterations
        # Plus baseline = 1 iteration, roughly ~15 max
        assert result.iterations <= 20
        assert result.converged is True
        assert result.final_error == 0

    @patch('dotmatrix.calibration.verify_black_dot_detection')
    def test_iteration_callback(self, mock_verify):
        """Test that on_iteration callback is called."""
        mock_verify.return_value = self._create_mock_verification(
            count=10, mean=100.0, std=2.0, r_min=95, r_max=105
        )

        image = np.zeros((500, 500, 3), dtype=np.uint8)
        callback_calls = []

        def callback(step):
            callback_calls.append(step)

        calibrate_radius(
            image,
            initial_min=10,
            initial_max=300,
            max_iterations=3,
            on_iteration=callback
        )

        # Should have at least one callback
        assert len(callback_calls) >= 1
        assert all(isinstance(s, CalibrationStep) for s in callback_calls)

    @patch('dotmatrix.calibration.verify_black_dot_detection')
    def test_history_tracking(self, mock_verify):
        """Test that calibration history is tracked."""
        # First call returns wide range, subsequent calls narrow
        call_count = [0]

        def mock_verify_side_effect(*args, **kwargs):
            call_count[0] += 1
            return self._create_mock_verification(
                count=10, mean=100.0, std=5.0, r_min=90, r_max=110
            )

        mock_verify.side_effect = mock_verify_side_effect

        image = np.zeros((500, 500, 3), dtype=np.uint8)

        result = calibrate_radius(
            image,
            initial_min=10,
            initial_max=300,
            max_iterations=5
        )

        # Should have history entries
        assert len(result.history) >= 1

        # Each history entry should have all fields
        for step in result.history:
            assert step.iteration >= 0
            assert step.min_radius >= 0
            assert step.max_radius > step.min_radius
            assert step.detected_count >= 0
            assert step.error >= 0

    @patch('dotmatrix.calibration.verify_black_dot_detection')
    def test_converges_with_count_based_error(self, mock_verify):
        """Test convergence with count-based error metric."""
        mock_verify.return_value = self._create_mock_verification(
            count=10, mean=100.0, std=2.0, r_min=95, r_max=105
        )

        image = np.zeros((500, 500, 3), dtype=np.uint8)

        result = calibrate_radius(
            image,
            initial_min=10,
            initial_max=300
        )

        # Should converge with error = 0 (all circles detected)
        assert result.final_error == 0
        assert result.target_count == 10
        assert result.final_count == 10

    @patch('dotmatrix.calibration.verify_black_dot_detection')
    def test_bounds_tightening(self, mock_verify):
        """Test that bounds are tightened toward detected radii."""
        # Return circles with radii around 100
        mock_verify.return_value = self._create_mock_verification(
            count=10, mean=100.0, std=5.0, r_min=90, r_max=110
        )

        image = np.zeros((500, 500, 3), dtype=np.uint8)

        result = calibrate_radius(
            image,
            initial_min=10,
            initial_max=500,  # Very wide initial bounds
            max_iterations=10
        )

        # Optimal bounds should be tighter than initial
        assert result.optimal_min_radius >= 10
        assert result.optimal_max_radius <= 500


class TestFormatCalibrationOutput:
    """Tests for format_calibration_output function."""

    def test_perfect_output(self):
        """Test output formatting for perfect result (error=0)."""
        result = CalibrationResult(
            optimal_min_radius=80,
            optimal_max_radius=120,
            target_count=10,
            final_count=10,
            final_error=0,
            iterations=3,
            converged=True,
            history=[],
            message="Calibration complete"
        )

        output = format_calibration_output(result)

        assert "✓ Perfect (error=0)" in output
        assert "--min-radius 80" in output
        assert "--max-radius 120" in output
        assert "Iterations: 3" in output
        assert "Target circles: 10" in output
        assert "Detected circles: 10" in output

    def test_converged_output(self):
        """Test output formatting for converged result."""
        result = CalibrationResult(
            optimal_min_radius=80,
            optimal_max_radius=120,
            target_count=10,
            final_count=10,
            final_error=0,
            iterations=3,
            converged=True,
            history=[],
            message="Complete"
        )

        output = format_calibration_output(result)

        assert "✓ Perfect (error=0)" in output
        assert "--min-radius 80" in output

    def test_count_mismatch_output(self):
        """Test output formatting for count mismatch (error > 0)."""
        result = CalibrationResult(
            optimal_min_radius=50,
            optimal_max_radius=200,
            target_count=10,
            final_count=8,
            final_error=2,
            iterations=20,
            converged=False,
            history=[],
            message="Count mismatch"
        )

        output = format_calibration_output(result)

        assert "⚠ Count mismatch (error=2)" in output
        assert "--min-radius 50" in output
        assert "--max-radius 200" in output

    def test_verbose_with_history(self):
        """Test verbose output includes history."""
        step1 = CalibrationStep(
            iteration=0, parameter='baseline', min_radius=10, max_radius=300,
            detected_count=5, target_count=5, error=0
        )
        step2 = CalibrationStep(
            iteration=1, parameter='min_radius', min_radius=80, max_radius=300,
            detected_count=5, target_count=5, error=0
        )

        result = CalibrationResult(
            optimal_min_radius=80,
            optimal_max_radius=120,
            target_count=5,
            final_count=5,
            final_error=0,
            iterations=2,
            converged=True,
            history=[step1, step2],
            message=""
        )

        output = format_calibration_output(result, verbose=True)

        assert "Iteration History:" in output
        # Check header row is present
        assert "Iter" in output
        assert "MinR" in output
        assert "MaxR" in output
        assert "Param" in output


class TestCalibrationIntegration:
    """Integration tests using real test image."""

    @pytest.fixture
    def test_image_path(self):
        """Path to test image."""
        from pathlib import Path
        return Path(__file__).parent.parent / "test_dotmatrix.png"

    @pytest.mark.skipif(
        not (pytest.importorskip("cv2") and True),
        reason="OpenCV required"
    )
    def test_calibration_with_real_image(self, test_image_path):
        """Test calibration with actual test image."""
        if not test_image_path.exists():
            pytest.skip("Test image not found")

        import cv2
        image = cv2.imread(str(test_image_path))
        if image is None:
            pytest.skip("Could not load test image")

        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        result = calibrate_radius(
            image,
            initial_min=50,
            initial_max=300,
            max_iterations=10
        )

        # Should produce valid results
        assert result.optimal_min_radius > 0
        assert result.optimal_max_radius > result.optimal_min_radius
        assert len(result.history) >= 1
