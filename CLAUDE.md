# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Verse is an interactive Bible reader with AI-powered insights built with React/TypeScript frontend and FastAPI/Python backend. Users can highlight biblical passages to receive historical context, theological significance, and practical applications through Claude AI integration.

## Development Commands

### Backend (Python/FastAPI)

**Initial Setup:**
```bash
cd backend
uv sync                    # Creates venv and installs dependencies
uv sync --group dev        # Includes pytest and dev dependencies
```

**Running the Server:**
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Testing:**
```bash
uv run pytest                    # Run all tests
uv run pytest --cov=app         # Run with coverage
uv run pytest tests/test_api.py # Run single test file
```

**Note:** CI tests run with SQLite (`DATABASE_URL=sqlite:///./test.db`) for simplicity.

### Frontend (TypeScript/React/Vite)

**Initial Setup:**
```bash
cd frontend
bun install               # Use bun, not npm or yarn
```

**Development:**
```bash
bun run dev              # Start dev server (port 5173)
bun run lint             # Check linting
bun run lint:fix         # Fix linting issues
bun test                 # Run tests
bun run build            # Build for production
tsc --noEmit            # Type checking only
```

### Docker

**Full-stack Development:**
```bash
docker compose up --build    # Start all services (db, backend, frontend)
docker compose down          # Stop all services
docker compose logs -f       # Follow all logs
```

**Required:** `.env` file with `ANTHROPIC_API_KEY` (copy from `.env.example`)

## Architecture

### Backend Layer Structure

The backend follows a strict layered architecture with abstraction:

```
API Routes (app/api/routes.py)
    ↓
Service Layer (app/services/)
    ↓
Client Abstraction Layer (app/clients/)
    ↓
Concrete Client Implementations
```

**Key Design Patterns:**

1. **Abstract Base Classes** - Both `BibleClient` and `AIClient` are abstract classes. Concrete implementations (`HelloAOBibleClient`, `ClaudeAIClient`) implement these interfaces. This prevents vendor lock-in.

2. **Service Layer Pattern** - Business logic lives in services (`bible_service.py`, `insight_service.py`, `chat_service.py`, `user_service.py`), not in API routes. Services orchestrate client operations and handle database interactions.

3. **Anonymous User Middleware** - All users are anonymous by default. The `AnonymousUserMiddleware` (app/core/middleware.py) manages anonymous user sessions via cookies. Users are created/retrieved using the `get_current_user` dependency in routes.

4. **Database ORM** - SQLAlchemy models (app/models/models.py) handle all database operations. Tables are created on startup via `Base.metadata.create_all()` in the lifespan context manager.

### Frontend Architecture

**State Management:**
- React hooks (useState, useEffect) for local state
- No global state library (Redux/Zustand) - state lives in App.tsx and is passed down

**Key Components:**
- `PassageSearch` - Bible passage search form
- `BibleReader` - Main Bible text display with text selection
- `InsightsModal` - Displays AI-generated insights
- `ChatModal` - Chat interface for follow-up questions on insights
- `InsightsHistory` - Historical insights management
- `ChatHistory` - Standalone chats not tied to specific insights

**API Layer:**
- All API calls go through `services/api.ts` using axios
- Service methods return typed responses based on `types/index.ts`

### Database Schema

**Tables:**
- `users` - Anonymous users (via anonymous_id cookie)
- `saved_passages` - Bible passages (linked to users)
- `saved_insights` - Cached AI insights (linked to passages and users)
- `chat_messages` - Follow-up questions on specific insights
- `standalone_chats` - Independent chat conversations
- `standalone_chat_messages` - Messages in standalone chats
- `user_translations` - User translation preferences

**Important:** Insights are cached in the database. Before calling Claude API, check if insight exists for that passage text.

## Adding New Providers

### Adding a New Bible API

1. Create new client in `backend/app/clients/` extending `BibleClient`
2. Implement abstract methods: `get_verse`, `get_verses`, `get_chapter`
3. Update `BibleService` to use new client

### Adding a New AI Provider

1. Create new client in `backend/app/clients/` extending `AIClient`
2. Implement `generate_insights` and `send_chat_message` methods
3. Update `InsightService` and `ChatService` to use new client

## Code Style & Best Practices

**Python Backend:**
- Use British English spelling in user-facing strings and documentation
- Extract magic numbers to module-level constants
- Use environment variables for deployment settings (e.g., `cookie_secure` for HTTPS)
- Clean up unused imports
- Use `delete().rowcount` directly instead of separate count queries
- Wrap `JSON.parse` in try-catch with specific error messages
- Specify `ondelete='CASCADE'` on foreign keys for proper cleanup

**TypeScript Frontend:**
- Use `bun` for all package management (not npm/yarn)
- Match icons to context (CheckCircle for success, AlertCircle for errors)
- Give users adequate time to read messages before auto-reloading (2500ms minimum)
- Use try-catch for JSON parsing with specific error messages
- Clean up unused catch block variables (use `catch {}` if not needed)

**Database:**
- Index foreign keys and frequently filtered columns
- Use proper linking tables for many-to-many relationships
- Validate data structure early before processing
- Consider batch operations for imports/exports with multiple items

## Testing

**Backend:**
- Tests in `backend/tests/`
- Use pytest fixtures in `conftest.py` for common setup
- Mock external API calls (Claude API, Bible API)
- Test data validation and error handling

**Frontend:**
- Uses Vitest with jsdom environment
- React Testing Library for component tests
- Co-located with components or in `__tests__` directories

## Environment Configuration

**Backend (.env):**
- `DATABASE_URL` - PostgreSQL connection string
- `ANTHROPIC_API_KEY` - Claude API key (required)
- `ENVIRONMENT` - development or production
- `DEBUG` - Enable debug mode

**Frontend:**
- `VITE_API_URL` - Backend API URL (for development)

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):
- Backend tests with pytest (Python 3.11+)
- Frontend lint with ESLint (using Bun)
- Docker build verification

All checks must pass before merging PRs.

## API Endpoints

**Bible:**
- `GET /api/passage` - Get specific verses
- `GET /api/chapter` - Get entire chapter

**Insights:**
- `POST /api/insights` - Generate AI insights (checks cache first)
- `GET /api/insights/{insight_id}` - Get saved insight
- `DELETE /api/insights/{insight_id}` - Delete insight

**Chat:**
- `POST /api/chat/message` - Send follow-up question on an insight
- `POST /api/chat/standalone` - Create new standalone chat
- `POST /api/chat/standalone/message` - Send message in standalone chat
- `GET /api/chat/history` - Get user's chat history

**User:**
- `GET /api/user/insights` - Get user's insight history
- `POST /api/user/translation` - Set preferred translation
- `POST /api/user/import` - Import user data
- `GET /api/user/export` - Export user data

## Common Patterns

**Caching Strategy:**
Insights are expensive (Claude API calls), so they're cached in the database. The `InsightService.generate_insights()` method first queries the database for existing insights before calling the AI client.

**User Management:**
All users are anonymous. The middleware sets a cookie with `anonymous_id`, and `UserService.get_or_create_user()` handles user creation/retrieval. This happens transparently via the `get_current_user` dependency.

**Text Selection:**
The `BibleReader` component handles text selection. When users highlight text, it captures the selection and associated verse reference, which is then sent to the insights endpoint.

**Error Handling:**
- API routes return appropriate HTTP status codes
- Frontend displays user-friendly error messages
- Backend validates input data early
- External API failures are caught and reported clearly
