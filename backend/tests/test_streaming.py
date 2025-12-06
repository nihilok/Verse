"""Tests for streaming chat functionality."""

from unittest.mock import Mock, patch

import pytest

from app.clients.claude_client import ClaudeAIClient
from app.models.models import (
    ChatMessage,
    SavedInsight,
    StandaloneChat,
    StandaloneChatMessage,
)
from app.services.chat_service import CHAT_ID_MARKER, ChatService


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

    with patch.object(client.client.messages, "stream") as mock_stream:
        mock_stream.return_value = MockStreamResponse(mock_tokens)

        # Create a mock chat history
        mock_history = [
            Mock(role="user", content="Previous question"),
            Mock(role="assistant", content="Previous answer"),
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
                "practical_application": "Practice",
            },
            chat_history=mock_history,
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

    with patch.object(client.client.messages, "stream") as mock_stream:
        mock_stream.return_value = MockStreamResponse(mock_tokens)

        # Collect streamed tokens and stop_reason
        tokens = []
        stop_reason = None
        async for (
            chunk,
            chunk_stop_reason,
        ) in client.generate_standalone_chat_response_stream(
            user_message="Test question",
            passage_text="Test passage",
            passage_reference="Test 1:1",
            chat_history=[],
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
async def test_chat_service_send_message_stream(async_db, async_test_user):
    """Test that chat service streams messages and saves to DB atomically."""
    # Create an insight
    insight = SavedInsight(
        passage_reference="John 3:16",
        passage_text="For God so loved the world...",
        historical_context="Historical context...",
        theological_significance="Theological significance...",
        practical_application="Practical application...",
    )
    async_db.add(insight)
    await async_db.flush()
    await async_db.refresh(insight)

    service = ChatService()
    mock_tokens = ["Test", " ", "streaming", " ", "response"]

    # Mock the AI client streaming method
    with patch.object(service.client, "generate_chat_response_stream") as mock_stream:
        # Make it an async generator that yields tuples
        async def async_gen():
            for token in mock_tokens:
                yield (token, None)
            yield ("", "end_turn")

        mock_stream.return_value = async_gen()

        # Collect streamed tokens
        tokens = []
        async for chunk, _stop_reason in service.send_message_stream(
            db=async_db,
            insight_id=insight.id,
            user_id=async_test_user.id,
            user_message="Test message",
            passage_text="Test passage",
            passage_reference="Test 1:1",
            insight_context={
                "historical_context": "History",
                "theological_significance": "Theology",
                "practical_application": "Practice",
            },
        ):
            if chunk:
                tokens.append(chunk)

        # Verify tokens were streamed
        assert tokens == mock_tokens

        # Verify messages were saved to database
        from sqlalchemy import select

        result = await async_db.execute(
            select(ChatMessage).where(
                ChatMessage.insight_id == insight.id,
                ChatMessage.user_id == async_test_user.id,
            )
        )
        messages = list(result.scalars().all())

        assert len(messages) == 2  # User message + AI response
        assert messages[0].role == "user"
        assert messages[0].content == "Test message"
        assert messages[1].role == "assistant"
        assert messages[1].content == "".join(mock_tokens)


@pytest.mark.asyncio
async def test_chat_service_send_standalone_message_stream(async_db, async_test_user):
    """Test that chat service streams standalone messages correctly."""
    # Create a standalone chat
    chat = StandaloneChat(
        user_id=async_test_user.id,
        title="Test Chat",
        passage_text="Test passage",
        passage_reference="Test 1:1",
    )
    async_db.add(chat)
    await async_db.flush()
    await async_db.refresh(chat)

    service = ChatService()
    mock_tokens = ["Standalone", " ", "response"]

    # Mock the AI client streaming method
    with patch.object(service.client, "generate_standalone_chat_response_stream") as mock_stream:

        async def async_gen():
            for token in mock_tokens:
                yield (token, None)
            yield ("", "end_turn")

        mock_stream.return_value = async_gen()

        # Collect streamed tokens
        tokens = []
        async for chunk, _stop_reason in service.send_standalone_message_stream(
            db=async_db, chat_id=chat.id, user_id=async_test_user.id, user_message="Test message"
        ):
            if chunk:
                tokens.append(chunk)

        # Verify tokens were streamed
        assert tokens == mock_tokens

        # Verify messages were saved to database
        from sqlalchemy import select

        result = await async_db.execute(
            select(StandaloneChatMessage).where(StandaloneChatMessage.chat_id == chat.id)
        )
        messages = list(result.scalars().all())

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Test message"
        assert messages[1].role == "assistant"
        assert messages[1].content == "".join(mock_tokens)


@pytest.mark.asyncio
async def test_chat_service_create_standalone_chat_stream(async_db, async_test_user):
    """Test that chat service creates chat and streams first message."""
    service = ChatService()
    mock_tokens = ["First", " ", "message"]

    # Mock the AI client streaming method
    with patch.object(service.client, "generate_standalone_chat_response_stream") as mock_stream:

        async def async_gen():
            for token in mock_tokens:
                yield (token, None)
            yield ("", "end_turn")

        mock_stream.return_value = async_gen()

        # Collect streamed tokens and chat_id
        tokens = []
        chat_id = None
        async for chunk, _stop_reason in service.create_standalone_chat_stream(
            db=async_db,
            user_id=async_test_user.id,
            user_message="First message",
            passage_text="Test passage",
            passage_reference="Test 1:1",
        ):
            if chunk.startswith(CHAT_ID_MARKER):
                chat_id = int(chunk.split(":", 1)[1])
            elif chunk:
                tokens.append(chunk)

        # Verify tokens were streamed
        assert tokens == mock_tokens
        assert chat_id is not None

        # Verify chat was created
        from sqlalchemy import select

        result = await async_db.execute(select(StandaloneChat).where(StandaloneChat.id == chat_id))
        chat = result.scalar_one_or_none()

        assert chat is not None
        assert chat.user_id == async_test_user.id
        assert chat.passage_text == "Test passage"
        assert chat.passage_reference == "Test 1:1"
        assert chat.title == "First message"

        # Verify messages were saved
        result = await async_db.execute(
            select(StandaloneChatMessage).where(StandaloneChatMessage.chat_id == chat_id)
        )
        messages = list(result.scalars().all())

        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "First message"
        assert messages[1].role == "assistant"
        assert messages[1].content == "".join(mock_tokens)


@pytest.mark.asyncio
async def test_streaming_atomic_db_save_on_error(async_db, async_test_user):
    """Test that DB is not modified if streaming fails."""
    # Create an insight
    insight = SavedInsight(
        passage_reference="Test 1:1",
        passage_text="Test passage",
        historical_context="History",
        theological_significance="Theology",
        practical_application="Practice",
    )
    async_db.add(insight)
    await async_db.flush()
    await async_db.refresh(insight)

    service = ChatService()

    # Mock the AI client to raise an error during streaming
    with patch.object(service.client, "generate_chat_response_stream") as mock_stream:

        async def async_gen():
            yield ("Test", None)
            yield (" ", None)
            raise Exception("Streaming error")

        mock_stream.return_value = async_gen()

        # Try to stream (should fail)
        with pytest.raises(Exception, match="Streaming error"):
            tokens = []
            async for chunk, _stop_reason in service.send_message_stream(
                db=async_db,
                insight_id=insight.id,
                user_id=async_test_user.id,
                user_message="Test message",
                passage_text="Test passage",
                passage_reference="Test 1:1",
                insight_context={},
            ):
                if chunk:
                    tokens.append(chunk)

        # Verify no messages were saved (atomic rollback)
        from sqlalchemy import select

        result = await async_db.execute(
            select(ChatMessage).where(
                ChatMessage.insight_id == insight.id,
                ChatMessage.user_id == async_test_user.id,
            )
        )
        messages = list(result.scalars().all())

        assert len(messages) == 0


@pytest.mark.asyncio
async def test_sse_event_format():
    """Test that SSE events are formatted correctly."""
    import json

    from app.services.chat_service import ChatService

    # Create a test service instance
    service = ChatService()

    # Mock the streaming method to return tuples
    with patch.object(service, "send_message_stream") as mock_stream:

        async def async_gen():
            yield ("Hello", None)
            yield (" ", None)
            yield ("world", None)
            yield ("", "end_turn")

        mock_stream.return_value = async_gen()

        # Manually create the event stream generator like the endpoint does
        async def event_stream():
            stop_reason = None
            try:
                async for chunk, chunk_stop_reason in async_gen():
                    if chunk:  # Send non-empty content chunks
                        yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"
                    if chunk_stop_reason:  # Capture stop_reason
                        stop_reason = chunk_stop_reason

                # Send completion event with stop_reason
                data = {"status": "complete", "stop_reason": stop_reason}
                yield f"event: done\ndata: {json.dumps(data)}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        # Collect events
        events = []
        async for event in event_stream():
            events.append(event)

        # Verify event format
        assert len(events) == 4  # 3 tokens + 1 done
        assert events[0].startswith("event: token\ndata:")
        assert '"token": "Hello"' in events[0]
        assert events[1].startswith("event: token\ndata:")
        assert '"token": " "' in events[1]
        assert events[2].startswith("event: token\ndata:")
        assert '"token": "world"' in events[2]
        assert events[3].startswith("event: done\ndata:")
        assert '"stop_reason": "end_turn"' in events[3]


@pytest.mark.asyncio
async def test_sse_chat_id_marker_event():
    """Test that chat_id marker is properly converted to SSE event."""
    import json

    from app.services.chat_service import CHAT_ID_MARKER

    # Simulate what the endpoint does with the chat_id marker (returns tuples)
    async def event_stream():
        # Simulate the tuple stream from create_standalone_chat_stream
        token_tuples = [
            ("First", None),
            (" ", None),
            ("message", None),
            (f"{CHAT_ID_MARKER}123", None),
            ("", "end_turn"),
        ]

        stop_reason = None
        for chunk, chunk_stop_reason in token_tuples:
            # Check if this is the chat_id marker
            if chunk.startswith(CHAT_ID_MARKER):
                chat_id = int(chunk.split(":", 1)[1])
                # Send chat_id event
                yield f"event: chat_id\ndata: {json.dumps({'chat_id': chat_id})}\n\n"
            elif chunk:  # Send non-empty content chunks
                # Send token as SSE event
                yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"

            if chunk_stop_reason:  # Capture stop_reason
                stop_reason = chunk_stop_reason

        # Send completion event with stop_reason
        yield f"event: done\ndata: {json.dumps({'status': 'complete', 'stop_reason': stop_reason})}\n\n"

    # Collect events
    events = []
    async for event in event_stream():
        events.append(event)

    # Verify events (3 tokens + 1 chat_id + 1 done)
    assert len(events) == 5

    # Check for chat_id event
    chat_id_events = [e for e in events if "event: chat_id" in e]
    assert len(chat_id_events) == 1
    assert '"chat_id": 123' in chat_id_events[0]

    # Check for done event with stop_reason
    done_events = [e for e in events if "event: done" in e]
    assert len(done_events) == 1
    assert '"stop_reason": "end_turn"' in done_events[0]


@pytest.mark.asyncio
async def test_was_truncated_field_when_max_tokens(async_db, async_test_user):
    """Test that was_truncated is set to True when stop_reason is max_tokens."""
    # Create an insight
    insight = SavedInsight(
        passage_reference="Test 1:1",
        passage_text="Test passage",
        historical_context="History",
        theological_significance="Theology",
        practical_application="Practice",
    )
    async_db.add(insight)
    await async_db.flush()
    await async_db.refresh(insight)

    service = ChatService()
    mock_tokens = ["This", " ", "was", " ", "truncated"]

    # Mock the AI client to return max_tokens as stop_reason
    with patch.object(service.client, "generate_chat_response_stream") as mock_stream:

        async def async_gen():
            for token in mock_tokens:
                yield (token, None)
            yield ("", "max_tokens")  # Indicate truncation

        mock_stream.return_value = async_gen()

        # Stream the message
        tokens = []
        async for chunk, _stop_reason in service.send_message_stream(
            db=async_db,
            insight_id=insight.id,
            user_id=async_test_user.id,
            user_message="Test message",
            passage_text="Test passage",
            passage_reference="Test 1:1",
            insight_context={},
        ):
            if chunk:
                tokens.append(chunk)

        # Verify message was saved with was_truncated=True
        from sqlalchemy import select

        result = await async_db.execute(
            select(ChatMessage).where(
                ChatMessage.insight_id == insight.id,
                ChatMessage.user_id == async_test_user.id,
                ChatMessage.role == "assistant",
            )
        )
        messages = list(result.scalars().all())

        assert len(messages) == 1
        assert messages[0].was_truncated is True
        assert messages[0].content == "".join(mock_tokens)


@pytest.mark.asyncio
async def test_was_truncated_field_when_end_turn(async_db, async_test_user):
    """Test that was_truncated is set to False when stop_reason is end_turn."""
    # Create an insight
    insight = SavedInsight(
        passage_reference="Test 1:1",
        passage_text="Test passage",
        historical_context="History",
        theological_significance="Theology",
        practical_application="Practice",
    )
    async_db.add(insight)
    await async_db.flush()
    await async_db.refresh(insight)

    service = ChatService()
    mock_tokens = ["Complete", " ", "response"]

    # Mock the AI client to return end_turn as stop_reason
    with patch.object(service.client, "generate_chat_response_stream") as mock_stream:

        async def async_gen():
            for token in mock_tokens:
                yield (token, None)
            yield ("", "end_turn")  # Normal completion

        mock_stream.return_value = async_gen()

        # Stream the message
        tokens = []
        async for chunk, _stop_reason in service.send_message_stream(
            db=async_db,
            insight_id=insight.id,
            user_id=async_test_user.id,
            user_message="Test message",
            passage_text="Test passage",
            passage_reference="Test 1:1",
            insight_context={},
        ):
            if chunk:
                tokens.append(chunk)

        # Verify message was saved with was_truncated=False
        from sqlalchemy import select

        result = await async_db.execute(
            select(ChatMessage).where(
                ChatMessage.insight_id == insight.id,
                ChatMessage.user_id == async_test_user.id,
                ChatMessage.role == "assistant",
            )
        )
        messages = list(result.scalars().all())

        assert len(messages) == 1
        assert messages[0].was_truncated is False
        assert messages[0].content == "".join(mock_tokens)


@pytest.mark.asyncio
async def test_was_truncated_field_standalone_chat_max_tokens(async_db, async_test_user):
    """Test that was_truncated works for standalone chats when truncated."""
    # Create a standalone chat
    chat = StandaloneChat(
        user_id=async_test_user.id,
        title="Test Chat",
        passage_text="Test passage",
        passage_reference="Test 1:1",
    )
    async_db.add(chat)
    await async_db.flush()
    await async_db.refresh(chat)

    service = ChatService()
    mock_tokens = ["Truncated", " ", "standalone"]

    # Mock the AI client to return max_tokens as stop_reason
    with patch.object(service.client, "generate_standalone_chat_response_stream") as mock_stream:

        async def async_gen():
            for token in mock_tokens:
                yield (token, None)
            yield ("", "max_tokens")  # Indicate truncation

        mock_stream.return_value = async_gen()

        # Stream the message
        tokens = []
        async for chunk, _stop_reason in service.send_standalone_message_stream(
            db=async_db, chat_id=chat.id, user_id=async_test_user.id, user_message="Test message"
        ):
            if chunk:
                tokens.append(chunk)

        # Verify message was saved with was_truncated=True
        from sqlalchemy import select

        result = await async_db.execute(
            select(StandaloneChatMessage).where(
                StandaloneChatMessage.chat_id == chat.id,
                StandaloneChatMessage.role == "assistant",
            )
        )
        messages = list(result.scalars().all())

        assert len(messages) == 1
        assert messages[0].was_truncated is True
        assert messages[0].content == "".join(mock_tokens)


@pytest.mark.asyncio
async def test_was_truncated_field_standalone_chat_complete(async_db, async_test_user):
    """Test that was_truncated works for standalone chats when complete."""
    # Create a standalone chat
    chat = StandaloneChat(
        user_id=async_test_user.id,
        title="Test Chat",
        passage_text="Test passage",
        passage_reference="Test 1:1",
    )
    async_db.add(chat)
    await async_db.flush()
    await async_db.refresh(chat)

    service = ChatService()
    mock_tokens = ["Complete", " ", "standalone"]

    # Mock the AI client to return end_turn as stop_reason
    with patch.object(service.client, "generate_standalone_chat_response_stream") as mock_stream:

        async def async_gen():
            for token in mock_tokens:
                yield (token, None)
            yield ("", "end_turn")  # Normal completion

        mock_stream.return_value = async_gen()

        # Stream the message
        tokens = []
        async for chunk, _stop_reason in service.send_standalone_message_stream(
            db=async_db, chat_id=chat.id, user_id=async_test_user.id, user_message="Test message"
        ):
            if chunk:
                tokens.append(chunk)

        # Verify message was saved with was_truncated=False
        from sqlalchemy import select

        result = await async_db.execute(
            select(StandaloneChatMessage).where(
                StandaloneChatMessage.chat_id == chat.id,
                StandaloneChatMessage.role == "assistant",
            )
        )
        messages = list(result.scalars().all())

        assert len(messages) == 1
        assert messages[0].was_truncated is False
        assert messages[0].content == "".join(mock_tokens)
