"""Tests for insights functionality."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base, SavedInsight
from app.services.insight_service import InsightService


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_save_and_get_insight_with_same_text(db):
    """Test that insights are cached based on both reference and text."""
    service = InsightService()
    
    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"
    
    # Save an insight
    service.save_insight(
        db,
        passage_reference="John 3",
        passage_text="For God so loved the world",
        insights=MockInsight()
    )
    
    # Retrieve the same insight
    saved = service.get_saved_insight(
        db,
        passage_reference="John 3",
        passage_text="For God so loved the world"
    )
    
    assert saved is not None
    assert saved.passage_reference == "John 3"
    assert saved.passage_text == "For God so loved the world"
    assert saved.historical_context == "Historical context"


def test_different_text_same_reference_not_cached(db):
    """Test that different texts with same reference are not cached together."""
    service = InsightService()
    
    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"
    
    # Save an insight with one text
    service.save_insight(
        db,
        passage_reference="John 3",
        passage_text="For God so loved the world",
        insights=MockInsight()
    )
    
    # Try to retrieve with different text but same reference
    saved = service.get_saved_insight(
        db,
        passage_reference="John 3",
        passage_text="that he gave his only Son"
    )
    
    # Should not find a cached result
    assert saved is None


def test_get_all_insights(db):
    """Test getting all insights."""
    service = InsightService()
    
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"
    
    # Save multiple insights
    service.save_insight(
        db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight()
    )
    
    service.save_insight(
        db,
        passage_reference="John 3:17",
        passage_text="For God did not send his Son into the world",
        insights=MockInsight()
    )
    
    # Get all insights
    insights = service.get_all_insights(db, limit=50)
    
    assert len(insights) == 2


def test_clear_all_insights(db):
    """Test clearing all insights."""
    service = InsightService()
    
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"
    
    # Save some insights
    service.save_insight(
        db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight()
    )
    
    service.save_insight(
        db,
        passage_reference="John 3:17",
        passage_text="For God did not send his Son into the world",
        insights=MockInsight()
    )
    
    # Clear all insights
    count = service.clear_all_insights(db)
    
    assert count == 2
    
    # Verify all insights are cleared
    insights = service.get_all_insights(db, limit=50)
    assert len(insights) == 0
