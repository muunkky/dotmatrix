"""Circle detection using Hough Circle Transform."""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import cv2


# Sensitivity presets for HoughCircles parameters
SENSITIVITY_PRESETS = {
    "strict": {
        "param1": 100,  # Higher threshold = stricter edge detection
        "param2": 40,   # Higher threshold = fewer false positives
    },
    "normal": {
        "param1": 50,   # Balanced threshold
        "param2": 30,   # Balanced accumulator threshold
    },
    "relaxed": {
        "param1": 30,   # Lower threshold = more permissive
        "param2": 20,   # Lower threshold = more detections
    },
}


@dataclass
class Circle:
    """Represents a detected circle.

    Attributes:
        center_x: X coordinate of circle center
        center_y: Y coordinate of circle center
        radius: Circle radius in pixels
        confidence: Detection confidence score (0-100%)
    """
    center_x: float
    center_y: float
    radius: float
    confidence: float = 100.0

    def __repr__(self) -> str:
        return f"Circle(center=({self.center_x:.1f}, {self.center_y:.1f}), radius={self.radius:.1f}, confidence={self.confidence:.1f})"


def detect_circles(
    image: np.ndarray,
    min_radius: int = 10,
    max_radius: int = 500,
    sensitivity: Optional[str] = None,
    min_distance: int = 20
) -> List[Circle]:
    """Detect circles in an image using Hough Circle Transform.

    Uses OpenCV's HoughCircles with the HOUGH_GRADIENT method. The algorithm:
    1. Converts image to grayscale
    2. Applies Gaussian blur to reduce noise
    3. Uses Canny edge detection internally
    4. Performs Hough voting to find circles

    Args:
        image: Input image as BGR numpy array (height, width, 3)
        min_radius: Minimum circle radius in pixels (default: 10)
        max_radius: Maximum circle radius in pixels (default: 500)
        sensitivity: Detection sensitivity preset: "strict", "normal", or "relaxed"
                    (default: "normal"). Strict detects fewer circles with high
                    confidence, relaxed detects more circles with lower thresholds.
        min_distance: Minimum distance between circle centers in pixels (default: 20).
                     Larger values prevent overlapping detections.

    Returns:
        List of detected Circle objects, sorted by descending radius

    Raises:
        ValueError: If image is invalid (empty or wrong dimensions) or
                   sensitivity preset is invalid

    Example:
        >>> image = load_image("photo.png")
        >>> circles = detect_circles(image, min_radius=20, max_radius=200)
        >>> # Use strict sensitivity for high-quality images
        >>> circles = detect_circles(image, sensitivity="strict")
        >>> # Use relaxed sensitivity for noisy images
        >>> circles = detect_circles(image, sensitivity="relaxed")
        >>> # Prevent overlapping detections with larger min_distance
        >>> circles = detect_circles(image, min_distance=50)
    """
    # Validate input
    if image.size == 0:
        raise ValueError("Image is empty")

    if len(image.shape) != 3 or image.shape[2] != 3:
        raise ValueError(
            f"Image must be a 3-channel BGR image, got shape {image.shape}"
        )

    # Default to normal sensitivity
    if sensitivity is None:
        sensitivity = "normal"

    # Validate sensitivity preset
    if sensitivity not in SENSITIVITY_PRESETS:
        valid_options = ", ".join(SENSITIVITY_PRESETS.keys())
        raise ValueError(
            f"Invalid sensitivity: '{sensitivity}'. "
            f"Must be one of: {valid_options}"
        )

    # Get parameters for sensitivity preset
    params = SENSITIVITY_PRESETS[sensitivity]

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise and improve circle detection
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    # Detect circles using Hough Circle Transform
    # Parameters configured by sensitivity preset and user-provided filters
    detected = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,  # Inverse ratio of accumulator resolution
        minDist=min_distance,  # Minimum distance between circle centers (configurable)
        param1=params["param1"],  # Upper threshold for Canny edge detector
        param2=params["param2"],  # Accumulator threshold for circle centers
        minRadius=min_radius,  # Minimum circle radius (configurable)
        maxRadius=max_radius  # Maximum circle radius (configurable)
    )

    # Convert to list of Circle objects with confidence scores
    circles = []

    if detected is not None:
        # detected shape is (1, N, 3) where each row is [x, y, radius]
        detected = np.round(detected[0, :]).astype(int)

        # HoughCircles returns circles sorted by accumulator value (best first)
        # Calculate confidence based on detection order as proxy for quality
        num_circles = len(detected)

        for idx, (x, y, r) in enumerate(detected):
            # Confidence formula: quadratic falloff from 100% to lower values
            # First circle = 100%, subsequent circles decrease
            if num_circles == 1:
                confidence = 100.0
            else:
                # Normalize index to 0-1 range
                normalized_idx = idx / (num_circles - 1)
                # Quadratic falloff: confidence = 100 * (1 - normalized_idx)^2
                confidence = 100.0 * (1 - normalized_idx) ** 2

            circles.append(Circle(
                center_x=float(x),
                center_y=float(y),
                radius=float(r),
                confidence=round(confidence, 1)
            ))

        # Sort by descending radius (larger circles first), preserving confidence
        circles.sort(key=lambda c: c.radius, reverse=True)

    return circles
