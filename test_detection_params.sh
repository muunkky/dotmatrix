#!/bin/bash
# Test various detection parameters to find optimal settings for 16-circle image

echo "Testing detection parameters to find ~16 circles..."
echo "Expected: 16 circles (4 black, 4 cyan, 4 magenta, 4 yellow)"
echo ""

# Test different combinations
configs=(
    "normal:10:None"
    "normal:20:None"
    "normal:30:None"
    "normal:40:None"
    "strict:10:None"
    "strict:20:None"
    "strict:30:None"
    "strict:40:None"
    "strict:50:None"
)

for config in "${configs[@]}"; do
    IFS=':' read -r sensitivity min_radius min_dist <<< "$config"

    cmd="python3 -m dotmatrix --input test_dotmatrix.png --sensitivity $sensitivity --min-radius $min_radius"

    if [ "$min_dist" != "None" ]; then
        cmd="$cmd --min-distance $min_dist"
    fi

    count=$(eval "$cmd --format json 2>/dev/null" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0")

    printf "%-10s min-radius=%-3s min-dist=%-4s -> %3s circles\n" "$sensitivity" "$min_radius" "$min_dist" "$count"
done

echo ""
echo "Testing with min-distance variations..."

for min_dist in 30 40 50 60 70; do
    count=$(python3 -m dotmatrix --input test_dotmatrix.png --sensitivity strict --min-radius 30 --min-distance $min_dist --format json 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0")
    printf "strict     min-radius=30  min-dist=%-4s -> %3s circles\n" "$min_dist" "$count"
done
