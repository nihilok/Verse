#!/usr/bin/env node

/**
 * Simple icon generator using Canvas
 * This creates placeholder icons if ImageMagick is not available
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ICON_DIR = path.join(__dirname, "public", "icons");
const SIZES = [72, 96, 128, 144, 152, 192, 384, 512];
const MASKABLE_SIZES = [192, 512];

// Create icons directory if it doesn't exist
if (!fs.existsSync(ICON_DIR)) {
  fs.mkdirSync(ICON_DIR, { recursive: true });
}

console.log("Creating placeholder icons...");
console.log(
  "Note: These are SVG placeholders. For production, create proper PNG icons.",
);

// Generate SVG icons (lightweight placeholders)
SIZES.forEach((size) => {
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="${size}" height="${size}" fill="#4f46e5"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial, sans-serif" font-size="${size * 0.6}" font-weight="bold" fill="white">V</text>
</svg>`;

  const filename = `icon-${size}x${size}.svg`;
  fs.writeFileSync(path.join(ICON_DIR, filename), svg);
  console.log(`Created: ${filename}`);
});

// Generate maskable icons
MASKABLE_SIZES.forEach((size) => {
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="${size}" height="${size}" fill="#4f46e5"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial, sans-serif" font-size="${size * 0.5}" font-weight="bold" fill="white">V</text>
</svg>`;

  const filename = `icon-maskable-${size}x${size}.svg`;
  fs.writeFileSync(path.join(ICON_DIR, filename), svg);
  console.log(`Created: ${filename}`);
});

console.log("\n✅ Placeholder icons created!");
console.log(
  "⚠️  For production, replace these SVG files with proper PNG icons.",
);
console.log("   See public/icons/README.md for more information.\n");
