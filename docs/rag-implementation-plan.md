# RAG Implementation Plan for Verse

This document outlines the strategy for implementing Retrieval-Augmented Generation (RAG) within the Verse ecosystem. This feature enables the AI to recall context from historical conversations, personalised to each user, using the existing PostgreSQL infrastructure.

## 1. Executive Summary

We will leverage PostgreSQL with the pgvector extension to store and query vector embeddings. This avoids the cost and complexity of a dedicated vector database (like Pinecone) while adhering to our "No Vendor Lock-in" principle.

### Key Technical Decisions:
- **Database:** PostgreSQL + pgvector extension
- **Isolation:** Metadata filtering (WHERE user_id = X) to ensure strict data privacy
- **Embedding Model:** OpenAI text-embedding-3-small (Cost-effective, high performance) or open-source equivalent via HuggingFace
- **Architecture:** Adhering to the existing Service/Repository pattern

## 2. Database Architecture

### 2.1 Extension Setup

The database must support vector operations. This is a one-time migration.

```python
# Migration: migrations/enable_vector.py
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2.2 Schema Updates

We will modify the chat_messages table (or create a new insights table) to store the vector representations of the text.

**SQLAlchemy Model (backend/app/models/models.py):**

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 1536 dimensions matches OpenAI's text-embedding-3-small
    embedding = mapped_column(Vector(1536))

    user = relationship("User", back_populates="messages")

    # Composite Index for performance:
    # Allows Postgres to quickly filter by User ID first, then do vector search.
    # Note: 'hnsw' is generally faster than 'ivfflat' for larger datasets.
    __table_args__ = (
        Index(
            'ix_chat_message_embedding_user',
            'embedding',
            postgresql_using='hnsw',
            postgresql_with={'m': 16, 'ef_construction': 64},
            postgresql_ops={'embedding': 'vector_cosine_ops'}
        ),
    )
```

## 3. Client Abstraction Layer

We introduce a new EmbeddingClient to handle the conversion of text to vectors.

**Interface (backend/app/clients/embedding_client.py):**

```python
from abc import ABC, abstractmethod
from typing import List

class EmbeddingClient(ABC):
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """Converts text string into a list of floats (vector)."""
        pass
```

**Implementation (backend/app/clients/openai_embedding_client.py):**

```python
from openai import AsyncOpenAI
from app.clients.embedding_client import EmbeddingClient

class OpenAIEmbeddingClient(EmbeddingClient):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"

    async def get_embedding(self, text: str) -> List[float]:
        # Strip newlines to improve embedding performance
        clean_text = text.replace("\n", " ")
        response = await self.client.embeddings.create(
            input=[clean_text],
            model=self.model
        )
        return response.data[0].embedding
```

## 4. Service Layer Logic

The ChatService will now orchestrate the RAG pipeline. It handles the "write path" (saving vectors) and the "read path" (retrieving relevant context).

**Logic Flow (backend/app/services/chat_service.py):**

```python
from sqlalchemy import select
from app.models.models import ChatMessage

class ChatService:
    def __init__(self, db, ai_client, embedding_client):
        self.db = db
        self.ai_client = ai_client
        self.embedding_client = embedding_client

    async def _get_relevant_context(self, user_id: int, query: str, limit: int = 5):
        """
        Retrieves the most semantically similar messages for a specific user.
        """
        # 1. Generate embedding for the current query
        query_vector = await self.embedding_client.get_embedding(query)

        # 2. Semantic Search with Metadata Filtering
        # The <=> operator represents Cosine Distance in pgvector
        stmt = (
            select(ChatMessage)
            .filter(ChatMessage.user_id == user_id)  # STRICT ISOLATION
            .order_by(ChatMessage.embedding.cosine_distance(query_vector))
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def send_message(self, user_id: int, message_text: str):
        # 1. RAG Retrieval
        context_messages = await self._get_relevant_context(user_id, message_text)

        # 2. Construct System Prompt with Context
        context_block = "\n".join([f"- {msg.role}: {msg.content}" for msg in context_messages])
        system_prompt = (
            "You are a helpful Bible study assistant. "
            "Use the following history to answer the user if relevant:\n\n"
            f"{context_block}"
        )

        # 3. Get AI Response
        ai_response_text = await self.ai_client.chat(message_text, system_prompt)

        # 4. Save User Message (Write Path)
        user_embedding = await self.embedding_client.get_embedding(message_text)
        user_msg = ChatMessage(
            user_id=user_id,
            role="user",
            content=message_text,
            embedding=user_embedding
        )
        self.db.add(user_msg)

        # 5. Save AI Response (Write Path)
        # We embed the AI response so future queries can find answers we've already given.
        ai_embedding = await self.embedding_client.get_embedding(ai_response_text)
        ai_msg = ChatMessage(
            user_id=user_id,
            role="assistant",
            content=ai_response_text,
            embedding=ai_embedding
        )
        self.db.add(ai_msg)

        await self.db.commit()
        return ai_response_text
```

## 5. Security & Performance Considerations

### User Isolation (Privacy)

By including `.filter(ChatMessage.user_id == user_id)` in every vector search query, we utilise PostgreSQL's standard indexing to restrict the search space. This prevents cross-user data leakage.

- **Mechanism:** Standard SQL WHERE clause
- **Performance:** The composite index allows Postgres to filter rows before performing the expensive vector distance calculation

### Rate Limiting & Costs

- **Embeddings:** These are significantly cheaper than LLM generation tokens. However, batch processing historical data (if any) should be done carefully
- **Latency:** Calling the embedding API adds latency
- **Optimisation:** Fire the embedding_client.get_embedding calls asynchronously while the LLM is generating the text, then save to DB after the response is sent to the user (using FastAPI BackgroundTasks)

### Migration Strategy

1. **Phase 1:** Add the embedding column (nullable initially)
2. **Phase 2:** Deploy code that writes embeddings for new messages
3. **Phase 3:** Run a background script to backfill embeddings for old messages
4. **Phase 4:** Enable the RAG retrieval logic in the ChatService

## 6. Development Setup

### Requirements additions (pyproject.toml):

```toml
dependencies = [
    # ... existing dependencies
    "pgvector>=0.2.4",
    "openai>=1.0.0",
]
```

### Docker Compose Update:

Ensure your database image supports pgvector:

```yaml
services:
  db:
    image: pgvector/pgvector:pg18  # Replaces standard postgres:18
    # ... rest of config
```
