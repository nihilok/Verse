# Database Schema

Verse uses PostgreSQL with SQLAlchemy ORM for data persistence.

## Schema Overview

```
users
  ├─→ user_insights ←─ saved_insights ─→ chat_messages
  ├─→ user_definitions ←─ saved_definitions
  └─→ standalone_chats ─→ standalone_chat_messages
```

## Tables

### users

Stores anonymous users identified by a UUID cookie.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| anonymous_id | String(36) | UUID for anonymous identification |
| created_at | DateTime | When user was created |

**Indexes:**
- `anonymous_id` (unique)

**Relationships:**
- Has many insights (via `user_insights`)
- Has many definitions (via `user_definitions`)
- Has many chat_messages
- Has many standalone_chats

---

### saved_passages

Stores Bible passages retrieved from the Bible API.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| reference | String(100) | Passage reference (e.g., "John 3:16") |
| book | String(50) | Book name |
| chapter | Integer | Chapter number |
| verse_start | Integer | Starting verse |
| verse_end | Integer | Ending verse (nullable) |
| translation | String(10) | Translation code (default: "WEB") |
| text | Text | The passage text |
| created_at | DateTime | When passage was saved |
| updated_at | DateTime | When passage was updated |

**Indexes:**
- `reference`

**Notes:**
- Currently not linked to users (global cache)
- May be linked to users in future versions

---

### saved_insights

Stores AI-generated insights for Bible passages.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| passage_reference | String(100) | Passage reference |
| passage_text | Text | The passage text |
| historical_context | Text | Historical background |
| theological_significance | Text | Theological themes |
| practical_application | Text | Practical applications |
| created_at | DateTime | When insight was generated |

**Indexes:**
- `passage_reference`
- `passage_text`
- Composite unique: (`passage_reference`, `passage_text`)

**Relationships:**
- Belongs to many users (via `user_insights`)
- Has many chat_messages (cascade delete)

**Notes:**
- Insights are cached globally but linked to users via `user_insights`
- Same passage + text = same insight (cached)
- Deleting an insight deletes all related chat messages

---

### saved_definitions

Stores AI-generated word definitions.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| word | String(100) | The word being defined |
| passage_reference | String(100) | Where the word appears |
| verse_text | Text | The verse containing the word |
| definition | Text | Modern definition |
| biblical_usage | Text | Usage in biblical context |
| original_language | Text | Hebrew/Greek insights |
| created_at | DateTime | When definition was generated |

**Indexes:**
- `word`
- `passage_reference`
- Composite unique: (`word`, `passage_reference`, `verse_text`)

**Relationships:**
- Belongs to many users (via `user_definitions`)

**Notes:**
- Same word in same verse = same definition (cached)
- Different verses may have different contexts

---

### user_insights

Linking table for many-to-many relationship between users and insights.

| Column | Type | Description |
|--------|------|-------------|
| user_id | Integer | Foreign key to users |
| insight_id | Integer | Foreign key to saved_insights |
| created_at | DateTime | When user saved this insight |

**Composite Primary Key:** (`user_id`, `insight_id`)

**Indexes:**
- Composite: (`user_id`, `created_at`) for efficient history queries

**Foreign Keys:**
- `user_id` → users(id) CASCADE DELETE
- `insight_id` → saved_insights(id) CASCADE DELETE

---

### user_definitions

Linking table for many-to-many relationship between users and definitions.

| Column | Type | Description |
|--------|------|-------------|
| user_id | Integer | Foreign key to users |
| definition_id | Integer | Foreign key to saved_definitions |
| created_at | DateTime | When user saved this definition |

**Composite Primary Key:** (`user_id`, `definition_id`)

**Indexes:**
- Composite: (`user_id`, `created_at`) for efficient history queries

**Foreign Keys:**
- `user_id` → users(id) CASCADE DELETE
- `definition_id` → saved_definitions(id) CASCADE DELETE

---

### chat_messages

Stores chat messages related to specific insights.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| insight_id | Integer | Foreign key to saved_insights |
| user_id | Integer | Foreign key to users |
| role | String(20) | 'user' or 'assistant' |
| content | Text | Message content |
| created_at | DateTime | When message was created |

**Indexes:**
- `insight_id`
- `user_id`
- Composite: (`user_id`, `created_at`)
- Composite: (`insight_id`, `user_id`, `created_at`)

**Foreign Keys:**
- `insight_id` → saved_insights(id) CASCADE DELETE
- `user_id` → users(id) CASCADE DELETE

**Relationships:**
- Belongs to saved_insights
- Belongs to user

---

### standalone_chats

Chat sessions not linked to specific insights.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to users |
| title | String(200) | Chat title (nullable) |
| passage_reference | String(100) | Optional passage reference |
| passage_text | Text | Optional passage text |
| created_at | DateTime | When chat was created |
| updated_at | DateTime | When chat was last updated |

**Indexes:**
- `user_id`
- Composite: (`user_id`, `created_at`)

**Foreign Keys:**
- `user_id` → users(id) CASCADE DELETE

**Relationships:**
- Belongs to user
- Has many standalone_chat_messages (cascade delete)

---

### standalone_chat_messages

Messages in standalone chats.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| chat_id | Integer | Foreign key to standalone_chats |
| role | String(20) | 'user' or 'assistant' |
| content | Text | Message content |
| created_at | DateTime | When message was created |

**Indexes:**
- `chat_id`
- Composite: (`chat_id`, `created_at`)

**Foreign Keys:**
- `chat_id` → standalone_chats(id) CASCADE DELETE

**Relationships:**
- Belongs to standalone_chat

---

## Database Initialization

Tables are created automatically on application startup via:

```python
Base.metadata.create_all(bind=engine)
```

This happens in the application lifespan context manager in `app/main.py`.

## Migrations

For schema changes, use Alembic:

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

**Note:** Composite indexes require migrations for existing databases. New deployments get them automatically.

## Caching Strategy

### Insights Cache

Insights are cached based on:
- Passage reference
- Passage text (stripped of whitespace)

This means:
1. Same passage from same translation = cached
2. Different translations = different cache entries
3. Cache is shared across all users
4. Users can have their own "saved insights" via `user_insights`

### Definitions Cache

Definitions are cached based on:
- Word (stripped of whitespace)
- Passage reference
- Verse text

This means:
1. Same word in same verse = cached
2. Same word in different verses may have different definitions
3. Context-aware caching

## Performance Optimizations

### Indexes

Composite indexes for common query patterns:
- User insight history: (`user_id`, `created_at`)
- User definition history: (`user_id`, `created_at`)
- Chat messages: (`insight_id`, `user_id`, `created_at`)
- Standalone chat messages: (`chat_id`, `created_at`)

### Connection Pooling

PostgreSQL connection pooling is configured in `app/core/database.py`:
- Pool size: 10
- Max overflow: 20
- Pre-ping: true (for connection health checks)

**Note:** Connection pooling is only active for PostgreSQL. SQLite uses NullPool.

## Data Relationships

### User Data Ownership

All user data is linked via `user_id` with CASCADE DELETE:
- Deleting a user deletes all their chat messages
- Deleting a user removes their links to insights/definitions
- Shared insights/definitions persist (cached globally)

### Insight Chat History

Chat messages are linked to insights:
- Deleting an insight deletes all related chat messages
- Deleting a user deletes their chat messages
- Chat history is per-insight, not global

### Standalone Chats

Independent of insights:
- Can include passage context (optional)
- Have their own message history
- Deleted independently

---

## Related Documentation

- [API Reference](api.md) - API endpoints
- [Architecture Overview](../architecture/) - System design
- [Configuration Reference](configuration.md) - Environment variables
