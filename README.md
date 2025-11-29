# Verse

An interactive Bible reader with AI-powered insights. Highlight any passage to explore its historical context, theological significance, and practical application.

## Features

- **Interactive Bible Reading** - Search and read any Bible passage in multiple translations
- **AI-Powered Insights** - Get instant contextual analysis including:
  - Historical Context - Background and setting of the passage
  - Theological Significance - Doctrinal themes and meaning
  - Practical Application - Modern-day relevance and application
- **Word Definitions** - Select any word to get biblical definitions and original language insights
- **Chat Interface** - Ask follow-up questions about passages and insights
- **Insight History** - Save and revisit your previous insights
- **Responsive Design** - Works seamlessly on desktop and mobile devices

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Get Running in 3 Steps

```bash
# 1. Clone the repository
git clone https://github.com/nihilok/Verse.git
cd Verse

# 2. Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Start the application
docker compose up --build
```

**Access Points:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

For detailed setup instructions, see the [Getting Started Guide](docs/getting-started.md).

## Documentation

Comprehensive documentation is available in the [`/docs`](docs/) directory:

### Getting Started
- **[Quick Start Guide](docs/getting-started.md)** - Get up and running in minutes
- **[User Guide](docs/guides/user-guide.md)** - Learn all features (coming soon)

### Development
- **[Development Setup](docs/guides/development.md)** - Set up your local environment
- **[Backend Development](docs/guides/backend-development.md)** - Working with FastAPI (coming soon)
- **[Frontend Development](docs/guides/frontend-development.md)** - Working with React (coming soon)
- **[Testing Guide](docs/guides/testing.md)** - Running and writing tests (coming soon)

### Reference
- **[API Reference](docs/reference/api.md)** - Complete API endpoint documentation
- **[Database Schema](docs/reference/database.md)** - Database models and relationships
- **[Configuration](docs/reference/configuration.md)** - Environment variables and settings

### Architecture
- **[Architecture Overview](docs/architecture/)** - High-level system design
- **[Security](docs/architecture/security.md)** - Security features and best practices

## Technology Stack

### Frontend
- React 18 with TypeScript
- Vite for fast development and building
- Bun as the package manager
- Axios for API communication
- Modern responsive CSS

### Backend
- Python 3.11+ with FastAPI
- PostgreSQL for data storage
- SQLAlchemy ORM
- Anthropic Claude AI for insights
- HelloAO Bible API for Bible text
- Rate limiting and security middleware

### Infrastructure
- Docker & Docker Compose
- Nginx (production)
- Hot-reloading in development

## Project Structure

```
Verse/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── clients/        # External API clients (abstracted)
│   │   ├── core/           # Configuration and middleware
│   │   ├── models/         # Database models
│   │   └── services/       # Business logic
│   └── tests/              # Backend tests
├── frontend/                # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   └── public/             # Static assets
├── docs/                    # Documentation
├── .github/workflows/       # CI/CD workflows
├── docker-compose.yml       # Docker configuration
└── README.md               # This file
```

## Key Features

### Abstraction Layer Architecture

The backend uses abstract base classes for external services, making it easy to switch providers:

```python
# Easy to swap Bible API providers
class BibleClient(ABC):
    @abstractmethod
    async def get_verse(...): pass

# Easy to swap AI providers
class AIClient(ABC):
    @abstractmethod
    async def generate_insights(...): pass
```

See [Architecture Documentation](docs/architecture/README.md) for more details.

### Intelligent Caching

- AI insights are cached in PostgreSQL to reduce API calls and costs
- Automatic deduplication based on passage text
- User-specific insight history

### Rate Limiting

- AI endpoints: 10 requests/minute
- Chat endpoints: 20 requests/minute
- Prevents abuse and manages API costs

### Anonymous User Sessions

- No authentication required
- Privacy-preserving user tracking
- All data is linked to anonymous user IDs
- Can export/import user data

## Development

### Backend (Python/FastAPI)

```bash
cd backend
uv sync                    # Install dependencies
uv sync --group dev        # Include test dependencies
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Run tests:**
```bash
uv run pytest              # Run all tests
uv run pytest --cov=app    # With coverage
```

### Frontend (TypeScript/React)

```bash
cd frontend
bun install               # Install dependencies (use Bun, not npm)
bun run dev              # Start dev server
bun run lint             # Check linting
bun test                 # Run tests
```

For detailed development instructions, see the [Development Guide](docs/guides/development.md).

## API Endpoints

### Bible
- `GET /api/passage` - Get specific verses
- `GET /api/chapter` - Get entire chapter

### AI Features
- `POST /api/insights` - Generate passage insights
- `POST /api/definitions` - Get word definitions
- `POST /api/chat/message` - Chat about an insight
- `POST /api/chat/standalone` - Start standalone chat

### User
- `GET /api/user/insights` - Get insight history
- `GET /api/user/definitions` - Get definition history
- `POST /api/user/export` - Export user data
- `POST /api/user/import` - Import user data

For complete API documentation, see the [API Reference](docs/reference/api.md).

## Contributing

Contributions are welcome! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest` for backend, `bun test` for frontend)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: Check the [docs](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/nihilok/Verse/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nihilok/Verse/discussions)

## Acknowledgments

- Bible text provided by [HelloAO Bible API](https://bible.helloao.org)
- AI insights powered by [Anthropic Claude](https://www.anthropic.com/)

---

**Made with ❤️ by the Verse contributors**
