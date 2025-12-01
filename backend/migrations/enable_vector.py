"""
Database migration to enable pgvector extension.

This script should be run once to enable vector operations in PostgreSQL.
Usage: uv run python -m migrations.enable_vector
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import engine


def enable_vector_extension():
    """Enable the pgvector extension in the database."""
    print("Enabling pgvector extension...")

    with engine.begin() as conn:
        # Check if extension is already enabled
        result = conn.execute(
            text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        )
        extension_exists = result.scalar()

        if extension_exists:
            print("✓ pgvector extension is already enabled")
        else:
            # Enable the extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            print("✓ pgvector extension enabled successfully")

    print("\nMigration completed!")


if __name__ == "__main__":
    try:
        enable_vector_extension()
    except Exception as e:
        print(f"Error enabling pgvector extension: {e}", file=sys.stderr)
        sys.exit(1)
