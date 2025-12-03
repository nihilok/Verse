"""Tests for chat functionality."""

from app.models.models import ChatMessage, SavedInsight
from app.services.chat_service import ChatService


def test_chat_message_creation(db, test_user):
    """Test that chat messages can be created and linked to insights."""
    # Create an insight first
    insight = SavedInsight(
        passage_reference="John 3:16",
        passage_text="For God so loved the world...",
        historical_context="Historical context...",
        theological_significance="Theological significance...",
        practical_application="Practical application...",
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)

    # Create a chat message
    chat_msg = ChatMessage(
        insight_id=insight.id,
        user_id=test_user.id,
        role="user",
        content="What does this mean?",
    )
    db.add(chat_msg)
    db.commit()

    # Verify the chat message was created
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.insight_id == insight.id, ChatMessage.user_id == test_user.id)
        .all()
    )

    assert len(messages) == 1
    assert messages[0].role == "user"
    assert messages[0].content == "What does this mean?"


def test_get_chat_messages(db, test_user):
    """Test retrieving chat messages for an insight."""
    # Create an insight
    insight = SavedInsight(
        passage_reference="Romans 8:28",
        passage_text="And we know that in all things...",
        historical_context="Historical context...",
        theological_significance="Theological significance...",
        practical_application="Practical application...",
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)

    # Add multiple chat messages
    for i in range(3):
        role = "user" if i % 2 == 0 else "assistant"
        msg = ChatMessage(
            insight_id=insight.id,
            user_id=test_user.id,
            role=role,
            content=f"Message {i}",
        )
        db.add(msg)
    db.commit()

    # Get messages using service
    service = ChatService()
    messages = service.get_chat_messages(db, insight.id, test_user.id)

    assert len(messages) == 3
    assert messages[0].content == "Message 0"
    assert messages[1].content == "Message 1"
    assert messages[2].content == "Message 2"


def test_clear_chat_messages(db, test_user):
    """Test clearing chat messages for an insight."""
    # Create an insight
    insight = SavedInsight(
        passage_reference="Psalm 23:1",
        passage_text="The Lord is my shepherd...",
        historical_context="Historical context...",
        theological_significance="Theological significance...",
        practical_application="Practical application...",
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)

    # Add chat messages
    for i in range(5):
        msg = ChatMessage(
            insight_id=insight.id,
            user_id=test_user.id,
            role="user",
            content=f"Message {i}",
        )
        db.add(msg)
    db.commit()

    # Clear messages
    service = ChatService()
    count = service.clear_chat_messages(db, insight.id, test_user.id)

    assert count == 5

    # Verify messages are cleared
    messages = service.get_chat_messages(db, insight.id, test_user.id)
    assert len(messages) == 0


def test_cascade_delete_chat_messages(db, test_user):
    """Test that chat messages are deleted when insight is deleted."""
    # Create an insight
    insight = SavedInsight(
        passage_reference="Matthew 5:3",
        passage_text="Blessed are the poor in spirit...",
        historical_context="Historical context...",
        theological_significance="Theological significance...",
        practical_application="Practical application...",
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)

    # Add chat messages
    for i in range(3):
        msg = ChatMessage(
            insight_id=insight.id,
            user_id=test_user.id,
            role="user",
            content=f"Message {i}",
        )
        db.add(msg)
    db.commit()

    insight_id = insight.id

    # Delete the insight
    db.delete(insight)
    db.commit()

    # Verify chat messages are also deleted (cascade)
    messages = db.query(ChatMessage).filter(ChatMessage.insight_id == insight_id).all()

    assert len(messages) == 0
