# Progressive Web App (PWA) Setup

Verse is now a fully installable Progressive Web App! This means users can install it on their devices and use it like a native app, with offline support and improved performance.

## Features

- **Installable**: Users can install Verse on their home screen on mobile devices and desktops
- **Offline Support**: The app works offline with cached content
- **Fast Loading**: Assets are cached for instant loading
- **Native Feel**: Runs in standalone mode without browser UI
- **Auto-updates**: Service worker automatically updates when new versions are available

## How It Works

### Service Worker
The app uses `vite-plugin-pwa` to automatically generate an optimised service worker that:
- Caches static assets (JS, CSS, HTML, images)
- Implements a network-first strategy for API calls with fallback to cache
- Provides offline functionality
- Handles automatic updates

### Install Prompt
The app includes a custom install prompt component (`InstallPrompt.tsx`) that:
- Appears after the user has used the app (respects browser's install criteria)
- Can be dismissed and will reappear after 7 days
- Provides a better UX than the browser's default install prompt
- Only shows on supported browsers

## Installation for Users

### Desktop (Chrome, Edge, Opera)
1. Visit the Verse website
2. Look for the install icon in the address bar
3. Click "Install" in the popup
4. The app will open as a standalone window

### Mobile (Android)
1. Visit the Verse website in Chrome
2. Tap the "Install" button when the prompt appears
3. Or tap the three dots menu → "Install app"
4. The app will be added to your home screen

### Mobile (iOS/Safari)
1. Visit the Verse website in Safari
2. Tap the share button
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add" to confirm

## Development

### Testing PWA Features Locally

1. Build the production version:
   ```bash
   bun run build
   ```

2. Preview the built app:
   ```bash
   bun run preview
   ```

3. Open the app in your browser and check:
   - Lighthouse PWA audit (DevTools → Lighthouse)
   - Service Worker registration (DevTools → Application → Service Workers)
   - Cache storage (DevTools → Application → Cache Storage)
   - Manifest (DevTools → Application → Manifest)

### Generating Icons

The app requires various icon sizes. You can generate them using:

```bash
./generate-icons.sh
```

This requires ImageMagick. Install it with:
- macOS: `brew install imagemagick`
- Ubuntu: `sudo apt-get install imagemagick`

Or use an online tool like:
- [PWA Asset Generator](https://github.com/elegantapp/pwa-asset-generator)
- [RealFaviconGenerator](https://realfavicongenerator.net/)

### Icon Requirements

Place icons in `/public/icons/`:
- `icon-72x72.png` through `icon-512x512.png` - Standard icons
- `icon-maskable-192x192.png` and `icon-maskable-512x512.png` - Adaptive icons

See `/public/icons/README.md` for detailed specifications.

## Configuration

### Vite Configuration

The PWA is configured in `vite.config.ts`:

```typescript
VitePWA({
  registerType: 'prompt', // Prompts user to update
  includeAssets: ['vite.svg', 'icons/*.png'],
  manifest: { /* app manifest */ },
  workbox: { /* service worker config */ }
})
```

### Manifest

The web app manifest defines:
- App name and description
- Theme colours
- Display mode (standalone)
- Icons
- Start URL

### Caching Strategy

- **Static Assets**: Cache-first with network fallback
- **API Calls**: Network-first with cache fallback
- **Cache Expiration**: API cache expires after 24 hours

## Troubleshooting

### PWA Not Installing

1. Check browser compatibility (Chrome, Edge, Safari 11.1+)
2. Ensure HTTPS is enabled (required for service workers)
3. Check DevTools console for errors
4. Verify manifest is valid (DevTools → Application → Manifest)

### Service Worker Not Updating

1. Close all tabs with the app
2. Unregister old service workers (DevTools → Application → Service Workers)
3. Clear cache (DevTools → Application → Clear storage)
4. Hard reload (Ctrl/Cmd + Shift + R)

### Icons Not Showing

1. Verify icons exist in `/public/icons/`
2. Check icon paths in manifest
3. Clear browser cache
4. Regenerate icons with correct sizes

## Production Deployment

### Requirements

1. **HTTPS**: PWAs require a secure context
2. **Valid Icons**: All required icon sizes must be present
3. **Service Worker**: Must be served from the same origin
4. **Headers**: Consider adding these headers:
   ```
   Cache-Control: max-age=31536000 for static assets
   Cache-Control: no-cache for index.html
   ```

### Nginx Configuration

Add to your nginx config:

```nginx
# Cache static assets
location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# Don't cache service worker and index
location ~* (sw\.js|index\.html)$ {
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

### Docker

The Dockerfile should copy the built assets:

```dockerfile
COPY --from=build /app/dist /usr/share/nginx/html
```

## Testing

Run Lighthouse audit to verify PWA compliance:

1. Open DevTools → Lighthouse
2. Select "Progressive Web App"
3. Click "Generate report"
4. Aim for a score of 90+

## Resources

- [vite-plugin-pwa Documentation](https://vite-pwa-org.netlify.app/)
- [PWA Best Practices](https://web.dev/pwa/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)

