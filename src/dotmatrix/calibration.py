"""Auto-calibration for radius parameters using black dot ground truth.

Uses an iterative optimization algorithm to find optimal min_radius and max_radius
settings by comparing detected black dots against actual measurements. Black dots
serve as ground truth because they're always printed on top (never occluded).

The algorithm uses binary search optimization to minimize the error between
detected and actual circle radii.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Callable
import numpy as np

from .black_verification import verify_black_dot_detection, VerificationResult


@dataclass
class CalibrationStep:
    """Single iteration of the calibration process."""
    iteration: int
    min_radius: int
    max_radius: int
    detected_count: int
    detected_mean_radius: float
    detected_std_radius: float
    error: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class CalibrationResult:
    """Result of radius calibration process."""
    optimal_min_radius: int
    optimal_max_radius: int
    final_error: float
    iterations: int
    converged: bool
    history: List[CalibrationStep] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['history'] = [step.to_dict() for step in self.history]
        return result


def calculate_calibration_error(
    detected_mean: float,
    detected_std: float,
    target_mean: Optional[float] = None,
    target_std: Optional[float] = None,
) -> float:
    """Calculate error metric for calibration.

    The error metric combines:
    - Deviation from target mean radius (if provided)
    - Standard deviation (penalizes inconsistent detection)

    Lower error = better calibration.

    Args:
        detected_mean: Mean radius of detected circles
        detected_std: Standard deviation of detected radii
        target_mean: Optional target mean radius to match
        target_std: Optional target standard deviation

    Returns:
        Error value (lower is better)
    """
    if detected_mean == 0:
        return float('inf')  # No circles detected = worst error

    error = 0.0

    # If we have a target, penalize deviation from it
    if target_mean is not None:
        error += abs(detected_mean - target_mean)

    # Always penalize high variance (inconsistent detection)
    # Weight std less than mean error to prioritize accuracy
    error += detected_std * 0.5

    return error


def calibrate_radius(
    image: np.ndarray,
    initial_min: int = 10,
    initial_max: int = 300,
    tolerance: float = 2.0,
    max_iterations: int = 20,
    target_mean_radius: Optional[float] = None,
    ink_threshold: int = 100,
    black_threshold: int = 60,
    on_iteration: Optional[Callable[[CalibrationStep], None]] = None,
) -> CalibrationResult:
    """Calibrate min/max radius parameters using black dot detection.

    Uses iterative optimization to find radius bounds that produce
    accurate, consistent circle detection. The algorithm:

    1. Starts with initial bounds
    2. Runs detection with current params
    3. Calculates error from ground truth
    4. Adjusts bounds based on error direction
    5. Repeats until convergence or max iterations

    The optimization focuses on finding the "sweet spot" where:
    - min_radius is just below the smallest actual circles
    - max_radius is just above the largest actual circles

    Args:
        image: RGB image as numpy array (H, W, 3)
        initial_min: Starting minimum radius bound
        initial_max: Starting maximum radius bound
        tolerance: Convergence threshold (stop when error < tolerance)
        max_iterations: Maximum iterations before stopping
        target_mean_radius: Optional known target radius to optimize toward
        ink_threshold: Threshold for ink separation
        black_threshold: Threshold for black detection
        on_iteration: Optional callback called after each iteration

    Returns:
        CalibrationResult with optimal parameters and iteration history
    """
    history: List[CalibrationStep] = []

    # Current search bounds
    min_r = initial_min
    max_r = initial_max

    best_error = float('inf')
    best_min = min_r
    best_max = max_r

    # First pass: detect with wide bounds to establish baseline
    verification = verify_black_dot_detection(
        image,
        min_radius=min_r,
        max_radius=max_r,
        ink_threshold=ink_threshold,
        black_threshold=black_threshold,
    )

    if verification.black_circles_detected == 0:
        return CalibrationResult(
            optimal_min_radius=initial_min,
            optimal_max_radius=initial_max,
            final_error=float('inf'),
            iterations=0,
            converged=False,
            history=[],
            message="No black circles detected. Cannot calibrate without ground truth."
        )

    # Use detected radii as reference if no target provided
    if target_mean_radius is None:
        target_mean_radius = verification.radius_mean

    # Record initial state
    initial_error = calculate_calibration_error(
        verification.radius_mean,
        verification.radius_std,
        target_mean_radius
    )

    step = CalibrationStep(
        iteration=0,
        min_radius=min_r,
        max_radius=max_r,
        detected_count=verification.black_circles_detected,
        detected_mean_radius=verification.radius_mean,
        detected_std_radius=verification.radius_std,
        error=initial_error
    )
    history.append(step)

    if on_iteration:
        on_iteration(step)

    if initial_error < tolerance:
        return CalibrationResult(
            optimal_min_radius=min_r,
            optimal_max_radius=max_r,
            final_error=initial_error,
            iterations=1,
            converged=True,
            history=history,
            message="Already optimal with initial parameters."
        )

    best_error = initial_error
    best_min = min_r
    best_max = max_r

    # Optimization loop: adjust bounds based on detected radii
    for iteration in range(1, max_iterations + 1):
        # Strategy: tighten bounds toward detected mean
        # This assumes detected_mean is close to actual but bounds may be too wide

        detected_min = verification.radius_min
        detected_max = verification.radius_max
        detected_mean = verification.radius_mean

        # Add margin around detected range (10% padding)
        margin = max(5, int((detected_max - detected_min) * 0.1))

        # Tighten min_radius toward detected minimum (with margin)
        new_min = max(initial_min, detected_min - margin)

        # Tighten max_radius toward detected maximum (with margin)
        new_max = min(initial_max, detected_max + margin)

        # Ensure valid bounds
        if new_max <= new_min:
            new_max = new_min + margin * 2

        # Check if bounds changed significantly
        if abs(new_min - min_r) < 1 and abs(new_max - max_r) < 1:
            # Converged - bounds not changing
            return CalibrationResult(
                optimal_min_radius=best_min,
                optimal_max_radius=best_max,
                final_error=best_error,
                iterations=iteration,
                converged=True,
                history=history,
                message=f"Converged after {iteration} iterations."
            )

        min_r = new_min
        max_r = new_max

        # Re-run detection with tightened bounds
        verification = verify_black_dot_detection(
            image,
            min_radius=min_r,
            max_radius=max_r,
            ink_threshold=ink_threshold,
            black_threshold=black_threshold,
        )

        if verification.black_circles_detected == 0:
            # Lost all circles - revert and stop
            return CalibrationResult(
                optimal_min_radius=best_min,
                optimal_max_radius=best_max,
                final_error=best_error,
                iterations=iteration,
                converged=False,
                history=history,
                message=f"Stopped at iteration {iteration}: tightening bounds lost all circles."
            )

        error = calculate_calibration_error(
            verification.radius_mean,
            verification.radius_std,
            target_mean_radius
        )

        step = CalibrationStep(
            iteration=iteration,
            min_radius=min_r,
            max_radius=max_r,
            detected_count=verification.black_circles_detected,
            detected_mean_radius=verification.radius_mean,
            detected_std_radius=verification.radius_std,
            error=error
        )
        history.append(step)

        if on_iteration:
            on_iteration(step)

        # Track best result
        if error < best_error:
            best_error = error
            best_min = min_r
            best_max = max_r

        # Check convergence
        if error < tolerance:
            return CalibrationResult(
                optimal_min_radius=min_r,
                optimal_max_radius=max_r,
                final_error=error,
                iterations=iteration + 1,
                converged=True,
                history=history,
                message=f"Converged after {iteration + 1} iterations (error={error:.2f} < tolerance={tolerance})."
            )

    # Max iterations reached
    return CalibrationResult(
        optimal_min_radius=best_min,
        optimal_max_radius=best_max,
        final_error=best_error,
        iterations=max_iterations,
        converged=False,
        history=history,
        message=f"Max iterations ({max_iterations}) reached. Best error: {best_error:.2f}"
    )


def format_calibration_output(result: CalibrationResult, verbose: bool = False) -> str:
    """Format calibration result for console output.

    Args:
        result: CalibrationResult to format
        verbose: If True, include iteration history

    Returns:
        Formatted string for console display
    """
    lines = [
        "Radius Calibration Results:",
        f"  Status: {'✓ Converged' if result.converged else '⚠ Did not converge'}",
        f"  Iterations: {result.iterations}",
        f"  Final error: {result.final_error:.2f}",
        "",
        "Optimal Parameters:",
        f"  --min-radius {result.optimal_min_radius}",
        f"  --max-radius {result.optimal_max_radius}",
    ]

    if result.message:
        lines.extend(["", f"Note: {result.message}"])

    if verbose and result.history:
        lines.extend(["", "Iteration History:"])
        lines.append("  Iter  MinR  MaxR  Count   Mean   Std   Error")
        lines.append("  " + "-" * 50)
        for step in result.history:
            lines.append(
                f"  {step.iteration:4d}  {step.min_radius:4d}  {step.max_radius:4d}  "
                f"{step.detected_count:5d}  {step.detected_mean_radius:5.1f}  "
                f"{step.detected_std_radius:5.1f}  {step.error:5.2f}"
            )

    return "\n".join(lines)
