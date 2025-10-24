# Project Summary

## Verse - Interactive Bible Reader with AI-Powered Insights

### Overview
Verse is a modern web application that provides an interactive Bible reading experience enhanced with AI-powered insights. Users can search for any Bible passage, read it in a clean interface, and highlight text to receive contextual insights about the passage's historical context, theological significance, and practical application.

### Key Features
1. **Bible Text Retrieval**: Integration with bible.helloao.org API for accessing Bible text in multiple translations
2. **Text Selection**: Click-and-drag to select any portion of text
3. **AI Insights**: Get instant AI-generated insights using Claude AI
4. **Caching**: Insights are cached in PostgreSQL to reduce API calls and improve performance
5. **Responsive Design**: Works seamlessly on desktop and mobile devices
6. **Containerized**: Full Docker Compose setup for easy deployment

### Technology Stack

#### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite (with Bun support)
- **HTTP Client**: Axios
- **Styling**: Custom CSS with responsive design
- **Container**: Nginx (production), Vite dev server (development)

#### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy
- **API Integrations**:
  - HelloAO Bible API (bible.helloao.org)
  - Anthropic Claude AI API
- **Container**: Python with Uvicorn

#### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL with persistent volumes
- **Networking**: Internal Docker network with exposed ports

### Architecture Highlights

#### Abstraction Layers
The application uses abstract base classes for both Bible and AI clients, enabling:
- Easy swapping of providers
- Prevention of vendor lock-in
- Simplified testing with mock implementations
- Clear separation of concerns

#### Service Layer
Business logic is separated into service classes:
- `BibleService`: Handles Bible text retrieval and caching
- `InsightService`: Manages AI insight generation and storage

#### Database Models
- `SavedPassage`: Stores Bible passages for quick retrieval
- `SavedInsight`: Caches AI-generated insights

### File Structure

```
Verse/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── clients/           # External API clients (abstracted)
│   │   ├── core/              # Configuration and database
│   │   ├── models/            # Database models
│   │   └── services/          # Business logic
│   ├── tests/                 # Backend tests
│   ├── Dockerfile             # Backend container
│   └── requirements.txt       # Python dependencies
├── frontend/                   # React TypeScript frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API client
│   │   └── types/             # TypeScript types
│   ├── Dockerfile             # Production container
│   ├── Dockerfile.dev         # Development container
│   └── package.json           # Node dependencies
├── .github/workflows/         # CI/CD workflows
├── docker-compose.yml         # Development setup
├── docker-compose.prod.yml    # Production setup
├── start.sh                   # Helper script
└── Documentation files        # README, API, ARCHITECTURE, etc.
```

### API Endpoints

1. **GET /api/passage** - Retrieve a Bible passage
   - Parameters: book, chapter, verse_start, verse_end (optional), translation
   
2. **GET /api/chapter** - Retrieve an entire chapter
   - Parameters: book, chapter, translation

3. **POST /api/insights** - Generate AI insights
   - Body: passage_text, passage_reference, save (optional)

### Setup & Deployment

#### Quick Start
```bash
# Clone repository
git clone https://github.com/nihilok/Verse.git
cd Verse

# Configure environment
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Start application
./start.sh
# Or: docker compose up --build
```

#### Access Points
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Testing

#### Backend Tests
```bash
cd backend
pip install -r requirements-test.txt
pytest
```

Tests include:
- API endpoint tests
- Model validation tests
- Client abstraction tests

### Documentation

The project includes comprehensive documentation:
- **README.md**: Main documentation with setup instructions
- **API.md**: Detailed API endpoint documentation
- **ARCHITECTURE.md**: System architecture and design patterns
- **DEVELOPMENT.md**: Development environment setup guide
- **CONTRIBUTING.md**: Contribution guidelines
- **QUICKSTART.md**: Quick reference for common tasks
- **CHANGELOG.md**: Version history

### Security & Best Practices

1. **Environment Variables**: Sensitive data stored in .env files
2. **CORS Configuration**: Proper CORS setup for API security
3. **API Key Management**: Keys stored securely, not in code
4. **Input Validation**: Pydantic models for request validation
5. **Error Handling**: Comprehensive error handling throughout

### Extensibility

The architecture is designed for easy extension:

#### Adding New Bible API
1. Implement `BibleClient` abstract class
2. Update service to use new client
3. No frontend changes needed

#### Adding New AI Provider
1. Implement `AIClient` abstract class
2. Update service to use new client
3. No frontend changes needed

### Performance Optimizations

1. **Database Caching**: AI insights cached to reduce API calls
2. **Connection Pooling**: Efficient database connections
3. **Async Operations**: Asynchronous API calls for better performance
4. **Docker Optimization**: Multi-stage builds for smaller images

### Future Enhancements

Potential areas for expansion:
1. User authentication and personal libraries
2. Multiple AI provider support with fallback
3. Additional Bible translations
4. Cross-reference navigation
5. Social features (sharing, discussions)
6. Mobile app (React Native)
7. Offline support with service workers
8. Audio Bible integration

### Dependencies

#### Backend Core
- fastapi: Web framework
- sqlalchemy: ORM
- pydantic: Data validation
- anthropic: Claude AI client
- httpx: HTTP client
- psycopg2: PostgreSQL driver

#### Frontend Core
- react: UI framework
- typescript: Type safety
- axios: HTTP client
- vite: Build tool

### License
MIT License - See LICENSE file for details

### Contributing
See CONTRIBUTING.md for guidelines on contributing to the project.

### Support
For issues, questions, or contributions:
1. Check existing documentation
2. Search existing issues
3. Create a new issue with details

---

**Version**: 1.0.0
**Author**: Verse Contributors
**Repository**: https://github.com/nihilok/Verse
