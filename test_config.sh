#!/bin/bash
# Test the configuration system

set -e

echo "========================================"
echo "Testing DotMatrix Configuration System"
echo "========================================"
echo ""

# Test 1: Config file only
echo "Test 1: Using config file only..."
rm -rf demo_results/test_config_only
python3 -m dotmatrix \
    --config configs/cmyk-overlapping.json \
    --input test_dotmatrix.png \
    --extract demo_results/test_config_only

result=$(ls demo_results/test_config_only/*.png 2>/dev/null | wc -l)
if [ "$result" -eq 4 ]; then
    echo "✓ SUCCESS: Generated 4 color groups as expected"
else
    echo "✗ FAILED: Generated $result color groups (expected 4)"
fi
echo ""

# Test 2: Config file + CLI override
echo "Test 2: Config file + CLI override (max_colors=3)..."
rm -rf demo_results/test_config_override
python3 -m dotmatrix \
    --config configs/cmyk-overlapping.json \
    --input test_dotmatrix.png \
    --max-colors 3 \
    --extract demo_results/test_config_override

result=$(ls demo_results/test_config_override/*.png 2>/dev/null | wc -l)
if [ "$result" -eq 3 ]; then
    echo "✓ SUCCESS: CLI override worked, generated 3 color groups"
else
    echo "✗ FAILED: Generated $result color groups (expected 3)"
fi
echo ""

# Test 3: Verify config loads correct parameters (create temp config without extract-only params)
echo "Test 3: Verifying config parameters..."
cat > /tmp/test_detect_only.json <<EOF
{
  "sensitivity": "strict",
  "min_radius": 30,
  "min_distance": 50,
  "edge_sampling": true,
  "edge_method": "band"
}
EOF

output=$(python3 -m dotmatrix \
    --config /tmp/test_detect_only.json \
    --input test_dotmatrix.png \
    --format json | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))")

if [ "$output" -eq 16 ]; then
    echo "✓ SUCCESS: Config detected 16 circles (correct detection params)"
else
    echo "✗ FAILED: Detected $output circles (expected 16)"
fi
echo ""

echo "========================================"
echo "Configuration System Tests Complete"
echo "========================================"
echo ""
echo "Usage examples:"
echo ""
echo "1. Use config as-is:"
echo "   dotmatrix --config configs/cmyk-overlapping.json --input image.png --extract output/"
echo ""
echo "2. Override specific parameters:"
echo "   dotmatrix --config configs/cmyk-overlapping.json --input image.png --max-colors 5 --extract output/"
echo ""
echo "3. With debug output:"
echo "   dotmatrix --config configs/cmyk-overlapping.json --input image.png --debug --extract output/"
