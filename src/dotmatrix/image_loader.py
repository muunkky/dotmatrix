"""Image loading and validation module."""

from pathlib import Path
from typing import Union
import numpy as np
import cv2


class ImageLoadError(Exception):
    """Raised when an image cannot be loaded."""
    pass


class ImageFormatError(Exception):
    """Raised when an image format is not supported."""
    pass


def load_image(path: Union[str, Path]) -> np.ndarray:
    """Load an image file and return as BGR numpy array.

    Args:
        path: Path to image file (PNG, JPG, JPEG)

    Returns:
        Image as BGR numpy array (height, width, 3)

    Raises:
        ImageLoadError: If file doesn't exist or cannot be loaded
        ImageFormatError: If file format is not supported

    Example:
        >>> image = load_image("photo.png")
        >>> print(image.shape)  # (height, width, 3)
    """
    # Convert to Path object
    path = Path(path)

    # Check file exists
    if not path.exists():
        raise ImageLoadError(f"Image file does not exist: {path}")

    # Check file extension
    valid_extensions = {'.png', '.jpg', '.jpeg'}
    if path.suffix.lower() not in valid_extensions:
        raise ImageFormatError(
            f"Unsupported image format '{path.suffix}'. "
            f"Supported formats: {', '.join(valid_extensions)}"
        )

    # Load image using OpenCV
    image = cv2.imread(str(path))

    # Check if image was loaded successfully
    if image is None:
        raise ImageLoadError(
            f"Failed to load image: {path}. "
            f"File may be corrupted or not a valid image."
        )

    # Validate image dimensions
    if image.size == 0:
        raise ImageLoadError(f"Image has invalid dimensions: {path}")

    return image
