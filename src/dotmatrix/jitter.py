"""Jitter/randomization module for breaking up grid patterns.

Implements Gaussian and uniform jitter algorithms for adding controlled
randomization to circle positions and sizes. Supports reproducible 
randomization via seed parameter.

Based on research from card sxy0kc:
- Gaussian jitter recommended (natural distribution, maintains perception)
- Default thresholds: 25% position, 20% size (conservative)
- 3-sigma rule: 99.7% of values within specified range
"""

import random
from typing import Tuple


def validate_jitter_params(position_pct: float, size_pct: float) -> None:
    """Validate jitter parameters are within acceptable ranges.
    
    Args:
        position_pct: Position jitter percentage (0-100)
        size_pct: Size jitter percentage (0-100)
        
    Raises:
        ValueError: If parameters are out of range
    """
    if not 0 <= position_pct <= 100:
        raise ValueError(f"position_pct must be 0-100, got {position_pct}")
    if not 0 <= size_pct <= 100:
        raise ValueError(f"size_pct must be 0-100, got {size_pct}")


def apply_position_jitter(
    x: float,
    y: float,
    position_pct: float,
    base_radius: float,
    seed: int,
    algorithm: str = 'gaussian'
) -> Tuple[float, float]:
    """Apply position jitter to circle center coordinates.
    
    Args:
        x: Original x coordinate
        y: Original y coordinate
        position_pct: Jitter strength as percentage of base_radius (0-100)
        base_radius: Reference radius for calculating jitter magnitude
        seed: Random seed for reproducibility
        algorithm: 'gaussian' or 'uniform'
        
    Returns:
        Tuple of (jittered_x, jittered_y)
        
    Raises:
        ValueError: If algorithm is invalid
    """
    if position_pct == 0:
        return (x, y)
    
    # Create seeded RNG
    rng = random.Random(seed)
    
    # Calculate jitter magnitude (max offset)
    max_offset = (position_pct / 100) * base_radius
    
    if algorithm == 'gaussian':
        # Gaussian distribution with 3-sigma = max_offset
        # sigma = max_offset / 3 ensures 99.7% within range
        sigma = max_offset / 3
        offset_x = rng.gauss(0, sigma)
        offset_y = rng.gauss(0, sigma)
        
    elif algorithm == 'uniform':
        # Uniform distribution in circle of radius max_offset
        # Generate random angle and radius
        import math
        angle = rng.uniform(0, 2 * math.pi)
        # Use sqrt for uniform distribution in circle (not uniform in radius)
        r = max_offset * (rng.random() ** 0.5)
        offset_x = r * math.cos(angle)
        offset_y = r * math.sin(angle)
        
    else:
        raise ValueError(f"algorithm must be 'gaussian' or 'uniform', got '{algorithm}'")
    
    return (x + offset_x, y + offset_y)


def apply_size_jitter(
    radius: float,
    size_pct: float,
    seed: int,
    algorithm: str = 'gaussian'
) -> float:
    """Apply size jitter to circle radius.
    
    Args:
        radius: Original radius
        size_pct: Jitter strength as percentage of radius (0-100)
        seed: Random seed for reproducibility
        algorithm: 'gaussian' or 'uniform'
        
    Returns:
        Jittered radius (always positive)
        
    Raises:
        ValueError: If algorithm is invalid
    """
    if size_pct == 0:
        return radius
    
    # Create seeded RNG
    rng = random.Random(seed)
    
    # Calculate jitter magnitude
    max_deviation = (size_pct / 100) * radius
    
    if algorithm == 'gaussian':
        # Gaussian distribution with 3-sigma = max_deviation
        sigma = max_deviation / 3
        offset = rng.gauss(0, sigma)
        
    elif algorithm == 'uniform':
        # Uniform distribution in [-max_deviation, +max_deviation]
        offset = rng.uniform(-max_deviation, max_deviation)
        
    else:
        raise ValueError(f"algorithm must be 'gaussian' or 'uniform', got '{algorithm}'")
    
    # Ensure radius stays positive (clamp to minimum 0.5px)
    jittered_radius = max(0.5, radius + offset)
    
    return jittered_radius
