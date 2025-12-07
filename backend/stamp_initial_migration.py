#!/usr/bin/env python3
"""
Mark the initial migration as applied for existing databases.

This script is for production databases that were created with
Base.metadata.create_all() before Alembic was introduced.
"""

import sys

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config
from app.core.config import get_settings

settings = get_settings()


def main():
    """Stamp the database with the initial migration revision."""
    print("Checking database state...")

    engine = create_engine(settings.database_url)

    # Check if alembic_version table exists
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')")
        )
        alembic_exists = result.scalar()

        if alembic_exists:
            # Check current version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"✓ Alembic is already initialized at version: {version}")
            return 0

    # Check if tables exist (meaning this is an existing DB)
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")
        )
        tables_exist = result.scalar()

        if not tables_exist:
            print("✗ Database appears empty - run migrations normally")
            return 1

    print("✓ Found existing tables without alembic_version")
    print("Stamping database with initial migration...")

    # Configure Alembic
    alembic_cfg = Config("alembic.ini")

    try:
        # Stamp the database with the initial migration revision
        # This creates alembic_version table and marks migration as applied
        command.stamp(alembic_cfg, "head")
        print("✓ Successfully stamped database with initial migration")
        print("You can now run 'alembic upgrade head' for future migrations")
        return 0
    except Exception as e:
        print(f"✗ Error stamping database: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
