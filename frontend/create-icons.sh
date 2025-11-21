#!/bin/bash

# Usage: ./create-icons.sh [-o output_dir] path/to/source.png
# Requires: ImageMagick (convert)

set -e

usage() {
  echo "Usage: $0 [-o output_dir] path/to/source-1024x1024.png"
  echo "  -o output_dir   Output directory for icons (default: ./public/icons relative to script)"
  echo "  path/to/source-1024x1024.png   Source PNG image (1024x1024 recommended)"
  exit 1
}

cleanup() {
  echo "Script interrupted or failed. Exiting."
  exit 1
}

trap cleanup INT TERM ERR

# Check for ImageMagick (convert)
if ! command -v convert >/dev/null 2>&1; then
  echo "Error: ImageMagick 'convert' command not found. Please install ImageMagick."
  exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ICON_DIR="$SCRIPT_DIR/public/icons"

# Parse options
while getopts "o:h" opt; do
  case $opt in
    o)
      # If output dir is relative, resolve it relative to script dir
      case $OPTARG in
        /*) ICON_DIR="$OPTARG" ;;
        *) ICON_DIR="$SCRIPT_DIR/$OPTARG" ;;
      esac
      ;;
    h)
      usage
      ;;
    *)
      usage
      ;;
  esac
done
shift $((OPTIND-1))

SRC="$1"
SIZES=(72 96 128 144 152 192 384 512)
MASKABLE_SIZES=(192 512)

if [[ -z "$SRC" || ! -f "$SRC" ]]; then
  usage
fi

mkdir -p "$ICON_DIR"

echo "Generating standard PWA icons from $SRC..."
for size in "${SIZES[@]}"; do
  convert "$SRC" -resize ${size}x${size} "$ICON_DIR/icon-${size}x${size}.png"
  echo "Created: $ICON_DIR/icon-${size}x${size}.png"
done

echo "Generating maskable PWA icons from $SRC..."
for size in "${MASKABLE_SIZES[@]}"; do
  convert "$SRC" -resize ${size}x${size} -gravity center -extent ${size}x${size} "$ICON_DIR/icon-maskable-${size}x${size}.png"
  echo "Created: $ICON_DIR/icon-maskable-${size}x${size}.png"
done

echo "All icons generated in $ICON_DIR"
