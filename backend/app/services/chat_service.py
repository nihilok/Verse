import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import select
from app.clients.claude_client import ClaudeAIClient
from app.clients.openai_embedding_client import OpenAIEmbeddingClient
from app.clients.embedding_client import EmbeddingClient
from app.models.models import ChatMessage, StandaloneChat, StandaloneChatMessage
from app.core.config import get_settings

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

    def __init__(self, embedding_client: Optional[EmbeddingClient] = None):
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

    async def _get_relevant_context(
        self,
        db: Session,
        user_id: int,
        query: str,
        limit: int = RAG_CONTEXT_LIMIT
    ) -> List[ChatMessage]:
        """
        Retrieve the most semantically similar messages for a specific user.

        This implements RAG (Retrieval-Augmented Generation) by finding relevant
        historical context from the user's chat history using vector similarity search.

        Args:
            db: Database session
            user_id: User ID to filter messages (ensures data privacy)
            query: The query text to search for similar messages
            limit: Maximum number of relevant messages to return

        Returns:
            List of ChatMessage objects, ordered by relevance (most similar first)
        """
        if not self.embedding_client:
            return []

        try:
            # Generate embedding for the current query
            query_vector = await self.embedding_client.get_embedding(query)

            # Semantic search with metadata filtering
            # The <=> operator represents Cosine Distance in pgvector
            # We filter by user_id first for privacy and performance
            stmt = (
                select(ChatMessage)
                .filter(
                    ChatMessage.user_id == user_id,
                    ChatMessage.embedding.isnot(None)  # Only consider messages with embeddings
                )
                .order_by(ChatMessage.embedding.cosine_distance(query_vector))
                .limit(limit)
            )

            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving relevant context for user {user_id}: {e}", exc_info=True)
            return []

    async def _get_relevant_standalone_context(
        self,
        db: Session,
        user_id: int,
        query: str,
        limit: int = RAG_CONTEXT_LIMIT
    ) -> List[StandaloneChatMessage]:
        """
        Retrieve the most semantically similar standalone chat messages for a specific user.

        Args:
            db: Database session
            user_id: User ID to filter messages (ensures data privacy)
            query: The query text to search for similar messages
            limit: Maximum number of relevant messages to return

        Returns:
            List of StandaloneChatMessage objects, ordered by relevance
        """
        if not self.embedding_client:
            return []

        try:
            # Generate embedding for the current query
            query_vector = await self.embedding_client.get_embedding(query)

            # Semantic search across standalone messages
            # Join with StandaloneChat to filter by user_id
            stmt = (
                select(StandaloneChatMessage)
                .join(StandaloneChat)
                .filter(
                    StandaloneChat.user_id == user_id,
                    StandaloneChatMessage.embedding.isnot(None)
                )
                .order_by(StandaloneChatMessage.embedding.cosine_distance(query_vector))
                .limit(limit)
            )

            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving relevant standalone context for user {user_id}: {e}", exc_info=True)
            return []

    async def send_message(
        self,
        db: Session,
        insight_id: int,
        user_id: int,
        user_message: str,
        passage_text: str,
        passage_reference: str,
        insight_context: dict
    ) -> Optional[str]:
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
        chat_history = self.get_chat_messages(db, insight_id, user_id)
        
        # Generate AI response with context
        ai_response = await self.client.generate_chat_response(
            user_message=user_message,
            passage_text=passage_text,
            passage_reference=passage_reference,
            insight_context=insight_context,
            chat_history=chat_history
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
                    logger.error(f"Error generating embeddings for insight {insight_id}, user {user_id}: {e}", exc_info=True)
                    # Continue without embeddings rather than failing the entire operation

            # Save user message
            user_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="user",
                content=user_message,
                embedding=user_embedding
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="assistant",
                content=ai_response,
                embedding=ai_embedding
            )
            db.add(ai_msg)

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving chat messages for insight {insight_id}, user {user_id}: {e}", exc_info=True)
            # Return None to indicate failure even though we got an AI response
            return None
        
        return ai_response
    
    def get_chat_messages(
        self,
        db: Session,
        insight_id: int,
        user_id: int
    ) -> List[ChatMessage]:
        """Get all chat messages for an insight for a specific user."""
        return db.query(ChatMessage).filter(
            ChatMessage.insight_id == insight_id,
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.created_at).all()
    
    def clear_chat_messages(
        self,
        db: Session,
        insight_id: int,
        user_id: int
    ) -> int:
        """Clear all chat messages for an insight for a specific user."""
        count = db.query(ChatMessage).filter(
            ChatMessage.insight_id == insight_id,
            ChatMessage.user_id == user_id
        ).delete()
        db.commit()
        return count
    
    async def create_standalone_chat(
        self,
        db: Session,
        user_id: int,
        user_message: str,
        passage_text: Optional[str] = None,
        passage_reference: Optional[str] = None
    ) -> Optional[int]:
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
            passage_reference=passage_reference
        )
        db.add(chat)
        db.flush()  # Flush to get the chat ID

        # Generate AI response
        ai_response = await self.client.generate_standalone_chat_response(
            user_message=user_message,
            passage_text=passage_text,
            passage_reference=passage_reference,
            chat_history=[]
        )

        if not ai_response:
            db.rollback()
            return None

        # Generate title from the first message
        title = user_message[:self.MAX_CHAT_TITLE_LENGTH] + (
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
                    logger.error(f"Error generating embeddings for standalone chat, user {user_id}: {e}", exc_info=True)
                    # Continue without embeddings

            # Save user message
            user_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="user",
                content=user_message,
                embedding=user_embedding
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="assistant",
                content=ai_response,
                embedding=ai_embedding
            )
            db.add(ai_msg)

            db.commit()
            return chat.id
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating standalone chat for user {user_id}: {e}", exc_info=True)
            return None

    async def create_standalone_chat_stream(
        self,
        db: Session,
        user_id: int,
        user_message: str,
        passage_text: Optional[str] = None,
        passage_reference: Optional[str] = None
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
            passage_reference=passage_reference
        )
        db.add(chat)
        db.flush()  # Flush to get the chat ID

        # Generate title from the first message
        title = user_message[:self.MAX_CHAT_TITLE_LENGTH] + (
            "..." if len(user_message) > self.MAX_CHAT_TITLE_LENGTH else ""
        )
        chat.title = title

        # Buffer the complete response as we stream
        complete_response = ""
        stop_reason = None

        try:
            # Stream from AI client
            async for chunk, chunk_stop_reason in self.client.generate_standalone_chat_response_stream(
                user_message=user_message,
                passage_text=passage_text,
                passage_reference=passage_reference,
                chat_history=[]
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
                    logger.error(f"Error generating embeddings for standalone chat stream, user {user_id}: {e}", exc_info=True)
                    # Continue without embeddings

            # Save user message
            user_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="user",
                content=user_message,
                embedding=user_embedding
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="assistant",
                content=complete_response,
                was_truncated=(stop_reason == "max_tokens"),
                embedding=ai_embedding
            )
            db.add(ai_msg)

            db.commit()

            # Yield the chat_id as a special marker (maintaining backward compatibility)
            yield (f"{CHAT_ID_MARKER}{chat.id}", None)

            # Yield final chunk with stop_reason
            yield ("", stop_reason)
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating standalone chat stream for user {user_id}: {e}", exc_info=True)
            raise
    
    async def send_standalone_message(
        self,
        db: Session,
        chat_id: int,
        user_id: int,
        user_message: str
    ) -> Optional[str]:
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
        chat = db.query(StandaloneChat).filter(
            StandaloneChat.id == chat_id,
            StandaloneChat.user_id == user_id
        ).first()
        if not chat:
            return None
        
        # Get previous chat history
        chat_history = self.get_standalone_chat_messages(db, chat_id, user_id)
        
        # Generate AI response
        ai_response = await self.client.generate_standalone_chat_response(
            user_message=user_message,
            passage_text=chat.passage_text,
            passage_reference=chat.passage_reference,
            chat_history=chat_history
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
                    logger.error(f"Error generating embeddings for chat {chat_id}, user {user_id}: {e}", exc_info=True)
                    # Continue without embeddings

            # Save user message
            user_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="user",
                content=user_message,
                embedding=user_embedding
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="assistant",
                content=ai_response,
                embedding=ai_embedding
            )
            db.add(ai_msg)

            # Update chat's updated_at timestamp
            chat.updated_at = func.now()

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error sending standalone chat message for chat {chat_id}, user {user_id}: {e}", exc_info=True)
            return None
        
        return ai_response
    
    def get_standalone_chat_messages(
        self,
        db: Session,
        chat_id: int,
        user_id: int
    ) -> List[StandaloneChatMessage]:
        """Get all messages for a standalone chat for a specific user."""
        # Verify the chat belongs to the user
        chat = db.query(StandaloneChat).filter(
            StandaloneChat.id == chat_id,
            StandaloneChat.user_id == user_id
        ).first()
        
        if not chat:
            return []
        
        return db.query(StandaloneChatMessage).filter(
            StandaloneChatMessage.chat_id == chat_id
        ).order_by(StandaloneChatMessage.created_at).all()
    
    def get_standalone_chats(
        self,
        db: Session,
        user_id: int,
        limit: int = 50
    ) -> List[StandaloneChat]:
        """Get all standalone chat sessions for a specific user."""
        return db.query(StandaloneChat).filter(
            StandaloneChat.user_id == user_id
        ).order_by(
            StandaloneChat.updated_at.desc()
        ).limit(limit).all()
    
    def delete_standalone_chat(
        self,
        db: Session,
        chat_id: int,
        user_id: int
    ) -> bool:
        """Delete a standalone chat session for a specific user."""
        chat = db.query(StandaloneChat).filter(
            StandaloneChat.id == chat_id,
            StandaloneChat.user_id == user_id
        ).first()
        if chat:
            db.delete(chat)
            db.commit()
            return True
        return False

    async def send_message_stream(
        self,
        db: Session,
        insight_id: int,
        user_id: int,
        user_message: str,
        passage_text: str,
        passage_reference: str,
        insight_context: dict
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

        Yields:
            Tuple[str, Optional[str]]: (text_chunk, stop_reason)
                - text_chunk: Text content from the stream
                - stop_reason: None for intermediate chunks, set to stop reason on final chunk
        """
        # Get previous chat history for this user
        chat_history = self.get_chat_messages(db, insight_id, user_id)

        # Buffer the complete response as we stream
        complete_response = ""
        stop_reason = None

        try:
            # Stream from AI client
            async for chunk, chunk_stop_reason in self.client.generate_chat_response_stream(
                user_message=user_message,
                passage_text=passage_text,
                passage_reference=passage_reference,
                insight_context=insight_context,
                chat_history=chat_history
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
                    logger.error(f"Error generating embeddings for insight {insight_id}, user {user_id}: {e}", exc_info=True)
                    # Continue without embeddings

            # Save user message
            user_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="user",
                content=user_message,
                embedding=user_embedding
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="assistant",
                content=complete_response,
                was_truncated=(stop_reason == "max_tokens"),
                embedding=ai_embedding
            )
            db.add(ai_msg)

            db.commit()

            # Yield final chunk with stop_reason
            yield ("", stop_reason)
        except Exception as e:
            db.rollback()
            logger.error(f"Error streaming chat messages for insight {insight_id}, user {user_id}: {e}", exc_info=True)
            raise

    async def send_standalone_message_stream(
        self,
        db: Session,
        chat_id: int,
        user_id: int,
        user_message: str
    ):
        """
        Stream standalone chat response and save to database after completion.

        Args:
            db: Database session
            chat_id: ID of the chat session
            user_id: ID of the user sending the message
            user_message: The user's message

        Yields:
            Tuple[str, Optional[str]]: (text_chunk, stop_reason)
                - text_chunk: Text content from the stream
                - stop_reason: None for intermediate chunks, set to stop reason on final chunk
        """
        # Get the chat session and verify it belongs to the user
        chat = db.query(StandaloneChat).filter(
            StandaloneChat.id == chat_id,
            StandaloneChat.user_id == user_id
        ).first()
        if not chat:
            raise ValueError(f"Chat {chat_id} not found for user {user_id}")

        # Get previous chat history
        chat_history = self.get_standalone_chat_messages(db, chat_id, user_id)

        # Buffer the complete response as we stream
        complete_response = ""
        stop_reason = None

        try:
            # Stream from AI client
            async for chunk, chunk_stop_reason in self.client.generate_standalone_chat_response_stream(
                user_message=user_message,
                passage_text=chat.passage_text,
                passage_reference=chat.passage_reference,
                chat_history=chat_history
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
                    logger.error(f"Error generating embeddings for chat {chat_id}, user {user_id}: {e}", exc_info=True)
                    # Continue without embeddings

            # Save user message
            user_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="user",
                content=user_message,
                embedding=user_embedding
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="assistant",
                content=complete_response,
                was_truncated=(stop_reason == "max_tokens"),
                embedding=ai_embedding
            )
            db.add(ai_msg)

            # Update chat's updated_at timestamp
            chat.updated_at = func.now()

            db.commit()

            # Yield final chunk with stop_reason
            yield ("", stop_reason)
        except Exception as e:
            db.rollback()
            logger.error(f"Error streaming standalone chat message for chat {chat_id}, user {user_id}: {e}", exc_info=True)
            raise
