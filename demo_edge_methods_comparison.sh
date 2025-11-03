#!/bin/bash
# Comparison demo of all four edge sampling methods

set -e

INPUT="test_dotmatrix.png"
BASE_DIR="demo_results/edge_methods_comparison"

# Create base directory
mkdir -p "$BASE_DIR"

echo "========================================"
echo "Edge Sampling Methods Comparison Demo"
echo "========================================"
echo ""
echo "Testing all four edge sampling methods on: $INPUT"
echo ""

# Method 1: Circumference (original)
echo "1. Running CIRCUMFERENCE method (original edge sampling)..."
mkdir -p "$BASE_DIR/circumference"
python3 -m dotmatrix \
    --input "$INPUT" \
    --debug \
    --extract "$BASE_DIR/circumference" \
    --edge-sampling \
    --edge-method circumference \
    --max-colors 6 \
    > "$BASE_DIR/circumference_output.log" 2>&1
echo "   Results: $(ls -1 $BASE_DIR/circumference/*.png | wc -l) PNG files"

# Method 2: Canny (edge pixels)
echo "2. Running CANNY method (actual edge pixels)..."
mkdir -p "$BASE_DIR/canny"
python3 -m dotmatrix \
    --input "$INPUT" \
    --debug \
    --extract "$BASE_DIR/canny" \
    --edge-sampling \
    --edge-method canny \
    --max-colors 6 \
    > "$BASE_DIR/canny_output.log" 2>&1
echo "   Results: $(ls -1 $BASE_DIR/canny/*.png | wc -l) PNG files"

# Method 3: Exposed (occlusion-aware)
echo "3. Running EXPOSED method (visible arcs only)..."
mkdir -p "$BASE_DIR/exposed"
python3 -m dotmatrix \
    --input "$INPUT" \
    --debug \
    --extract "$BASE_DIR/exposed" \
    --edge-sampling \
    --edge-method exposed \
    --max-colors 6 \
    > "$BASE_DIR/exposed_output.log" 2>&1
echo "   Results: $(ls -1 $BASE_DIR/exposed/*.png | wc -l) PNG files"

# Method 4: Band (pixel band)
echo "4. Running BAND method (edge pixel band)..."
mkdir -p "$BASE_DIR/band"
python3 -m dotmatrix \
    --input "$INPUT" \
    --debug \
    --extract "$BASE_DIR/band" \
    --edge-sampling \
    --edge-method band \
    --max-colors 6 \
    > "$BASE_DIR/band_output.log" 2>&1
echo "   Results: $(ls -1 $BASE_DIR/band/*.png | wc -l) PNG files"

# Bonus: Area sampling for comparison
echo "5. Running AREA method (baseline for comparison)..."
mkdir -p "$BASE_DIR/area"
python3 -m dotmatrix \
    --input "$INPUT" \
    --debug \
    --extract "$BASE_DIR/area" \
    --max-colors 6 \
    > "$BASE_DIR/area_output.log" 2>&1
echo "   Results: $(ls -1 $BASE_DIR/area/*.png | wc -l) PNG files"

echo ""
echo "========================================"
echo "Comparison Complete!"
echo "========================================"
echo ""
echo "Results saved to: $BASE_DIR/"
echo ""
echo "Method summary:"
echo "  - circumference: Full 360° edge sampling (original)"
echo "  - canny:        Samples actual Canny edge pixels"
echo "  - exposed:      Samples only visible (non-occluded) arcs"
echo "  - band:         Samples from edge pixel band"
echo "  - area:         Area-based sampling (baseline)"
echo ""
echo "Expected for test_dotmatrix.png: 4-5 color groups (CMYK + white)"
echo "Actual results:"
grep "Extracted" "$BASE_DIR"/*_output.log | sed 's/.*\//  /' | sed 's/_output.log:/: /'
