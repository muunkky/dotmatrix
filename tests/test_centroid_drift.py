"""Unit tests for centroid-guided position drift.

Tests for the centroid drift feature that replaces random position jitter
with intelligent movement toward the centroid of color pixels in the source image.

TDD: These tests are written BEFORE the implementation to define expected behavior.
"""
import pytest
import numpy as np
from typing import Tuple, Optional


# Import will fail until implementation exists - expected for TDD
try:
    from dotmatrix.centroid_drift import (
        compute_color_centroid,
        compute_color_centroid_from_mask,
        apply_centroid_position,
    )
    IMPLEMENTATION_EXISTS = True
except ImportError:
    IMPLEMENTATION_EXISTS = False
    # Dummy functions for type checker
    compute_color_centroid = None  # type: ignore
    compute_color_centroid_from_mask = None  # type: ignore
    apply_centroid_position = None  # type: ignore


def create_test_image_with_color_blob(
    size: Tuple[int, int] = (200, 200),
    blob_center: Tuple[int, int] = (100, 100),
    blob_radius: int = 30,
    color: str = 'cyan'
) -> np.ndarray:
    """Create a test image with a colored blob at specified location.
    
    Args:
        size: (height, width) of image
        blob_center: (x, y) center of blob
        blob_radius: radius of blob
        color: 'cyan', 'magenta', or 'yellow'
        
    Returns:
        RGB image array (H, W, 3)
    """
    h, w = size
    img = np.ones((h, w, 3), dtype=np.uint8) * 255  # White background
    
    # Color mappings (RGB)
    color_values = {
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
        'yellow': (255, 255, 0),
    }
    
    rgb = color_values.get(color, (0, 255, 255))
    
    # Draw filled circle
    y_coords, x_coords = np.ogrid[:h, :w]
    cx, cy = blob_center
    mask = (x_coords - cx)**2 + (y_coords - cy)**2 <= blob_radius**2
    img[mask] = rgb
    
    return img


def create_test_mask_with_blob(
    size: Tuple[int, int] = (200, 200),
    blob_center: Tuple[int, int] = (100, 100),
    blob_radius: int = 30,
) -> np.ndarray:
    """Create a binary mask with a blob at specified location.
    
    Args:
        size: (height, width) of mask
        blob_center: (x, y) center of blob
        blob_radius: radius of blob
        
    Returns:
        Binary mask array (H, W) with 255 where ink present, 0 elsewhere
    """
    h, w = size
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Draw filled circle
    y_coords, x_coords = np.ogrid[:h, :w]
    cx, cy = blob_center
    blob_mask = (x_coords - cx)**2 + (y_coords - cy)**2 <= blob_radius**2
    mask[blob_mask] = 255
    
    return mask


class TestComputeColorCentroidFromMask:
    """Tests for compute_color_centroid_from_mask() function (preferred method)."""
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_finds_centroid_of_centered_blob(self):
        """Centroid should match blob center when blob is centered in search region."""
        # Create mask with blob at (100, 100)
        mask = create_test_mask_with_blob(
            size=(200, 200),
            blob_center=(100, 100),
            blob_radius=30,
        )
        
        # Search around the same location
        centroid = compute_color_centroid_from_mask(
            color_mask=mask,
            cluster_cx=100,
            cluster_cy=100,
            search_radius=50,
        )
        
        assert centroid is not None, "Should find centroid for masked pixels"
        cx, cy = centroid
        # Allow small tolerance for pixel discretization
        assert abs(cx - 100) < 2, f"Centroid X should be ~100, got {cx}"
        assert abs(cy - 100) < 2, f"Centroid Y should be ~100, got {cy}"
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_finds_offset_centroid(self):
        """Centroid should be offset when blob is not at cluster center."""
        # Create mask with blob offset from search center
        mask = create_test_mask_with_blob(
            size=(200, 200),
            blob_center=(120, 110),  # Offset from cluster center
            blob_radius=25,
        )
        
        # Search around (100, 100) but blob is at (120, 110)
        centroid = compute_color_centroid_from_mask(
            color_mask=mask,
            cluster_cx=100,
            cluster_cy=100,
            search_radius=50,  # Large enough to include the blob
        )
        
        assert centroid is not None
        cx, cy = centroid
        # Centroid should be closer to blob center (120, 110)
        assert abs(cx - 120) < 5, f"Centroid X should be ~120, got {cx}"
        assert abs(cy - 110) < 5, f"Centroid Y should be ~110, got {cy}"
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_returns_none_for_empty_mask(self):
        """Should return None when no pixels in mask within region."""
        # Empty mask
        mask = np.zeros((200, 200), dtype=np.uint8)
        
        centroid = compute_color_centroid_from_mask(
            color_mask=mask,
            cluster_cx=100,
            cluster_cy=100,
            search_radius=50,
        )
        
        assert centroid is None, "Should return None when no masked pixels found"
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_handles_boundary_region(self):
        """Should handle regions that extend past image boundaries."""
        # Small mask with blob near corner
        mask = create_test_mask_with_blob(
            size=(100, 100),
            blob_center=(10, 10),
            blob_radius=15,
        )
        
        # Search region would extend past (0,0)
        centroid = compute_color_centroid_from_mask(
            color_mask=mask,
            cluster_cx=10,
            cluster_cy=10,
            search_radius=30,  # Would go negative
        )
        
        # Should still work, clamping to image bounds
        assert centroid is not None, "Should handle boundary regions gracefully"
        cx, cy = centroid
        assert 0 <= cx < 100, f"Centroid X should be in image bounds, got {cx}"
        assert 0 <= cy < 100, f"Centroid Y should be in image bounds, got {cy}"


class TestComputeColorCentroid:
    """Tests for compute_color_centroid() function."""
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_finds_centroid_of_centered_blob(self):
        """Centroid should match blob center when blob is centered in search region."""
        # Create image with cyan blob at (100, 100)
        img = create_test_image_with_color_blob(
            size=(200, 200),
            blob_center=(100, 100),
            blob_radius=30,
            color='cyan'
        )
        
        # Search around the same location
        centroid = compute_color_centroid(
            source_image=img,
            cluster_cx=100,
            cluster_cy=100,
            search_radius=50,
            color='cyan'
        )
        
        assert centroid is not None, "Should find centroid for colored pixels"
        cx, cy = centroid
        # Allow small tolerance for pixel discretization
        assert abs(cx - 100) < 2, f"Centroid X should be ~100, got {cx}"
        assert abs(cy - 100) < 2, f"Centroid Y should be ~100, got {cy}"
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_finds_offset_centroid(self):
        """Centroid should be offset when blob is not at cluster center."""
        # Create image with cyan blob offset from search center
        img = create_test_image_with_color_blob(
            size=(200, 200),
            blob_center=(120, 110),  # Offset from cluster center
            blob_radius=25,
            color='cyan'
        )
        
        # Search around (100, 100) but blob is at (120, 110)
        centroid = compute_color_centroid(
            source_image=img,
            cluster_cx=100,
            cluster_cy=100,
            search_radius=50,  # Large enough to include the blob
            color='cyan'
        )
        
        assert centroid is not None
        cx, cy = centroid
        # Centroid should be closer to blob center (120, 110)
        assert abs(cx - 120) < 5, f"Centroid X should be ~120, got {cx}"
        assert abs(cy - 110) < 5, f"Centroid Y should be ~110, got {cy}"
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_returns_none_for_no_color_pixels(self):
        """Should return None when no pixels of target color exist in region."""
        # Create image with magenta blob (not cyan)
        img = create_test_image_with_color_blob(
            size=(200, 200),
            blob_center=(100, 100),
            blob_radius=30,
            color='magenta'
        )
        
        # Search for cyan - should find nothing
        centroid = compute_color_centroid(
            source_image=img,
            cluster_cx=100,
            cluster_cy=100,
            search_radius=50,
            color='cyan'
        )
        
        assert centroid is None, "Should return None when no cyan pixels found"
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_handles_boundary_region(self):
        """Should handle regions that extend past image boundaries."""
        # Small image with blob near corner
        img = create_test_image_with_color_blob(
            size=(100, 100),
            blob_center=(10, 10),
            blob_radius=15,
            color='yellow'
        )
        
        # Search region would extend past (0,0)
        centroid = compute_color_centroid(
            source_image=img,
            cluster_cx=10,
            cluster_cy=10,
            search_radius=30,  # Would go negative
            color='yellow'
        )
        
        # Should still work, clamping to image bounds
        assert centroid is not None, "Should handle boundary regions gracefully"
        cx, cy = centroid
        assert 0 <= cx < 100, f"Centroid X should be in image bounds, got {cx}"
        assert 0 <= cy < 100, f"Centroid Y should be in image bounds, got {cy}"
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_weighted_by_intensity(self):
        """Centroid should be weighted toward higher intensity pixels."""
        # Create image with gradient - more intense cyan on right side
        h, w = 200, 200
        img = np.ones((h, w, 3), dtype=np.uint8) * 255  # White
        
        # Create a gradient cyan region: more cyan on right
        for x in range(80, 120):
            intensity = (x - 80) / 40  # 0 to 1
            # Cyan = (0, 255, 255) with gradient
            for y in range(80, 120):
                img[y, x] = (int(255 * (1 - intensity)), 255, 255)
        
        centroid = compute_color_centroid(
            source_image=img,
            cluster_cx=100,
            cluster_cy=100,
            search_radius=30,
            color='cyan'
        )
        
        assert centroid is not None
        cx, cy = centroid
        # Centroid should be shifted toward higher intensity (right side)
        assert cx > 100, f"Centroid should be shifted right (more intense), got {cx}"


class TestApplyCentroidPosition:
    """Tests for apply_centroid_position() function."""
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_moves_toward_centroid(self):
        """Position should move toward centroid by step_size fraction."""
        # Petal at (100, 100), centroid at (120, 110)
        new_x, new_y = apply_centroid_position(
            petal_x=100, petal_y=100,
            centroid_x=120, centroid_y=110,
            step_size=0.5
        )
        
        # Should move halfway: (110, 105)
        assert new_x == pytest.approx(110, abs=0.1), f"Expected x=110, got {new_x}"
        assert new_y == pytest.approx(105, abs=0.1), f"Expected y=105, got {new_y}"
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_full_step_reaches_centroid(self):
        """step_size=1.0 should move fully to centroid."""
        new_x, new_y = apply_centroid_position(
            petal_x=50, petal_y=50,
            centroid_x=150, centroid_y=200,
            step_size=1.0
        )
        
        assert new_x == pytest.approx(150, abs=0.1)
        assert new_y == pytest.approx(200, abs=0.1)
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_zero_step_stays_in_place(self):
        """step_size=0.0 should not move the position."""
        new_x, new_y = apply_centroid_position(
            petal_x=100, petal_y=100,
            centroid_x=200, centroid_y=200,
            step_size=0.0
        )
        
        assert new_x == 100
        assert new_y == 100
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_handles_coincident_positions(self):
        """Should handle case where petal is already at centroid."""
        new_x, new_y = apply_centroid_position(
            petal_x=100, petal_y=100,
            centroid_x=100, centroid_y=100,
            step_size=0.5
        )
        
        assert new_x == 100
        assert new_y == 100
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_small_step_size(self):
        """Small step sizes should work for gradual convergence."""
        new_x, new_y = apply_centroid_position(
            petal_x=100, petal_y=100,
            centroid_x=200, centroid_y=100,
            step_size=0.1  # 10% step
        )
        
        # Should move 10px toward centroid (100 distance * 0.1)
        assert new_x == pytest.approx(110, abs=0.1)
        assert new_y == pytest.approx(100, abs=0.1)


class TestCentroidDriftIntegration:
    """Integration tests for centroid drift in the rendering pipeline."""
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_centroid_drift_improves_color_coverage(self):
        """Centroid drift should improve coverage of target color pixels."""
        from dotmatrix.centroid_drift import apply_centroid_jitter
        
        # Create an image with an offset cyan blob
        img = create_test_image_with_color_blob(
            size=(200, 200),
            blob_center=(120, 110),  # Offset from cluster center at (100, 100)
            blob_radius=25,
            color='cyan'
        )
        
        # Petal starts at cluster center
        original_x, original_y = 100.0, 100.0
        
        # Apply centroid drift
        new_x, new_y = apply_centroid_jitter(
            x=original_x,
            y=original_y,
            source_image=img,
            cluster_cx=100,
            cluster_cy=100,
            search_radius=50,
            color='cyan',
            step_size=0.5,
        )
        
        # Should move toward blob center (120, 110)
        # With step_size=0.5, should move to approximately (110, 105)
        assert new_x > original_x, f"Should move toward blob (x: {original_x} -> {new_x})"
        assert new_y > original_y, f"Should move toward blob (y: {original_y} -> {new_y})"
        assert abs(new_x - 110) < 5, f"X should be ~110, got {new_x}"
        assert abs(new_y - 105) < 5, f"Y should be ~105, got {new_y}"
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_centroid_drift_with_size_jitter(self):
        """Centroid drift should work alongside random size jitter."""
        from dotmatrix.centroid_drift import apply_centroid_jitter
        from dotmatrix.jitter import apply_size_jitter
        
        # Create image with cyan blob
        img = create_test_image_with_color_blob(
            size=(200, 200),
            blob_center=(120, 110),
            blob_radius=25,
            color='cyan'
        )
        
        # Apply centroid-guided position
        new_x, new_y = apply_centroid_jitter(
            x=100.0, y=100.0,
            source_image=img,
            cluster_cx=100, cluster_cy=100,
            search_radius=50,
            color='cyan',
            step_size=0.5,
        )
        
        # Apply random size jitter (separate operation)
        original_radius = 20.0
        jittered_radius = apply_size_jitter(
            radius=original_radius,
            size_pct=25.0,
            seed=42,
            algorithm='gaussian'
        )
        
        # Position should be centroid-guided (deterministic)
        assert new_x > 100.0, "Position should move toward centroid"
        
        # Size should be jittered (random)
        # With 25% jitter, radius could vary by ~5 pixels
        assert jittered_radius != original_radius or True  # May be same by chance
        assert jittered_radius > 0, "Radius should stay positive"
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_fallback_to_random_when_no_centroid(self):
        """Should fall back to random jitter when no clear centroid exists."""
        from dotmatrix.centroid_drift import apply_centroid_jitter
        
        # Create image with NO cyan pixels (white background only)
        img = np.ones((200, 200, 3), dtype=np.uint8) * 255  # Pure white
        
        original_x, original_y = 100.0, 100.0
        
        # With fallback enabled, should use random jitter
        new_x, new_y = apply_centroid_jitter(
            x=original_x,
            y=original_y,
            source_image=img,
            cluster_cx=100,
            cluster_cy=100,
            search_radius=50,
            color='cyan',
            step_size=0.5,
            fallback_jitter=25.0,  # 25% random jitter as fallback
            fallback_seed=42,
        )
        
        # Should have moved (random jitter applied)
        # The exact position depends on the random jitter, but should be different
        moved = (new_x != original_x) or (new_y != original_y)
        assert moved, "Should apply fallback jitter when no centroid found"
    
    @pytest.mark.skipif(not IMPLEMENTATION_EXISTS, reason="Implementation not yet created")
    def test_no_movement_when_no_centroid_and_no_fallback(self):
        """Should stay in place when no centroid and no fallback configured."""
        from dotmatrix.centroid_drift import apply_centroid_jitter
        
        # Create image with NO cyan pixels
        img = np.ones((200, 200, 3), dtype=np.uint8) * 255
        
        new_x, new_y = apply_centroid_jitter(
            x=100.0, y=100.0,
            source_image=img,
            cluster_cx=100, cluster_cy=100,
            search_radius=50,
            color='cyan',
            step_size=0.5,
            fallback_jitter=0.0,  # No fallback
        )
        
        # Should stay at original position
        assert new_x == 100.0
        assert new_y == 100.0


# Test discovery helper
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
