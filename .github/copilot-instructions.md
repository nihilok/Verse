# GitHub Copilot Instructions for Verse

## Project Overview

Verse is an interactive Bible reader with AI-powered insights. Users can highlight any passage to explore its historical context, theological significance, and practical application.

## Project Goals

- Create an intuitive and accessible Bible reading experience
- Integrate AI capabilities to provide meaningful insights on biblical passages
- Focus on user experience and ease of use
- Maintain respectful and thoughtful handling of religious content

## Coding Standards

### General Guidelines
- Write clear, maintainable, and well-documented code
- Follow language-specific best practices and conventions
- Use descriptive variable and function names
- Keep functions focused and single-purpose
- Comment complex logic and algorithms

### Code Style
- Use consistent indentation (2 or 4 spaces depending on language convention)
- Follow the existing code style in the repository
- Use meaningful commit messages that explain the "why" behind changes
- Use British English spelling conventions where applicable

## Security Guidelines

- Never commit API keys, secrets, or credentials to the repository
- Use environment variables for sensitive configuration
- Validate and sanitise all user inputs
- Follow security best practices for authentication and authorisation
- Be mindful of rate limits when integrating with external APIs

## Testing Requirements

- Write tests for new features and bug fixes when test infrastructure exists
- Ensure changes don't break existing functionality
- Test edge cases and error handling
- Consider accessibility in all user-facing features

## Documentation

- Update documentation when adding or modifying features
- Document API endpoints and data structures
- Include usage examples for complex features
- Keep README.md up to date with setup and usage instructions
- Use British English spelling conventions

## AI Integration Guidelines

- Use AI responsibly and transparently
- Ensure AI-generated content is accurate and appropriate
- Consider context and cultural sensitivity when providing biblical insights
- Provide citations and sources for AI-generated information when possible

## Accessibility

- Follow WCAG guidelines for web accessibility
- Ensure the application is usable with keyboard navigation
- Use semantic HTML and ARIA attributes appropriately
- Support screen readers and assistive technologies
- Consider users with different reading abilities and preferences

## Best Practices

- Prioritise user privacy and data security
- Optimise for performance and loading times
- Support multiple devices and screen sises
- Handle errors gracefully with helpful error messages
- Consider internationalisation and localisation needs

## Tooling

- Use `bun` for JavaScript/TypeScript package management and scripts in the frontend. Prefer `bun` over `npm` or `yarn` for all relevant commands.
- Use `uv` for Python environment management where possible.

## Development Workflow

### Initial Setup

1. Clone the repository and navigate to the project directory
2. Copy `.env.example` to `.env` and configure environment variables (especially `ANTHROPIC_API_KEY`)
3. Use Docker Compose for full-stack development: `docker compose up --build`

### Frontend Development

- **Install dependencies**: `cd frontend && bun install`
- **Run development server**: `bun run dev` (starts on port 5173)
- **Run linter**: `bun run lint`
- **Fix linting issues**: `bun run lint:fix`
- **Run tests**: `bun test` or `bun run test:unit`
- **Build for production**: `bun run build`
- **Type checking**: `tsc --noEmit`

### Backend Development

- **Install dependencies**: `cd backend && pip install -r requirements.txt`
- **Install test dependencies**: `pip install -r requirements-test.txt`
- **Run development server**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Run tests**: `pytest`
- **Test with coverage**: `pytest --cov=app`
- **CI environment**: Tests run with SQLite database using `DATABASE_URL=sqlite:///./test.db`

### Docker Development

- **Build and start all services**: `docker compose up --build`
- **Stop services**: `docker compose down`
- **View logs**: `docker compose logs [service_name]`
- **Production build**: Uses `docker-compose.prod.yml`

## Project Architecture

The application follows a modular, layered architecture:

### Backend Structure

- **API Layer** (`app/api/`): FastAPI routes and endpoints
- **Service Layer** (`app/services/`): Business logic for Bible and insights operations
- **Client Layer** (`app/clients/`): Abstracted interfaces for external APIs (Bible API, AI providers)
- **Models** (`app/models/`): SQLAlchemy database models
- **Core** (`app/core/`): Configuration, database setup, and shared utilities

### Frontend Structure

- **Components** (`src/components/`): Reusable React components
- **Services** (`src/services/`): API client and service layer
- **Types** (`src/types/`): TypeScript type definitions
- **Main Application**: `App.tsx` and `main.tsx`

### Key Design Patterns

- **Abstraction**: Bible and AI clients use abstract base classes to prevent vendor lock-in
- **Service Layer**: Business logic is separated from API endpoints
- **Type Safety**: TypeScript in frontend, type hints in backend
- **Dependency Injection**: Services receive client instances
- **Environment Configuration**: All secrets and configuration via environment variables

## File Organisation

- **Documentation**: See `README.md`, `DEVELOPMENT.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`, and `API.md`
- **Configuration**: Environment variables in `.env` (not committed), example in `.env.example`
- **Tests**: Backend tests in `backend/tests/`, frontend tests co-located with components
- **Docker**: `Dockerfile` in each service directory, `docker-compose.yml` at root

## Working with Tests

### Backend Testing

- Tests use `pytest` with async support (`pytest-asyncio`)
- Mock external API calls in tests
- Use test fixtures for common setup
- Tests are located in `backend/tests/`
- Configuration in `backend/pytest.ini`

### Frontend Testing

- Tests use Vitest with jsdom environment
- Use React Testing Library for component tests
- Tests should be co-located with components or in `__tests__` directories
- Run with `bun test` or `bun run test:unit`

## Common Commands Reference

### Frontend
```bash
cd frontend
bun install           # Install dependencies
bun run dev          # Start dev server
bun run lint         # Check linting
bun run lint:fix     # Fix linting issues
bun test             # Run tests
bun run build        # Build for production
```

### Backend
```bash
cd backend
pip install -r requirements.txt          # Install dependencies
pip install -r requirements-test.txt     # Install test dependencies
uvicorn app.main:app --reload           # Start dev server
pytest                                   # Run tests
pytest --cov=app                        # Run tests with coverage
```

### Docker
```bash
docker compose up --build    # Build and start all services
docker compose down          # Stop all services
docker compose logs -f       # Follow logs from all services
```

## CI/CD

The project uses GitHub Actions for continuous integration (see `.github/workflows/ci.yml`):

- **Backend Tests**: Runs `pytest` with Python 3.11
- **Frontend Lint**: Runs ESLint using Bun
- **Docker Build**: Verifies Docker images build successfully

All CI jobs must pass before merging pull requests.
