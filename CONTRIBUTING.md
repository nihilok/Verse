# Contributing to Verse

Thank you for your interest in contributing to Verse! This guide will help you get started.

## Code of Conduct

Please be respectful and constructive in all interactions with the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Verse.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Commit your changes: `git commit -m "Add feature X"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions.

## Project Structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for the architecture overview.

## Testing

### Backend Tests

```bash
cd backend
uv sync --group dev  # Install dev dependencies including pytest
uv run pytest
# or with coverage
uv run pytest --cov=app
```

### Frontend Tests

```bash
cd frontend
bun test  # or npm test
```

## Code Style

### Python (Backend)

- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Keep functions focused and small

Example:
```python
async def get_passage(
    self,
    book: str,
    chapter: int,
    verse_start: int,
    verse_end: Optional[int] = None
) -> Optional[BiblePassage]:
    """
    Get a Bible passage.

    Args:
        book: Name of the Bible book
        chapter: Chapter number
        verse_start: Starting verse number
        verse_end: Ending verse number (optional)

    Returns:
        BiblePassage object or None if not found
    """
    # Implementation
```

### TypeScript (Frontend)

- Use TypeScript for all components
- Define interfaces for all data structures
- Use functional components with hooks
- Follow React best practices

Example:
```typescript
interface BibleReaderProps {
  passage: BiblePassage | null;
  onTextSelected: (text: string, reference: string) => void;
}

const BibleReader: React.FC<BibleReaderProps> = ({ passage, onTextSelected }) => {
  // Implementation
};
```

## Adding Features

### Adding a New Bible API Provider

1. Create a new client implementing `BibleClient`:
   ```python
   from app.clients.bible_client import BibleClient

   class NewBibleClient(BibleClient):
       async def get_verse(self, ...):
           # Implementation
   ```

2. Add tests for your client
3. Update service to use new client
4. Document in API.md

### Adding a New AI Provider

1. Create a new client implementing `AIClient`:
   ```python
   from app.clients.ai_client import AIClient

   class NewAIClient(AIClient):
       async def generate_insights(self, ...):
           # Implementation
   ```

2. Add tests for your client
3. Update service to use new client
4. Document in API.md

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md (if exists)
5. Request review from maintainers

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Write clear commit messages
- Include tests for new functionality
- Update documentation as needed
- Respond to review comments promptly

## Bug Reports

When reporting bugs, include:
- Clear description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, browser, etc.)
- Screenshots if applicable

## Feature Requests

When requesting features, include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if any)
- Any relevant examples

## Questions?

If you have questions, please:
- Check existing documentation
- Search existing issues
- Create a new issue with the "question" label

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
