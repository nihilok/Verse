# API Reference

Complete reference for all Verse API endpoints.

## Base URL

- Development: `http://localhost:8000`
- Production: Configure based on your deployment

## Authentication

The current version uses anonymous user sessions via cookies. No explicit authentication is required, but all requests must include cookies for session tracking.

## Rate Limiting

AI-powered endpoints have rate limiting to prevent abuse:

- **Insights & Definitions**: 10 requests per minute
- **Chat endpoints**: 20 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

## Endpoints

### Health Check

#### GET /health

Check API status.

**Response:**
```json
{
  "status": "healthy"
}
```

---

### Bible Endpoints

#### GET /api/passage

Retrieve a specific Bible passage.

**Query Parameters:**
- `book` (required): Book name (e.g., "John", "Genesis")
- `chapter` (required): Chapter number (integer)
- `verse_start` (required): Starting verse (integer)
- `verse_end` (optional): Ending verse (integer)
- `translation` (optional): Translation code (default: "WEB")

**Example:**
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

#### GET /api/chapter

Retrieve an entire chapter.

**Query Parameters:**
- `book` (required): Book name
- `chapter` (required): Chapter number (integer)
- `translation` (optional): Translation code (default: "WEB")

**Example:**
```bash
GET /api/chapter?book=Psalm&chapter=23
```

**Response:** Same format as `/api/passage`

---

### Insights Endpoints

#### POST /api/insights

Generate AI-powered insights for a Bible passage.

**Rate Limit:** 10 requests per minute

**Request Body:**
```json
{
  "passage_text": "For God so loved the world...",
  "passage_reference": "John 3:16",
  "save": true
}
```

**Fields:**
- `passage_text` (required): The passage text
- `passage_reference` (required): Reference (e.g., "John 3:16")
- `save` (optional): Save to history (default: false)

**Response:**
```json
{
  "id": 123,
  "historical_context": "This passage is from Jesus's conversation with Nicodemus...",
  "theological_significance": "This verse encapsulates the core message of Christianity...",
  "practical_application": "In modern life, this passage reminds us...",
  "cached": false
}
```

**Fields:**
- `id`: Insight ID for chat follow-ups
- `historical_context`: Historical background
- `theological_significance`: Theological themes
- `practical_application`: Practical applications
- `cached`: Whether retrieved from cache

**Status Codes:**
- `200 OK`: Success
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Generation failed

---

#### GET /api/insights/{insight_id}

Retrieve a saved insight by ID.

**Response:** Same as POST `/api/insights`

---

#### DELETE /api/insights/{insight_id}

Delete a saved insight.

**Status Codes:**
- `200 OK`: Deleted successfully
- `404 Not Found`: Insight not found
- `403 Forbidden`: Not authorized to delete

---

### Definition Endpoints

#### POST /api/definitions

Generate AI-powered definition for a biblical word.

**Rate Limit:** 10 requests per minute

**Request Body:**
```json
{
  "word": "righteousness",
  "verse_text": "Blessed are those who hunger and thirst for righteousness...",
  "passage_reference": "Matthew 5:6",
  "save": true
}
```

**Response:**
```json
{
  "id": 456,
  "word": "righteousness",
  "definition": "The quality of being morally right or justifiable...",
  "biblical_usage": "In biblical context, righteousness refers to...",
  "original_language": "Greek: δικαιοσύνη (dikaiosynē)...",
  "cached": false
}
```

**Status Codes:**
- `200 OK`: Success
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Generation failed

---

### Chat Endpoints

#### POST /api/chat/message

Send a follow-up question about an insight.

**Rate Limit:** 20 requests per minute

**Request Body:**
```json
{
  "insight_id": 123,
  "message": "Can you explain more about the historical context?",
  "passage_text": "For God so loved the world...",
  "passage_reference": "John 3:16",
  "insight_context": {
    "historical_context": "...",
    "theological_significance": "...",
    "practical_application": "..."
  }
}
```

**Response:**
```json
{
  "response": "Certainly! The historical context of this passage..."
}
```

---

#### POST /api/chat/standalone

Create a new standalone chat (not linked to an insight).

**Rate Limit:** 20 requests per minute

**Request Body:**
```json
{
  "message": "What does the Bible say about prayer?",
  "passage_text": null,
  "passage_reference": null
}
```

**Response:**
```json
{
  "chat_id": 789,
  "response": "The Bible has much to say about prayer..."
}
```

---

#### POST /api/chat/standalone/message

Send a message in an existing standalone chat.

**Rate Limit:** 20 requests per minute

**Request Body:**
```json
{
  "chat_id": 789,
  "message": "Can you give me some specific examples?"
}
```

**Response:**
```json
{
  "response": "Here are some examples from Scripture..."
}
```

---

#### GET /api/chat/history

Get the current user's chat history.

**Response:**
```json
[
  {
    "id": 789,
    "title": "Prayer in the Bible",
    "last_message": "Can you give me some specific examples?",
    "created_at": "2024-11-29T10:30:00Z",
    "updated_at": "2024-11-29T10:35:00Z",
    "message_count": 4
  }
]
```

---

#### GET /api/chat/standalone/{chat_id}

Get a specific standalone chat with all messages.

**Response:**
```json
{
  "id": 789,
  "title": "Prayer in the Bible",
  "created_at": "2024-11-29T10:30:00Z",
  "messages": [
    {
      "role": "user",
      "content": "What does the Bible say about prayer?",
      "created_at": "2024-11-29T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "The Bible has much to say about prayer...",
      "created_at": "2024-11-29T10:30:05Z"
    }
  ]
}
```

---

#### DELETE /api/chat/standalone/{chat_id}

Delete a standalone chat and all its messages.

**Status Codes:**
- `200 OK`: Deleted successfully
- `404 Not Found`: Chat not found
- `403 Forbidden`: Not authorized to delete

---

### User Endpoints

#### GET /api/user/insights

Get the current user's insight history.

**Response:**
```json
[
  {
    "id": 123,
    "passage_reference": "John 3:16",
    "passage_text": "For God so loved the world...",
    "created_at": "2024-11-29T09:00:00Z",
    "has_chat": true
  }
]
```

---

#### GET /api/user/definitions

Get the current user's definition history.

**Response:**
```json
[
  {
    "id": 456,
    "word": "righteousness",
    "passage_reference": "Matthew 5:6",
    "created_at": "2024-11-29T09:15:00Z"
  }
]
```

---

#### POST /api/user/translation

Set the user's preferred Bible translation.

**Request Body:**
```json
{
  "translation": "KJV"
}
```

**Response:**
```json
{
  "translation": "KJV"
}
```

---

#### POST /api/user/import

Import user data (insights, chats, definitions) from a JSON export.

**Request Body:**
```json
{
  "insights": [...],
  "chats": [...],
  "definitions": [...]
}
```

**Response:**
```json
{
  "insights_imported": 5,
  "chats_imported": 3,
  "definitions_imported": 10
}
```

---

#### GET /api/user/export

Export all user data as JSON.

**Response:**
```json
{
  "insights": [...],
  "chats": [...],
  "definitions": [...],
  "exported_at": "2024-11-29T10:00:00Z"
}
```

---

## Error Handling

All endpoints return errors in a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Status Codes:**
- `400 Bad Request`: Invalid input parameters
- `403 Forbidden`: Not authorized
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Supported Translations

**Current Status:** Verse currently supports 6 hardcoded translations:

- `WEB`: World English Bible (default)
- `KJV`: King James Version
- `BSB`: Berean Standard Bible
- `LSV`: Literal Standard Version
- `SRV`: Spanish Reina-Valera 1909
- `BES`: Spanish Biblia en Español Sencillo

**Available Translations:** The HelloAO Bible API provides access to **1,200+ translations** in 100+ languages. You can query all available translations:

```bash
curl https://bible.helloao.org/api/available_translations.json
```

**Future Enhancement:** Verse will be updated to dynamically support all available translations instead of the current hardcoded list. See [Configuration Reference](configuration.md#bible-translations) for details on this planned enhancement.

---

## Related Documentation

- [Getting Started](../getting-started.md) - Initial setup
- [Database Schema](database.md) - Data models
- [Security](../architecture/security.md) - Security features
