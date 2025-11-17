from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.models import User, SavedInsight, ChatMessage, StandaloneChat, StandaloneChatMessage, user_insights
import uuid


class UserService:
    """Service for managing anonymous users."""
    
    def get_or_create_user(self, db: Session, anonymous_id: Optional[str] = None) -> User:
        """
        Get an existing user by anonymous_id or create a new one.
        
        Args:
            db: Database session
            anonymous_id: Optional anonymous ID from cookie
        
        Returns:
            User instance
        """
        if anonymous_id:
            user = db.query(User).filter(User.anonymous_id == anonymous_id).first()
            if user:
                return user
        
        # Create new user with unique anonymous_id
        new_user = User(anonymous_id=str(uuid.uuid4()))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    def get_user_by_anonymous_id(self, db: Session, anonymous_id: str) -> Optional[User]:
        """Get a user by their anonymous ID."""
        return db.query(User).filter(User.anonymous_id == anonymous_id).first()
    
    def clear_user_data(self, db: Session, user_id: int) -> Dict[str, int]:
        """
        Clear all data for a user.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Dictionary with counts of deleted items
        """
        # Delete user-insight associations
        insight_count = db.execute(
            user_insights.delete().where(user_insights.c.user_id == user_id)
        ).rowcount
        
        # Delete chat messages (cascades from user relationship)
        chat_message_count = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).count()
        
        # Delete standalone chats (cascades will delete messages)
        standalone_chat_count = db.query(StandaloneChat).filter(StandaloneChat.user_id == user_id).count()
        
        # Delete the associations and records
        db.query(ChatMessage).filter(ChatMessage.user_id == user_id).delete()
        db.query(StandaloneChat).filter(StandaloneChat.user_id == user_id).delete()
        
        db.commit()
        
        return {
            "insights": insight_count,
            "chat_messages": chat_message_count,
            "standalone_chats": standalone_chat_count
        }
    
    def export_user_data(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Export all data for a user as JSON.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Dictionary containing all user data
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Get user's insights through the linking table
        insights_data = []
        for insight in user.insights:
            insights_data.append({
                "id": insight.id,
                "passage_reference": insight.passage_reference,
                "passage_text": insight.passage_text,
                "historical_context": insight.historical_context,
                "theological_significance": insight.theological_significance,
                "practical_application": insight.practical_application,
                "created_at": insight.created_at.isoformat() if insight.created_at else None
            })
        
        # Get user's chat messages
        chat_messages_data = []
        for msg in user.chat_messages:
            chat_messages_data.append({
                "insight_id": msg.insight_id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            })
        
        # Get user's standalone chats with messages
        standalone_chats_data = []
        for chat in user.standalone_chats:
            messages = []
            for msg in chat.messages:
                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                })
            
            standalone_chats_data.append({
                "title": chat.title,
                "passage_reference": chat.passage_reference,
                "passage_text": chat.passage_text,
                "created_at": chat.created_at.isoformat() if chat.created_at else None,
                "updated_at": chat.updated_at.isoformat() if chat.updated_at else None,
                "messages": messages
            })
        
        return {
            "user": {
                "anonymous_id": user.anonymous_id,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "insights": insights_data,
            "chat_messages": chat_messages_data,
            "standalone_chats": standalone_chats_data
        }
    
    def import_user_data(self, db: Session, user_id: int, data: Dict[str, Any]) -> Dict[str, int]:
        """
        Import user data from JSON.
        
        Args:
            db: Database session
            user_id: User ID
            data: Dictionary containing user data
        
        Returns:
            Dictionary with counts of imported items
        """
        counts = {
            "insights": 0,
            "chat_messages": 0,
            "standalone_chats": 0
        }
        
        # Import insights
        for insight_data in data.get("insights", []):
            # Check if insight already exists (by reference and text)
            existing_insight = db.query(SavedInsight).filter(
                SavedInsight.passage_reference == insight_data["passage_reference"],
                SavedInsight.passage_text == insight_data["passage_text"]
            ).first()
            
            if existing_insight:
                # Link existing insight to user if not already linked
                stmt = select(user_insights).where(
                    user_insights.c.user_id == user_id,
                    user_insights.c.insight_id == existing_insight.id
                )
                result = db.execute(stmt).first()
                if not result:
                    db.execute(
                        user_insights.insert().values(
                            user_id=user_id,
                            insight_id=existing_insight.id
                        )
                    )
                    counts["insights"] += 1
            else:
                # Create new insight
                new_insight = SavedInsight(
                    passage_reference=insight_data["passage_reference"],
                    passage_text=insight_data["passage_text"],
                    historical_context=insight_data["historical_context"],
                    theological_significance=insight_data["theological_significance"],
                    practical_application=insight_data["practical_application"]
                )
                db.add(new_insight)
                db.flush()
                
                # Link to user
                db.execute(
                    user_insights.insert().values(
                        user_id=user_id,
                        insight_id=new_insight.id
                    )
                )
                counts["insights"] += 1
        
        # Import standalone chats
        for chat_data in data.get("standalone_chats", []):
            new_chat = StandaloneChat(
                user_id=user_id,
                title=chat_data.get("title"),
                passage_reference=chat_data.get("passage_reference"),
                passage_text=chat_data.get("passage_text")
            )
            db.add(new_chat)
            db.flush()
            
            # Import messages for this chat
            for msg_data in chat_data.get("messages", []):
                new_msg = StandaloneChatMessage(
                    chat_id=new_chat.id,
                    role=msg_data["role"],
                    content=msg_data["content"]
                )
                db.add(new_msg)
            
            counts["standalone_chats"] += 1
        
        db.commit()
        
        return counts
