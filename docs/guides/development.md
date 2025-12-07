# Development Setup

This guide will help you set up Verse for local development.

## Prerequisites

- **Python 3.11+** (for backend)
- **uv** (Python package manager) - [Install uv](https://github.com/astral-sh/uv)
- **Bun** (for frontend) - [Install Bun](https://bun.sh/)
- **PostgreSQL** (or use Docker)
- **Anthropic API Key** from [console.anthropic.com](https://console.anthropic.com/)

## Quick Start (Docker)

For the fastest setup, use Docker:

```bash
# Clone and configure
git clone https://github.com/nihilok/Verse.git
cd Verse
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Start all services
docker compose up --build
```

See [Getting Started](../getting-started.md) for more details.

## Local Development (Without Docker)

For a more traditional development setup:

### 1. Clone the Repository

```bash
git clone https://github.com/nihilok/Verse.git
cd Verse
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
ANTHROPIC_API_KEY=your_key_here
DATABASE_URL=postgresql://verse_user:verse_password@localhost:5432/verse_db
ENVIRONMENT=development
DEBUG=true
```

### 3. Set Up PostgreSQL

**Option A: Using Docker**

```bash
docker run -d \
  --name verse-postgres \
  -e POSTGRES_USER=verse_user \
  -e POSTGRES_PASSWORD=verse_password \
  -e POSTGRES_DB=verse_db \
  -p 5432:5432 \
  postgres:15
```

**Option B: Local PostgreSQL**

```bash
# Install PostgreSQL (macOS example)
brew install postgresql@15
brew services start postgresql@15

# Create database and user
createuser -P verse_user  # Enter password when prompted
createdb -O verse_user verse_db
```

### 4. Set Up Backend

```bash
cd backend

# Create virtual environment and install dependencies
uv sync

# Install development dependencies (includes pytest)
uv sync --group dev

# Run the server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at http://localhost:8000

**Alternative:** Activate the virtual environment:

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Set Up Frontend

In a new terminal:

```bash
cd frontend

# Install dependencies
bun install

# Start development server
bun run dev
```

The frontend will be available at http://localhost:5173

## Development Workflow

### Running Tests

**Backend:**

```bash
cd backend

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_api.py

# Run with verbose output
uv run pytest -v
```

**Frontend:**

```bash
cd frontend

# Run tests
bun run test

# Run tests once (CI mode)
bun run test:unit

# Run in watch mode
bun run test
```

### Code Quality

**Backend:**

```bash
cd backend

# Type checking (if using mypy)
mypy app/

# Linting
ruff check app/

# Formatting
black app/
```

**Frontend:**

```bash
cd frontend

# Type checking
tsc --noEmit

# Linting
bun run lint

# Fix linting issues
bun run lint:fix
```

### Database Migrations

When you modify database models:

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

## Project Structure

```
Verse/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   └── routes.py
│   │   ├── clients/           # External API clients
│   │   │   ├── bible_client.py      (abstract)
│   │   │   ├── helloao_client.py    (implementation)
│   │   │   ├── ai_client.py         (abstract)
│   │   │   └── claude_client.py     (implementation)
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py            (settings)
│   │   │   ├── database.py          (DB setup)
│   │   │   ├── middleware.py        (anonymous users)
│   │   │   ├── rate_limiter.py      (rate limiting)
│   │   │   └── security_headers.py  (security)
│   │   ├── models/            # Database models
│   │   │   └── models.py
│   │   ├── services/          # Business logic
│   │   │   ├── bible_service.py
│   │   │   ├── insight_service.py
│   │   │   ├── definition_service.py
│   │   │   ├── chat_service.py
│   │   │   └── user_service.py
│   │   └── main.py           # FastAPI application
│   ├── tests/                 # Backend tests
│   ├── alembic/              # Database migrations
│   ├── Dockerfile
│   ├── pyproject.toml        # Python dependencies (uv)
│   └── uv.lock
├── frontend/                   # React TypeScript frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── BibleReader.tsx
│   │   │   ├── PassageSearch.tsx
│   │   │   ├── InsightsPanel.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── InsightsHistory.tsx
│   │   │   └── ui/           # UI components
│   │   ├── services/          # API client
│   │   │   └── api.ts
│   │   ├── types/             # TypeScript types
│   │   │   └── index.ts
│   │   ├── App.tsx           # Main application
│   │   └── main.tsx          # Entry point
│   ├── public/               # Static assets
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── package.json
│   └── vite.config.ts
├── docs/                      # Documentation
├── .github/workflows/         # CI/CD
├── docker-compose.yml
├── .env.example
└── README.md
```

## Common Development Tasks

### Adding a New API Endpoint

1. **Define route in `backend/app/api/routes.py`:**

```python
@router.get("/api/new-endpoint")
async def new_endpoint(db: Session = Depends(get_db)):
    # Implementation
    return {"result": "data"}
```

2. **Add business logic in service:**

```python
# backend/app/services/new_service.py
class NewService:
    async def process(self):
        # Business logic
        pass
```

3. **Add frontend API call:**

```typescript
// frontend/src/services/api.ts
export const callNewEndpoint = async () => {
  const response = await api.get('/api/new-endpoint');
  return response.data;
};
```

4. **Add tests:**

```python
# backend/tests/test_new_endpoint.py
def test_new_endpoint(client):
    response = client.get("/api/new-endpoint")
    assert response.status_code == 200
```

### Adding a New React Component

1. **Create component:**

```typescript
// frontend/src/components/NewComponent.tsx
interface NewComponentProps {
  data: string;
}

export const NewComponent: React.FC<NewComponentProps> = ({ data }) => {
  return <div>{data}</div>;
};
```

2. **Add to parent component:**

```typescript
import { NewComponent } from './components/NewComponent';

<NewComponent data={myData} />
```

3. **Add types if needed:**

```typescript
// frontend/src/types/index.ts
export interface NewData {
  field: string;
}
```

### Debugging

**Backend:**

```python
# Add logging
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

**Frontend:**

```typescript
// Use console methods
console.log('Data:', data);
console.error('Error:', error);

// React Developer Tools browser extension is helpful
```

### Viewing Logs

**Docker:**

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend

# Last 100 lines
docker compose logs --tail=100 backend
```

**Local:**

Backend logs appear in the terminal running uvicorn.
Frontend logs appear in browser console.

## Environment-Specific Configuration

### Development

```env
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://verse_user:verse_password@localhost:5432/verse_db
ANTHROPIC_API_KEY=your_key
```

### Testing

```env
ENVIRONMENT=test
DEBUG=false
DATABASE_URL=sqlite:///./test.db
ANTHROPIC_API_KEY=test_key
```

### Production

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/verse_db
ANTHROPIC_API_KEY=your_prod_key
```

## Next Steps

- [Architecture Documentation](../architecture/) - System design and patterns
- [API Reference](../reference/api.md) - Complete API documentation
- [Database Schema](../reference/database.md) - Database structure
- [Contributing Guidelines](../../CONTRIBUTING.md) - Contribution workflow

## Getting Help

- Check the [Troubleshooting Guide](troubleshooting.md)
- Review existing [GitHub Issues](https://github.com/nihilok/Verse/issues)
- Read the [Architecture Documentation](../architecture/)
