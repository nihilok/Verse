#!/bin/bash
# Helper script to run database migration
# Usage: ./migrations/run_migration.sh

set -e  # Exit on error

echo "🔍 Checking for Docker Compose database..."

# Check if verse-db container is running
if docker ps --format '{{.Names}}' | grep -q "^verse-db$"; then
    echo "✅ Found running verse-db container"
    echo ""
    echo "📊 Running migration..."
    docker exec -i verse-db psql -U verse_user -d verse_db < "$(dirname "$0")/add_was_truncated_column.sql"
    echo ""
    echo "✅ Migration completed successfully!"

elif [ -n "$DATABASE_URL" ]; then
    echo "✅ Found DATABASE_URL environment variable"
    echo ""
    echo "📊 Running migration..."
    psql "$DATABASE_URL" -f "$(dirname "$0")/add_was_truncated_column.sql"
    echo ""
    echo "✅ Migration completed successfully!"

else
    echo "❌ Error: No database connection found"
    echo ""
    echo "Please either:"
    echo "  1. Start the Docker Compose database: docker compose up -d db"
    echo "  2. Set DATABASE_URL environment variable"
    echo "  3. Run the migration manually (see migrations/README.md)"
    exit 1
fi
