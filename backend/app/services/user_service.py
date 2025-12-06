import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import (
    ChatMessage,
    SavedInsight,
    StandaloneChat,
    StandaloneChatMessage,
    User,
    user_insights,
)


class UserService:
    """Service for managing anonymous users."""

    # Import Validation Constants (to prevent DoS attacks)
    MAX_INSIGHTS_IMPORT = 1000  # Maximum insights per import
    MAX_STANDALONE_CHATS_IMPORT = 500  # Maximum chats per import
    MAX_TEXT_LENGTH = 50000  # Maximum passage text length
    MAX_FIELD_LENGTH = 10000  # Maximum field length for insights/messages
    MAX_REFERENCE_LENGTH = 100  # Maximum passage reference length (matches DB schema String(100))
    MAX_TITLE_LENGTH = 200  # Maximum title length (matches DB schema String(200))

    def get_or_create_user(self, db: Session, anonymous_id: str | None = None) -> User:
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

    async def get_user_by_anonymous_id(self, db, anonymous_id: str) -> User | None:
        """Get a user by their anonymous ID."""
        result = await db.execute(select(User).where(User.anonymous_id == anonymous_id))
        return result.scalar_one_or_none()

    async def _link_insight_to_user(self, db, user_id: int, insight_id: int) -> bool:
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
            user_insights.c.user_id == user_id, user_insights.c.insight_id == insight_id
        )
        result = await db.execute(stmt)
        existing = result.first()

        if not existing:
            await db.execute(user_insights.insert().values(user_id=user_id, insight_id=insight_id))
            return True
        return False

    async def clear_user_data(self, db, user_id: int) -> dict[str, int]:
        """
        Clear all data for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dictionary with counts of deleted items
        """
        from sqlalchemy import delete

        # Delete user-insight associations
        result = await db.execute(user_insights.delete().where(user_insights.c.user_id == user_id))
        insight_count = result.rowcount

        # Delete chat messages (cascades from user relationship)
        result = await db.execute(delete(ChatMessage).where(ChatMessage.user_id == user_id))
        chat_message_count = result.rowcount

        # Delete standalone chats (cascades will delete messages)
        result = await db.execute(delete(StandaloneChat).where(StandaloneChat.user_id == user_id))
        standalone_chat_count = result.rowcount

        return {
            "insights": insight_count,
            "chat_messages": chat_message_count,
            "standalone_chats": standalone_chat_count,
        }

    async def export_user_data(self, db, user_id: int) -> dict[str, Any]:
        """
        Export all data for a user as JSON.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dictionary containing all user data
        """
        from sqlalchemy.orm import selectinload

        # Use eager loading to load all relationships at once
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.insights),
                selectinload(User.chat_messages),
                selectinload(User.standalone_chats).selectinload(StandaloneChat.messages),
            )
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

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
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
                for msg in user.chat_messages
                if msg.insight_id == insight.id
            ]

            insights_data.append(
                {
                    "passage_reference": insight.passage_reference,
                    "passage_text": insight.passage_text,
                    "historical_context": insight.historical_context,
                    "theological_significance": insight.theological_significance,
                    "practical_application": insight.practical_application,
                    "created_at": insight.created_at.isoformat() if insight.created_at else None,
                    "chat_messages": insight_chat_messages,
                }
            )

        # Get user's standalone chats with messages
        standalone_chats_data = []
        for chat in user.standalone_chats:
            messages = []
            for msg in chat.messages:
                messages.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat() if msg.created_at else None,
                    }
                )

            standalone_chats_data.append(
                {
                    "title": chat.title,
                    "passage_reference": chat.passage_reference,
                    "passage_text": chat.passage_text,
                    "created_at": chat.created_at.isoformat() if chat.created_at else None,
                    "updated_at": chat.updated_at.isoformat() if chat.updated_at else None,
                    "messages": messages,
                }
            )

        return {
            "user": {
                "anonymous_id": user.anonymous_id,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
            "insights": insights_data,
            "standalone_chats": standalone_chats_data,
        }

    def _validate_field_length(self, value: str | None, field_name: str, max_length: int) -> None:
        """
        Validate that a field value doesn't exceed maximum length.

        Args:
            value: The field value to validate (may be None)
            field_name: Name of the field for error messages
            max_length: Maximum allowed length

        Raises:
            ValueError: If field exceeds maximum length
        """
        # Handle None values by converting to empty string
        actual_value = value or ""
        if len(actual_value) > max_length:
            raise ValueError(f"{field_name} too long (max {max_length} characters)")

    async def import_user_data(self, db, user_id: int, data: dict[str, Any]) -> dict[str, int]:
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
            raise ValueError(
                f"Too many standalone chats: {chats_count} (max {self.MAX_STANDALONE_CHATS_IMPORT})"
            )

        counts = {"insights": 0, "chat_messages": 0, "standalone_chats": 0}

        try:
            # Import insights
            for insight_data in data.get("insights", []):
                # Validate required fields
                required_fields = [
                    "passage_reference",
                    "passage_text",
                    "historical_context",
                    "theological_significance",
                    "practical_application",
                ]
                for field in required_fields:
                    if field not in insight_data:
                        raise ValueError(f"Missing required field '{field}' in insight data")

                # Validate field lengths
                self._validate_field_length(
                    insight_data.get("passage_text"),
                    "Passage text",
                    self.MAX_TEXT_LENGTH,
                )
                self._validate_field_length(
                    insight_data.get("passage_reference"),
                    "Passage reference",
                    self.MAX_REFERENCE_LENGTH,
                )
                self._validate_field_length(
                    insight_data.get("historical_context"),
                    "Historical context",
                    self.MAX_FIELD_LENGTH,
                )
                self._validate_field_length(
                    insight_data.get("theological_significance"),
                    "Theological significance",
                    self.MAX_FIELD_LENGTH,
                )
                self._validate_field_length(
                    insight_data.get("practical_application"),
                    "Practical application",
                    self.MAX_FIELD_LENGTH,
                )

                # Check if insight already exists (by reference and text)
                result = await db.execute(
                    select(SavedInsight).where(
                        SavedInsight.passage_reference == insight_data["passage_reference"],
                        SavedInsight.passage_text == insight_data["passage_text"],
                    )
                )
                existing_insight = result.scalar_one_or_none()

                if existing_insight:
                    # Link existing insight to user if not already linked
                    if await self._link_insight_to_user(db, user_id, existing_insight.id):
                        counts["insights"] += 1
                    insight_id = existing_insight.id
                else:
                    # Create new insight
                    new_insight = SavedInsight(
                        passage_reference=insight_data["passage_reference"],
                        passage_text=insight_data["passage_text"],
                        historical_context=insight_data["historical_context"],
                        theological_significance=insight_data["theological_significance"],
                        practical_application=insight_data["practical_application"],
                    )
                    db.add(new_insight)
                    await db.flush()

                    # Link to user
                    await self._link_insight_to_user(db, user_id, new_insight.id)
                    counts["insights"] += 1
                    insight_id = new_insight.id

                # Import chat messages for this insight
                for msg_data in insight_data.get("chat_messages", []):
                    if "role" not in msg_data or "content" not in msg_data:
                        continue  # Skip invalid messages

                    # Validate message content length
                    self._validate_field_length(
                        msg_data.get("content"),
                        "Message content",
                        self.MAX_FIELD_LENGTH,
                    )

                    new_msg = ChatMessage(
                        insight_id=insight_id,
                        user_id=user_id,
                        role=msg_data["role"],
                        content=msg_data["content"],
                    )
                    db.add(new_msg)
                    counts["chat_messages"] += 1

            # Import standalone chats
            for chat_data in data.get("standalone_chats", []):
                # Extract and validate chat field lengths
                title = chat_data.get("title")
                passage_text = chat_data.get("passage_text")
                passage_reference = chat_data.get("passage_reference")

                self._validate_field_length(title, "Chat title", self.MAX_TITLE_LENGTH)
                self._validate_field_length(passage_text, "Chat passage text", self.MAX_TEXT_LENGTH)
                self._validate_field_length(
                    passage_reference,
                    "Chat passage reference",
                    self.MAX_REFERENCE_LENGTH,
                )

                new_chat = StandaloneChat(
                    user_id=user_id,
                    title=title,
                    passage_reference=passage_reference,
                    passage_text=passage_text,
                )
                db.add(new_chat)
                await db.flush()

                # Import messages for this chat
                for msg_data in chat_data.get("messages", []):
                    if "role" not in msg_data or "content" not in msg_data:
                        continue  # Skip invalid messages

                    # Validate message content length
                    self._validate_field_length(
                        msg_data.get("content"),
                        "Message content",
                        self.MAX_FIELD_LENGTH,
                    )

                    new_msg = StandaloneChatMessage(
                        chat_id=new_chat.id,
                        role=msg_data["role"],
                        content=msg_data["content"],
                    )
                    db.add(new_msg)

                counts["standalone_chats"] += 1

        except Exception as e:
            await db.rollback()
            raise ValueError(f"Failed to import data: {str(e)}") from e

        return counts
