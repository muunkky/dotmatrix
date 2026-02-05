"""Isolated test of drift measurement function - reproducing actual bug."""

import sys
sys.path.insert(0, 'src')

from dotmatrix.circle_renderer import _measure_full_flower_exposure
import math

def test_case(name, cyan, magenta, yellow, black, h, w):
    """Run single test case and show results."""
    result = _measure_full_flower_exposure(
        cyan_circle=cyan,
        magenta_circle=magenta,
        yellow_circle=yellow,
        black_circle=black,
        h=h,
        w=w
    )
    
    print(f"\n{name}")
    print(f"  Black: pos=({black[0]:.1f}, {black[1]:.1f}), r={black[2]:.1f} → actual={result['black']}")
    
    for color, circle in [('cyan', cyan), ('magenta', magenta), ('yellow', yellow)]:
        if circle:
            expected_area = math.pi * circle[2]**2
            dist_from_black = math.sqrt((circle[0] - black[0])**2 + (circle[1] - black[1])**2)
            print(f"  {color}: pos=({circle[0]:.1f}, {circle[1]:.1f}), r={circle[2]:.1f}, dist={dist_from_black:.1f} → actual={result[color]} (expected ~{expected_area:.0f})")
    
    return result

h, w = 250, 250

# Test 1: Bug reproduction - petal at same position as black (like cluster 1 cyan)
# This should show actual=0 because cyan is completely under black
test_case(
    "BUG CASE 1: Cyan at black position (should be 0)",
    cyan=(100, 100, 19.6),  # Same position as black
    magenta=None,
    yellow=None,
    black=(100, 100, 24.1),
    h=h, w=w
)

# Test 2: Bug reproduction - magenta partially overlapping black
# After jitter, magenta might be at a position where it's partly under black
test_case(
    "BUG CASE 2: Magenta partially under black",
    cyan=None,
    magenta=(110, 110, 33.5),  # Overlaps black
    yellow=None,
    black=(100, 100, 24.1),
    h=h, w=w
)

# Test 3: All petals at center (worst case - all should be 0)
test_case(
    "BUG CASE 3: All petals at black center (all should be 0)",
    cyan=(100, 100, 19.6),
    magenta=(100, 100, 33.5),
    yellow=(100, 100, 15.0),
    black=(100, 100, 24.1),
    h=h, w=w
)

# Test 4: Normal flower (should all be exposed)
test_case(
    "NORMAL CASE: Well-separated flower",
    cyan=(100, 130, 15),
    magenta=(130, 100, 15),
    yellow=(70, 100, 15),
    black=(100, 100, 20),
    h=h, w=w
)

print("\n" + "="*60)
print("DIAGNOSIS:")
print("If BUG CASEs show actual=0 for petals at/near black center: CORRECT")
print("If BUG CASEs show actual>0 for petals at black center: MEASUREMENT BUG")
print("="*60)
