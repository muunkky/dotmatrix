"""Fit metric for measuring circle detection accuracy from diff images.

This module provides quantitative measurement of how well detected circles
match the original dots in an image. It analyzes diff images to determine:
- Overfit: Detected circles extend beyond original dot boundaries (black pixels)
- Underfit: Original dot colors showing through detected circles (colored pixels)
- Fit score: Overall quality metric (1.0 = perfect, 0.0 = no match)
"""

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class FitMetrics:
    """Container for circle fit accuracy metrics.

    Attributes:
        fit_score: Overall fit quality (0.0 to 1.0, higher is better)
        overfit_ratio: Proportion of pixels that are overfit (0.0 to 1.0)
        underfit_ratio: Proportion of pixels that are underfit (0.0 to 1.0)
        overfit_pixels: Raw count of overfit pixels
        underfit_pixels: Raw count of underfit pixels
        total_pixels: Total pixels in the image
    """

    fit_score: float
    overfit_ratio: float
    underfit_ratio: float
    overfit_pixels: int
    underfit_pixels: int
    total_pixels: int

    @property
    def fit_bias(self) -> float:
        """Calculate fit bias: positive = overfit, negative = underfit, 0 = balanced."""
        return self.overfit_ratio - self.underfit_ratio

    def to_dict(self) -> dict:
        """Convert metrics to dictionary for serialization."""
        return {
            'fit_score': self.fit_score,
            'overfit_ratio': self.overfit_ratio,
            'underfit_ratio': self.underfit_ratio,
            'overfit_pixels': self.overfit_pixels,
            'underfit_pixels': self.underfit_pixels,
            'total_pixels': self.total_pixels,
        }


def calculate_fit_accuracy(
    diff_image: np.ndarray,
    background_color: Tuple[int, int, int] = (255, 255, 255),
    overfit_threshold: int = 30,
) -> FitMetrics:
    """Calculate fit accuracy metrics from a diff image.

    The diff image shows the difference between original and reconstructed images:
    - Background pixels: Match perfectly (counted toward fit_score)
    - Black/dark pixels: Overfit - detected circles extend beyond original dots
    - Colored pixels: Underfit - original dot color showing through (circle too small)

    Args:
        diff_image: RGB diff image as numpy array (H, W, 3)
        background_color: The background color (default white)
        overfit_threshold: Maximum brightness value considered as overfit (default 30)
                          Pixels with all RGB values <= this are counted as overfit

    Returns:
        FitMetrics dataclass with accuracy measurements
    """
    if diff_image.ndim != 3 or diff_image.shape[2] != 3:
        raise ValueError("diff_image must be RGB with shape (H, W, 3)")

    total_pixels = diff_image.shape[0] * diff_image.shape[1]

    # Background mask: pixels matching background color (perfect fit)
    background = np.array(background_color, dtype=np.uint8)
    background_mask = np.all(diff_image == background, axis=-1)

    # Overfit mask: dark pixels (black or near-black) indicate drawn circle
    # extends beyond original dot boundary
    max_channel = np.max(diff_image, axis=-1)
    overfit_mask = max_channel <= overfit_threshold

    # Underfit mask: colored pixels (not background, not dark)
    # These are original dot colors showing through the detected circle
    underfit_mask = ~background_mask & ~overfit_mask

    overfit_pixels = int(np.sum(overfit_mask))
    underfit_pixels = int(np.sum(underfit_mask))

    # Calculate ratios
    overfit_ratio = overfit_pixels / total_pixels if total_pixels > 0 else 0.0
    underfit_ratio = underfit_pixels / total_pixels if total_pixels > 0 else 0.0

    # Fit score: proportion of pixels that match (background = perfect)
    fit_score = 1.0 - overfit_ratio - underfit_ratio

    return FitMetrics(
        fit_score=fit_score,
        overfit_ratio=overfit_ratio,
        underfit_ratio=underfit_ratio,
        overfit_pixels=overfit_pixels,
        underfit_pixels=underfit_pixels,
        total_pixels=total_pixels,
    )
