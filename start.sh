#!/bin/bash

# Verse Application Start Script

echo "🚀 Starting Verse - Interactive Bible Reader"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it and add your ANTHROPIC_API_KEY"
    echo ""
    read -p "Press enter to continue or Ctrl+C to exit and edit .env first..."
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    echo "ℹ️  Using 'docker compose' instead of 'docker-compose'"
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "🐳 Building and starting Docker containers..."
echo ""

# Build and start containers
$COMPOSE_CMD up --build -d

echo ""
echo "✅ Verse is starting up!"
echo ""
echo "📱 Access the application at:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 View logs with: $COMPOSE_CMD logs -f"
echo "🛑 Stop with: $COMPOSE_CMD down"
echo ""
