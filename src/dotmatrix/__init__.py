"""DotMatrix: Circle detection CLI tool.

DotMatrix detects circles in images and outputs their center coordinates,
radius, and color - even when circles overlap.
"""

__version__ = "0.1.0"
__author__ = "Cameron"
__license__ = "MIT"

from .image_loader import load_image, ImageLoadError, ImageFormatError
from .circle_detector import Circle, detect_circles
from .color_extractor import extract_color
from .formatter import format_json, format_csv

__all__ = [
    "load_image",
    "ImageLoadError",
    "ImageFormatError",
    "Circle",
    "detect_circles",
    "extract_color",
    "format_json",
    "format_csv",
]
