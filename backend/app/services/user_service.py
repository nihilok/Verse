from typing import Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.models.models import User, SavedInsight, ChatMessage, StandaloneChat, StandaloneChatMessage, user_insights
import uuid


class UserService:
    """Service for managing anonymous users."""

    # Import Validation Constants (to prevent DoS attacks)
    MAX_INSIGHTS_IMPORT = 1000  # Maximum insights per import
    MAX_STANDALONE_CHATS_IMPORT = 500  # Maximum chats per import
    MAX_TEXT_LENGTH = 50000  # Maximum passage text length
    MAX_FIELD_LENGTH = 10000  # Maximum field length for insights/messages
    MAX_REFERENCE_LENGTH = 200  # Maximum reference/title length

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
    
    def _link_insight_to_user(self, db: Session, user_id: int, insight_id: int) -> bool:
        """
        Helper method to link an insight to a user if not already linked.
        
        Args:
            db: Database session
            user_id: User ID
            insight_id: Insight ID
        
        Returns:
            True if link was created, False if already existed
        """
        # Check if already linked
        stmt = select(user_insights).where(
            user_insights.c.user_id == user_id,
            user_insights.c.insight_id == insight_id
        )
        result = db.execute(stmt).first()
        
        if not result:
            db.execute(
                user_insights.insert().values(
                    user_id=user_id,
                    insight_id=insight_id
                )
            )
            return True
        return False
    
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
        chat_message_count = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).delete()
        
        # Delete standalone chats (cascades will delete messages)
        standalone_chat_count = db.query(StandaloneChat).filter(StandaloneChat.user_id == user_id).delete()
        
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
        # Use eager loading to load all relationships at once
        user = db.query(User).options(
            joinedload(User.insights),
            joinedload(User.chat_messages),
            joinedload(User.standalone_chats).joinedload(StandaloneChat.messages)
        ).filter(User.id == user_id).first()

        if not user:
            return {}
        
        # Get user's insights through the linking table with their chat messages
        insights_data = []
        for insight in user.insights:
            # Get chat messages for this insight
            insight_chat_messages = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in user.chat_messages if msg.insight_id == insight.id
            ]
            
            insights_data.append({
                "passage_reference": insight.passage_reference,
                "passage_text": insight.passage_text,
                "historical_context": insight.historical_context,
                "theological_significance": insight.theological_significance,
                "practical_application": insight.practical_application,
                "created_at": insight.created_at.isoformat() if insight.created_at else None,
                "chat_messages": insight_chat_messages
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

        Raises:
            ValueError: If data structure is invalid or exceeds size limits
        """
        # Validate data structure
        if not isinstance(data, dict):
            raise ValueError("Import data must be a dictionary")

        if "insights" in data and not isinstance(data["insights"], list):
            raise ValueError("Insights must be a list")

        if "standalone_chats" in data and not isinstance(data["standalone_chats"], list):
            raise ValueError("Standalone chats must be a list")

        # Validate size limits
        insights_count = len(data.get("insights", []))
        if insights_count > self.MAX_INSIGHTS_IMPORT:
            raise ValueError(f"Too many insights: {insights_count} (max {self.MAX_INSIGHTS_IMPORT})")

        chats_count = len(data.get("standalone_chats", []))
        if chats_count > self.MAX_STANDALONE_CHATS_IMPORT:
            raise ValueError(f"Too many standalone chats: {chats_count} (max {self.MAX_STANDALONE_CHATS_IMPORT})")
        
        counts = {
            "insights": 0,
            "chat_messages": 0,
            "standalone_chats": 0
        }
        
        try:
            # Import insights
            for insight_data in data.get("insights", []):
                # Validate required fields
                required_fields = ["passage_reference", "passage_text", "historical_context",
                                   "theological_significance", "practical_application"]
                for field in required_fields:
                    if field not in insight_data:
                        raise ValueError(f"Missing required field '{field}' in insight data")

                # Validate field lengths
                if len(insight_data.get("passage_text", "")) > self.MAX_TEXT_LENGTH:
                    raise ValueError(f"Passage text too long (max {self.MAX_TEXT_LENGTH} characters)")
                if len(insight_data.get("passage_reference", "")) > self.MAX_REFERENCE_LENGTH:
                    raise ValueError(f"Passage reference too long (max {self.MAX_REFERENCE_LENGTH} characters)")
                if len(insight_data.get("historical_context", "")) > self.MAX_FIELD_LENGTH:
                    raise ValueError(f"Historical context too long (max {self.MAX_FIELD_LENGTH} characters)")
                if len(insight_data.get("theological_significance", "")) > self.MAX_FIELD_LENGTH:
                    raise ValueError(f"Theological significance too long (max {self.MAX_FIELD_LENGTH} characters)")
                if len(insight_data.get("practical_application", "")) > self.MAX_FIELD_LENGTH:
                    raise ValueError(f"Practical application too long (max {self.MAX_FIELD_LENGTH} characters)")
                
                # Check if insight already exists (by reference and text)
                existing_insight = db.query(SavedInsight).filter(
                    SavedInsight.passage_reference == insight_data["passage_reference"],
                    SavedInsight.passage_text == insight_data["passage_text"]
                ).first()
                
                if existing_insight:
                    # Link existing insight to user if not already linked
                    if self._link_insight_to_user(db, user_id, existing_insight.id):
                        counts["insights"] += 1
                    insight_id = existing_insight.id
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
                    self._link_insight_to_user(db, user_id, new_insight.id)
                    counts["insights"] += 1
                    insight_id = new_insight.id
                
                # Import chat messages for this insight
                for msg_data in insight_data.get("chat_messages", []):
                    if "role" not in msg_data or "content" not in msg_data:
                        continue  # Skip invalid messages

                    # Validate message content length
                    if len(msg_data.get("content", "")) > self.MAX_FIELD_LENGTH:
                        raise ValueError(f"Message content too long (max {self.MAX_FIELD_LENGTH} characters)")

                    new_msg = ChatMessage(
                        insight_id=insight_id,
                        user_id=user_id,
                        role=msg_data["role"],
                        content=msg_data["content"]
                    )
                    db.add(new_msg)
                    counts["chat_messages"] += 1
            
            # Import standalone chats
            for chat_data in data.get("standalone_chats", []):
                # Validate chat field lengths
                title = chat_data.get("title", "")
                passage_text = chat_data.get("passage_text", "")
                passage_reference = chat_data.get("passage_reference", "")

                if title and len(title) > self.MAX_REFERENCE_LENGTH:
                    raise ValueError(f"Chat title too long (max {self.MAX_REFERENCE_LENGTH} characters)")
                if passage_text and len(passage_text) > self.MAX_TEXT_LENGTH:
                    raise ValueError(f"Chat passage text too long (max {self.MAX_TEXT_LENGTH} characters)")
                if passage_reference and len(passage_reference) > self.MAX_REFERENCE_LENGTH:
                    raise ValueError(f"Chat passage reference too long (max {self.MAX_REFERENCE_LENGTH} characters)")

                new_chat = StandaloneChat(
                    user_id=user_id,
                    title=title,
                    passage_reference=passage_reference,
                    passage_text=passage_text
                )
                db.add(new_chat)
                db.flush()

                # Import messages for this chat
                for msg_data in chat_data.get("messages", []):
                    if "role" not in msg_data or "content" not in msg_data:
                        continue  # Skip invalid messages

                    # Validate message content length
                    if len(msg_data.get("content", "")) > self.MAX_FIELD_LENGTH:
                        raise ValueError(f"Message content too long (max {self.MAX_FIELD_LENGTH} characters)")

                    new_msg = StandaloneChatMessage(
                        chat_id=new_chat.id,
                        role=msg_data["role"],
                        content=msg_data["content"]
                    )
                    db.add(new_msg)
                
                counts["standalone_chats"] += 1
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to import data: {str(e)}")
        
        return counts
