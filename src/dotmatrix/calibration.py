"""Auto-calibration for radius parameters using black dot ground truth.

Uses binary search optimization to find optimal min_radius and max_radius
settings by detecting black dots and tightening bounds while maintaining
the same count. Black dots serve as ground truth because they're always
printed on top (never occluded).

The algorithm uses count-based error: error = 0 when detected_count == target_count.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Callable, Tuple
import numpy as np

from .black_verification import verify_black_dot_detection, VerificationResult


@dataclass
class CalibrationStep:
    """Single iteration of the calibration process."""
    iteration: int
    parameter: str  # 'min_radius' or 'max_radius' or 'baseline'
    min_radius: int
    max_radius: int
    detected_count: int
    target_count: int
    error: int  # abs(detected_count - target_count)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class CalibrationResult:
    """Result of radius calibration process."""
    optimal_min_radius: int
    optimal_max_radius: int
    target_count: int
    final_count: int
    final_error: int  # 0 means perfect calibration
    iterations: int
    converged: bool
    history: List[CalibrationStep] = field(default_factory=list)
    message: str = ""
    # Additional stats from ground truth detection
    detected_radius_min: int = 0
    detected_radius_max: int = 0
    detected_radius_mean: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['history'] = [step.to_dict() for step in self.history]
        return result


def _binary_search_min_radius(
    image: np.ndarray,
    target_count: int,
    low: int,
    high: int,
    fixed_max: int,
    ink_threshold: int,
    black_threshold: int,
    on_iteration: Optional[Callable[[CalibrationStep], None]] = None,
    history: Optional[List[CalibrationStep]] = None,
    iteration_offset: int = 0,
) -> Tuple[int, int]:
    """Binary search for the largest min_radius that still detects target_count circles.

    Args:
        image: RGB image
        target_count: Number of circles we must detect
        low: Lower bound of search (start here, known to work)
        high: Upper bound of search (may lose circles)
        fixed_max: Fixed max_radius during this search
        ink_threshold: Threshold for ink separation
        black_threshold: Threshold for black detection
        on_iteration: Optional callback
        history: Optional list to append steps to
        iteration_offset: Offset for iteration numbering

    Returns:
        Tuple of (optimal_min_radius, iterations_used)
    """
    iterations = 0
    best_min = low

    while low <= high:
        mid = (low + high) // 2
        iterations += 1

        verification = verify_black_dot_detection(
            image,
            min_radius=mid,
            max_radius=fixed_max,
            ink_threshold=ink_threshold,
            black_threshold=black_threshold,
        )

        count = verification.black_circles_detected
        error = abs(count - target_count)

        step = CalibrationStep(
            iteration=iteration_offset + iterations,
            parameter='min_radius',
            min_radius=mid,
            max_radius=fixed_max,
            detected_count=count,
            target_count=target_count,
            error=error,
        )

        if history is not None:
            history.append(step)
        if on_iteration:
            on_iteration(step)

        if count >= target_count:
            # Still detecting all circles, try higher min_radius
            best_min = mid
            low = mid + 1
        else:
            # Lost circles, min_radius too high
            high = mid - 1

    return best_min, iterations


def _binary_search_max_radius(
    image: np.ndarray,
    target_count: int,
    low: int,
    high: int,
    fixed_min: int,
    ink_threshold: int,
    black_threshold: int,
    on_iteration: Optional[Callable[[CalibrationStep], None]] = None,
    history: Optional[List[CalibrationStep]] = None,
    iteration_offset: int = 0,
) -> Tuple[int, int]:
    """Binary search for the smallest max_radius that still detects target_count circles.

    Args:
        image: RGB image
        target_count: Number of circles we must detect
        low: Lower bound of search (may lose circles)
        high: Upper bound of search (start here, known to work)
        fixed_min: Fixed min_radius during this search
        ink_threshold: Threshold for ink separation
        black_threshold: Threshold for black detection
        on_iteration: Optional callback
        history: Optional list to append steps to
        iteration_offset: Offset for iteration numbering

    Returns:
        Tuple of (optimal_max_radius, iterations_used)
    """
    iterations = 0
    best_max = high

    while low <= high:
        mid = (low + high) // 2
        iterations += 1

        verification = verify_black_dot_detection(
            image,
            min_radius=fixed_min,
            max_radius=mid,
            ink_threshold=ink_threshold,
            black_threshold=black_threshold,
        )

        count = verification.black_circles_detected
        error = abs(count - target_count)

        step = CalibrationStep(
            iteration=iteration_offset + iterations,
            parameter='max_radius',
            min_radius=fixed_min,
            max_radius=mid,
            detected_count=count,
            target_count=target_count,
            error=error,
        )

        if history is not None:
            history.append(step)
        if on_iteration:
            on_iteration(step)

        if count >= target_count:
            # Still detecting all circles, try lower max_radius
            best_max = mid
            high = mid - 1
        else:
            # Lost circles, max_radius too low
            low = mid + 1

    return best_max, iterations


def calibrate_radius(
    image: np.ndarray,
    initial_min: int = 1,
    initial_max: int = 300,
    max_iterations: int = 50,
    target_mean_radius: Optional[float] = None,  # Kept for API compatibility, unused
    ink_threshold: int = 100,
    black_threshold: int = 60,
    on_iteration: Optional[Callable[[CalibrationStep], None]] = None,
) -> CalibrationResult:
    """Calibrate min/max radius parameters using black dot detection.

    Uses binary search to find the TIGHTEST radius bounds that detect
    all black circles. The algorithm:

    1. Detect with wide bounds to establish ground truth count
    2. Binary search min_radius: find LARGEST value where count == target
    3. Binary search max_radius: find SMALLEST value where count == target
    4. Return bounds with error = 0 (all circles detected)

    Error metric: abs(detected_count - target_count)
    Goal: error = 0

    Args:
        image: RGB image as numpy array (H, W, 3)
        initial_min: Starting minimum radius bound (default: 1)
        initial_max: Starting maximum radius bound (default: 300)
        max_iterations: Maximum total iterations (for both searches)
        target_mean_radius: DEPRECATED - kept for API compatibility, unused
        ink_threshold: Threshold for ink separation
        black_threshold: Threshold for black detection
        on_iteration: Optional callback called after each iteration

    Returns:
        CalibrationResult with optimal parameters and iteration history
    """
    history: List[CalibrationStep] = []

    # Step 1: Establish ground truth with wide bounds
    verification = verify_black_dot_detection(
        image,
        min_radius=initial_min,
        max_radius=initial_max,
        ink_threshold=ink_threshold,
        black_threshold=black_threshold,
    )

    target_count = verification.black_circles_detected

    if target_count == 0:
        return CalibrationResult(
            optimal_min_radius=initial_min,
            optimal_max_radius=initial_max,
            target_count=0,
            final_count=0,
            final_error=0,
            iterations=0,
            converged=False,
            history=[],
            message="No black circles detected. Cannot calibrate without ground truth."
        )

    # Record baseline
    baseline_step = CalibrationStep(
        iteration=0,
        parameter='baseline',
        min_radius=initial_min,
        max_radius=initial_max,
        detected_count=target_count,
        target_count=target_count,
        error=0,
    )
    history.append(baseline_step)
    if on_iteration:
        on_iteration(baseline_step)

    # Get detected radius range for search bounds
    detected_min_r = verification.radius_min
    detected_max_r = verification.radius_max
    detected_mean_r = verification.radius_mean

    # Step 2: Binary search for optimal min_radius
    # Search from initial_min up to detected_min_r (can't be higher than smallest circle)
    optimal_min, min_iters = _binary_search_min_radius(
        image=image,
        target_count=target_count,
        low=initial_min,
        high=detected_min_r,
        fixed_max=initial_max,
        ink_threshold=ink_threshold,
        black_threshold=black_threshold,
        on_iteration=on_iteration,
        history=history,
        iteration_offset=1,
    )

    # Step 3: Binary search for optimal max_radius
    # Search from detected_max_r up to initial_max (can't be lower than largest circle)
    optimal_max, max_iters = _binary_search_max_radius(
        image=image,
        target_count=target_count,
        low=detected_max_r,
        high=initial_max,
        fixed_min=optimal_min,
        ink_threshold=ink_threshold,
        black_threshold=black_threshold,
        on_iteration=on_iteration,
        history=history,
        iteration_offset=1 + min_iters,
    )

    # Step 4: Final verification
    final_verification = verify_black_dot_detection(
        image,
        min_radius=optimal_min,
        max_radius=optimal_max,
        ink_threshold=ink_threshold,
        black_threshold=black_threshold,
    )

    final_count = final_verification.black_circles_detected
    final_error = abs(final_count - target_count)

    total_iterations = 1 + min_iters + max_iters
    converged = final_error == 0

    if converged:
        message = f"Calibration complete. Found tightest bounds [{optimal_min}, {optimal_max}] for {target_count} circles."
    else:
        message = f"Warning: Final count {final_count} differs from target {target_count}."

    return CalibrationResult(
        optimal_min_radius=optimal_min,
        optimal_max_radius=optimal_max,
        target_count=target_count,
        final_count=final_count,
        final_error=final_error,
        iterations=total_iterations,
        converged=converged,
        history=history,
        message=message,
        detected_radius_min=detected_min_r,
        detected_radius_max=detected_max_r,
        detected_radius_mean=detected_mean_r,
    )


def format_calibration_output(result: CalibrationResult, verbose: bool = False) -> str:
    """Format calibration result for console output.

    Args:
        result: CalibrationResult to format
        verbose: If True, include iteration history

    Returns:
        Formatted string for console display
    """
    if result.final_error == 0:
        status = "✓ Perfect (error=0)"
    elif result.converged:
        status = "✓ Converged"
    else:
        status = f"⚠ Count mismatch (error={result.final_error})"

    lines = [
        "Radius Calibration Results:",
        f"  Status: {status}",
        f"  Target circles: {result.target_count}",
        f"  Detected circles: {result.final_count}",
        f"  Iterations: {result.iterations}",
        "",
        "Optimal Parameters:",
        f"  --min-radius {result.optimal_min_radius}",
        f"  --max-radius {result.optimal_max_radius}",
    ]

    if result.detected_radius_min > 0:
        lines.extend([
            "",
            "Detected Circle Stats:",
            f"  Smallest radius: {result.detected_radius_min}",
            f"  Largest radius: {result.detected_radius_max}",
            f"  Mean radius: {result.detected_radius_mean:.1f}",
        ])

    if result.message:
        lines.extend(["", f"Note: {result.message}"])

    if verbose and result.history:
        lines.extend(["", "Iteration History:"])
        lines.append("  Iter  Param       MinR  MaxR  Count  Target  Error")
        lines.append("  " + "-" * 55)
        for step in result.history:
            param_str = step.parameter[:10].ljust(10)
            lines.append(
                f"  {step.iteration:4d}  {param_str}  {step.min_radius:4d}  {step.max_radius:4d}  "
                f"{step.detected_count:5d}  {step.target_count:6d}  {step.error:5d}"
            )

    return "\n".join(lines)


# Backward compatibility: keep old function signature working
def calculate_calibration_error(
    detected_mean: float,
    detected_std: float,
    target_mean: Optional[float] = None,
    target_std: Optional[float] = None,
) -> float:
    """DEPRECATED: Old error metric based on std.

    Kept for backward compatibility. New code should use count-based error.
    """
    if detected_mean == 0:
        return float('inf')
    error = 0.0
    if target_mean is not None:
        error += abs(detected_mean - target_mean)
    error += detected_std * 0.5
    return error
