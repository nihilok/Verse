# Database Migrations

This directory contains manual SQL migration scripts for updating the database schema.

## When Do You Need to Run Migrations?

### Development (SQLite)
**You probably DON'T need this.** The app uses `Base.metadata.create_all()` which will automatically create missing columns when you restart the backend.

### Production (PostgreSQL with existing data)
**You MUST run this migration** before deploying the new code if:
- Your database already has data in `chat_messages` or `standalone_chat_messages` tables
- You're running in production with PostgreSQL

## How to Run the Migration

### Option 1: Using psql (Recommended for Production)

```bash
# Connect to your PostgreSQL database
psql $DATABASE_URL

# Run the migration
\i migrations/add_was_truncated_column.sql

# Exit
\q
```

### Option 2: Using psql with file directly

```bash
# Run migration from command line
psql $DATABASE_URL -f backend/migrations/add_was_truncated_column.sql
```

### Option 3: Using Docker (if database is in Docker)

```bash
# Copy migration into the container
docker cp backend/migrations/add_was_truncated_column.sql <postgres-container-name>:/tmp/

# Execute it
docker exec -it <postgres-container-name> psql -U <username> -d <database> -f /tmp/add_was_truncated_column.sql
```

## What This Migration Does

Adds the `was_truncated` column to:
- `chat_messages` table
- `standalone_chat_messages` table

This column tracks whether an AI response was cut off due to token limits, enabling the "continue response" feature.

## Rollback (if needed)

If you need to remove these columns:

```sql
ALTER TABLE chat_messages DROP COLUMN IF EXISTS was_truncated;
ALTER TABLE standalone_chat_messages DROP COLUMN IF EXISTS was_truncated;
```

## RAG (Retrieval-Augmented Generation) Setup

To enable RAG functionality for chat messages, run these migrations in order:

### 1. Enable pgvector Extension

This migration enables the pgvector extension in PostgreSQL, which is required for vector similarity search.

```bash
cd backend
uv run python -m migrations.enable_vector
```

**Note:** This requires your database to support pgvector. If you're using Docker Compose, make sure you're using the `pgvector/pgvector:pg16` image (already configured in docker-compose.yml).

### 2. Update Database Schema

After enabling pgvector, restart your backend to create the new columns and indexes:

```bash
# If using Docker Compose:
docker compose restart backend

# Or if running locally:
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will automatically create the `embedding` columns and HNSW indexes via SQLAlchemy's `create_all()`.

### 3. Backfill Existing Messages (Optional)

If you have existing chat messages, backfill embeddings for them:

```bash
cd backend
uv run python -m migrations.backfill_embeddings
```

This script:
- Processes all existing messages without embeddings
- Generates embeddings using OpenAI's text-embedding-3-small model
- Processes messages in batches of 100 to respect API rate limits
- Can be safely interrupted and rerun

**Requirements:**
- `OPENAI_API_KEY` must be set in your .env file

**Cost Estimate:**
- OpenAI text-embedding-3-small: ~$0.00002 per 1,000 tokens
- 1,000 messages ≈ $0.02-0.04

### RAG Migration Order

1. `enable_vector.py` - Enable the extension
2. Restart backend - Create schema changes
3. `backfill_embeddings.py` - Populate existing data (optional)

## Future Migrations

For future schema changes, consider setting up Alembic for automatic migration management:

```bash
# Initialize Alembic (one-time setup)
cd backend
uv pip install alembic
alembic init alembic

# Then for each change:
alembic revision --autogenerate -m "description of change"
alembic upgrade head
```
