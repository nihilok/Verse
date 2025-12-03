import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """Model for anonymous users identified by device."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    anonymous_id = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    device_count = Column(Integer, default=1, nullable=False)

    # Relationships
    insights = relationship("SavedInsight", secondary="user_insights", back_populates="users")
    definitions = relationship("SavedDefinition", secondary="user_definitions", back_populates="users")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    standalone_chats = relationship("StandaloneChat", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")


# Linking table for many-to-many relationship between users and insights
# NOTE: The indexes defined below require database migrations for existing databases.
# For new deployments, indexes are created automatically by create_all().
# For existing databases, use Alembic migrations:
#   alembic revision --autogenerate -m "add composite indexes"
#   alembic upgrade head
user_insights = Table(
    "user_insights",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "insight_id",
        Integer,
        ForeignKey("saved_insights.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Index("idx_user_insights_user_created", "user_id", "created_at"),
)


# Linking table for many-to-many relationship between users and definitions
user_definitions = Table(
    "user_definitions",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "definition_id",
        Integer,
        ForeignKey("saved_definitions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Index("idx_user_definitions_user_created", "user_id", "created_at"),
)


class SavedPassage(Base):
    """Model for saved Bible passages."""

    __tablename__ = "saved_passages"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(100), nullable=False, index=True)
    book = Column(String(50), nullable=False)
    chapter = Column(Integer, nullable=False)
    verse_start = Column(Integer, nullable=False)
    verse_end = Column(Integer, nullable=True)
    translation = Column(String(10), nullable=False, default="WEB")
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SavedInsight(Base):
    """Model for saved AI-generated insights."""

    __tablename__ = "saved_insights"

    id = Column(Integer, primary_key=True, index=True)
    passage_reference = Column(String(100), nullable=False, index=True)
    passage_text = Column(Text, nullable=False)
    historical_context = Column(Text, nullable=False)
    theological_significance = Column(Text, nullable=False)
    practical_application = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    users = relationship("User", secondary="user_insights", back_populates="insights")
    chat_messages = relationship("ChatMessage", back_populates="insight", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("passage_reference", "passage_text", name="uix_passage_reference_text"),
        Index("idx_passage_text", "passage_text"),
    )


class SavedDefinition(Base):
    """Model for saved AI-generated word definitions."""

    __tablename__ = "saved_definitions"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(100), nullable=False, index=True)
    passage_reference = Column(String(100), nullable=False, index=True)
    verse_text = Column(Text, nullable=False)
    definition = Column(Text, nullable=False)
    biblical_usage = Column(Text, nullable=False)
    original_language = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    users = relationship("User", secondary="user_definitions", back_populates="definitions")

    __table_args__ = (
        UniqueConstraint("word", "passage_reference", "verse_text", name="uix_word_reference_verse"),
        Index("idx_word", "word"),
    )


class ChatMessage(Base):
    """Model for chat messages related to insights."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(
        Integer,
        ForeignKey("saved_insights.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    was_truncated = Column(Boolean, default=False, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Vector embedding for RAG (1536 dimensions matches OpenAI text-embedding-3-small)
    embedding = mapped_column(Vector(1536), nullable=True)

    # Relationships
    insight = relationship("SavedInsight", back_populates="chat_messages")
    user = relationship("User", back_populates="chat_messages")

    __table_args__ = (
        Index("idx_chat_messages_user_created", "user_id", "created_at"),
        Index(
            "idx_chat_messages_insight_user_created",
            "insight_id",
            "user_id",
            "created_at",
        ),
        # HNSW index for efficient vector similarity search with user isolation
        Index(
            "idx_chat_messages_embedding_user",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class StandaloneChat(Base):
    """Model for standalone chat sessions (not linked to insights)."""

    __tablename__ = "standalone_chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=True)  # Optional title derived from first message
    passage_reference = Column(String(100), nullable=True)  # Optional reference if started from passage
    passage_text = Column(Text, nullable=True)  # Optional passage text
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="standalone_chats")
    messages = relationship("StandaloneChatMessage", back_populates="chat", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_standalone_chats_user_updated", "user_id", "updated_at"),)


class StandaloneChatMessage(Base):
    """Model for messages in standalone chat sessions."""

    __tablename__ = "standalone_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(
        Integer,
        ForeignKey("standalone_chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    was_truncated = Column(Boolean, default=False, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Vector embedding for RAG (1536 dimensions matches OpenAI text-embedding-3-small)
    embedding = mapped_column(Vector(1536), nullable=True)

    # Relationship to chat
    chat = relationship("StandaloneChat", back_populates="messages")

    __table_args__ = (
        # HNSW index for efficient vector similarity search
        Index(
            "idx_standalone_messages_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class ConversationSummary(Base):
    """Model for cached conversation summaries used in RAG context."""

    __tablename__ = "conversation_summaries"

    id = Column(Integer, primary_key=True, index=True)
    conversation_type = Column(String(20), nullable=False)  # 'insight' or 'standalone'
    conversation_id = Column(Integer, nullable=False)
    summary_text = Column(Text, nullable=False)
    message_count = Column(Integer, nullable=False)  # For cache invalidation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index(
            "idx_conversation_lookup",
            "conversation_type",
            "conversation_id",
            unique=True,
        ),
    )


class UserDevice(Base):
    """Model for tracking devices linked to a user account."""

    __tablename__ = "user_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name = Column(String(100))
    device_type = Column(String(20))  # 'mobile', 'desktop', 'tablet', 'unknown'
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="devices")

    __table_args__ = (Index("idx_user_devices_last_active", "user_id", "last_active"),)


class DeviceLinkCode(Base):
    """Model for managing device linking codes."""

    __tablename__ = "device_link_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)  # Hashed token
    display_code = Column(String(20), unique=True, nullable=False, index=True)  # User-friendly format
    source_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_device_id = Column(Integer, ForeignKey("user_devices.id", ondelete="CASCADE"))
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    target_device_id = Column(Integer, ForeignKey("user_devices.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    status = Column(String(20), default="pending", nullable=False)

    # Relationships
    source_user = relationship("User", foreign_keys=[source_user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    source_device = relationship("UserDevice", foreign_keys=[source_device_id])
    target_device = relationship("UserDevice", foreign_keys=[target_device_id])
