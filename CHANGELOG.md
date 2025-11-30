# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- RAG (Retrieval-Augmented Generation) now correctly excludes current chat messages from retrieval
- Added missing `rag_context` parameter to streaming chat response method
- Improved RAG context formatting in AI prompts for better context utilization
- Increased RAG context preview from 150 to 500 characters per message

### Added
- Debug API endpoint `/api/debug/rag-status` for diagnosing RAG configuration
- Python diagnostic script `backend/test_rag_debug.py` for checking RAG status
- Bash quick-check script `quick-rag-check.sh` for rapid diagnostics
- Comprehensive RAG debugging guide in `backend/RAG_DEBUGGING.md`
- Enhanced logging for RAG retrieval operations
- Helper method `_format_rag_context()` for consistent context formatting

### Changed
- RAG retrieval now excludes messages from current chat/insight to avoid redundancy
- RAG context prompts are now more explicit about instructing AI to use provided context
- Improved RAG-related log messages with query previews and message IDs

## [1.0.0] - 2024-10-24

### Added
- Initial release of Verse interactive Bible reader
- React TypeScript frontend with Vite
- Python FastAPI backend
- PostgreSQL database for caching
- Integration with bible.helloao.org API for Bible text
- Integration with Anthropic Claude for AI insights
- Text selection feature in Bible reader
- AI-powered insights with three categories:
  - Historical Context
  - Theological Significance
  - Practical Application
- Docker Compose setup for easy deployment
- Comprehensive documentation:
  - README with quick start guide
  - API documentation
  - Architecture overview
  - Development guide
  - Contributing guidelines
- Abstraction layers for Bible and AI clients to prevent vendor lock-in
- Caching of AI insights to reduce API calls
- Responsive design for mobile and desktop

### Features
- Search Bible passages by book, chapter, and verse
- View entire chapters
- Select any text to get AI insights
- Multiple Bible translation support (default: WEB)
- Save passages and insights to database
- Interactive API documentation via Swagger UI

### Technical Details
- Backend: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL
- Frontend: React 18, TypeScript, Vite, Axios
- Infrastructure: Docker, Docker Compose, Nginx (production)
- External APIs: HelloAO Bible API, Anthropic Claude API

[1.0.0]: https://github.com/nihilok/Verse/releases/tag/v1.0.0
