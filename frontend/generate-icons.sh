#!/bin/bash

# Script to generate placeholder PWA icons
# This creates simple colored squares as placeholders until proper icons are designed

ICON_DIR="./public/icons"
SIZES=(72 96 128 144 152 192 384 512)
MASKABLE_SIZES=(192 512)

# Colors for the placeholder icons
BG_COLOR="#4f46e5"  # Primary color (indigo)
TEXT_COLOR="#ffffff"

# Create icons directory if it doesn't exist
mkdir -p "$ICON_DIR"

echo "Generating placeholder PWA icons..."

# Generate standard icons
for size in "${SIZES[@]}"; do
  output="$ICON_DIR/icon-${size}x${size}.png"

  # Use ImageMagick if available, otherwise provide instructions
  if command -v convert &> /dev/null; then
    convert -size ${size}x${size} xc:"$BG_COLOR" \
      -gravity center \
      -pointsize $((size / 4)) \
      -fill "$TEXT_COLOR" \
      -font "Helvetica-Bold" \
      -annotate +0+0 "V" \
      "$output"
    echo "Created: $output"
  else
    echo "ImageMagick not found. Please install it or create icons manually."
    echo "On macOS: brew install imagemagick"
    echo "On Ubuntu: sudo apt-get install imagemagick"
    exit 1
  fi
done

# Generate maskable icons (with safe zone)
for size in "${MASKABLE_SIZES[@]}"; do
  output="$ICON_DIR/icon-maskable-${size}x${size}.png"
  padding=$((size / 5))  # 20% padding for safe zone
  inner_size=$((size - 2 * padding))

  if command -v convert &> /dev/null; then
    # Create icon with safe zone
    convert -size ${size}x${size} xc:"$BG_COLOR" \
      -gravity center \
      -pointsize $((inner_size / 2)) \
      -fill "$TEXT_COLOR" \
      -font "Helvetica-Bold" \
      -annotate +0+0 "V" \
      "$output"
    echo "Created: $output"
  fi
done

echo ""
echo "Placeholder icons generated successfully!"
echo "Remember to replace these with proper branded icons for production."

