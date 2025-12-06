# Passage Links Feature

## Overview

The Passage Links feature allows users to navigate to specific Bible passages using URL parameters. When a passage link is opened, the entire chapter is loaded for context, and the specified verse(s) are highlighted and automatically scrolled into view.

## URL Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `book` | string | Yes* | Bible book name (e.g., "John", "1 Corinthians") |
| `chapter` | number | Yes* | Chapter number |
| `verse` | number | No | Single verse to highlight |
| `verseStart` | number | No | Start of verse range |
| `verseEnd` | number | No | End of verse range |
| `translation` | string | No | Bible translation code (e.g., "KJV", "WEB") |

\* `book` and `chapter` are required together

## Examples

### Single Verse
```
?book=John&chapter=3&verse=16
```

### Verse Range
```
?book=John&chapter=3&verseStart=16&verseEnd=17
```

### With Translation
```
?book=John&chapter=3&verse=16&translation=KJV
```

## Programmatic Usage

```typescript
import { createPassageLink, formatPassageReference } from '@/lib/passageLinks';

// Create a link
const link = createPassageLink({
  book: "John",
  chapter: 3,
  verseStart: 16
});

// Format a reference
const ref = formatPassageReference({
  book: "John",
  chapter: 3,
  verseStart: 16,
  verseEnd: 17
});
// Returns: "John 3:16-17"
```

## Testing

Run tests with:
```bash
cd frontend
bun test src/lib/__tests__/urlParser.test.ts
bun test src/lib/__tests__/passageLinks.test.ts
```

38 tests covering URL parsing, link generation, and reference formatting.
