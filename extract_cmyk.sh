#!/bin/bash
# Extract CMYK overlapping circles using optimized config

set -e

# Default values
INPUT=""
OUTPUT="output"
CONFIG="configs/cmyk-overlapping.json"
DEBUG=""
MAX_COLORS=""

# Help message
show_help() {
    cat << EOF
Usage: ./extract_cmyk.sh --input IMAGE [OPTIONS]

Extract CMYK overlapping circles from an image using optimized detection parameters.

Required:
  --input IMAGE          Input image file path

Optional:
  --output DIR           Output directory (default: output)
  --config FILE          Config file (default: configs/cmyk-overlapping.json)
  --max-colors N         Override max colors (default: 4 from config)
  --debug                Enable debug output
  --help                 Show this help message

Examples:
  ./extract_cmyk.sh --input test_dotmatrix.png
  ./extract_cmyk.sh --input image.png --output results/ --debug
  ./extract_cmyk.sh --input image.png --max-colors 5

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --input)
            INPUT="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --config)
            CONFIG="$2"
            shift 2
            ;;
        --max-colors)
            MAX_COLORS="$2"
            shift 2
            ;;
        --debug)
            DEBUG="--debug"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$INPUT" ]; then
    echo "Error: --input is required"
    echo "Use --help for usage information"
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "Error: Input file not found: $INPUT"
    exit 1
fi

if [ ! -f "$CONFIG" ]; then
    echo "Error: Config file not found: $CONFIG"
    exit 1
fi

# Build command
CMD="python3 -m dotmatrix --config $CONFIG --input $INPUT --extract $OUTPUT"

if [ -n "$MAX_COLORS" ]; then
    CMD="$CMD --max-colors $MAX_COLORS"
fi

if [ -n "$DEBUG" ]; then
    CMD="$CMD $DEBUG"
fi

# Run the command
echo "Extracting CMYK circles from: $INPUT"
echo "Output directory: $OUTPUT"
echo ""

$CMD

echo ""
echo "Done! Check $OUTPUT/ for extracted color groups."
