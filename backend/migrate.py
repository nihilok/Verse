#!/usr/bin/env python3
"""
Run database migrations using Alembic.

This script is meant to be run in a Docker container or during deployment
to ensure the database schema is up-to-date before starting the application.
"""

import logging
import sys
import time

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def wait_for_db(max_retries: int = 30, delay: int = 2) -> bool:
    """Wait for database to be available."""
    settings = get_settings()

    logger.info("Waiting for database to be available...")

    for attempt in range(max_retries):
        try:
            engine = create_engine(settings.database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ Database is available")
            engine.dispose()
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(delay)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                return False

    return False


def run_migrations() -> None:
    """Run database migrations."""
    logger.info("Running database migrations...")

    # Configure Alembic
    alembic_cfg = Config("alembic.ini")

    try:
        # Run migrations to head
        command.upgrade(alembic_cfg, "head")
        logger.info("✓ Migrations completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def main() -> int:
    """Main entry point."""
    try:
        # Wait for database
        if not wait_for_db():
            return 1

        # Run migrations
        run_migrations()

        logger.info("✓ Migration script completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Migration script failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
