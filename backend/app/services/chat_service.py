import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.clients.claude_client import ClaudeAIClient
from app.models.models import ChatMessage, StandaloneChat, StandaloneChatMessage

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

    def __init__(self):
        self.client = ClaudeAIClient()
    
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
            # Save user message
            user_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="user",
                content=user_message
            )
            db.add(user_msg)
            
            # Save AI response
            ai_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="assistant",
                content=ai_response
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
            # Save user message
            user_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="user",
                content=user_message
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="assistant",
                content=ai_response
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
            Text tokens as they arrive from Claude, then chat_id as final event
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

        try:
            # Stream from AI client
            async for token in self.client.generate_standalone_chat_response_stream(
                user_message=user_message,
                passage_text=passage_text,
                passage_reference=passage_reference,
                chat_history=[]
            ):
                complete_response += token
                yield token

            # Save to database atomically after streaming completes
            # Save user message
            user_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="user",
                content=user_message
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = StandaloneChatMessage(
                chat_id=chat.id,
                role="assistant",
                content=complete_response
            )
            db.add(ai_msg)

            db.commit()

            # Yield the chat_id as a special marker at the end
            yield f"{CHAT_ID_MARKER}{chat.id}"
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
            # Save user message
            user_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="user",
                content=user_message
            )
            db.add(user_msg)
            
            # Save AI response
            ai_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="assistant",
                content=ai_response
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
            Text tokens as they arrive from Claude
        """
        # Get previous chat history for this user
        chat_history = self.get_chat_messages(db, insight_id, user_id)

        # Buffer the complete response as we stream
        complete_response = ""

        try:
            # Stream from AI client
            async for token in self.client.generate_chat_response_stream(
                user_message=user_message,
                passage_text=passage_text,
                passage_reference=passage_reference,
                insight_context=insight_context,
                chat_history=chat_history
            ):
                complete_response += token
                yield token

            # Save to database atomically after streaming completes
            # Save user message
            user_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="user",
                content=user_message
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = ChatMessage(
                insight_id=insight_id,
                user_id=user_id,
                role="assistant",
                content=complete_response
            )
            db.add(ai_msg)

            db.commit()
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
            Text tokens as they arrive from Claude
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

        try:
            # Stream from AI client
            async for token in self.client.generate_standalone_chat_response_stream(
                user_message=user_message,
                passage_text=chat.passage_text,
                passage_reference=chat.passage_reference,
                chat_history=chat_history
            ):
                complete_response += token
                yield token

            # Save to database atomically after streaming completes
            # Save user message
            user_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="user",
                content=user_message
            )
            db.add(user_msg)

            # Save AI response
            ai_msg = StandaloneChatMessage(
                chat_id=chat_id,
                role="assistant",
                content=complete_response
            )
            db.add(ai_msg)

            # Update chat's updated_at timestamp
            chat.updated_at = func.now()

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error streaming standalone chat message for chat {chat_id}, user {user_id}: {e}", exc_info=True)
            raise
