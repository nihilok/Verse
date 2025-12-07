# Wake Lock API - User Interface

## Settings Panel

The Wake Lock settings are located in the **Settings** tab of the sidebar.

### Location in UI
```
Sidebar → Settings Tab → Wake Lock Section
```

### Visual Layout

```
┌─────────────────────────────────────────────────┐
│                   Settings                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  [User ID Section]                              │
│  ...                                            │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  🌙 Wake Lock                                   │
│  ─────────────────────────────────────────────  │
│                                                 │
│  Keep your device awake while reading. The      │
│  wake lock will automatically release after     │
│  the specified timeout period of inactivity.    │
│                                                 │
│  Timeout: [5 minutes        ▼]                  │
│           ┌──────────────────┐                  │
│           │ 1 minute         │                  │
│           │ 2 minutes        │                  │
│           │ 5 minutes    ✓   │                  │
│           │ 10 minutes       │                  │
│           │ 15 minutes       │                  │
│           │ 30 minutes       │                  │
│           │ Disabled         │                  │
│           └──────────────────┘                  │
│                                                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  Data Management                                │
│  ...                                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Key UI Elements

### 1. Section Header
- **Icon**: 🌙 Moon icon (using lucide-react's Moon component)
- **Text**: "Wake Lock" in medium font weight
- **Styling**: Flexbox layout with gap for icon and text

### 2. Description
- **Text**: Clear explanation of the feature's purpose
- **Styling**: Small text, muted foreground color
- **Content**: Explains that the device stays awake during reading and auto-releases after inactivity

### 3. Timeout Selector
- **Label**: "Timeout:" in small, muted text
- **Input**: Native HTML `<select>` dropdown
- **Options**:
  - 1 minute
  - 2 minutes
  - **5 minutes** (default, selected on first use)
  - 10 minutes
  - 15 minutes
  - 30 minutes
  - Disabled (turns off wake lock)
- **Styling**: Rounded border, consistent with app's design system

### 4. User Feedback
When the timeout is changed:
- **Success Message**: "Wake lock timeout updated. Reload the page for changes to take effect."
- **Display**: Green success notification at the top of the app
- **Duration**: Persists until user dismisses it

## Responsive Behavior

### Desktop (lg breakpoint and above)
- Settings panel is always visible in the sidebar
- Wake Lock section appears in natural flow

### Mobile (below lg breakpoint)
- Settings accessed via sidebar menu button
- Wake Lock section scrolls with other settings
- Dropdown selector adapts to touch input

## Accessibility

### Features
- **Label Association**: Proper `htmlFor` attribute linking label to select
- **Keyboard Navigation**: Full keyboard support for dropdown
- **Focus Indicators**: Visual ring on focus
- **Screen Reader Support**: Semantic HTML elements for proper announcement

### ARIA Attributes
```html
<label for="wake-lock-timeout">Timeout:</label>
<select id="wake-lock-timeout" ...>
```

## Visual Design Tokens

### Colors
- **Border**: `border-input` (theme-aware)
- **Background**: `bg-background` (theme-aware)
- **Text**: `text-muted-foreground` for descriptions
- **Focus Ring**: `ring-ring` (theme-aware)

### Spacing
- **Section Gap**: `space-y-2` (0.5rem between elements)
- **Internal Gap**: `gap-2` (0.5rem between label and select)

### Typography
- **Header**: `text-sm font-medium`
- **Description**: `text-xs`
- **Dropdown**: `text-xs`

## User Flow

### First-Time User
1. Opens app
2. Wake lock is active with 5-minute default timeout
3. Can optionally adjust in Settings if desired

### Changing Settings
1. Click sidebar → Settings tab
2. Scroll to "Wake Lock" section
3. Click timeout dropdown
4. Select desired timeout (or "Disabled")
5. See success message
6. Reload page for changes to take effect

### Disabling Feature
1. Navigate to Settings → Wake Lock
2. Select "Disabled" from dropdown
3. Wake lock will not activate on next page load

## Browser Console Feedback

When feature is active, developers can see:
```
Wake Lock acquired
```

When wake lock is released:
```
Wake Lock released
```

On unsupported browsers:
```
Wake Lock API not supported in this browser
```

## Integration with Reading Experience

### BibleReader Component
The wake lock works seamlessly in the background:
- **Invisible to User**: No UI changes in the reader itself
- **Activity Detection**: Triggers on scroll and navigation
- **No Interruptions**: Doesn't interfere with text selection, insights, or other features

### Benefits
- 📖 Read longer without screen timeout
- 📱 Better mobile reading experience
- 🔋 Battery-conscious with configurable timeout
- ⚙️ Fully configurable per user preference
