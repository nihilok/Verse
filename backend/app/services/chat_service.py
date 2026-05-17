import logging
from datetime import UTC, datetime, timedelta

from fastapi import BackgroundTasks
from sqlalchemy import delete, not_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func, true

from app.clients.claude_client import ClaudeAIClient
from app.clients.embedding_client import EmbeddingClient
from app.clients.openai_embedding_client import OpenAIEmbeddingClient
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.models import ChatMessage, ConversationSummary, StandaloneChat, StandaloneChatMessage
from app.services.rag_service import RagService

logger = logging.getLogger(__name__)

# Special marker for streaming chat_id in SSE responses
CHAT_ID_MARKER = "__CHAT_ID__:"


class ChatService:
    """Service for chat operations with AI."""

    # Configuration Constants
    # The database allows chat titles up to 200 characters (see models.py: title = Column(String(200))).
    # We limit auto-generated titles to 50 characters for UI clarity and to prevent overly long
    # titles from the first message. This value is intentionally lower than the database maximum
    # to ensure titles display well in all UI contexts (chat history lists, mobile views, etc.).
    # User-provided titles or manual edits can still use the full 200 characters if needed.
    MAX_CHAT_TITLE_LENGTH = 50  # Maximum length for auto-generated chat titles (UI/display limit)

    # RAG Configuration
    RAG_CONTEXT_LIMIT = 5  # Number of relevant messages to retrieve for context

    def __init__(self, embedding_client: EmbeddingClient | None = None):
        self.client = ClaudeAIClient()
        settings = get_settings()

        # Use provided embedding client or create default OpenAI client if API key is available
        if embedding_client:
            self.embedding_client = embedding_client
        elif settings.openai_api_key:
            self.embedding_client = OpenAIEmbeddingClient(settings.openai_api_key)
        else:
            self.embedding_client = None
            logger.warning("No OpenAI API key configured - RAG functionality will be disabled")

        # Initialize RAG service
        self.rag_service = RagService(embedding_client=self.embedding_client)

    async def _get_conversation_summary(
        self, db: AsyncSession, conversation_type: str, conversation_id: int
    ) -> ConversationSummary | None:
        """Fetch an existing conversation summary that has a last_message_id set."""
        result = await db.execute(
            select(ConversationSummary).where(
                ConversationSummary.conversation_type == conversation_type,
                ConversationSummary.conversation_id == conversation_id,
                ConversationSummary.last_message_id.isnot(None),
            )
        )
        return result.scalar_one_or_none()

    async def send_message(
        self,
        db: AsyncSession,
        insight_id: int,
        user_id: int,
        user_message: str,
        passage_text: str,
        passage_reference: str,
        insight_context: dict,
    ) -> str | None:
        """
        Send a message in the chat and get AI response.

        Args:
            db: Database session
            insight_id: ID of the insight this chat belongs to
            user_id: ID of the user sending the message
            user_message: The user's message
            passage_text: The Bible passage text
            passage_reference: The Bible passage reference
            insight_context: The original insights (historical, theological, practical)

        Returns:
            The AI's response message
        """
        # Get previous chat history for this user
        chat_history = await self.get_chat_messages(db, insight_id, user_id)

        # Get enhanced RAG context from past conversations
        rag_context_text = ""
        if self.embedding_client:
            try:
                enhanced_contexts = await self.rag_service.get_enhanced_rag_context(
                    db=db,
                    user_id=user_id,
                    query=user_message,
                    conversation_type="insight",
                    ai_client=self.client,
                    current_conversation_id=insight_id,
                )
                rag_context_text = self.rag_service.format_enhanced_rag_context(enhanced_contexts)
                logger.info(
                    f"Retrieved {len(enhanced_contexts)} enhanced RAG contexts "
                    f"for insight {insight_id} (user {user_id})"
                )
            except Exception as e:
                logger.warning(f"Failed to retrieve enhanced RAG context for user {user_id}: {e}")
                # Continue without RAG context

        # Generate AI response with context
        ai_response = await self.client.generate_chat_response(
            user_message=user_message,
            passage_text=passage_text,
            passage_reference=passage_reference,
            insight_context=insight_context,
            chat_history=chat_history,
            rag_context=rag_context_text,
        )

        if not ai_response:
            return None

        # Save user message and AI response in a transaction
        try:
            # Generate embeddings for both messages if embedding client is available
            user_embedding = None
            ai_embedding = None

            if self.embedding_client:
                try:
                    user_embedding = await self.embedding_client.get_embedding(user_message)
                    ai_embedding = await self.embedding_client.get_embedding(ai_response)
                except Exception as e:
                    logger.error(
                        f"Error generating embeddings for insight {insight_id}, user {user_id}: {e}",
                        exc_info=True,
                    )
                    # Continue without embeddings rather than failing the entire operation

            # Save user message
            user_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="user",
                content=user_message,
                embedding=user_embedding,
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="assistant",
                content=ai_response,
                embedding=ai_embedding,
            )
            db.add(ai_msg)

            # No commit needed - handled by get_db() dependency
        except Exception as e:
            logger.error(
                f"Error saving chat messages for insight {insight_id}, user {user_id}: {e}",
                exc_info=True,
            )
            # Re-raise to trigger automatic rollback
            raise

        return ai_response

    async def get_chat_messages(
        self, db: AsyncSession, insight_id: int, user_id: int, after_message_id: int | None = None
    ) -> list[ChatMessage]:
        """Get all chat messages for an insight for a specific user."""
        result = await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.insight_id == insight_id,
                ChatMessage.user_id == user_id,
                ChatMessage.id > after_message_id if after_message_id else true(),
            )
            .order_by(ChatMessage.created_at)
        )
        return list(result.scalars().all())

    async def clear_chat_messages(self, db: AsyncSession, insight_id: int, user_id: int) -> int:
        """Clear all chat messages for an insight for a specific user."""
        result = await db.execute(
            delete(ChatMessage).where(ChatMessage.insight_id == insight_id, ChatMessage.user_id == user_id)
        )
        return result.rowcount

    async def create_standalone_chat(
        self,
        db: AsyncSession,
        user_id: int,
        user_message: str,
        passage_text: str | None = None,
        passage_reference: str | None = None,
    ) -> int | None:
        """
        Create a new standalone chat session and send the first message.

        Args:
            db: Database session
            user_id: ID of the user creating the chat
            user_message: The user's first message
            passage_text: Optional Bible passage text for context
            passage_reference: Optional Bible passage reference

        Returns:
            The chat ID if successful, None otherwise
        """
        # Create the chat session
        chat = StandaloneChat(
            user_id=user_id,
            passage_text=passage_text,
            passage_reference=passage_reference,
        )
        db.add(chat)
        await db.flush()  # Flush to get the chat ID

        # Generate AI response (no RAG context for first message, no history to search)
        ai_response = await self.client.generate_standalone_chat_response(
            user_message=user_message,
            passage_text=passage_text,
            passage_reference=passage_reference,
            chat_history=[],
            rag_context="",
        )

        if not ai_response:
            raise ValueError("Failed to generate AI response")

        # Generate title from the first message
        title = user_message[: self.MAX_CHAT_TITLE_LENGTH] + (
            "..." if len(user_message) > self.MAX_CHAT_TITLE_LENGTH else ""
        )
        chat.title = title

        try:
            # Generate embeddings for both messages if embedding client is available
            user_embedding = None
            ai_embedding = None

            if self.embedding_client:
                try:
                    user_embedding = await self.embedding_client.get_embedding(user_message)
                    ai_embedding = await self.embedding_client.get_embedding(ai_response)
                except Exception as e:
                    logger.error(
                        f"Error generating embeddings for standalone chat, user {user_id}: {e}",
                        exc_info=True,
                    )
                    # Continue without embeddings

            # Save user message
            user_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="user",
                content=user_message,
                embedding=user_embedding,
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="assistant",
                content=ai_response,
                embedding=ai_embedding,
            )
            db.add(ai_msg)

            # No commit needed - handled by get_db() dependency
            return chat.id
        except Exception as e:
            logger.error(f"Error creating standalone chat for user {user_id}: {e}", exc_info=True)
            raise

    async def create_standalone_chat_stream(
        self,
        db: AsyncSession,
        user_id: int,
        user_message: str,
        passage_text: str | None = None,
        passage_reference: str | None = None,
    ):
        """
        Create a new standalone chat session and stream the first message.

        Args:
            db: Database session
            user_id: ID of the user creating the chat
            user_message: The user's first message
            passage_text: Optional Bible passage text for context
            passage_reference: Optional Bible passage reference

        Yields:
            Tuple[str, Optional[str]]: (text_chunk, stop_reason)
                - text_chunk: Text content from the stream or special markers
                - stop_reason: None for intermediate chunks, set to stop reason on completion
        """
        # Create the chat session
        chat = StandaloneChat(
            user_id=user_id,
            passage_text=passage_text,
            passage_reference=passage_reference,
        )
        db.add(chat)
        await db.flush()  # Flush to get the chat ID

        # Generate title from the first message
        title = user_message[: self.MAX_CHAT_TITLE_LENGTH] + (
            "..." if len(user_message) > self.MAX_CHAT_TITLE_LENGTH else ""
        )
        chat.title = title

        # Buffer the complete response as we stream
        complete_response = ""
        stop_reason = None

        try:
            # Stream from AI client (no RAG context for first message)
            async for (
                chunk,
                chunk_stop_reason,
            ) in self.client.generate_standalone_chat_response_stream(
                user_message=user_message,
                passage_text=passage_text,
                passage_reference=passage_reference,
                chat_history=[],
                rag_context="",
            ):
                if chunk:  # Only yield non-empty chunks
                    complete_response += chunk
                    yield (chunk, None)
                if chunk_stop_reason:  # Final chunk with stop_reason
                    stop_reason = chunk_stop_reason

            # Save to database atomically after streaming completes
            # Generate embeddings for both messages if embedding client is available
            user_embedding = None
            ai_embedding = None

            if self.embedding_client:
                try:
                    user_embedding = await self.embedding_client.get_embedding(user_message)
                    ai_embedding = await self.embedding_client.get_embedding(complete_response)
                except Exception as e:
                    logger.error(
                        f"Error generating embeddings for standalone chat stream, user {user_id}: {e}",
                        exc_info=True,
                    )
                    # Continue without embeddings

            # Save user message with explicit timestamp
            now = datetime.now(UTC)
            user_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="user",
                content=user_message,
                embedding=user_embedding,
                created_at=now,
            )
            db.add(user_msg)

            # Save AI response with slightly later timestamp to ensure correct ordering
            ai_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="assistant",
                content=complete_response,
                was_truncated=(stop_reason == "max_tokens"),
                embedding=ai_embedding,
                created_at=now + timedelta(microseconds=1),
            )
            db.add(ai_msg)

            # Commit to save chat and messages
            await db.commit()

            # Yield the chat_id as a special marker (maintaining backward compatibility)
            yield (f"{CHAT_ID_MARKER}{chat.id}", None)

            # Yield final chunk with stop_reason
            yield ("", stop_reason)
        except Exception as e:
            logger.error(
                f"Error creating standalone chat stream for user {user_id}: {e}",
                exc_info=True,
            )
            raise

    async def send_standalone_message(
        self, db: AsyncSession, chat_id: int, user_id: int, user_message: str
    ) -> str | None:
        """
        Send a message in a standalone chat and get AI response.

        Args:
            db: Database session
            chat_id: ID of the chat session
            user_id: ID of the user sending the message
            user_message: The user's message

        Returns:
            The AI's response message
        """
        # Get the chat session and verify it belongs to the user
        result = await db.execute(
            select(StandaloneChat).where(StandaloneChat.id == chat_id, StandaloneChat.user_id == user_id)
        )
        chat = result.scalar_one_or_none()
        if not chat:
            return None

        # Get previous chat history
        chat_history = await self.get_standalone_chat_messages(db, chat_id, user_id)

        # Get enhanced RAG context from past conversations
        rag_context_text = ""
        if self.embedding_client:
            try:
                enhanced_contexts = await self.rag_service.get_enhanced_rag_context(
                    db=db,
                    user_id=user_id,
                    query=user_message,
                    conversation_type="standalone",
                    ai_client=self.client,
                    current_conversation_id=chat_id,
                )
                rag_context_text = self.rag_service.format_enhanced_rag_context(enhanced_contexts)
                logger.info(
                    f"Retrieved {len(enhanced_contexts)} enhanced RAG contexts "
                    f"for standalone chat {chat_id} (user {user_id})"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to retrieve enhanced RAG context for standalone chat (user {user_id}): {e}"
                )
                # Continue without RAG context

        # Generate AI response
        ai_response = await self.client.generate_standalone_chat_response(
            user_message=user_message,
            passage_text=chat.passage_text,
            passage_reference=chat.passage_reference,
            chat_history=chat_history,
            rag_context=rag_context_text,
        )

        if not ai_response:
            return None

        try:
            # Generate embeddings for both messages if embedding client is available
            user_embedding = None
            ai_embedding = None

            if self.embedding_client:
                try:
                    user_embedding = await self.embedding_client.get_embedding(user_message)
                    ai_embedding = await self.embedding_client.get_embedding(ai_response)
                except Exception as e:
                    logger.error(
                        f"Error generating embeddings for chat {chat_id}, user {user_id}: {e}",
                        exc_info=True,
                    )
                    # Continue without embeddings

            # Save user message
            user_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="user",
                content=user_message,
                embedding=user_embedding,
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="assistant",
                content=ai_response,
                embedding=ai_embedding,
            )
            db.add(ai_msg)

            # Update chat's updated_at timestamp
            chat.updated_at = func.now()

            # No commit needed - handled by get_db() dependency
        except Exception as e:
            logger.error(
                f"Error sending standalone chat message for chat {chat_id}, user {user_id}: {e}",
                exc_info=True,
            )
            raise

        return ai_response

    async def get_standalone_chat_messages(
        self, db: AsyncSession, chat_id: int, user_id: int, after_message_id: int | None = None
    ) -> list[StandaloneChatMessage]:
        """Get all messages for a standalone chat for a specific user."""
        # Verify the chat belongs to the user
        result = await db.execute(
            select(StandaloneChat).where(StandaloneChat.id == chat_id, StandaloneChat.user_id == user_id)
        )
        chat = result.scalar_one_or_none()

        if not chat:
            return []

        result = await db.execute(
            select(StandaloneChatMessage)
            .where(
                StandaloneChatMessage.chat_id == chat_id,
                StandaloneChatMessage.id > after_message_id if after_message_id else true(),
            )
            .order_by(StandaloneChatMessage.created_at)
        )
        return list(result.scalars().all())

    async def get_standalone_chats(
        self, db: AsyncSession, user_id: int, limit: int = 50
    ) -> list[StandaloneChat]:
        """Get all standalone chat sessions for a specific user."""
        result = await db.execute(
            select(StandaloneChat)
            .where(StandaloneChat.user_id == user_id)
            .order_by(StandaloneChat.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_standalone_chat(self, db: AsyncSession, chat_id: int, user_id: int) -> bool:
        """Delete a standalone chat session for a specific user."""
        result = await db.execute(
            delete(StandaloneChat).where(StandaloneChat.id == chat_id, StandaloneChat.user_id == user_id)
        )
        return result.rowcount > 0

    async def send_message_stream(
        self,
        db: AsyncSession,
        insight_id: int,
        user_id: int,
        user_message: str,
        passage_text: str,
        passage_reference: str,
        insight_context: dict,
        background_tasks: BackgroundTasks | None = None,
    ):
        """
        Stream chat response and save to database after completion.

        Args:
            db: Database session
            insight_id: ID of the insight this chat belongs to
            user_id: ID of the user sending the message
            user_message: The user's message
            passage_text: The Bible passage text
            passage_reference: The Bible passage reference
            insight_context: The original insights (historical, theological, practical)
            background_tasks: Optional FastAPI BackgroundTasks for async summarization

        Yields:
            Tuple[str, Optional[str]]: (text_chunk, stop_reason)
                - text_chunk: Text content from the stream
                - stop_reason: None for intermediate chunks, set to stop reason on final chunk
        """
        settings = get_settings()
        conv_summary = await self._get_conversation_summary(db, "insight", insight_id)
        summary_text = conv_summary.summary_text if conv_summary else ""
        after_id = conv_summary.last_message_id if conv_summary else None

        # Get previous chat history for this user (filtered by summary cutoff if present)
        chat_history = await self.get_chat_messages(db, insight_id, user_id, after_message_id=after_id)

        # Fallback tail-truncation if history still exceeds the char limit
        total_chars = sum(len(m.content) for m in chat_history)
        if total_chars > settings.conversation_history_char_limit:
            chat_history = chat_history[-50:]

        # Get enhanced RAG context from past conversations
        rag_context_text = ""
        if self.embedding_client:
            try:
                enhanced_contexts = await self.rag_service.get_enhanced_rag_context(
                    db=db,
                    user_id=user_id,
                    query=user_message,
                    conversation_type="insight",
                    ai_client=self.client,
                    current_conversation_id=insight_id,
                )
                rag_context_text = self.rag_service.format_enhanced_rag_context(enhanced_contexts)
                logger.info(
                    f"Retrieved {len(enhanced_contexts)} enhanced RAG contexts "
                    f"for streaming insight {insight_id} (user {user_id})"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to retrieve enhanced RAG context for streaming chat (user {user_id}): {e}"
                )
                # Continue without RAG context

        # Buffer the complete response as we stream
        complete_response = ""
        stop_reason = None

        try:
            # Stream from AI client
            async for (
                chunk,
                chunk_stop_reason,
            ) in self.client.generate_chat_response_stream(
                user_message=user_message,
                passage_text=passage_text,
                passage_reference=passage_reference,
                insight_context=insight_context,
                chat_history=chat_history,
                rag_context=rag_context_text,
                conversation_summary=summary_text,
            ):
                if chunk:  # Only yield non-empty chunks
                    complete_response += chunk
                    yield (chunk, None)
                if chunk_stop_reason:  # Final chunk with stop_reason
                    stop_reason = chunk_stop_reason

            # Save to database atomically after streaming completes
            # Generate embeddings for both messages if embedding client is available
            user_embedding = None
            ai_embedding = None

            if self.embedding_client:
                try:
                    user_embedding = await self.embedding_client.get_embedding(user_message)
                    ai_embedding = await self.embedding_client.get_embedding(complete_response)
                except Exception as e:
                    logger.error(
                        f"Error generating embeddings for insight {insight_id}, user {user_id}: {e}",
                        exc_info=True,
                    )
                    # Continue without embeddings

            # Save user message with explicit timestamp
            now = datetime.now(UTC)
            user_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="user",
                content=user_message,
                embedding=user_embedding,
                created_at=now,
            )
            db.add(user_msg)

            # Save AI response with slightly later timestamp to ensure correct ordering
            ai_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="assistant",
                content=complete_response,
                was_truncated=(stop_reason == "max_tokens"),
                embedding=ai_embedding,
                created_at=now + timedelta(microseconds=1),
            )
            db.add(ai_msg)

            # Commit to save messages
            await db.commit()

            # Trigger background summarization if total history exceeds the char limit
            full_history_chars = (
                sum(len(m.content) for m in chat_history) + len(complete_response) + len(user_message)
            )
            if full_history_chars > settings.conversation_history_char_limit and background_tasks:
                logger.info(f"Triggering conversation summarization for insight {insight_id}")
                background_tasks.add_task(self._run_summarization, "insight", insight_id, user_id)

            # Yield final chunk with stop_reason
            yield ("", stop_reason)
        except Exception as e:
            logger.error(
                f"Error streaming chat messages for insight {insight_id}, user {user_id}: {e}",
                exc_info=True,
            )
            raise

    async def send_standalone_message_stream(
        self,
        db: AsyncSession,
        chat_id: int,
        user_id: int,
        user_message: str,
        background_tasks: BackgroundTasks | None = None,
    ):
        """
        Stream standalone chat response and save to database after completion.

        Args:
            db: Database session
            chat_id: ID of the chat session
            user_id: ID of the user sending the message
            user_message: The user's message
            background_tasks: Optional FastAPI BackgroundTasks for async summarization

        Yields:
            Tuple[str, Optional[str]]: (text_chunk, stop_reason)
                - text_chunk: Text content from the stream
                - stop_reason: None for intermediate chunks, set to stop reason on final chunk
        """
        settings = get_settings()
        conv_summary = await self._get_conversation_summary(db, "standalone", chat_id)
        summary_text = conv_summary.summary_text if conv_summary else ""
        after_id = conv_summary.last_message_id if conv_summary else None

        # Get the chat session and verify it belongs to the user
        result = await db.execute(
            select(StandaloneChat).where(StandaloneChat.id == chat_id, StandaloneChat.user_id == user_id)
        )
        chat = result.scalar_one_or_none()
        if not chat:
            raise ValueError(f"Chat {chat_id} not found for user {user_id}")

        # Get previous chat history (filtered by summary cutoff if present)
        chat_history = await self.get_standalone_chat_messages(
            db, chat_id, user_id, after_message_id=after_id
        )

        # Fallback tail-truncation if history still exceeds the char limit
        total_chars = sum(len(m.content) for m in chat_history)
        if total_chars > settings.conversation_history_char_limit:
            chat_history = chat_history[-50:]

        # Get enhanced RAG context from past conversations
        rag_context_text = ""
        if self.embedding_client:
            try:
                enhanced_contexts = await self.rag_service.get_enhanced_rag_context(
                    db=db,
                    user_id=user_id,
                    query=user_message,
                    conversation_type="standalone",
                    ai_client=self.client,
                    current_conversation_id=chat_id,
                )
                rag_context_text = self.rag_service.format_enhanced_rag_context(enhanced_contexts)
                logger.info(
                    f"Retrieved {len(enhanced_contexts)} enhanced RAG contexts "
                    f"for streaming standalone chat {chat_id} (user {user_id})"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to retrieve enhanced RAG context "
                    f"for streaming standalone chat (user {user_id}): {e}"
                )
                # Continue without RAG context

        # Buffer the complete response as we stream
        complete_response = ""
        stop_reason = None

        try:
            # Stream from AI client
            async for (
                chunk,
                chunk_stop_reason,
            ) in self.client.generate_standalone_chat_response_stream(
                user_message=user_message,
                passage_text=chat.passage_text,
                passage_reference=chat.passage_reference,
                chat_history=chat_history,
                rag_context=rag_context_text,
                conversation_summary=summary_text,
            ):
                if chunk:  # Only yield non-empty chunks
                    complete_response += chunk
                    yield (chunk, None)
                if chunk_stop_reason:  # Final chunk with stop_reason
                    stop_reason = chunk_stop_reason

            # Save to database atomically after streaming completes
            # Generate embeddings for both messages if embedding client is available
            user_embedding = None
            ai_embedding = None

            if self.embedding_client:
                try:
                    user_embedding = await self.embedding_client.get_embedding(user_message)
                    ai_embedding = await self.embedding_client.get_embedding(complete_response)
                except Exception as e:
                    logger.error(
                        f"Error generating embeddings for chat {chat_id}, user {user_id}: {e}",
                        exc_info=True,
                    )
                    # Continue without embeddings

            # Save user message with explicit timestamp
            now = datetime.now(UTC)
            user_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="user",
                content=user_message,
                embedding=user_embedding,
                created_at=now,
            )
            db.add(user_msg)

            # Save AI response with slightly later timestamp to ensure correct ordering
            ai_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="assistant",
                content=complete_response,
                was_truncated=(stop_reason == "max_tokens"),
                embedding=ai_embedding,
                created_at=now + timedelta(microseconds=1),
            )
            db.add(ai_msg)

            # Update chat's updated_at timestamp
            chat.updated_at = func.now()

            # Commit to save messages
            await db.commit()

            # Trigger background summarization if total history exceeds the char limit
            full_history_chars = (
                sum(len(m.content) for m in chat_history) + len(complete_response) + len(user_message)
            )
            if full_history_chars > settings.conversation_history_char_limit and background_tasks:
                logger.info(f"Triggering conversation summarization for standalone chat {chat_id}")
                background_tasks.add_task(self._run_summarization, "standalone", chat_id, user_id)

            # Yield final chunk with stop_reason
            yield ("", stop_reason)
        except Exception as e:
            logger.error(
                f"Error streaming standalone chat message for chat {chat_id}, user {user_id}: {e}",
                exc_info=True,
            )
            raise

    async def _run_summarization(self, conversation_type: str, conversation_id: int, user_id: int) -> None:
        """
        Background task: summarize the first 80% of a conversation and store/update the
        ConversationSummary row so that future loads can start after last_message_id.
        """
        async with AsyncSessionLocal() as db:
            try:
                # Fetch all messages (no after_message_id — we want everything)
                if conversation_type == "insight":
                    messages = await self.get_chat_messages(db, conversation_id, user_id)
                else:
                    messages = await self.get_standalone_chat_messages(db, conversation_id, user_id)

                if not messages:
                    return

                # Summarize the first 80% of messages
                cutoff = max(1, int(len(messages) * 0.8))
                to_summarize = messages[:cutoff]
                last_msg = to_summarize[-1]

                conversation_text = "\n".join(
                    f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}" for m in to_summarize
                )

                summary_text = await self.client.generate_truncation_summary(conversation_text)
                if not summary_text:
                    logger.warning(
                        f"Failed to generate truncation summary for {conversation_type} {conversation_id}"
                    )
                    return

                # Upsert ConversationSummary
                result = await db.execute(
                    select(ConversationSummary).where(
                        ConversationSummary.conversation_type == conversation_type,
                        ConversationSummary.conversation_id == conversation_id,
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.summary_text = summary_text
                    existing.last_message_id = last_msg.id
                    existing.message_count = len(to_summarize)
                else:
                    db.add(
                        ConversationSummary(
                            conversation_type=conversation_type,
                            conversation_id=conversation_id,
                            summary_text=summary_text,
                            last_message_id=last_msg.id,
                            message_count=len(to_summarize),
                        )
                    )

                await db.commit()
                logger.info(
                    f"Saved truncation summary for {conversation_type} {conversation_id}, "
                    f"last_message_id={last_msg.id}"
                )
            except Exception as e:
                logger.error(f"Error in _run_summarization: {e}", exc_info=True)

    async def startup_summarize_long_conversations(self) -> None:
        """
        One-shot startup scan: find all conversations over the char limit that have no
        truncation summary yet and summarize them sequentially.
        """
        settings = get_settings()
        limit = settings.conversation_history_char_limit

        async with AsyncSessionLocal() as db:
            already_insight = select(ConversationSummary.conversation_id).where(
                ConversationSummary.conversation_type == "insight",
                ConversationSummary.last_message_id.isnot(None),
            )
            insight_rows = (
                await db.execute(
                    select(
                        ChatMessage.insight_id,
                        ChatMessage.user_id,
                        func.sum(func.length(ChatMessage.content)).label("total_chars"),
                    )
                    .where(not_(ChatMessage.insight_id.in_(already_insight)))
                    .group_by(ChatMessage.insight_id, ChatMessage.user_id)
                    .having(func.sum(func.length(ChatMessage.content)) > limit)
                )
            ).all()

            already_standalone = select(ConversationSummary.conversation_id).where(
                ConversationSummary.conversation_type == "standalone",
                ConversationSummary.last_message_id.isnot(None),
            )
            standalone_rows = (
                await db.execute(
                    select(
                        StandaloneChatMessage.chat_id,
                        StandaloneChat.user_id,
                        func.sum(func.length(StandaloneChatMessage.content)).label("total_chars"),
                    )
                    .join(StandaloneChat, StandaloneChat.id == StandaloneChatMessage.chat_id)
                    .where(not_(StandaloneChatMessage.chat_id.in_(already_standalone)))
                    .group_by(StandaloneChatMessage.chat_id, StandaloneChat.user_id)
                    .having(func.sum(func.length(StandaloneChatMessage.content)) > limit)
                )
            ).all()

        total = len(insight_rows) + len(standalone_rows)
        if total == 0:
            logger.info("Startup summarization scan: no conversations need summarizing")
            return

        logger.info(
            f"Startup summarization scan: {total} conversations to summarize "
            f"({len(insight_rows)} insight, {len(standalone_rows)} standalone)"
        )

        for insight_id, user_id, total_chars in insight_rows:
            logger.info(f"Startup: summarizing insight {insight_id} ({total_chars} chars)")
            await self._run_summarization("insight", insight_id, user_id)

        for chat_id, user_id, total_chars in standalone_rows:
            logger.info(f"Startup: summarizing standalone chat {chat_id} ({total_chars} chars)")
            await self._run_summarization("standalone", chat_id, user_id)

        logger.info("Startup summarization scan: complete")
