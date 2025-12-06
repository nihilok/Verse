# Database Migrations with Alembic

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database schema management and migrations.

## Overview

Database migrations are automatically run on startup using a dedicated `migrate` service in Docker Compose. This ensures your database schema is always up-to-date before the application starts.

## Migration Flow

1. **Database starts** - PostgreSQL with pgvector extension support
2. **Migration service runs** - Waits for DB, then runs `alembic upgrade head`
3. **Backend starts** - Only after migrations complete successfully

## Creating New Migrations

### Auto-generated Migration (Recommended)

Auto-generation requires database access and compares current schema with models:

```bash
cd backend
# Start the database if not running
docker compose up -d db

# Generate migration (automatically formatted and linted with ruff)
DATABASE_URL=postgresql://verse_user:verse_password@localhost:5432/verse_db \
  uv run alembic revision --autogenerate -m "description"

# Review the generated file in alembic/versions/
# Test the migration
DATABASE_URL=postgresql://verse_user:verse_password@localhost:5432/verse_db \
  uv run alembic upgrade head
```

### Manual Migration (For Complex Changes)

```bash
cd backend
uv run alembic revision -m "description of changes"
# Edit the generated file in alembic/versions/
# Add your custom logic to upgrade() and downgrade()
uv run alembic upgrade head  # Test locally
```

⚠️ **Important**:
- Always review auto-generated migrations - Alembic may not detect all changes correctly
- Migrations are automatically formatted and linted with ruff via post-write hooks
- Replace `pgvector.sqlalchemy.vector.VECTOR(dim=1536)` with `Vector(1536)` if it appears

## Migration Best Practices

### DO:
- ✅ Review every migration before committing
- ✅ Test migrations on a local database first
- ✅ Use descriptive names: `add_user_preferences_table`
- ✅ Handle both `upgrade()` and `downgrade()` operations
- ✅ Use transactions (default behavior)
- ✅ Add data migrations when renaming/restructuring

### DON'T:
- ❌ Auto-generate migrations without review
- ❌ Modify existing migrations after they're merged
- ❌ Mix schema and data changes in one migration
- ❌ Forget to handle existing data when changing columns

## Common Operations

### Adding a New Table

```python
def upgrade() -> None:
    op.create_table(
        'new_table',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_new_table_name', 'new_table', ['name'])

def downgrade() -> None:
    op.drop_index('idx_new_table_name')
    op.drop_table('new_table')
```

### Adding a Column

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(255), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'email')
```

### Modifying a Column (with data migration)

```python
def upgrade() -> None:
    # 1. Add new column
    op.add_column('users', sa.Column('status_new', sa.String(50)))

    # 2. Migrate data
    op.execute("UPDATE users SET status_new = CAST(status_old AS VARCHAR)")

    # 3. Drop old column
    op.drop_column('users', 'status_old')

    # 4. Rename new column
    op.alter_column('users', 'status_new', new_column_name='status')

def downgrade() -> None:
    # Reverse the process
    op.alter_column('users', 'status', new_column_name='status_new')
    op.add_column('users', sa.Column('status_old', sa.Integer()))
    op.execute("UPDATE users SET status_old = CAST(status_new AS INTEGER)")
    op.drop_column('users', 'status_new')
```

### Using pgvector Types

```python
from pgvector.sqlalchemy import Vector

def upgrade() -> None:
    op.add_column('saved_insights',
        sa.Column('embedding', Vector(1536), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('saved_insights', 'embedding')
```

## Migration Commands

```bash
# Check current migration status
uv run alembic current

# View migration history
uv run alembic history

# Upgrade to latest
uv run alembic upgrade head

# Upgrade by 1 version
uv run alembic upgrade +1

# Downgrade by 1 version
uv run alembic downgrade -1

# Downgrade to specific version
uv run alembic downgrade <revision>

# Show SQL without executing
uv run alembic upgrade head --sql
```

## Docker Compose Integration

### Development

```bash
# Migrations run automatically on startup
docker compose up --build

# Run migrations manually if needed
docker compose run --rm migrate
```

### Production

```bash
# Same automatic behavior
docker compose -f docker-compose.prod.yml up --build

# Run migrations only (useful for testing)
docker compose -f docker-compose.prod.yml run --rm migrate
```

## Troubleshooting

### Migration Failed

```bash
# Check migration logs
docker logs verse-migrate

# Check current database version
docker exec verse-db psql -U verse_user -d verse_db -c "SELECT * FROM alembic_version;"

# Manually mark as complete (DANGEROUS - only if migration actually succeeded)
docker exec verse-db psql -U verse_user -d verse_db -c "UPDATE alembic_version SET version_num='<revision>';"
```

### Rollback After Failed Migration

```bash
# Connect to database
docker exec -it verse-db psql -U verse_user -d verse_db

# Check what was created
\dt

# Manually clean up if needed
DROP TABLE problematic_table;

# Update alembic version
UPDATE alembic_version SET version_num='<previous_revision>';
```

### Reset Database (Development Only)

```bash
# WARNING: This deletes all data!
docker compose down -v
docker compose up --build
```

## File Structure

```
backend/
├── alembic/
│   ├── versions/           # Migration files
│   │   └── 2122fc345830_initial_migration_with_pgvector.py
│   ├── env.py             # Alembic environment config
│   ├── script.py.mako     # Template for new migrations
│   └── README
├── alembic.ini            # Alembic configuration
├── migrate.py             # Migration runner script
└── Dockerfile.migrate     # Docker image for migrations
```

## Environment Variables

The migration script uses these environment variables:

- `DATABASE_URL` - PostgreSQL connection string (required)
- `ENVIRONMENT` - `development` or `production` (optional)

These are automatically set in docker-compose.yml.
