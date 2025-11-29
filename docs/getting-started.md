# Getting Started with Verse

This guide will help you get Verse up and running on your local machine in minutes.

## Prerequisites

Before you begin, ensure you have:

- **Docker** and **Docker Compose** installed ([Get Docker](https://docs.docker.com/get-docker/))
- **Anthropic API Key** from [Anthropic Console](https://console.anthropic.com/)

That's it! Docker will handle all other dependencies.

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/nihilok/Verse.git
cd Verse
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```env
ANTHROPIC_API_KEY=your_actual_api_key_here
```

### 3. Start the Application

```bash
docker compose up --build
```

This command will:
- Build the frontend and backend containers
- Start a PostgreSQL database
- Create all necessary database tables
- Start the development servers

First build may take a few minutes. Subsequent starts will be much faster.

### 4. Access the Application

Once the containers are running, open your browser:

- **Frontend (Main App)**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Using Verse

### Reading a Passage

1. Enter a book name (e.g., "John", "Genesis", "Psalms")
2. Enter the chapter number
3. Optionally specify verse range
4. Click "Load Passage"

### Getting AI Insights

1. After loading a passage, highlight any text you want to explore
2. Click "Get Insights" or "Get Definition" from the selection menu
3. View the AI-generated insights in the side panel

**Insights include:**
- Historical Context - Background and setting
- Theological Significance - Doctrinal themes and meaning
- Practical Application - Modern-day relevance

### Chat Feature

After viewing insights, you can ask follow-up questions:
- Click "Ask a Question" in the insights panel
- Type your question and get AI responses
- Chat history is saved and linked to the insight

You can also start standalone chats from the chat history panel.

### Word Definitions

Select a single word to get:
- Biblical definition and meaning
- Usage in biblical context
- Original language (Hebrew/Greek) insights

## Stopping the Application

Press `Ctrl+C` in the terminal running Docker Compose, then:

```bash
docker compose down
```

To remove all data including the database:

```bash
docker compose down -v
```

## Viewing Logs

To see what's happening inside the containers:

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

## Next Steps

- **[User Guide](guides/user-guide.md)** - Learn all features in detail
- **[Development Setup](guides/development.md)** - Set up for contributing
- **[API Reference](reference/api.md)** - Explore the API endpoints
- **[Troubleshooting](guides/troubleshooting.md)** - Fix common issues

## Common Issues

### Port Already in Use

If you see errors about ports 5173, 8000, or 5432 already being in use:

```bash
# Find what's using the port
lsof -i :5173  # or :8000 or :5432

# Either stop the conflicting service or edit docker-compose.yml to use different ports
```

### API Key Error

If you see Claude API errors, verify:
1. Your `.env` file exists in the project root
2. The `ANTHROPIC_API_KEY` is set correctly
3. The API key is valid (test at console.anthropic.com)

### Database Connection Failed

Wait a few seconds for PostgreSQL to fully start, then:

```bash
docker compose restart backend
```

For more issues, see the [Troubleshooting Guide](guides/troubleshooting.md).
