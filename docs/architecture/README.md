# Architecture Overview

Verse follows a modern, layered architecture with clear separation of concerns and abstraction layers to prevent vendor lock-in.

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         User Browser                           │
│                    http://localhost:5173                       │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            │ HTTP/REST API
                            │
┌───────────────────────────▼────────────────────────────────────┐
│                   Frontend (React + TypeScript)                │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │   Passage    │  │    Bible     │  │   Insights Panel   │    │
│  │    Search    │  │    Reader    │  │   Chat Interface   │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API Service Layer (Axios)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            │ REST API (JSON)
                            │
┌───────────────────────────▼────────────────────────────────────┐
│                   Backend (FastAPI + Python)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Middleware Layer                                 │  │
│  │  ┌────────────────┐ ┌────────────────┐ ┌─────────────┐   │  │
│  │  │ Anonymous User │ │ Rate Limiting  │ │  Security   │   │  │
│  │  │   Middleware   │ │   Middleware   │ │  Headers    │   │  │
│  │  └────────────────┘ └────────────────┘ └─────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routes Layer                      │  │
│  │   /api/passage  │  /api/insights  │  /api/chat           │  │
│  └────────────┬──────────────┬──────────────┬───────────────┘  │
│               │              │              │                  │
│  ┌────────────▼──────────────▼──────────────▼───────────────┐  │
│  │                   Service Layer                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐   │  │
│  │  │  Bible   │  │ Insight  │  │   Chat   │  │  User   │   │  │
│  │  │ Service  │  │ Service  │  │ Service  │  │ Service │   │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘   │  │
│  └───────┬──────────────┬──────────────┬──────────┬─────────┘  │
│          │              │              │          │            │
│  ┌───────▼──────────────▼──────────────▼──────────▼─────────┐  │
│  │              Client Abstraction Layer                    │  │
│  │  ┌──────────────────┐      ┌─────────────────────────┐   │  │
│  │  │  BibleClient     │      │      AIClient           │   │  │
│  │  │  (Abstract)      │      │      (Abstract)         │   │  │
│  │  └────────┬─────────┘      └──────────┬──────────────┘   │  │
│  └───────────┼───────────────────────────┼──────────────────┘  │
│              │                           │                     │
│  ┌───────────▼────────────┐   ┌──────────▼──────────────────┐  │
│  │  HelloAOBibleClient    │   │    ClaudeAIClient           │  │
│  │  (Implementation)      │   │    (Implementation)         │  │
│  └───────────┬────────────┘   └──────────┬──────────────────┘  │
└──────────────┼───────────────────────────┼─────────────────────┘
               │                           │
    ┌──────────▼──────────┐     ┌──────────▼─────────┐
    │  bible.helloao.org  │     │  Anthropic Claude  │
    │      Bible API      │     │       API          │
    └─────────────────────┘     └────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                    Database (PostgreSQL)                      │
│  ┌──────────┐ ┌─────────────┐ ┌──────────────┐ ┌───────────┐  │
│  │  users   │ │   insights  │ │ definitions  │ │   chats   │  │
│  └──────────┘ └─────────────┘ └──────────────┘ └───────────┘  │
└───────────────────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. Layered Architecture

Each layer has specific responsibilities:

**Frontend Layer**

- User interface and interactions
- State management
- API communication
- Client-side validation

**Backend API Layer**

- Request/response handling
- Input validation
- Route definitions
- HTTP status codes

**Service Layer**

- Business logic
- Data transformation
- Orchestration of clients
- Database operations

**Client Abstraction Layer**

- Abstract interfaces for external services
- Prevents vendor lock-in
- Enables easy provider switching

**Implementation Layer**

- Concrete implementations of abstract clients
- External API communication
- Provider-specific logic

### 2. Abstraction Pattern

Abstract base classes define interfaces for external services:

```python
# Abstract interface
class BibleClient(ABC):
    @abstractmethod
    async def get_verse(...): pass

# Concrete implementation
class HelloAOBibleClient(BibleClient):
    async def get_verse(...):
        # HelloAO-specific implementation
```

**Benefits:**

- Easy to switch providers (e.g., from HelloAO to ESV API)
- Testing with mock implementations
- No vendor lock-in
- Clear contracts between layers

### 3. Service Layer Pattern

Business logic is separated from API routes:

```python
# routes.py - thin controller
@router.get("/api/passage")
async def get_passage(...):
    service = BibleService()
    return await service.get_passage(...)

# bible_service.py - business logic
class BibleService:
    async def get_passage(self, ...):
        # Check cache
        # Call client
        # Transform data
        # Save to database
```

**Benefits:**

- Reusable business logic
- Easier testing
- Clear separation of concerns
- Can be called from multiple routes

### 4. Anonymous User System

All users are anonymous by default:

```python
# Middleware sets anonymous_id cookie
# Service creates/retrieves user
user = user_service.get_or_create_user(db, anonymous_id)
```

**Benefits:**

- No authentication required
- User data is still tracked
- Can be upgraded to authenticated users later
- Privacy-friendly

## Data Flow Examples

### Reading a Bible Passage

1. User enters search criteria in `PassageSearch` component
2. Frontend calls `api.getPassage()` via axios
3. Request hits `/api/passage` endpoint
4. `BibleService.get_passage()` is called
5. Service calls `BibleClient.get_verse()`
6. `HelloAOBibleClient` makes HTTP request to Bible API
7. Response flows back through layers
8. Frontend renders passage in `BibleReader`

### Getting AI Insights

1. User selects text in `BibleReader`
2. Frontend calls `api.generateInsights()`
3. Request hits rate limiter middleware (10 req/min)
4. Route calls `InsightService.generate_insights()`
5. Service checks database for cached insights
6. If not cached, calls `AIClient.generate_insights()`
7. `ClaudeAIClient` makes request to Claude API
8. Service saves insight to database
9. Service links insight to user via `user_insights` table
10. Response returns with `cached: false`
11. Frontend displays in `InsightsPanel`

### Chat Follow-up

1. User types question in chat interface
2. Frontend calls `api.sendChatMessage()`
3. Request hits rate limiter (20 req/min)
4. Route calls `ChatService.send_message()`
5. Service retrieves conversation history from database
6. Service calls `AIClient.chat()` with context
7. `ClaudeAIClient` sends request with message history
8. Service saves both user message and AI response
9. Frontend updates chat display

## Technology Choices

### Frontend

**React + TypeScript**

- Type safety prevents runtime errors
- Component-based architecture
- Large ecosystem and community

**Vite**

- Fast development server
- Hot module replacement
- Optimized production builds

**Bun**

- Faster than npm/yarn
- Built-in TypeScript support
- Modern JavaScript runtime

### Backend

**FastAPI**

- Automatic API documentation
- Type validation with Pydantic
- Async support
- Python 3.11+ features

**SQLAlchemy**

- Powerful ORM
- Database agnostic
- Migration support with Alembic

**PostgreSQL**

- Robust and reliable
- ACID compliance
- Excellent performance
- Rich data types

### External Services

**HelloAO Bible API**

- Free and open
- Multiple translations
- RESTful interface

**Anthropic Claude**

- State-of-the-art AI
- Good at theological content
- Reliable API
- Rate limits built-in

## Scalability Considerations

### Horizontal Scaling

The backend is **stateless**:

- No in-memory sessions
- All state in database or cookies
- Can run multiple instances
- Load balancer ready

### Caching Strategy

**Insights Cache:**

- Stored in PostgreSQL
- Shared across users
- Reduces Claude API calls
- Significant cost savings

**Database Connection Pooling:**

- 10 base connections
- 20 overflow connections
- Health checks with pre-ping

### Rate Limiting

Per-endpoint rate limits:

- Insights/Definitions: 10/min per user
- Chat: 20/min per user
- Prevents abuse
- Redis backend for distributed systems

## Security Features

### Middleware

**Anonymous User Middleware**

- Manages user sessions
- Sets secure cookies
- Creates/retrieves users

**Rate Limiter Middleware**

- Protects AI endpoints
- Per-user tracking
- Configurable limits

**Security Headers Middleware**

- HSTS
- Content Security Policy
- X-Frame-Options
- X-Content-Type-Options

### CORS Configuration

Strict CORS policy:

- Specific allowed origins
- Credentials support
- Configurable per environment

### Database Security

- Parameterized queries (SQL injection protection)
- CASCADE DELETE for data integrity
- Proper indexing (no table scans)

## Extension Points

### Adding a New Bible Provider

1. Create new client extending `BibleClient`
2. Implement required methods
3. Update `BibleService` to use new client
4. No frontend changes needed

See [Backend Development Guide](guides/backend-development.md) for details.

### Adding a New AI Provider

1. Create new client extending `AIClient`
2. Implement required methods
3. Update `InsightService` and `ChatService`
4. No frontend changes needed

### Adding Authentication

1. Add authentication middleware
2. Update `User` model with auth fields
3. Add login/register endpoints
4. Update frontend with auth UI
5. Link anonymous users to authenticated accounts

## Deployment Architecture

### Development

```
Docker Compose:
├── PostgreSQL container (port 5432)
├── Backend container (port 8000, hot-reload)
└── Frontend container (port 5173, Vite dev server)
```

### Production

```
Docker Compose:
├── PostgreSQL container (internal)
├── Backend container (Uvicorn, internal)
└── Frontend container (Nginx, port 80/443)
```

---

## Related Documentation

- [Backend Architecture Details](architecture/backend.md)
- [Frontend Architecture Details](architecture/frontend.md)
- [Security Features](architecture/security.md)
- [Database Schema](reference/database.md)
