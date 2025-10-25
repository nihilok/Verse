from typing import Optional
from sqlalchemy.orm import Session
from app.clients.ai_client import InsightRequest, InsightResponse
from app.clients.claude_client import ClaudeAIClient
from app.models.models import SavedInsight


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
        insights: InsightResponse
    ) -> SavedInsight:
        """Save insights to the database."""
        db_insight = SavedInsight(
            passage_reference=passage_reference,
            passage_text=passage_text,
            historical_context=insights.historical_context,
            theological_significance=insights.theological_significance,
            practical_application=insights.practical_application
        )
        db.add(db_insight)
        db.commit()
        db.refresh(db_insight)
        return db_insight
    
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
    
    def get_all_insights(
        self,
        db: Session,
        limit: int = 50
    ) -> list[SavedInsight]:
        """Get all saved insights ordered by creation date."""
        return db.query(SavedInsight).order_by(
            SavedInsight.created_at.desc()
        ).limit(limit).all()
    
    def clear_all_insights(
        self,
        db: Session
    ) -> int:
        """Clear all saved insights from the database."""
        count = db.query(SavedInsight).delete()
        db.commit()
        return count
