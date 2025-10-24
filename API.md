# API Documentation

## Base URL

- Development: `http://localhost:8000`
- Production: Configure based on deployment

## Endpoints

### Health Check

#### GET /health

Check if the API is running.

**Response:**
```json
{
  "status": "healthy"
}
```

---

### Get Bible Passage

#### GET /api/passage

Retrieve a specific Bible passage.

**Query Parameters:**
- `book` (required): Book name (e.g., "John", "Genesis", "Romans")
- `chapter` (required): Chapter number (integer)
- `verse_start` (required): Starting verse number (integer)
- `verse_end` (optional): Ending verse number (integer)
- `translation` (optional): Bible translation code (default: "WEB")
- `save` (optional): Save passage to database (boolean, default: false)

**Example Request:**
```bash
GET /api/passage?book=John&chapter=3&verse_start=16&verse_end=17&translation=WEB
```

**Response:**
```json
{
  "reference": "John 3:16-17",
  "verses": [
    {
      "book": "John",
      "chapter": 3,
      "verse": 16,
      "text": "For God so loved the world...",
      "translation": "WEB"
    },
    {
      "book": "John",
      "chapter": 3,
      "verse": 17,
      "text": "For God didn't send his Son...",
      "translation": "WEB"
    }
  ],
  "translation": "WEB"
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Passage not found
- `500 Internal Server Error`: Server error

---

### Get Bible Chapter

#### GET /api/chapter

Retrieve an entire chapter.

**Query Parameters:**
- `book` (required): Book name
- `chapter` (required): Chapter number (integer)
- `translation` (optional): Bible translation code (default: "WEB")
- `save` (optional): Save chapter to database (boolean, default: false)

**Example Request:**
```bash
GET /api/chapter?book=Psalm&chapter=23&translation=WEB
```

**Response:**
```json
{
  "reference": "Psalm 23",
  "verses": [
    {
      "book": "Psalm",
      "chapter": 23,
      "verse": 1,
      "text": "Yahweh is my shepherd...",
      "translation": "WEB"
    },
    ...
  ],
  "translation": "WEB"
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Chapter not found
- `500 Internal Server Error`: Server error

---

### Generate AI Insights

#### POST /api/insights

Generate AI-powered insights for a Bible passage.

**Request Body:**
```json
{
  "passage_text": "For God so loved the world that he gave his one and only Son...",
  "passage_reference": "John 3:16",
  "save": true
}
```

**Fields:**
- `passage_text` (required): The text of the passage
- `passage_reference` (required): Reference to the passage (e.g., "John 3:16")
- `save` (optional): Save insights to database (boolean, default: false)

**Response:**
```json
{
  "historical_context": "This passage is from Jesus's conversation with Nicodemus...",
  "theological_significance": "This verse encapsulates the core message of Christianity...",
  "practical_application": "In modern life, this passage reminds us...",
  "cached": false
}
```

**Fields:**
- `historical_context`: Historical background and context
- `theological_significance`: Theological themes and meaning
- `practical_application`: Practical ways to apply the passage
- `cached`: Whether the result was retrieved from cache

**Status Codes:**
- `200 OK`: Success
- `500 Internal Server Error`: Failed to generate insights

---

## Supported Bible Translations

The application uses the HelloAO Bible API, which supports various translations. Common ones include:

- `WEB`: World English Bible (default)
- `KJV`: King James Version
- `ASV`: American Standard Version
- `BBE`: Bible in Basic English
- `YLT`: Young's Literal Translation

Note: Translation availability may vary. Check the HelloAO API documentation for the full list.

---

## Error Handling

All endpoints follow consistent error handling:

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Error Codes:**
- `400 Bad Request`: Invalid input parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Rate Limiting

The API does not implement rate limiting by default, but it's recommended for production deployments.

---

## Authentication

The current version does not require authentication. For production, consider adding API key authentication or OAuth.

---

## Data Models

### BibleVerse
```typescript
{
  book: string;
  chapter: number;
  verse: number;
  text: string;
  translation: string;
}
```

### BiblePassage
```typescript
{
  reference: string;
  verses: BibleVerse[];
  translation: string;
}
```

### Insight
```typescript
{
  historical_context: string;
  theological_significance: string;
  practical_application: string;
  cached?: boolean;
}
```

---

## Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation powered by Swagger UI.
