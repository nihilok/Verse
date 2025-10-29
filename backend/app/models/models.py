from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


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
    
    # Relationship to chat messages
    chat_messages = relationship("ChatMessage", back_populates="insight", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('passage_reference', 'passage_text', name='uix_passage_reference_text'),
        Index('idx_passage_text', 'passage_text'),
    )


class ChatMessage(Base):
    """Model for chat messages related to insights."""
    
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(Integer, ForeignKey('saved_insights.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to insight
    insight = relationship("SavedInsight", back_populates="chat_messages")


class StandaloneChat(Base):
    """Model for standalone chat sessions (not linked to insights)."""
    
    __tablename__ = "standalone_chats"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=True)  # Optional title derived from first message
    passage_reference = Column(String(100), nullable=True)  # Optional reference if started from passage
    passage_text = Column(Text, nullable=True)  # Optional passage text
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to chat messages
    messages = relationship("StandaloneChatMessage", back_populates="chat", cascade="all, delete-orphan")


class StandaloneChatMessage(Base):
    """Model for messages in standalone chat sessions."""
    
    __tablename__ = "standalone_chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('standalone_chats.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to chat
    chat = relationship("StandaloneChat", back_populates="messages")
