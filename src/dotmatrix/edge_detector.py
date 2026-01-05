"""Edge detection module for improved circle detection with overlapping circles.

This module implements Canny edge detection and adaptive thresholding preprocessing
to enhance circle detection accuracy, particularly for overlapping circles.

Part of M2 milestone: Overlapping Circle Detection
Roadmap: v1 > M2 > advanced-detection > edge-detection project

TDD Spec:
- False positive rate < 10% on overlapping circles
- Performance overhead < 20%
"""

import numpy as np
import cv2
from typing import Tuple, Optional


def detect_edges_canny(
    image: np.ndarray,
    low_threshold: int = 50,
    high_threshold: int = 150,
    aperture_size: int = 3
) -> np.ndarray:
    """Apply Canny edge detection to image.
    
    Uses Canny edge detector with configurable thresholds to identify edges
    in the image. This preprocessing step improves circle detection for
    overlapping circles by clearly defining boundaries.
    
    Args:
        image: Input grayscale image (uint8)
        low_threshold: Lower threshold for Canny edge detection (default: 50)
        high_threshold: Upper threshold for Canny edge detection (default: 150)
        aperture_size: Sobel kernel size for gradient calculation (default: 3)
        
    Returns:
        Binary edge map (uint8) where edges are 255, non-edges are 0
        
    Examples:
        >>> image = cv2.imread('circles.png', cv2.IMREAD_GRAYSCALE)
        >>> edges = detect_edges_canny(image, low_threshold=50, high_threshold=150)
        >>> # Use edges for improved circle detection
    """
    if image is None or image.size == 0:
        raise ValueError("Input image cannot be None or empty")
    
    # Ensure image is grayscale
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Canny edge detection
    edges = cv2.Canny(
        image,
        threshold1=low_threshold,
        threshold2=high_threshold,
        apertureSize=aperture_size,
        L2gradient=True  # More accurate gradient calculation
    )
    
    return edges


def apply_adaptive_threshold(
    image: np.ndarray,
    block_size: int = 11,
    c: int = 2
) -> np.ndarray:
    """Apply adaptive thresholding to handle varying lighting conditions.
    
    Uses Gaussian adaptive thresholding to create a binary image that
    handles non-uniform lighting. This preprocessing step is useful before
    edge detection when the input has varying illumination.
    
    Args:
        image: Input grayscale image (uint8)
        block_size: Size of neighborhood for threshold calculation (odd number)
        c: Constant subtracted from weighted mean (default: 2)
        
    Returns:
        Binary thresholded image (uint8) where foreground is 255, background is 0
        
    Examples:
        >>> image = cv2.imread('uneven_lighting.png', cv2.IMREAD_GRAYSCALE)
        >>> binary = apply_adaptive_threshold(image, block_size=11)
        >>> edges = detect_edges_canny(binary)
    """
    if image is None or image.size == 0:
        raise ValueError("Input image cannot be None or empty")
    
    # Ensure image is grayscale
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Ensure block_size is odd
    if block_size % 2 == 0:
        block_size += 1
    
    # Apply adaptive threshold
    thresholded = cv2.adaptiveThreshold(
        image,
        maxValue=255,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=block_size,
        C=c
    )
    
    return thresholded


def calculate_false_positive_rate(
    detected: np.ndarray,
    ground_truth: np.ndarray,
    tolerance: int = 2
) -> float:
    """Calculate false positive rate by comparing detected edges to ground truth.
    
    Computes the percentage of detected edge pixels that are not within
    tolerance distance of any ground truth edge. This metric measures
    the accuracy of edge detection.
    
    Args:
        detected: Binary edge map from detection (uint8)
        ground_truth: Binary ground truth edge map (uint8)
        tolerance: Distance in pixels to consider as match (default: 2)
        
    Returns:
        False positive rate as float between 0.0 and 1.0
        
    Examples:
        >>> detected = detect_edges_canny(image)
        >>> fpr = calculate_false_positive_rate(detected, ground_truth)
        >>> assert fpr < 0.10, "FPR exceeds 10% threshold"
    """
    if detected.shape != ground_truth.shape:
        raise ValueError("Detected and ground truth must have same shape")
    
    # Binarize if needed
    detected_binary = (detected > 0).astype(np.uint8) * 255
    gt_binary = (ground_truth > 0).astype(np.uint8) * 255
    
    # Get coordinates of detected edges
    detected_coords = np.column_stack(np.where(detected_binary > 0))
    if len(detected_coords) == 0:
        return 0.0  # No detections, no false positives
    
    # Dilate ground truth by tolerance to create "acceptable" region
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*tolerance+1, 2*tolerance+1))
    gt_dilated = cv2.dilate(gt_binary, kernel)
    
    # Count false positives: detected pixels not in dilated ground truth
    false_positives = np.sum((detected_binary > 0) & (gt_dilated == 0))
    total_detected = np.sum(detected_binary > 0)
    
    if total_detected == 0:
        return 0.0
    
    fpr = false_positives / total_detected
    return float(fpr)


class EdgeDetector:
    """Edge detector with configurable preprocessing and Canny detection.
    
    Provides a complete edge detection pipeline with optional adaptive
    thresholding preprocessing and configurable Canny edge detection.
    
    Attributes:
        canny_low: Lower threshold for Canny edge detection
        canny_high: Upper threshold for Canny edge detection
        use_adaptive_threshold: Whether to apply adaptive thresholding first
        block_size: Block size for adaptive thresholding
        aperture_size: Sobel kernel size for Canny
        
    Examples:
        >>> detector = EdgeDetector(canny_low=50, canny_high=150)
        >>> edges = detector.process(image)
        >>> # Use edges for circle detection
    """
    
    def __init__(
        self,
        canny_low: int = 50,
        canny_high: int = 150,
        use_adaptive_threshold: bool = False,
        block_size: int = 11,
        aperture_size: int = 3
    ):
        """Initialize EdgeDetector with parameters.
        
        Args:
            canny_low: Lower threshold for Canny (default: 50)
            canny_high: Upper threshold for Canny (default: 150)
            use_adaptive_threshold: Apply adaptive threshold first (default: False)
            block_size: Block size for adaptive threshold (default: 11)
            aperture_size: Sobel kernel size (default: 3)
        """
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.use_adaptive_threshold = use_adaptive_threshold
        self.block_size = block_size
        self.aperture_size = aperture_size
    
    def process(self, image: np.ndarray) -> np.ndarray:
        """Process image through edge detection pipeline.
        
        Applies optional adaptive thresholding followed by Canny edge detection.
        
        Args:
            image: Input grayscale image (uint8)
            
        Returns:
            Binary edge map (uint8)
        """
        # Apply preprocessing if enabled
        if self.use_adaptive_threshold:
            image = apply_adaptive_threshold(image, block_size=self.block_size)
        
        # Apply Canny edge detection
        edges = detect_edges_canny(
            image,
            low_threshold=self.canny_low,
            high_threshold=self.canny_high,
            aperture_size=self.aperture_size
        )
        
        return edges
