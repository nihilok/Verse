# Wake Lock Feature

## Overview

The Wake Lock feature keeps your device awake while reading Bible passages, preventing the screen from dimming or turning off during reading sessions.

## How It Works

The feature uses the browser's Screen Wake Lock API to prevent automatic screen timeout. It's designed to be battery-conscious with automatic timeout after inactivity.

### Activity Detection

The wake lock is refreshed when you:
- Scroll through the passage
- Navigate to previous/next chapters
- Load a new passage

### Automatic Release

After a configured timeout period of inactivity (default: 5 minutes), the wake lock is automatically released to save battery.

## Configuration

You can configure the wake lock timeout in Settings:

1. Open the sidebar
2. Navigate to the Settings tab
3. Find the "Wake Lock" section (moon icon)
4. Select your preferred timeout:
   - 1 minute
   - 2 minutes
   - 5 minutes (default)
   - 10 minutes
   - 15 minutes
   - 30 minutes
   - Disabled

Your preference is saved and persists across sessions.

## Browser Compatibility

The Wake Lock API is supported in:
- Chrome/Edge 84+
- Safari 16.4+ (iOS and macOS)
- Opera 70+

On unsupported browsers, the feature gracefully degrades—the app continues to work normally, just without wake lock functionality.

## Privacy & Battery

- **No Permissions Required**: The Wake Lock API doesn't require explicit user permission
- **No Data Collection**: No personal data is collected or transmitted
- **Battery Conscious**: Automatic timeout prevents battery drain
- **Local Storage Only**: Only your timeout preference is stored locally

## Technical Details

### Implementation

The feature is implemented using:
- Custom React hook: `useWakeLock` (`frontend/src/hooks/useWakeLock.ts`)
- Integration in `BibleReader` component with debounced scroll events (300ms)
- Settings UI in `UserSettings` component
- Local storage functions for persistence

### Code Location

- Hook: `frontend/src/hooks/useWakeLock.ts`
- Integration: `frontend/src/components/BibleReader.tsx`
- Settings: `frontend/src/components/UserSettings.tsx`
- Storage: `frontend/src/lib/storage.ts`

## See Also

- [Getting Started Guide](../getting-started.md)
- [FAQ](../faq.md)
