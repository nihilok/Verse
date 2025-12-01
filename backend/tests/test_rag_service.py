"""
Tests for RagService - Enhanced RAG context with summaries and surrounding messages
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.rag_service import RagService, EnhancedRagContext
from app.models.models import ChatMessage, StandaloneChatMessage, ConversationSummary


@pytest.fixture
def mock_embedding_client():
    """Mock embedding client for tests."""
    client = Mock()
    client.get_embedding = AsyncMock(return_value=[0.1] * 1536)
    return client


@pytest.fixture
def mock_ai_client():
    """Mock AI client for summary generation."""
    client = Mock()
    client.generate_conversation_summary = AsyncMock(
        return_value="Discussion about biblical interpretation and context"
    )
    return client


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock(spec=Session)
    return db


@pytest.fixture
def rag_service(mock_embedding_client):
    """Create RagService instance with mock embedding client."""
    return RagService(embedding_client=mock_embedding_client)


def test_rag_service_initialization():
    """Test RagService can be initialized."""
    service = RagService(embedding_client=None)
    assert service is not None
    assert service.embedding_client is None


def test_rag_service_with_embedding_client(mock_embedding_client):
    """Test RagService initialization with embedding client."""
    service = RagService(embedding_client=mock_embedding_client)
    assert service.embedding_client is not None


@pytest.mark.asyncio
async def test_get_enhanced_rag_context_no_embedding_client(mock_db, mock_ai_client):
    """Test that RAG returns empty list when no embedding client configured."""
    service = RagService(embedding_client=None)
    
    result = await service.get_enhanced_rag_context(
        db=mock_db,
        user_id=1,
        query="test query",
        conversation_type="insight",
        ai_client=mock_ai_client
    )
    
    assert result == []


def test_format_enhanced_rag_context_empty(rag_service):
    """Test formatting with no context returns empty string."""
    result = rag_service.format_enhanced_rag_context([])
    assert result == ""


def test_format_enhanced_rag_context_with_data(rag_service):
    """Test formatting with enhanced context data."""
    # Create mock message objects
    mock_message = Mock()
    mock_message.role = "user"
    mock_message.content = "What does this passage mean?"
    mock_message.created_at = datetime(2024, 3, 15, 14, 30)
    
    mock_message_before = Mock()
    mock_message_before.role = "assistant"
    mock_message_before.content = "Let me explain the historical context."
    mock_message_before.created_at = datetime(2024, 3, 15, 14, 25)
    
    mock_message_after = Mock()
    mock_message_after.role = "assistant"
    mock_message_after.content = "This passage relates to..."
    mock_message_after.created_at = datetime(2024, 3, 15, 14, 35)
    
    # Create enhanced context
    context = EnhancedRagContext(
        conversation_id=1,
        conversation_type="insight",
        summary="Discussion about biblical interpretation",
        matched_message=mock_message,
        messages_before=[mock_message_before],
        messages_after=[mock_message_after],
        conversation_date=datetime(2024, 3, 15, 14, 20)
    )
    
    result = rag_service.format_enhanced_rag_context([context])
    
    # Verify formatting
    assert "RELEVANT CONTEXT FROM PAST CONVERSATIONS:" in result
    assert "Discussion about biblical interpretation" in result
    assert "---excerpt---" in result
    assert "---end excerpt---" in result
    assert "What does this passage mean?" in result
    assert "Retrieved via semantic search" in result
    assert "2024-03-15 14:30" in result


@pytest.mark.asyncio
async def test_get_conversation_date(rag_service, mock_db):
    """Test getting conversation date."""
    # Mock first message
    mock_message = Mock()
    mock_message.created_at = datetime(2024, 3, 15, 10, 0)
    
    # Mock database query
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.first.return_value = mock_message
    mock_db.query.return_value = mock_query
    
    result = await rag_service._get_conversation_date(
        db=mock_db,
        model_class=ChatMessage,
        conversation_id=1,
        conversation_id_field="insight_id"
    )
    
    assert result == datetime(2024, 3, 15, 10, 0)


def test_conversation_summary_model():
    """Test ConversationSummary model can be created."""
    summary = ConversationSummary(
        conversation_type="insight",
        conversation_id=1,
        summary_text="Test summary",
        message_count=5
    )
    
    assert summary.conversation_type == "insight"
    assert summary.conversation_id == 1
    assert summary.summary_text == "Test summary"
    assert summary.message_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
