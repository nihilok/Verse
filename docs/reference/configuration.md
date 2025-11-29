# Configuration Reference

Verse is configured primarily through environment variables.

## Environment Variables

### Required Variables

#### ANTHROPIC_API_KEY

**Description:** API key for Anthropic Claude AI service

**Required:** Yes

**Example:**
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

**Where to get it:** [Anthropic Console](https://console.anthropic.com/)

**Notes:**
- Required for all AI features (insights, definitions, chat)
- Keep this secret and never commit to version control
- Different keys for development and production recommended

---

### Database Configuration

#### DATABASE_URL

**Description:** PostgreSQL connection string

**Required:** No (defaults provided)

**Default:** `postgresql://verse_user:verse_password@db:5432/verse_db` (Docker)

**Examples:**

```env
# Docker Compose
DATABASE_URL=postgresql://verse_user:verse_password@db:5432/verse_db

# Local PostgreSQL
DATABASE_URL=postgresql://verse_user:verse_password@localhost:5432/verse_db

# Testing with SQLite
DATABASE_URL=sqlite:///./test.db

# Production (with connection pooling parameters)
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=10&max_overflow=20
```

**Notes:**
- SQLite is supported but not recommended for production
- Connection pooling is automatic for PostgreSQL
- Use SSL for production: `?sslmode=require`

---

### Application Settings

#### ENVIRONMENT

**Description:** Application environment

**Required:** No

**Default:** `development`

**Options:** `development`, `production`, `test`

**Example:**
```env
ENVIRONMENT=production
```

**Impact:**
- `development`: Debug mode, verbose logging, CORS allows localhost
- `production`: No debug, secure cookies, strict CORS
- `test`: Special test configuration, mock external APIs

---

#### DEBUG

**Description:** Enable debug mode

**Required:** No

**Default:** `false`

**Example:**
```env
DEBUG=true
```

**Impact:**
- Enables verbose logging
- Shows detailed error messages
- Should be `false` in production

---

### Security Settings

#### COOKIE_SECURE

**Description:** Whether to use secure cookies (HTTPS only)

**Required:** No

**Default:** Depends on `ENVIRONMENT` (true for production, false otherwise)

**Example:**
```env
COOKIE_SECURE=true
```

**Notes:**
- Set to `true` when using HTTPS
- Set to `false` for local development over HTTP
- Automatically configured based on `ENVIRONMENT`

---

#### ALLOWED_ORIGINS

**Description:** Comma-separated list of allowed CORS origins

**Required:** No

**Default:** `http://localhost:5173,http://localhost:3000` (development)

**Example:**
```env
ALLOWED_ORIGINS=https://verse.example.com,https://www.verse.example.com
```

**Notes:**
- Critical for security in production
- Must match your frontend URL exactly
- Include protocol (http/https)
- No trailing slashes

---

### Rate Limiting

#### AI_ENDPOINT_LIMIT

**Description:** Rate limit for AI endpoints (insights, definitions)

**Required:** No

**Default:** `10/minute`

**Example:**
```env
AI_ENDPOINT_LIMIT=20/minute
```

**Format:** `{number}/{period}` where period is `second`, `minute`, `hour`, or `day`

---

#### CHAT_ENDPOINT_LIMIT

**Description:** Rate limit for chat endpoints

**Required:** No

**Default:** `20/minute`

**Example:**
```env
CHAT_ENDPOINT_LIMIT=30/minute
```

---

### Bible Translations

#### Current Implementation

**Status:** Limited to 6 hardcoded translations

Verse currently supports these translations via the `TRANSLATION_IDS` mapping in `backend/app/clients/helloao_client.py`:

- **WEB** - World English Bible (default)
- **KJV** - King James Version
- **BSB** - Berean Standard Bible
- **LSV** - Literal Standard Version
- **SRV** - Spanish Reina-Valera 1909
- **BES** - Spanish Biblia en Español Sencillo

**Adding More Translations (Current Method):**

Edit `backend/app/clients/helloao_client.py` and add to the `TRANSLATION_IDS` dictionary:

```python
TRANSLATION_IDS = {
    "WEB": "ENGWEBP",
    "YourName": "API_ID_FROM_HELLOAO",
    # ...
}
```

Find available translation IDs at: `https://bible.helloao.org/api/available_translations.json`

---

#### Future Enhancement: Dynamic Translation Support

**Planned:** Update Verse to dynamically fetch and support all available translations

The HelloAO Bible API supports **1,200+ translations** in 100+ languages that can be queried dynamically:

**API Endpoint:**
```
GET https://bible.helloao.org/api/available_translations.json
```

**Response includes:**
- Translation ID (used in API calls)
- Full name and short name
- Language and text direction (LTR/RTL)
- Number of books/chapters/verses
- License information

**Planned Implementation:**
1. Fetch available translations on startup or cache them
2. Expose `/api/translations` endpoint for frontend
3. Allow users to select any available translation
4. Store user's preferred translation in database
5. Update UI to show translation picker with all options

**Benefits:**
- Support all 1,200+ translations without code changes
- Always up-to-date with HelloAO API additions
- Better internationalization support
- User-configurable translation preferences

---

### External API Configuration

#### BIBLE_API_BASE_URL

**Description:** Base URL for Bible API

**Required:** No

**Default:** `https://bible.helloao.org`

**Example:**
```env
BIBLE_API_BASE_URL=https://api.esv.org
```

**Notes:**
- Change this when switching Bible API providers
- Requires updating `BibleClient` implementation

---

#### BIBLE_API_TIMEOUT

**Description:** Timeout for Bible API requests (seconds)

**Required:** No

**Default:** `10`

**Example:**
```env
BIBLE_API_TIMEOUT=15
```

---

#### ANTHROPIC_API_TIMEOUT

**Description:** Timeout for Anthropic API requests (seconds)

**Required:** No

**Default:** `60`

**Example:**
```env
ANTHROPIC_API_TIMEOUT=90
```

**Notes:**
- AI requests can take longer
- Increase if getting timeout errors
- Don't set too high (affects user experience)

---

### Frontend Configuration

Frontend configuration uses Vite's environment variable system.

#### VITE_API_URL

**Description:** Backend API URL

**Required:** No (only for development with different ports)

**Default:** Same origin as frontend

**Example:**
```env
VITE_API_URL=http://localhost:8000
```

**Notes:**
- Only needed if backend is on different port/host
- Must start with `VITE_` to be accessible in frontend
- Set in `frontend/.env.local` (not committed)

---

## Configuration Files

### Backend Configuration

**File:** `backend/app/core/config.py`

Python configuration class that reads environment variables:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str = "postgresql://..."
    environment: str = "development"
    debug: bool = False

    class Config:
        env_file = ".env"
```

### Frontend Configuration

**File:** `frontend/vite.config.ts`

Vite configuration for build and development:

```typescript
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

### Docker Configuration

**File:** `docker-compose.yml`

Docker Compose configuration:

```yaml
services:
  backend:
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=postgresql://...
```

---

## Environment File Examples

### Development (.env)

```env
# AI Service
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Database
DATABASE_URL=postgresql://verse_user:verse_password@localhost:5432/verse_db

# Application
ENVIRONMENT=development
DEBUG=true

# Security (disabled for local dev)
COOKIE_SECURE=false
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Production (.env)

```env
# AI Service
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx-prod

# Database (with SSL)
DATABASE_URL=postgresql://user:password@prod-db.example.com:5432/verse_db?sslmode=require

# Application
ENVIRONMENT=production
DEBUG=false

# Security (enabled for production)
COOKIE_SECURE=true
ALLOWED_ORIGINS=https://verse.example.com

# Rate Limiting (more restrictive)
AI_ENDPOINT_LIMIT=5/minute
CHAT_ENDPOINT_LIMIT=10/minute

# API Timeouts
BIBLE_API_TIMEOUT=15
ANTHROPIC_API_TIMEOUT=90
```

### Testing (.env.test)

```env
# AI Service (mock key for testing)
ANTHROPIC_API_KEY=test_key

# Database (SQLite for tests)
DATABASE_URL=sqlite:///./test.db

# Application
ENVIRONMENT=test
DEBUG=false

# Rate Limiting (disabled for tests)
AI_ENDPOINT_LIMIT=1000/minute
CHAT_ENDPOINT_LIMIT=1000/minute
```

---

## Configuration Priority

Environment variables are loaded in this order (later overrides earlier):

1. System environment variables
2. `.env` file in project root
3. `.env.local` file (not committed to git)
4. Docker Compose `environment` section
5. Command-line overrides

---

## Validating Configuration

### Backend

The application validates configuration on startup. Check logs for errors:

```bash
# Docker
docker compose logs backend | grep -i error

# Local
uvicorn app.main:app --reload
# Look for startup errors
```

### Required Variable Check

Backend will fail to start if `ANTHROPIC_API_KEY` is missing:

```
Error: ANTHROPIC_API_KEY environment variable is required
```

### Database Connection

Backend checks database connection on startup:

```
INFO:     Database connected successfully
```

Or on failure:

```
ERROR:    Could not connect to database: connection refused
```

---

## Security Best Practices

1. **Never commit `.env` files** - use `.env.example` as template
2. **Use different keys** for development and production
3. **Rotate keys regularly** - especially after team member changes
4. **Use secrets management** in production (e.g., AWS Secrets Manager)
5. **Set COOKIE_SECURE=true** in production
6. **Use strict ALLOWED_ORIGINS** - no wildcards in production
7. **Enable DATABASE_URL SSL** for production databases

---

## Related Documentation

- [Getting Started](../getting-started.md) - Initial setup
- [Development Guide](../guides/development.md) - Development environment
- [Production Deployment](../guides/production.md) - Production configuration
- [Security](../architecture/security.md) - Security features
