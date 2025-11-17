from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.clients.ai_client import InsightRequest, InsightResponse
from app.clients.claude_client import ClaudeAIClient
from app.models.models import SavedInsight, user_insights


class InsightService:
    """Service for AI insight operations."""
    
    def __init__(self):
        self.client = ClaudeAIClient()
    
    async def generate_insights(
        self,
        passage_text: str,
        passage_reference: str
    ) -> Optional[InsightResponse]:
        """Generate insights for a passage."""
        request = InsightRequest(
            passage_text=passage_text,
            passage_reference=passage_reference
        )
        return await self.client.generate_insights(request)
    
    def save_insight(
        self,
        db: Session,
        passage_reference: str,
        passage_text: str,
        insights: InsightResponse,
        user_id: int
    ) -> SavedInsight:
        """Save insights to the database and link to user."""
        db_insight = SavedInsight(
            passage_reference=passage_reference,
            passage_text=passage_text,
            historical_context=insights.historical_context,
            theological_significance=insights.theological_significance,
            practical_application=insights.practical_application
        )
        db.add(db_insight)
        db.flush()
        
        # Link insight to user
        db.execute(
            user_insights.insert().values(
                user_id=user_id,
                insight_id=db_insight.id
            )
        )
        
        db.commit()
        db.refresh(db_insight)
        return db_insight
    
    def link_insight_to_user(
        self,
        db: Session,
        insight_id: int,
        user_id: int
    ) -> bool:
        """Link an existing insight to a user if not already linked."""
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
            db.commit()
            return True
        return False
    
    def get_saved_insight(
        self,
        db: Session,
        passage_reference: str,
        passage_text: str
    ) -> Optional[SavedInsight]:
        """Get a saved insight from the database."""
        return db.query(SavedInsight).filter(
            SavedInsight.passage_reference == passage_reference,
            SavedInsight.passage_text == passage_text
        ).first()
    
    def get_user_insights(
        self,
        db: Session,
        user_id: int,
        limit: int = 50
    ) -> list[SavedInsight]:
        """Get all saved insights for a user ordered by creation date."""
        return db.query(SavedInsight).join(
            user_insights,
            SavedInsight.id == user_insights.c.insight_id
        ).filter(
            user_insights.c.user_id == user_id
        ).order_by(
            SavedInsight.created_at.desc()
        ).limit(limit).all()
    
    def clear_user_insights(
        self,
        db: Session,
        user_id: int
    ) -> int:
        """Clear all insight associations for a user."""
        count = db.execute(
            user_insights.delete().where(user_insights.c.user_id == user_id)
        ).rowcount
        db.commit()
        return count
