from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.ai_client import DefinitionRequest, DefinitionResponse
from app.clients.claude_client import ClaudeAIClient
from app.models.models import SavedDefinition, user_definitions


class DefinitionService:
    """Service for AI word definition operations."""

    def __init__(self):
        self.client = ClaudeAIClient()

    async def generate_definition(
        self, word: str, verse_text: str, passage_reference: str
    ) -> DefinitionResponse | None:
        """Generate a definition for a word in context."""
        request = DefinitionRequest(word=word, verse_text=verse_text, passage_reference=passage_reference)
        return await self.client.generate_definition(request)

    def save_definition(
        self,
        db: Session,
        word: str,
        passage_reference: str,
        verse_text: str,
        definition: DefinitionResponse,
        user_id: int,
    ) -> SavedDefinition:
        """Save a definition to the database and link to user."""
        db_definition = SavedDefinition(
            word=word,
            passage_reference=passage_reference,
            verse_text=verse_text,
            definition=definition.definition,
            biblical_usage=definition.biblical_usage,
            original_language=definition.original_language,
        )
        db.add(db_definition)
        db.flush()

        # Link definition to user
        db.execute(user_definitions.insert().values(user_id=user_id, definition_id=db_definition.id))

        db.commit()
        db.refresh(db_definition)
        return db_definition

    def link_definition_to_user(self, db: Session, definition_id: int, user_id: int) -> bool:
        """Link an existing definition to a user if not already linked."""
        # Check if already linked
        stmt = select(user_definitions).where(
            user_definitions.c.user_id == user_id,
            user_definitions.c.definition_id == definition_id,
        )
        result = db.execute(stmt).first()

        if not result:
            db.execute(user_definitions.insert().values(user_id=user_id, definition_id=definition_id))
            db.commit()
            return True
        return False

    def get_saved_definition(
        self, db: Session, word: str, passage_reference: str, verse_text: str
    ) -> SavedDefinition | None:
        """Get a saved definition from the database."""
        return (
            db.query(SavedDefinition)
            .filter(
                SavedDefinition.word == word,
                SavedDefinition.passage_reference == passage_reference,
                SavedDefinition.verse_text == verse_text,
            )
            .first()
        )

    def get_user_definitions(self, db: Session, user_id: int, limit: int = 50) -> list[SavedDefinition]:
        """Get all saved definitions for a user ordered by creation date."""
        return (
            db.query(SavedDefinition)
            .join(user_definitions, SavedDefinition.id == user_definitions.c.definition_id)
            .filter(user_definitions.c.user_id == user_id)
            .order_by(SavedDefinition.created_at.desc())
            .limit(limit)
            .all()
        )

    def clear_user_definitions(self, db: Session, user_id: int) -> int:
        """Clear all definition associations for a user."""
        count = db.execute(user_definitions.delete().where(user_definitions.c.user_id == user_id)).rowcount
        db.commit()
        return count
