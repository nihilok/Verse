# Verse

📖 An interactive Bible reader with AI-powered insights. Highlight any passage to explore its historical context, theological significance, and practical application.

## Features

- **Interactive Bible Reading**: Search and read any Bible passage
- **Text Selection**: Highlight any text in the Bible reader
- **AI-Powered Insights**: Get instant insights on selected passages including:
  - Historical Context
  - Theological Significance
  - Practical Application
- **Multiple Translations**: Support for various Bible translations (default: WEB)
- **Caching**: Insights are cached in the database to improve performance
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

### Frontend
- React 18 with TypeScript
- Vite for fast development and building
- Bun as the package manager
- Axios for API calls
- Modern CSS with responsive design

### Backend
- Python 3.11
- FastAPI for REST API
- PostgreSQL for data storage
- SQLAlchemy ORM
- Anthropic Claude AI for insights
- HelloAO Bible API for Bible text

### Infrastructure
- Docker & Docker Compose
- Nginx (production)
- Hot-reloading in development

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **Abstraction Layers**: Bible API and AI clients are abstracted to prevent vendor lock-in
- **Service Layer**: Business logic is separated from API endpoints
- **Database Models**: SQLAlchemy models for saved passages and insights
- **RESTful API**: Clean API design with proper HTTP methods

## Prerequisites

- Docker and Docker Compose
- Anthropic API key (for Claude AI)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/nihilok/Verse.git
cd Verse
```

### 2. Configure Environment Variables

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

You can get an API key from [Anthropic Console](https://console.anthropic.com/).

### 3. Start the Application

Run the entire application stack with Docker Compose:

```bash
docker compose up --build
```

This will:
- Start a PostgreSQL database
- Start the FastAPI backend on port 8000
- Start the React frontend on port 5173
- Automatically create database tables

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Usage

1. **Search for a Passage**:
   - Enter a book name (e.g., "John", "Genesis", "Romans")
   - Enter chapter and verse numbers
   - Click "Load Passage"

2. **Get AI Insights**:
   - Read the loaded passage
   - Highlight any text you want insights on
   - Click "Get AI Insights on Selected Text"
   - View the generated insights in the right panel

## API Endpoints

### Bible Endpoints

- `GET /api/passage` - Get a specific Bible passage
  - Parameters: book, chapter, verse_start, verse_end (optional), translation (optional)
- `GET /api/chapter` - Get an entire chapter
  - Parameters: book, chapter, translation (optional)

### Insights Endpoint

- `POST /api/insights` - Generate AI insights for a passage
  - Body: `{ "passage_text": "...", "passage_reference": "...", "save": true }`

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
bun install
bun run dev
```

## Project Structure

```
Verse/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── clients/       # Abstracted API clients
│   │   ├── core/          # Core configuration
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   └── main.py        # FastAPI application
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API service layer
│   │   ├── types/         # TypeScript types
│   │   ├── App.tsx        # Main application
│   │   └── main.tsx       # Entry point
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Extensibility

The application is designed to be easily extensible:

### Adding a New Bible API

1. Create a new client in `backend/app/clients/` that implements `BibleClient`
2. Update the service to use your new client

### Adding a New AI Provider

1. Create a new client in `backend/app/clients/` that implements `AIClient`
2. Update the service to use your new client

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
