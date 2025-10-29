from typing import Optional, List
from sqlalchemy.orm import Session
from app.clients.claude_client import ClaudeAIClient
from app.models.models import ChatMessage, StandaloneChat, StandaloneChatMessage


class ChatService:
    """Service for chat operations with AI."""
    
    def __init__(self):
        self.client = ClaudeAIClient()
    
    async def send_message(
        self,
        db: Session,
        insight_id: int,
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
            user_message: The user's message
            passage_text: The Bible passage text
            passage_reference: The Bible passage reference
            insight_context: The original insights (historical, theological, practical)
        
        Returns:
            The AI's response message
        """
        # Get previous chat history
        chat_history = self.get_chat_messages(db, insight_id)
        
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
                role="user",
                content=user_message
            )
            db.add(user_msg)
            
            # Save AI response
            ai_msg = ChatMessage(
                insight_id=insight_id,
                role="assistant",
                content=ai_response
            )
            db.add(ai_msg)
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error saving chat messages: {e}")
            # Return None to indicate failure even though we got an AI response
            return None
        
        return ai_response
    
    def get_chat_messages(
        self,
        db: Session,
        insight_id: int
    ) -> List[ChatMessage]:
        """Get all chat messages for an insight."""
        return db.query(ChatMessage).filter(
            ChatMessage.insight_id == insight_id
        ).order_by(ChatMessage.created_at).all()
    
    def clear_chat_messages(
        self,
        db: Session,
        insight_id: int
    ) -> int:
        """Clear all chat messages for an insight."""
        count = db.query(ChatMessage).filter(
            ChatMessage.insight_id == insight_id
        ).delete()
        db.commit()
        return count
    
    async def create_standalone_chat(
        self,
        db: Session,
        user_message: str,
        passage_text: Optional[str] = None,
        passage_reference: Optional[str] = None
    ) -> Optional[int]:
        """
        Create a new standalone chat session and send the first message.
        
        Args:
            db: Database session
            user_message: The user's first message
            passage_text: Optional Bible passage text for context
            passage_reference: Optional Bible passage reference
        
        Returns:
            The chat ID if successful, None otherwise
        """
        # Create the chat session
        chat = StandaloneChat(
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
        
        # Generate title from the first message (first 50 chars)
        title = user_message[:50] + ("..." if len(user_message) > 50 else "")
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
            print(f"Error creating standalone chat: {e}")
            return None
    
    async def send_standalone_message(
        self,
        db: Session,
        chat_id: int,
        user_message: str
    ) -> Optional[str]:
        """
        Send a message in a standalone chat and get AI response.
        
        Args:
            db: Database session
            chat_id: ID of the chat session
            user_message: The user's message
        
        Returns:
            The AI's response message
        """
        # Get the chat session
        chat = db.query(StandaloneChat).filter(StandaloneChat.id == chat_id).first()
        if not chat:
            return None
        
        # Get previous chat history
        chat_history = self.get_standalone_chat_messages(db, chat_id)
        
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
            from sqlalchemy.sql import func
            chat.updated_at = func.now()
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error sending standalone chat message: {e}")
            return None
        
        return ai_response
    
    def get_standalone_chat_messages(
        self,
        db: Session,
        chat_id: int
    ) -> List[StandaloneChatMessage]:
        """Get all messages for a standalone chat."""
        return db.query(StandaloneChatMessage).filter(
            StandaloneChatMessage.chat_id == chat_id
        ).order_by(StandaloneChatMessage.created_at).all()
    
    def get_standalone_chats(
        self,
        db: Session,
        limit: int = 50
    ) -> List[StandaloneChat]:
        """Get all standalone chat sessions."""
        return db.query(StandaloneChat).order_by(
            StandaloneChat.updated_at.desc()
        ).limit(limit).all()
    
    def delete_standalone_chat(
        self,
        db: Session,
        chat_id: int
    ) -> bool:
        """Delete a standalone chat session."""
        chat = db.query(StandaloneChat).filter(StandaloneChat.id == chat_id).first()
        if chat:
            db.delete(chat)
            db.commit()
            return True
        return False
