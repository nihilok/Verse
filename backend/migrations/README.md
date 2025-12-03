# Database Migrations

This directory contains SQL migration files for the Verse application.

## Applying Migrations

### Option 1: Using psql (Recommended for Development)

```bash
# Connect to your database and run the migration
psql -U your_username -d your_database -f migrations/add_device_linking.sql
```

### Option 2: Using Docker

If you're running the database in Docker:

```bash
# Copy migration into the container
docker cp migrations/add_device_linking.sql verse-db:/tmp/

# Execute the migration
docker exec -i verse-db psql -U verse_user -d verse_db -f /tmp/add_device_linking.sql
```

### Option 3: Using Environment Variable

If you have `DATABASE_URL` set:

```bash
psql $DATABASE_URL -f migrations/add_device_linking.sql
```

## Migration: add_device_linking.sql

**Description**: Adds support for device linking functionality

**Changes**:
- Adds `device_count` column to `users` table
- Creates `user_devices` table to track linked devices
- Creates `device_link_codes` table to manage linking codes
- Adds appropriate indexes for performance

**Rollback**: To rollback this migration, see the ROLLBACK section at the bottom of the migration file.

## Verifying Migration

After applying the migration, verify the tables were created:

```sql
-- Check if tables exist
\dt user_devices
\dt device_link_codes

-- Check if device_count column was added
\d users

-- Check indexes
\di idx_user_devices_*
\di idx_device_link_codes_*
```

## Production Deployment

For production deployments, consider:

1. **Backup First**: Always backup your database before running migrations
2. **Test in Staging**: Run the migration in a staging environment first
3. **Downtime**: This migration can be run without downtime as it only adds new tables/columns
4. **Monitoring**: Monitor database performance after applying indexes

## Future: Alembic Integration

This project can be configured to use Alembic for automated migrations. To set up Alembic:

```bash
# Install alembic
uv add alembic

# Initialize alembic
alembic init alembic

# Generate migrations from models
alembic revision --autogenerate -m "add device linking"

# Apply migrations
alembic upgrade head
```
