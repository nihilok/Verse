# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - System Prompt Enhancements
- **Verse App Context**: All AI prompts now include context about Verse being an interactive Bible reading app
- **Study Companion Role**: AI now understands its role as a thoughtful study companion rather than a lecturer
- **User Journey Awareness**: Prompts reflect that users are actively reading and highlighting passages
- **Adaptive Tone**: Instructions to meet users where they are—from first-time readers to seasoned students
- **Connection Building**: Encouragement to reference surrounding verses and related passages users might explore
- **Warm & Accessible**: Emphasis on being educational without being overly academic
- Updated prompts in: generate_insights(), generate_definition(), generate_chat_response(), generate_standalone_chat_response(), and all streaming variants

### Added - RAG Memory Enhancements
- **Enhanced RAG Context Format**: RAG context now includes conversation summaries, surrounding messages, and timestamps for richer contextual understanding
- **Conversation Summaries**: Auto-generated 1-2 sentence summaries using Claude Haiku for each relevant conversation
- **Surrounding Messages**: Each RAG match now includes 2 messages before and 2 after for better conversation flow
- **Temporal Context**: Full timestamps (YYYY-MM-DD HH:MM) on all messages and conversation dates in summaries
- **RagService**: New dedicated service (`app/services/rag_service.py`) for RAG operations, separating concerns from ChatService
- **Conversation Summary Caching**: New `conversation_summaries` database table with automatic cache invalidation based on message count
- **Enhanced Context Formatting**: Structured excerpts with clear delimiters (---excerpt--- / ---end excerpt---) and semantic search markers
- **Generic RAG Retrieval**: Unified method supporting both insight and standalone chats, eliminating code duplication
- Database migration: `add_conversation_summaries.sql` for summary caching infrastructure
- Comprehensive test suite: `tests/test_rag_service.py` with unit tests for RAG functionality
- Documentation: `docs/rag-implementation-summary.md` and `docs/rag-quick-reference.md`

### Changed - Code Quality Improvements
- **Eliminated ~200 lines of duplicated RAG code** by extracting unified methods into RagService
- **Created centralized prompts module** (`app/prompts/`) with composable prompt components, eliminating prompt duplication across 6 methods
- Refactored RAG retrieval to use consistent patterns across insight and standalone chats
- Updated all chat methods (send_message, send_standalone_message, streaming variants) to use enhanced RAG context
- All AI prompts now use prompt builder functions from `app.prompts` for consistency and maintainability
- Improved error handling with graceful fallbacks throughout RAG pipeline
- Removed obsolete `_format_rag_context()` method from ClaudeAIClient (now handled by RagService)

### Fixed
- RAG (Retrieval-Augmented Generation) now correctly excludes current chat messages from retrieval
- Added missing `rag_context` parameter to streaming chat response method
- Improved RAG context formatting in AI prompts for better context utilization
- Increased RAG context preview from 150 to 500 characters per message

### Added - Debugging Tools
- Debug API endpoint `/api/debug/rag-status` for diagnosing RAG configuration
- Python diagnostic script `backend/test_rag_debug.py` for checking RAG status
- Bash quick-check script `quick-rag-check.sh` for rapid diagnostics
- Comprehensive RAG debugging guide in `backend/RAG_DEBUGGING.md`
- Enhanced logging for RAG retrieval operations

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
