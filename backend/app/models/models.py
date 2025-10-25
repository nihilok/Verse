from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, Index
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
    
    __table_args__ = (
        UniqueConstraint('passage_reference', 'passage_text', name='uix_passage_reference_text'),
        Index('idx_passage_text', 'passage_text'),
    )
