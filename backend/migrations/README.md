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
