from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.bible_service import BibleService
from app.services.insight_service import InsightService

router = APIRouter()


class PassageRequest(BaseModel):
    """Request model for fetching a passage."""
    book: str
    chapter: int
    verse_start: int
    verse_end: Optional[int] = None
    translation: str = "WEB"


class InsightRequestModel(BaseModel):
    """Request model for generating insights."""
    passage_text: str
    passage_reference: str
    save: bool = False


@router.get("/passage")
async def get_passage(
    book: str = Query(..., description="Book name (e.g., 'John', 'Genesis')"),
    chapter: int = Query(..., description="Chapter number"),
    verse_start: int = Query(..., description="Starting verse number"),
    verse_end: Optional[int] = Query(None, description="Ending verse number (optional)"),
    translation: str = Query("WEB", description="Bible translation (default: WEB)"),
    save: bool = Query(False, description="Save passage to database"),
    db: Session = Depends(get_db)
):
    """Get a Bible passage."""
    service = BibleService()
    try:
        passage = await service.get_passage(
            book=book,
            chapter=chapter,
            verse_start=verse_start,
            verse_end=verse_end,
            translation=translation
        )
        
        if not passage:
            raise HTTPException(status_code=404, detail="Passage not found")
        
        if save:
            service.save_passage(db, passage)
        
        return passage
    finally:
        await service.close()


@router.get("/chapter")
async def get_chapter(
    book: str = Query(..., description="Book name"),
    chapter: int = Query(..., description="Chapter number"),
    translation: str = Query("WEB", description="Bible translation"),
    save: bool = Query(False, description="Save chapter to database"),
    db: Session = Depends(get_db)
):
    """Get an entire chapter."""
    service = BibleService()
    try:
        passage = await service.get_chapter(
            book=book,
            chapter=chapter,
            translation=translation
        )
        
        if not passage:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        if save:
            service.save_passage(db, passage)
        
        return passage
    finally:
        await service.close()


@router.post("/insights")
async def generate_insights(
    request: InsightRequestModel,
    db: Session = Depends(get_db)
):
    """Generate AI insights for a passage."""
    service = InsightService()
    
    # Check if we already have insights for this passage
    if request.save:
        existing = service.get_saved_insight(db, request.passage_reference)
        if existing:
            return {
                "historical_context": existing.historical_context,
                "theological_significance": existing.theological_significance,
                "practical_application": existing.practical_application,
                "cached": True
            }
    
    # Generate new insights
    insights = await service.generate_insights(
        passage_text=request.passage_text,
        passage_reference=request.passage_reference
    )
    
    if not insights:
        raise HTTPException(status_code=500, detail="Failed to generate insights")
    
    # Save if requested
    if request.save:
        service.save_insight(
            db,
            request.passage_reference,
            request.passage_text,
            insights
        )
    
    return {
        "historical_context": insights.historical_context,
        "theological_significance": insights.theological_significance,
        "practical_application": insights.practical_application,
        "cached": False
    }
