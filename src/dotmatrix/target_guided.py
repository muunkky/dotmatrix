"""Target-Guided Dot Optimization for Halftone Style Transfer.

This module implements algorithms for guiding flower/planetary dots toward
target positions and sizes extracted from a reference PNG halftone image.

Spike Investigation: feshwj
Feature Card: io1h5h (pending spike completion)

Algorithm: Per-Cluster Local Gradient with Target Assignment
1. Detect target circles per color channel from reference PNG
2. Build K-D tree for efficient nearest-neighbor lookup
3. For each source cluster, find nearest target cluster per color
4. Compute gradient toward matched target position/size
5. Apply gradient step with CMYK balance constraint (integrated with drift)
6. Repeat until convergence or max iterations

Cost Function (per dot):
    position_error = distance_to_target / max_distance
    radius_error = |r - target_r| / r
    mass_deviation = |actual_mass - expected_mass| / expected_mass
    
    total_cost = w_pos * position_error + w_rad * radius_error + w_mass * mass_deviation
    
    Configurable via --target-weight flag:
    - target_weight=0.0: Pure CMYK balance (existing drift)
    - target_weight=1.0: Pure target matching
    - target_weight=0.5: Balanced (default)
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

import cv2
import numpy as np

try:
    from scipy.spatial import KDTree
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from dotmatrix.circle_detector import detect_circles, Circle
from dotmatrix.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TargetCircle:
    """A circle detected from the target reference image."""
    x: float
    y: float
    radius: float
    color: str  # 'cyan', 'magenta', 'yellow', 'black'


@dataclass
class TargetGuidedConfig:
    """Configuration for target-guided optimization."""
    target_image_path: Path
    target_weight: float = 0.5  # Balance: 0=pure drift, 1=pure target
    position_weight: float = 0.5
    radius_weight: float = 0.3
    mass_weight: float = 0.2
    max_iterations: int = 50
    step_size: float = 0.1  # Gradient step size
    convergence_threshold: float = 0.01
    sensitivity: str = "relaxed"  # For circle detection


class TargetCircleIndex:
    """Spatial index for efficient target circle lookup.
    
    Uses K-D tree for O(log n) nearest-neighbor queries.
    Falls back to brute force O(n) if scipy not available.
    """
    
    def __init__(self, circles: List[TargetCircle]):
        """Build spatial index from target circles.
        
        Args:
            circles: List of detected target circles
        """
        self.circles = circles
        self._by_color: Dict[str, List[TargetCircle]] = {
            'cyan': [], 'magenta': [], 'yellow': [], 'black': []
        }
        self._kdtrees: Dict[str, Optional[Any]] = {}
        
        # Group by color
        for circle in circles:
            self._by_color[circle.color].append(circle)
        
        # Build K-D trees per color
        if HAS_SCIPY:
            for color, color_circles in self._by_color.items():
                if color_circles:
                    points = np.array([[c.x, c.y] for c in color_circles])
                    self._kdtrees[color] = KDTree(points)
                else:
                    self._kdtrees[color] = None
    
    def find_nearest(
        self, 
        x: float, 
        y: float, 
        color: str
    ) -> Optional[Tuple[TargetCircle, float]]:
        """Find nearest target circle of given color.
        
        Args:
            x, y: Query position
            color: Color channel to search
            
        Returns:
            Tuple of (nearest_circle, distance) or None if no targets
        """
        color_circles = self._by_color.get(color, [])
        if not color_circles:
            return None
        
        if HAS_SCIPY and self._kdtrees.get(color) is not None:
            # O(log n) lookup
            dist, idx = self._kdtrees[color].query([x, y])
            return color_circles[idx], dist
        else:
            # Brute force fallback
            min_dist = float('inf')
            nearest = None
            for circle in color_circles:
                dist = math.sqrt((x - circle.x)**2 + (y - circle.y)**2)
                if dist < min_dist:
                    min_dist = dist
                    nearest = circle
            return nearest, min_dist


def parse_target_image(
    image_path: Path,
    sensitivity: str = "relaxed",
    min_radius: int = 1,
    max_radius: int = 100,
) -> TargetCircleIndex:
    """Parse target halftone PNG and detect circles per color channel.
    
    Processes the target image in CMYK channels to detect circles
    for each color separately.
    
    Args:
        image_path: Path to target PNG image
        sensitivity: Detection sensitivity (strict/normal/relaxed)
        min_radius: Minimum circle radius to detect
        max_radius: Maximum circle radius to detect
        
    Returns:
        TargetCircleIndex for efficient nearest-neighbor queries
    """
    logger.info(f"Parsing target image: {image_path}")
    
    # Load image
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not load target image: {image_path}")
    
    # Convert BGR to CMYK-like channels
    # For halftone detection, we look for dark regions in each channel
    b, g, r = cv2.split(image)
    
    # CMYK extraction from RGB:
    # C (cyan) = 255 - R (high in areas with cyan ink)
    # M (magenta) = 255 - G
    # Y (yellow) = 255 - B
    # K (black) = min(C, M, Y) - but for halftone, look for dark areas
    
    cyan_channel = 255 - r
    magenta_channel = 255 - g
    yellow_channel = 255 - b
    
    # Black is where all channels are low (dark areas)
    black_channel = np.minimum(np.minimum(255-r, 255-g), 255-b)
    
    all_circles: List[TargetCircle] = []
    
    # Detect circles in each channel
    channel_map = {
        'cyan': cyan_channel,
        'magenta': magenta_channel,
        'yellow': yellow_channel,
        'black': black_channel,
    }
    
    for color, channel in channel_map.items():
        # Threshold to find ink regions
        _, binary = cv2.threshold(channel, 128, 255, cv2.THRESH_BINARY)
        
        # Create BGR image for detection
        channel_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        
        # Detect circles
        circles = detect_circles(
            channel_bgr,
            min_radius=min_radius,
            max_radius=max_radius,
            sensitivity=sensitivity,
            min_distance=int(min_radius * 2)
        )
        
        for circle in circles:
            all_circles.append(TargetCircle(
                x=circle.center_x,
                y=circle.center_y,
                radius=circle.radius,
                color=color
            ))
        
        logger.info(f"  {color}: detected {len(circles)} circles")
    
    logger.info(f"Total target circles: {len(all_circles)}")
    return TargetCircleIndex(all_circles)


def compute_target_gradient(
    source_x: float,
    source_y: float,
    source_r: float,
    target_circle: TargetCircle,
    max_distance: float,
    config: TargetGuidedConfig,
) -> Tuple[float, float, float]:
    """Compute gradient toward target circle.
    
    Args:
        source_x, source_y, source_r: Source circle position and radius
        target_circle: Target circle to move toward
        max_distance: Maximum possible distance (for normalization)
        config: Optimization configuration
        
    Returns:
        Tuple of (dx, dy, dr) - position and radius deltas
    """
    # Position delta (move toward target)
    dx = target_circle.x - source_x
    dy = target_circle.y - source_y
    distance = math.sqrt(dx*dx + dy*dy)
    
    # Scale by step size (direct lerp toward target)
    # step_size of 0.1 means move 10% of distance each iteration
    position_step = config.step_size * config.position_weight
    dx *= position_step
    dy *= position_step
    
    # Radius delta (match target size)
    # step_size of 0.1 means adjust 10% of radius difference each iteration
    radius_step = config.step_size * config.radius_weight
    dr = (target_circle.radius - source_r) * radius_step
    
    return dx, dy, dr


def apply_target_guided_optimization(
    circles_by_color: Dict[str, List[Tuple[float, float, float]]],
    cluster_metadata: List[Dict[str, Any]],
    cluster_circle_map: List[Dict[str, Tuple[int, int]]],
    target_index: TargetCircleIndex,
    image_shape: Tuple[int, int],
    config: TargetGuidedConfig,
) -> Dict[str, List[Tuple[float, float, float]]]:
    """Apply target-guided optimization to circles.
    
    Integrates with existing drift infrastructure to balance
    target-matching with CMYK color preservation.
    
    Args:
        circles_by_color: Dict mapping colors to list of (x, y, r) tuples
        cluster_metadata: List of cluster info dicts
        cluster_circle_map: List of dicts mapping color -> (circle_index, target_pixels)
        target_index: Spatial index of target circles
        image_shape: (height, width) for rendering
        config: Optimization configuration
        
    Returns:
        Updated circles_by_color dict with optimized positions/sizes
    """
    h, w = image_shape
    max_distance = math.sqrt(h*h + w*w)  # Diagonal for normalization
    
    # Convert to mutable lists
    circles_by_color = {
        color: list(circles)
        for color, circles in circles_by_color.items()
    }
    
    # Track convergence
    prev_total_error = float('inf')
    
    for iteration in range(config.max_iterations):
        total_error = 0.0
        adjustments = 0
        
        # Process each cluster
        for cluster_idx, circle_indices in enumerate(cluster_circle_map):
            if not circle_indices:
                continue
            
            # Adjust each CMY petal
            for color in ['cyan', 'magenta', 'yellow']:
                if color not in circle_indices:
                    continue
                
                circle_idx, target_pixels = circle_indices[color]
                cx, cy, r = circles_by_color[color][circle_idx]
                
                # Find nearest target circle
                match = target_index.find_nearest(cx, cy, color)
                if match is None:
                    continue
                
                target_circle, distance = match
                
                # Compute gradient toward target
                dx, dy, dr = compute_target_gradient(
                    cx, cy, r,
                    target_circle,
                    max_distance,
                    config
                )
                
                # Apply target weight (blend with drift)
                # When target_weight=0, no target-guided adjustment
                # When target_weight=1, full target-guided adjustment
                tw = config.target_weight
                dx *= tw
                dy *= tw
                dr *= tw
                
                # Apply gradient step
                new_cx = cx + dx
                new_cy = cy + dy
                new_r = max(0.5, r + dr)  # Minimum radius
                
                # Update circle
                circles_by_color[color][circle_idx] = (new_cx, new_cy, new_r)
                
                # Track error
                pos_error = distance / max_distance
                rad_error = abs(r - target_circle.radius) / r if r > 0 else 0
                total_error += pos_error + rad_error
                adjustments += 1
        
        # Check convergence
        if adjustments > 0:
            avg_error = total_error / adjustments
            error_change = abs(prev_total_error - total_error) / max(prev_total_error, 0.001)
            
            logger.debug(f"Iteration {iteration}: avg_error={avg_error:.4f}, change={error_change:.4f}")
            
            if error_change < config.convergence_threshold:
                logger.info(f"Target optimization converged after {iteration+1} iterations")
                break
            
            prev_total_error = total_error
    
    return circles_by_color


# Proof of concept test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m dotmatrix.target_guided <target_image.png>")
        sys.exit(1)
    
    target_path = Path(sys.argv[1])
    if not target_path.exists():
        print(f"Error: Target image not found: {target_path}")
        sys.exit(1)
    
    # Parse target image
    print(f"Parsing target image: {target_path}")
    index = parse_target_image(target_path)
    
    print(f"\nTarget circle summary:")
    for color in ['cyan', 'magenta', 'yellow', 'black']:
        count = len(index._by_color[color])
        print(f"  {color}: {count} circles")
    
    print("\nPoC complete - target parsing works!")
