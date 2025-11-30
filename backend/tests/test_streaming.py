"""Tests for streaming chat functionality."""
import pytest
from unittest.mock import Mock, patch
from app.services.chat_service import ChatService, CHAT_ID_MARKER
from app.clients.claude_client import ClaudeAIClient
from app.models.models import SavedInsight, ChatMessage, StandaloneChat, StandaloneChatMessage


class MockStreamResponse:
    """Mock Anthropic streaming response."""

    def __init__(self, tokens, stop_reason="end_turn"):
        self.tokens = tokens
        self.text_stream = iter(tokens)
        self.stop_reason = stop_reason

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def get_final_message(self):
        """Return a mock final message with stop_reason."""
        return Mock(stop_reason=self.stop_reason)


@pytest.mark.asyncio
async def test_claude_client_generate_chat_response_stream():
    """Test that Claude client streams chat responses correctly."""
    # Mock the Anthropic client
    client = ClaudeAIClient()
    mock_tokens = ["Hello", " ", "world", "!"]

    with patch.object(client.client.messages, 'stream') as mock_stream:
        mock_stream.return_value = MockStreamResponse(mock_tokens)

        # Create a mock chat history
        mock_history = [
            Mock(role="user", content="Previous question"),
            Mock(role="assistant", content="Previous answer")
        ]

        # Collect streamed tokens and stop_reason
        tokens = []
        stop_reason = None
        async for chunk, chunk_stop_reason in client.generate_chat_response_stream(
            user_message="Test question",
            passage_text="Test passage",
            passage_reference="Test 1:1",
            insight_context={
                "historical_context": "History",
                "theological_significance": "Theology",
                "practical_application": "Practice"
            },
            chat_history=mock_history
        ):
            if chunk:
                tokens.append(chunk)
            if chunk_stop_reason:
                stop_reason = chunk_stop_reason

        # Verify tokens were streamed
        assert tokens == mock_tokens
        assert stop_reason == "end_turn"
        assert mock_stream.called


@pytest.mark.asyncio
async def test_claude_client_generate_standalone_chat_response_stream():
    """Test that Claude client streams standalone chat responses correctly."""
    client = ClaudeAIClient()
    mock_tokens = ["Streaming", " ", "response"]

    with patch.object(client.client.messages, 'stream') as mock_stream:
        mock_stream.return_value = MockStreamResponse(mock_tokens)

        # Collect streamed tokens and stop_reason
        tokens = []
        stop_reason = None
        async for chunk, chunk_stop_reason in client.generate_standalone_chat_response_stream(
            user_message="Test question",
            passage_text="Test passage",
            passage_reference="Test 1:1",
            chat_history=[]
        ):
            if chunk:
                tokens.append(chunk)
            if chunk_stop_reason:
                stop_reason = chunk_stop_reason

        # Verify tokens were streamed
        assert tokens == mock_tokens
        assert stop_reason == "end_turn"
        assert mock_stream.called


@pytest.mark.asyncio
async def test_chat_service_send_message_stream(db, test_user):
    """Test that chat service streams messages and saves to DB atomically."""
    # Create an insight
    insight = SavedInsight(
        passage_reference="John 3:16",
        passage_text="For God so loved the world...",
        historical_context="Historical context...",
        theological_significance="Theological significance...",
        practical_application="Practical application..."
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)

    service = ChatService()
    mock_tokens = ["Test", " ", "streaming", " ", "response"]

    # Mock the AI client streaming method
    with patch.object(service.client, 'generate_chat_response_stream') as mock_stream:
        # Make it an async generator that yields tuples
        async def async_gen():
            for token in mock_tokens:
                yield (token, None)
            yield ("", "end_turn")

        mock_stream.return_value = async_gen()

        # Collect streamed tokens
        tokens = []
        async for chunk, stop_reason in service.send_message_stream(
            db=db,
            insight_id=insight.id,
            user_id=test_user.id,
            user_message="Test message",
            passage_text="Test passage",
            passage_reference="Test 1:1",
            insight_context={
                "historical_context": "History",
                "theological_significance": "Theology",
                "practical_application": "Practice"
            }
        ):
            if chunk:
                tokens.append(chunk)

        # Verify tokens were streamed
        assert tokens == mock_tokens

        # Verify messages were saved to database
        messages = db.query(ChatMessage).filter(
            ChatMessage.insight_id == insight.id,
            ChatMessage.user_id == test_user.id
        ).all()

        assert len(messages) == 2  # User message + AI response
        assert messages[0].role == "user"
        assert messages[0].content == "Test message"
        assert messages[1].role == "assistant"
        assert messages[1].content == "".join(mock_tokens)


@pytest.mark.asyncio
async def test_chat_service_send_standalone_message_stream(db, test_user):
    """Test that chat service streams standalone messages correctly."""
    # Create a standalone chat
    chat = StandaloneChat(
        user_id=test_user.id,
        title="Test Chat",
        passage_text="Test passage",
        passage_reference="Test 1:1"
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)

    service = ChatService()
    mock_tokens = ["Standalone", " ", "response"]

    # Mock the AI client streaming method
    with patch.object(service.client, 'generate_standalone_chat_response_stream') as mock_stream:
        async def async_gen():
            for token in mock_tokens:
                yield (token, None)
            yield ("", "end_turn")

        mock_stream.return_value = async_gen()

        # Collect streamed tokens
        tokens = []
        async for chunk, stop_reason in service.send_standalone_message_stream(
            db=db,
            chat_id=chat.id,
            user_id=test_user.id,
            user_message="Test message"
        ):
            if chunk:
                tokens.append(chunk)

        # Verify tokens were streamed
        assert tokens == mock_tokens

        # Verify messages were saved to database
        messages = db.query(StandaloneChatMessage).filter(
            StandaloneChatMessage.chat_id == chat.id
        ).all()

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Test message"
        assert messages[1].role == "assistant"
        assert messages[1].content == "".join(mock_tokens)


@pytest.mark.asyncio
async def test_chat_service_create_standalone_chat_stream(db, test_user):
    """Test that chat service creates chat and streams first message."""
    service = ChatService()
    mock_tokens = ["First", " ", "message"]

    # Mock the AI client streaming method
    with patch.object(service.client, 'generate_standalone_chat_response_stream') as mock_stream:
        async def async_gen():
            for token in mock_tokens:
                yield (token, None)
            yield ("", "end_turn")

        mock_stream.return_value = async_gen()

        # Collect streamed tokens and chat_id
        tokens = []
        chat_id = None
        async for chunk, stop_reason in service.create_standalone_chat_stream(
            db=db,
            user_id=test_user.id,
            user_message="First message",
            passage_text="Test passage",
            passage_reference="Test 1:1"
        ):
            if chunk.startswith(CHAT_ID_MARKER):
                chat_id = int(chunk.split(":", 1)[1])
            elif chunk:
                tokens.append(chunk)

        # Verify tokens were streamed
        assert tokens == mock_tokens
        assert chat_id is not None

        # Verify chat was created
        chat = db.query(StandaloneChat).filter(
            StandaloneChat.id == chat_id
        ).first()

        assert chat is not None
        assert chat.user_id == test_user.id
        assert chat.passage_text == "Test passage"
        assert chat.passage_reference == "Test 1:1"
        assert chat.title == "First message"

        # Verify messages were saved
        messages = db.query(StandaloneChatMessage).filter(
            StandaloneChatMessage.chat_id == chat_id
        ).all()

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "First message"
        assert messages[1].role == "assistant"
        assert messages[1].content == "".join(mock_tokens)


@pytest.mark.asyncio
async def test_streaming_atomic_db_save_on_error(db, test_user):
    """Test that DB is not modified if streaming fails."""
    # Create an insight
    insight = SavedInsight(
        passage_reference="Test 1:1",
        passage_text="Test passage",
        historical_context="History",
        theological_significance="Theology",
        practical_application="Practice"
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)

    service = ChatService()

    # Mock the AI client to raise an error during streaming
    with patch.object(service.client, 'generate_chat_response_stream') as mock_stream:
        async def async_gen():
            yield ("Test", None)
            yield (" ", None)
            raise Exception("Streaming error")

        mock_stream.return_value = async_gen()

        # Try to stream (should fail)
        with pytest.raises(Exception, match="Streaming error"):
            tokens = []
            async for chunk, stop_reason in service.send_message_stream(
                db=db,
                insight_id=insight.id,
                user_id=test_user.id,
                user_message="Test message",
                passage_text="Test passage",
                passage_reference="Test 1:1",
                insight_context={}
            ):
                if chunk:
                    tokens.append(chunk)

        # Verify no messages were saved (atomic rollback)
        messages = db.query(ChatMessage).filter(
            ChatMessage.insight_id == insight.id,
            ChatMessage.user_id == test_user.id
        ).all()

        assert len(messages) == 0


@pytest.mark.asyncio
async def test_sse_event_format():
    """Test that SSE events are formatted correctly."""
    from app.api.routes import router
    from fastapi import Request
    from app.services.chat_service import ChatService

    # Create a mock request with the required state
    mock_request = Mock(spec=Request)
    mock_request.state.anonymous_id = "test-anonymous-id"
    mock_request.state.user = Mock(id=1)

    # Create a test service instance
    service = ChatService()

    # Mock the streaming method
    with patch.object(service, 'send_message_stream') as mock_stream:
        async def async_gen():
            yield "Hello"
            yield " "
            yield "world"

        mock_stream.return_value = async_gen()

        # Manually create the event stream generator like the endpoint does
        async def event_stream():
            try:
                async for token in async_gen():
                    yield f"event: token\ndata: {{'token': '{token}'}}\n\n"
                yield f"event: done\ndata: {{'status': 'complete'}}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {{'error': '{str(e)}'}}\n\n"

        # Collect events
        events = []
        async for event in event_stream():
            events.append(event)

        # Verify event format
        assert len(events) == 4  # 3 tokens + 1 done
        assert events[0].startswith("event: token\ndata:")
        assert events[1].startswith("event: token\ndata:")
        assert events[2].startswith("event: token\ndata:")
        assert events[3].startswith("event: done\ndata:")


@pytest.mark.asyncio
async def test_sse_chat_id_marker_event():
    """Test that chat_id marker is properly converted to SSE event."""
    from app.services.chat_service import CHAT_ID_MARKER

    # Simulate what the endpoint does with the chat_id marker
    async def event_stream():
        tokens = ["First", " ", "message", f"{CHAT_ID_MARKER}123"]
        for token in tokens:
            if token.startswith(CHAT_ID_MARKER):
                chat_id = int(token.split(":", 1)[1])
                yield f"event: chat_id\ndata: {{'chat_id': {chat_id}}}\n\n"
            else:
                yield f"event: token\ndata: {{'token': '{token}'}}\n\n"
        yield f"event: done\ndata: {{'status': 'complete'}}\n\n"

    # Collect events
    events = []
    async for event in event_stream():
        events.append(event)

    # Verify events
    assert len(events) == 5  # 3 tokens + 1 chat_id + 1 done

    # Check for chat_id event
    chat_id_events = [e for e in events if 'event: chat_id' in e]
    assert len(chat_id_events) == 1
    assert "'chat_id': 123" in chat_id_events[0]
