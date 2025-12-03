# PWA Icons

This directory contains the icons required for the Progressive Web App (PWA) functionality.

## Required Icons

You need to create the following icon files:

### Standard Icons (any purpose)

- `icon-72x72.png` - 72x72 pixels
- `icon-96x96.png` - 96x96 pixels
- `icon-128x128.png` - 128x128 pixels
- `icon-144x144.png` - 144x144 pixels
- `icon-152x152.png` - 152x152 pixels (Apple Touch Icon)
- `icon-192x192.png` - 192x192 pixels
- `icon-384x384.png` - 384x384 pixels
- `icon-512x512.png` - 512x512 pixels

### Maskable Icons (adaptive icons with safe zone)

- `icon-maskable-192x192.png` - 192x192 pixels with safe zone
- `icon-maskable-512x512.png` - 512x512 pixels with safe zone

## Design Guidelines

### Standard Icons

- Use the Verse logo/branding
- Include padding around the icon (about 10% of the canvas)
- Use a transparent background or solid color that matches your brand

### Maskable Icons

- Maskable icons should fill the entire canvas
- Keep important content within the "safe zone" (center 80% of the canvas)
- The outer 20% may be cropped on some devices
- Use a background colour that matches your brand
- Read more: https://web.dev/maskable-icon/

## Tools to Generate Icons

You can use these tools to generate all required sizes:

1. **PWA Asset Generator**: https://github.com/elegantapp/pwa-asset-generator

   ```bash
   npx pwa-asset-generator [source-image] ./public/icons --manifest ./public/manifest.json
   ```

2. **RealFaviconGenerator**: https://realfavicongenerator.net/

3. **PWA Image Generator**: https://www.pwabuilder.com/imageGenerator

## Quick Start

If you have a source image (SVG or high-res PNG), you can generate all icons using:

```bash
# Using PWA Asset Generator (recommended)
npx pwa-asset-generator source-logo.svg ./public/icons \
  --manifest ./public/manifest.json \
  --background "#ffffff" \
  --opaque false \
  --padding "10%"
```

## Placeholder Icons

For development purposes, you can use placeholder icons temporarily. However, for production, you should create proper branded icons for a professional appearance.
