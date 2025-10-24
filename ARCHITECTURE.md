# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                            │
│                    http://localhost:5173                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTP/HTTPS
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      Frontend (React + TS)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │   Passage    │  │    Bible     │  │   Insights Panel   │   │
│  │    Search    │  │    Reader    │  │                    │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API Service Layer (Axios)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ REST API
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                   Backend (FastAPI + Python)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routes                            │  │
│  │   /api/passage  │  /api/chapter  │  /api/insights       │  │
│  └────────────┬──────────────┬──────────────┬───────────────┘  │
│               │              │              │                   │
│  ┌────────────▼──────────────▼──────────────▼───────────────┐  │
│  │                   Service Layer                          │  │
│  │  ┌──────────────────┐      ┌─────────────────────────┐  │  │
│  │  │  Bible Service   │      │   Insight Service       │  │  │
│  │  └────────┬─────────┘      └──────────┬──────────────┘  │  │
│  └───────────┼────────────────────────────┼─────────────────┘  │
│              │                            │                     │
│  ┌───────────▼────────────────────────────▼─────────────────┐  │
│  │              Abstraction Layer (Interfaces)              │  │
│  │  ┌──────────────────┐      ┌─────────────────────────┐  │  │
│  │  │  BibleClient     │      │      AIClient           │  │  │
│  │  │  (Abstract)      │      │      (Abstract)         │  │  │
│  │  └────────┬─────────┘      └──────────┬──────────────┘  │  │
│  └───────────┼────────────────────────────┼─────────────────┘  │
│              │                            │                     │
│  ┌───────────▼────────────┐   ┌──────────▼──────────────────┐ │
│  │  HelloAOBibleClient    │   │    ClaudeAIClient           │ │
│  │  (Implementation)      │   │    (Implementation)         │ │
│  └───────────┬────────────┘   └──────────┬──────────────────┘ │
└──────────────┼───────────────────────────┼─────────────────────┘
               │                           │
               │                           │
    ┌──────────▼──────────┐     ┌─────────▼──────────┐
    │  bible.helloao.org  │     │  Anthropic Claude  │
    │      Bible API      │     │       API          │
    └─────────────────────┘     └────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Database (PostgreSQL)                        │
│  ┌──────────────────┐          ┌────────────────────────────┐  │
│  │  saved_passages  │          │     saved_insights         │  │
│  └──────────────────┘          └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend Layer

**Technologies:** React 18, TypeScript, Vite, Axios

**Components:**
- `PassageSearch`: Search form for Bible passages
- `BibleReader`: Display Bible text with selection capability
- `InsightsPanel`: Display AI-generated insights

**Responsibilities:**
- User interface rendering
- Text selection handling
- API communication
- State management

### Backend Layer

**Technologies:** FastAPI, Python 3.11, SQLAlchemy

**API Routes:**
- Handle HTTP requests
- Request validation
- Response formatting

**Service Layer:**
- Business logic
- Orchestrate client operations
- Database operations

**Abstraction Layer:**
- Abstract base classes for clients
- Enables easy provider switching
- Prevents vendor lock-in

**Client Implementations:**
- Concrete implementations of abstract clients
- External API communication
- Error handling

### Database Layer

**Technology:** PostgreSQL 15

**Tables:**
- `saved_passages`: Stores Bible passages
- `saved_insights`: Caches AI-generated insights

### External Services

1. **HelloAO Bible API** (bible.helloao.org)
   - Provides Bible text in various translations
   - RESTful API
   - No authentication required

2. **Anthropic Claude API**
   - Generates AI insights
   - Requires API key
   - Uses Claude 3 Sonnet model

## Design Patterns

### 1. Abstraction Pattern

**Purpose:** Prevent vendor lock-in and enable easy provider switching

**Implementation:**
```python
# Abstract base class
class BibleClient(ABC):
    @abstractmethod
    async def get_verse(...): pass

# Concrete implementation
class HelloAOBibleClient(BibleClient):
    async def get_verse(...): 
        # HelloAO-specific implementation
        pass
```

**Benefits:**
- Easy to switch providers
- Testing with mock clients
- Clean separation of concerns

### 2. Service Layer Pattern

**Purpose:** Separate business logic from API routes

**Implementation:**
- Services orchestrate client operations
- Handle data transformation
- Manage database operations

**Benefits:**
- Reusable business logic
- Easier testing
- Clear separation of concerns

### 3. Repository Pattern (via SQLAlchemy)

**Purpose:** Abstract database operations

**Implementation:**
- SQLAlchemy ORM models
- Database session management
- Query abstraction

## Data Flow

### Reading a Bible Passage

1. User enters search criteria (book, chapter, verses)
2. Frontend sends GET request to `/api/passage`
3. Backend validates request parameters
4. Service calls Bible client
5. Bible client fetches data from HelloAO API
6. Response flows back through layers
7. Frontend displays passage
8. User can select text for insights

### Getting AI Insights

1. User selects text in Bible reader
2. Frontend sends POST request to `/api/insights`
3. Backend checks database for cached insights
4. If not cached, service calls AI client
5. AI client sends request to Claude API
6. Claude generates insights
7. Insights saved to database
8. Response flows back through layers
9. Frontend displays insights

## Scalability Considerations

### Horizontal Scaling
- Backend API is stateless
- Can run multiple instances behind load balancer
- Database connection pooling

### Caching
- AI insights cached in database
- Reduces API calls to Claude
- Improves response times

### Database Optimization
- Indexes on frequently queried fields
- Connection pooling
- Read replicas for scaling reads

## Security Considerations

### API Security
- CORS configuration for frontend
- Environment variables for secrets
- HTTPS in production

### Data Privacy
- No user authentication in v1
- No personal data storage
- API keys stored securely

### Rate Limiting
- Consider implementing for production
- Protect against abuse
- Respect external API limits

## Deployment Architecture

### Development
```
Docker Compose:
├── PostgreSQL container
├── Backend container (hot-reload)
└── Frontend container (Vite dev server)
```

### Production
```
Docker Compose:
├── PostgreSQL container
├── Backend container (Uvicorn)
└── Frontend container (Nginx)
```

## Future Enhancements

1. **User Authentication**
   - Save favorite passages
   - Personal notes
   - Usage history

2. **Additional Bible APIs**
   - Implement alternative providers
   - Fallback mechanisms
   - Translation management

3. **Enhanced AI Features**
   - Compare translations
   - Cross-reference passages
   - Topic exploration

4. **Performance Optimization**
   - Redis caching
   - CDN for static assets
   - Database query optimization

5. **Mobile App**
   - React Native version
   - Offline support
   - Push notifications
