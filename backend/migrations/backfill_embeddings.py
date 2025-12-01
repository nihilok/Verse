"""
Migration script to backfill embeddings for existing chat messages.

This script generates embeddings for all existing chat messages that don't have embeddings yet.
It processes messages in batches to avoid overwhelming the OpenAI API.

Usage: uv run python -m migrations.backfill_embeddings
"""

import sys
import asyncio
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.models import ChatMessage, StandaloneChatMessage
from app.clients.openai_embedding_client import OpenAIEmbeddingClient
from app.core.config import get_settings

# Configuration
BATCH_SIZE = 100  # Process messages in batches to avoid API rate limits


async def backfill_chat_messages(embedding_client: OpenAIEmbeddingClient, db: Session):
    """Backfill embeddings for ChatMessage records."""
    print("\nBackfilling embeddings for ChatMessage records...")

    # Get all messages without embeddings
    stmt = select(ChatMessage).filter(ChatMessage.embedding.is_(None))
    result = db.execute(stmt)
    messages = result.scalars().all()

    if not messages:
        print("No ChatMessage records need backfilling")
        return 0

    total = len(messages)
    print(f"Found {total} ChatMessage records without embeddings")

    updated = 0
    for i in range(0, total, BATCH_SIZE):
        batch = messages[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, total)
        print(f"Processing ChatMessage batch {i + 1}-{batch_end} of {total}...")

        # Extract text content from batch
        texts = [msg.content for msg in batch]

        try:
            # Generate embeddings in batch
            embeddings = await embedding_client.get_embeddings_batch(texts)

            # Update messages with embeddings
            for msg, embedding in zip(batch, embeddings):
                msg.embedding = embedding
                updated += 1

            # Commit batch
            db.commit()
            print(f"✓ Successfully processed {len(batch)} ChatMessage records")

        except Exception as e:
            db.rollback()
            print(f"✗ Error processing ChatMessage batch {i + 1}-{batch_end}: {e}")
            print("Continuing with next batch...")

        # Small delay between batches to respect rate limits
        await asyncio.sleep(1)

    return updated


async def backfill_standalone_messages(embedding_client: OpenAIEmbeddingClient, db: Session):
    """Backfill embeddings for StandaloneChatMessage records."""
    print("\nBackfilling embeddings for StandaloneChatMessage records...")

    # Get all messages without embeddings
    stmt = select(StandaloneChatMessage).filter(StandaloneChatMessage.embedding.is_(None))
    result = db.execute(stmt)
    messages = result.scalars().all()

    if not messages:
        print("No StandaloneChatMessage records need backfilling")
        return 0

    total = len(messages)
    print(f"Found {total} StandaloneChatMessage records without embeddings")

    updated = 0
    for i in range(0, total, BATCH_SIZE):
        batch = messages[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, total)
        print(f"Processing StandaloneChatMessage batch {i + 1}-{batch_end} of {total}...")

        # Extract text content from batch
        texts = [msg.content for msg in batch]

        try:
            # Generate embeddings in batch
            embeddings = await embedding_client.get_embeddings_batch(texts)

            # Update messages with embeddings
            for msg, embedding in zip(batch, embeddings):
                msg.embedding = embedding
                updated += 1

            # Commit batch
            db.commit()
            print(f"✓ Successfully processed {len(batch)} StandaloneChatMessage records")

        except Exception as e:
            db.rollback()
            print(f"✗ Error processing StandaloneChatMessage batch {i + 1}-{batch_end}: {e}")
            print("Continuing with next batch...")

        # Small delay between batches to respect rate limits
        await asyncio.sleep(1)

    return updated


async def main():
    """Main backfill function."""
    settings = get_settings()

    # Check if OpenAI API key is configured
    if not settings.openai_api_key:
        print("Error: OPENAI_API_KEY not configured in environment")
        print("Please set OPENAI_API_KEY in your .env file")
        sys.exit(1)

    print("Starting embedding backfill process...")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Using model: text-embedding-3-small (1536 dimensions)")

    # Initialise embedding client
    embedding_client = OpenAIEmbeddingClient(settings.openai_api_key)

    # Create database session
    db = SessionLocal()

    try:
        # Backfill both types of messages
        chat_updated = await backfill_chat_messages(embedding_client, db)
        standalone_updated = await backfill_standalone_messages(embedding_client, db)

        total_updated = chat_updated + standalone_updated

        print("\n" + "=" * 60)
        print("Backfill complete!")
        print(f"Total ChatMessage records updated: {chat_updated}")
        print(f"Total StandaloneChatMessage records updated: {standalone_updated}")
        print(f"Total records updated: {total_updated}")
        print("=" * 60)

    except Exception as e:
        print(f"\nFatal error during backfill: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nBackfill interrupted by user")
        sys.exit(130)
