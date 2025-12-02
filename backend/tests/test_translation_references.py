"""Tests for translation references in insights and chats."""
import pytest
from app.models.models import SavedInsight, StandaloneChat
from app.services.insight_service import InsightService
from app.services.chat_service import ChatService


def test_insight_with_translation_in_reference(db, test_user):
    """Test that insights can be saved with translation in the reference."""
    service = InsightService()
    
    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"
    
    # Save an insight with translation in reference
    saved = service.save_insight(
        db,
        passage_reference="John 3:16 (KJV)",
        passage_text="For God so loved the world...",
        insights=MockInsight(),
        user_id=test_user.id
    )
    
    assert saved is not None
    assert saved.passage_reference == "John 3:16 (KJV)"
    assert saved.passage_text == "For God so loved the world..."


def test_different_translations_cached_separately(db, test_user):
    """Test that different translations of the same verse are cached separately."""
    service = InsightService()
    
    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"
    
    # Save insight for KJV
    service.save_insight(
        db,
        passage_reference="John 3:16 (KJV)",
        passage_text="For God so loved the world, that he gave his only begotten Son...",
        insights=MockInsight(),
        user_id=test_user.id
    )
    
    # Save insight for WEB (different text, different translation)
    service.save_insight(
        db,
        passage_reference="John 3:16 (WEB)",
        passage_text="For God so loved the world, that he gave his only born Son...",
        insights=MockInsight(),
        user_id=test_user.id
    )
    
    # Retrieve KJV version
    kjv_insight = service.get_saved_insight(
        db,
        passage_reference="John 3:16 (KJV)",
        passage_text="For God so loved the world, that he gave his only begotten Son..."
    )
    
    # Retrieve WEB version
    web_insight = service.get_saved_insight(
        db,
        passage_reference="John 3:16 (WEB)",
        passage_text="For God so loved the world, that he gave his only born Son..."
    )
    
    assert kjv_insight is not None
    assert web_insight is not None
    assert kjv_insight.id != web_insight.id
    assert kjv_insight.passage_reference == "John 3:16 (KJV)"
    assert web_insight.passage_reference == "John 3:16 (WEB)"


def test_standalone_chat_with_translation_in_reference(db, test_user):
    """Test that standalone chats can store translation in passage reference."""
    # Create a standalone chat with translation in reference
    chat = StandaloneChat(
        user_id=test_user.id,
        title="Chat about John 3:16",
        passage_reference="John 3:16 (ASV)",
        passage_text="For God so loved the world..."
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    
    assert chat.passage_reference == "John 3:16 (ASV)"
    assert chat.passage_text == "For God so loved the world..."
    
    # Retrieve the chat
    service = ChatService()
    chats = service.get_standalone_chats(db, test_user.id)
    
    assert len(chats) == 1
    assert chats[0].passage_reference == "John 3:16 (ASV)"


def test_user_insights_with_multiple_translations(db, test_user):
    """Test that a user can have insights for the same verse in different translations."""
    service = InsightService()
    
    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"
    
    # Save insights for different translations
    service.save_insight(
        db,
        passage_reference="Romans 8:28 (KJV)",
        passage_text="And we know that all things work together for good...",
        insights=MockInsight(),
        user_id=test_user.id
    )
    
    service.save_insight(
        db,
        passage_reference="Romans 8:28 (BSB)",
        passage_text="And we know that God works all things together for good...",
        insights=MockInsight(),
        user_id=test_user.id
    )
    
    # Get user insights
    insights = service.get_user_insights(db, test_user.id)
    
    assert len(insights) == 2
    references = [i.passage_reference for i in insights]
    assert "Romans 8:28 (KJV)" in references
    assert "Romans 8:28 (BSB)" in references
