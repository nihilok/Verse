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

### Code Quality Best Practices

#### Backend Python
- **Remove unused imports**: Always clean up unused imports to keep code maintainable
- **Use constants for magic numbers**: Extract repeated values (e.g., cookie max age, timeouts) to named constants at module level
- **Make configuration flexible**: Use environment variables for deployment-specific settings (e.g., `cookie_secure` flag for HTTPS)
- **Optimize database queries**: Use `delete().rowcount` directly instead of separate count queries before deletion
- **Extract helper methods**: Reduce code duplication by extracting common patterns into reusable helper methods
- **Validate input data**: Add comprehensive validation for external data (imports, API requests) with clear error messages
- **Handle exceptions gracefully**: Wrap risky operations in try-catch blocks with specific error messages for better debugging
- **Use atomic operations**: Ensure database operations are atomic with proper rollback on errors

#### Frontend TypeScript
- **Better JSON parsing**: Wrap `JSON.parse` in try-catch with specific error messages for invalid JSON
- **Use appropriate icons**: Match icons to context (CheckCircle for success, AlertCircle for errors)
- **Handle async operations properly**: Give users adequate time to read messages before auto-reloading (2500ms minimum)
- **Unused variables**: Remove or properly handle catch block variables (use `catch { }` if not needed)

#### Database Design
- **Many-to-many relationships**: Use proper linking tables with appropriate columns
- **Foreign key constraints**: Always specify `ondelete='CASCADE'` for proper cleanup
- **Index frequently queried fields**: Add indexes to foreign keys and commonly filtered columns
- **Avoid N+1 queries**: Consider batch operations for imports/exports with multiple items

#### Error Handling
- **Specific error messages**: Provide context-specific error messages rather than generic ones
- **Validate early**: Check data structure and required fields before processing
- **User-friendly messages**: Distinguish between different types of errors (invalid JSON vs. invalid data structure)

#### Testing
- **Update tests when changing export/import structure**: Ensure test data matches actual export format
- **Test data validation**: Add tests for invalid data scenarios
- **Clean up test fixtures**: Remove unused variables and imports in tests

## Tooling

- Use `bun` for JavaScript/TypeScript package management and scripts in the frontend. Prefer `bun` over `npm` or `yarn` for all relevant commands.
- Use `uv` for Python environment management and running commands. Prefer `uv run` over direct `python` or `pytest` commands in the backend.
- Backend uses `pyproject.toml` for dependency management (not `requirements.txt`). Use `uv add` to add dependencies, `uv sync` to install them.

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

- **Install dependencies**: `cd backend && uv sync`
- **Add new dependency**: `uv add <package-name>` (automatically updates `pyproject.toml`)
- **Add dev dependency**: `uv add --dev <package-name>`
- **Run development server**: `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **Run tests**: `uv run pytest`
- **Test with coverage**: `uv run pytest --cov=app`
- **CI environment**: Tests run with SQLite database using `DATABASE_URL=sqlite:///./test.db`
- **Note**: Backend uses `pyproject.toml` for dependency management, not `requirements.txt`

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
- **Dependencies**: Backend uses `backend/pyproject.toml`, frontend uses `frontend/package.json`
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
uv sync                                     # Install all dependencies from pyproject.toml
uv add <package>                            # Add a new dependency
uv add --dev <package>                      # Add a dev dependency
uv run uvicorn app.main:app --reload       # Start dev server
uv run pytest                               # Run tests
uv run pytest --cov=app                    # Run tests with coverage
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
