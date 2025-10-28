from typing import Optional, List
from sqlalchemy.orm import Session
from app.clients.claude_client import ClaudeAIClient
from app.models.models import ChatMessage


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
