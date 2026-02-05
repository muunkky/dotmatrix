"""Shared color definitions for CMYK halftone rendering.

All colors use BGR format (OpenCV native). Never mix RGB and BGR formats.

This module provides centralized color constants used across all renderers
to ensure consistency and eliminate duplication. All renderers should import
colors from this module rather than defining them locally.

BGR Format Reminder:
    BGR means (Blue, Green, Red) channel order.
    
    Examples:
        cyan_bgr = (255, 255, 0)    # B=255, G=255, R=0
        magenta_bgr = (255, 0, 255)  # B=255, G=0, R=255
        yellow_bgr = (0, 255, 255)   # B=0, G=255, R=255

See docs/architecture/color-pipeline.md for the complete BGR convention.

Usage:
    from dotmatrix.colors import COLORS, COLORS_BGR, LAYER_ORDER
    
    # For renderers using COLORS dict
    color = COLORS['cyan']  # (255, 255, 0)
    
    # For renderers using COLORS_BGR dict (includes 'white')
    color = COLORS_BGR['cyan']  # (255, 255, 0)

Technical Debt Resolution:
    This module was created as part of the ARCHDEBT sprint (2026-01-08) to
    centralize color definitions that were previously duplicated across:
    - block_renderer.py
    - treemap_renderer.py
    - cluster_renderer.py
    - circle_renderer.py
    - cmyk_accuracy.py
"""

from typing import Dict, Tuple

# Type alias for BGR color tuple
BGRColor = Tuple[int, int, int]

# =============================================================================
# Primary Color Definitions (7 colors - CMYK + RGB overlaps)
# =============================================================================

COLORS: Dict[str, BGRColor] = {
    'yellow': (0, 255, 255),    # BGR: B=0, G=255, R=255
    'red': (0, 0, 255),         # BGR: B=0, G=0, R=255 (M∩Y overlap)
    'green': (0, 255, 0),       # BGR: B=0, G=255, R=0 (C∩Y overlap)
    'magenta': (255, 0, 255),   # BGR: B=255, G=0, R=255
    'blue': (255, 0, 0),        # BGR: B=255, G=0, R=0 (C∩M overlap)
    'cyan': (255, 255, 0),      # BGR: B=255, G=255, R=0
    'black': (0, 0, 0),         # BGR: B=0, G=0, R=0
}

# =============================================================================
# Extended Color Definitions (includes white for background)
# =============================================================================

COLORS_BGR: Dict[str, BGRColor] = {
    # Primary CMYK colors
    'cyan': (255, 255, 0),      # BGR
    'magenta': (255, 0, 255),   # BGR
    'yellow': (0, 255, 255),    # BGR
    'black': (0, 0, 0),         # BGR
    'white': (255, 255, 255),   # BGR (background/paper color)
    # Secondary colors from CMYK overlaps
    'red': (0, 0, 255),         # M + Y overlap
    'green': (0, 255, 0),       # C + Y overlap
    'blue': (255, 0, 0),        # C + M overlap
}

# =============================================================================
# Layer Ordering Constants
# =============================================================================

# Full 7-color layer order: outermost to innermost in halftone model
# Yellow first (largest coverage), black last (smallest/innermost)
LAYER_ORDER = ['yellow', 'red', 'green', 'magenta', 'blue', 'cyan', 'black']

# CMYK-only mode: 4 colors without RGB overlaps
LAYER_ORDER_CMYK = ['yellow', 'magenta', 'cyan', 'black']

# =============================================================================
# Petal Angles for Flower Renderer
# =============================================================================

# Petal angles for flower layout (degrees from top, clockwise)
# Black at center, CMY at 90° apart (N/E/S) to reduce neighbor black overlap
PETAL_ANGLES: Dict[str, int] = {
    'cyan': 0,       # Top (North)
    'magenta': 90,   # Right (East)
    'yellow': 180,   # Bottom (South)
}
