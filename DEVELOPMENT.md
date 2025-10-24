# Development Guide

## Setting Up Development Environment

### Backend Development

1. Create a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

1. Install dependencies:
```bash
cd frontend
bun install  # or npm install
```

2. Run the development server:
```bash
bun run dev  # or npm run dev
```

## Testing the APIs

### Bible API Testing

Test getting a passage:
```bash
curl "http://localhost:8000/api/passage?book=John&chapter=3&verse_start=16"
```

Test getting a chapter:
```bash
curl "http://localhost:8000/api/chapter?book=John&chapter=1"
```

### Insights API Testing

Test generating insights:
```bash
curl -X POST http://localhost:8000/api/insights \
  -H "Content-Type: application/json" \
  -d '{
    "passage_text": "For God so loved the world...",
    "passage_reference": "John 3:16",
    "save": true
  }'
```

## Code Structure

### Backend Architecture

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   └── routes.py     # Main API routes
│   ├── clients/          # External service clients
│   │   ├── bible_client.py      # Abstract Bible client
│   │   ├── helloao_client.py    # HelloAO implementation
│   │   ├── ai_client.py         # Abstract AI client
│   │   └── claude_client.py     # Claude implementation
│   ├── core/             # Core configuration
│   │   ├── config.py     # Application settings
│   │   └── database.py   # Database configuration
│   ├── models/           # Database models
│   │   └── models.py     # SQLAlchemy models
│   ├── services/         # Business logic
│   │   ├── bible_service.py    # Bible operations
│   │   └── insight_service.py  # Insight operations
│   └── main.py          # FastAPI application
```

### Frontend Architecture

```
frontend/
├── src/
│   ├── components/       # React components
│   │   ├── PassageSearch.tsx    # Search form
│   │   ├── BibleReader.tsx      # Bible text display
│   │   └── InsightsPanel.tsx    # Insights display
│   ├── services/         # API services
│   │   └── api.ts        # API client
│   ├── types/            # TypeScript types
│   │   └── index.ts      # Type definitions
│   ├── App.tsx           # Main application
│   └── main.tsx          # Entry point
```

## Adding New Features

### Adding a New Bible API Provider

1. Create a new client in `backend/app/clients/`:
```python
from app.clients.bible_client import BibleClient, BibleVerse, BiblePassage

class NewBibleClient(BibleClient):
    async def get_verse(self, book, chapter, verse, translation):
        # Implementation
        pass
```

2. Update `bible_service.py` to use your new client:
```python
from app.clients.new_bible_client import NewBibleClient

class BibleService:
    def __init__(self):
        self.client = NewBibleClient()
```

### Adding a New AI Provider

1. Create a new client in `backend/app/clients/`:
```python
from app.clients.ai_client import AIClient, InsightRequest, InsightResponse

class NewAIClient(AIClient):
    async def generate_insights(self, request):
        # Implementation
        pass
```

2. Update `insight_service.py` to use your new client:
```python
from app.clients.new_ai_client import NewAIClient

class InsightService:
    def __init__(self):
        self.client = NewAIClient()
```

## Database Migrations

If you modify the database models, you can use Alembic for migrations:

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

## Environment Variables

### Backend Variables

- `DATABASE_URL`: PostgreSQL connection string
- `ANTHROPIC_API_KEY`: Claude API key
- `ENVIRONMENT`: development or production
- `DEBUG`: Enable debug mode

### Frontend Variables

- `VITE_API_URL`: Backend API URL (for development)

## Common Issues

### CORS Errors

If you encounter CORS errors, ensure the backend CORS settings in `app/core/config.py` include your frontend URL.

### Database Connection Issues

Ensure PostgreSQL is running and accessible:
```bash
docker compose logs db
```

### API Key Issues

Verify your API keys are correctly set in the `.env` file.
