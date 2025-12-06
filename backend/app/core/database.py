from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import get_settings

settings = get_settings()


def convert_to_async_url(database_url: str) -> str:
    """
    Convert synchronous database URL to async driver format.

    Handles multiple PostgreSQL URL formats (postgresql://, postgresql+psycopg2://)
    and SQLite URLs.
    """
    if database_url.startswith("sqlite"):
        return database_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif database_url.startswith("postgresql"):
        # Handle both postgresql:// and postgresql+psycopg2:// formats
        return database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://").replace(
            "postgresql://", "postgresql+asyncpg://"
        )
    else:
        raise ValueError(f"Unsupported database URL: {database_url}")


# Configure async engine for application use
async_database_url = convert_to_async_url(settings.database_url)

if settings.database_url.startswith("sqlite"):
    async_engine = create_async_engine(
        async_database_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )
elif settings.database_url.startswith("postgresql"):
    async_engine = create_async_engine(
        async_database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )
else:
    raise ValueError(f"Unsupported database URL: {settings.database_url}")

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Keep sync engine for Alembic migrations
if settings.database_url.startswith("sqlite"):
    sync_engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
else:
    sync_engine = create_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

# Use sync engine for Base (migrations)
Base = declarative_base()
engine = sync_engine  # For backwards compatibility with migrations


async def get_db():
    """
    Async dependency for database session with automatic transaction management.

    The session is automatically committed if no exceptions occur, and rolled back
    if an exception is raised. This follows the FastAPI dependency injection pattern
    and ensures proper cleanup of database resources.

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            # Database operations here
            # Commit happens automatically on success
            # Rollback happens automatically on exception
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
