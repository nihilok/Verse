from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.ai_client import InsightRequest, InsightResponse
from app.clients.claude_client import ClaudeAIClient
from app.models.models import SavedInsight, user_insights


class InsightService:
    """Service for AI insight operations."""

    def __init__(self):
        self.client = ClaudeAIClient()

    async def generate_insights(self, passage_text: str, passage_reference: str) -> InsightResponse | None:
        """Generate insights for a passage."""
        request = InsightRequest(passage_text=passage_text, passage_reference=passage_reference)
        return await self.client.generate_insights(request)

    async def save_insight(
        self,
        db: AsyncSession,
        passage_reference: str,
        passage_text: str,
        insights: InsightResponse,
        user_id: int,
    ) -> SavedInsight:
        """Save insights to the database and link to user."""
        db_insight = SavedInsight(
            passage_reference=passage_reference,
            passage_text=passage_text,
            historical_context=insights.historical_context,
            theological_significance=insights.theological_significance,
            practical_application=insights.practical_application,
        )
        db.add(db_insight)
        await db.flush()

        # Link insight to user
        await db.execute(user_insights.insert().values(user_id=user_id, insight_id=db_insight.id))

        await db.refresh(db_insight)
        return db_insight

    async def link_insight_to_user(self, db: AsyncSession, insight_id: int, user_id: int) -> bool:
        """Link an existing insight to a user if not already linked."""
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

    async def get_saved_insight(
        self, db: AsyncSession, passage_reference: str, passage_text: str
    ) -> SavedInsight | None:
        """Get a saved insight from the database."""
        result = await db.execute(
            select(SavedInsight).where(
                SavedInsight.passage_reference == passage_reference,
                SavedInsight.passage_text == passage_text,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_insights(self, db: AsyncSession, user_id: int, limit: int = 50) -> list[SavedInsight]:
        """Get all saved insights for a user ordered by creation date."""
        result = await db.execute(
            select(SavedInsight)
            .join(user_insights, SavedInsight.id == user_insights.c.insight_id)
            .where(user_insights.c.user_id == user_id)
            .order_by(SavedInsight.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def clear_user_insights(self, db: AsyncSession, user_id: int) -> int:
        """Clear all insight associations for a user."""
        result = await db.execute(delete(user_insights).where(user_insights.c.user_id == user_id))
        return result.rowcount
