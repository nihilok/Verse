from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.services.bible_service import BibleService
from app.services.insight_service import InsightService
from app.services.chat_service import ChatService
from app.services.user_service import UserService
from app.models.models import User

router = APIRouter()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Dependency to get or create the current user."""
    # Check if user is already in request state
    if hasattr(request.state, 'user') and request.state.user:
        return request.state.user
    
    # Get anonymous_id from request state (set by middleware)
    anonymous_id = getattr(request.state, 'anonymous_id', None)
    
    # Get or create user
    user_service = UserService()
    user = user_service.get_or_create_user(db, anonymous_id)
    
    # Store user and anonymous_id in request state
    # Store anonymous_id separately so middleware can access it after session closes
    request.state.user = user
    request.state.user_anonymous_id = user.anonymous_id

    return user


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


class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message."""
    insight_id: int
    message: str
    passage_text: str
    passage_reference: str
    insight_context: dict  # Contains historical_context, theological_significance, practical_application


class StandaloneChatCreateRequest(BaseModel):
    """Request model for creating a standalone chat."""
    message: str
    passage_text: Optional[str] = None
    passage_reference: Optional[str] = None


class StandaloneChatMessageRequest(BaseModel):
    """Request model for sending a message in a standalone chat."""
    chat_id: int
    message: str


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI insights for a passage."""
    service = InsightService()
    
    # Check if we already have insights for this passage
    if request.save:
        existing = service.get_saved_insight(
            db, 
            request.passage_reference,
            request.passage_text
        )
        if existing:
            # Link the insight to the user if not already linked
            service.link_insight_to_user(db, existing.id, current_user.id)
            return {
                "id": existing.id,
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
    insight_id = None
    if request.save:
        saved_insight = service.save_insight(
            db,
            request.passage_reference,
            request.passage_text,
            insights,
            current_user.id
        )
        insight_id = saved_insight.id
    
    return {
        "id": insight_id,
        "historical_context": insights.historical_context,
        "theological_significance": insights.theological_significance,
        "practical_application": insights.practical_application,
        "cached": False
    }


@router.get("/insights/history")
async def get_insights_history(
    limit: int = Query(50, description="Maximum number of insights to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get insights history from the database for the current user."""
    service = InsightService()
    insights = service.get_user_insights(db, current_user.id, limit=limit)
    
    return [
        {
            "id": str(insight.id),
            "reference": insight.passage_reference,
            "text": insight.passage_text,
            "insight": {
                "historical_context": insight.historical_context,
                "theological_significance": insight.theological_significance,
                "practical_application": insight.practical_application,
            },
            "timestamp": int(insight.created_at.timestamp() * 1000)
        }
        for insight in insights
    ]


@router.delete("/insights/history")
async def clear_insights_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all insights history from the database for the current user."""
    service = InsightService()
    count = service.clear_user_insights(db, current_user.id)
    
    return {"message": f"Cleared {count} insights from history"}


@router.post("/chat/message")
async def send_chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a chat message and get AI response."""
    service = ChatService()
    
    try:
        response = await service.send_message(
            db=db,
            insight_id=request.insight_id,
            user_id=current_user.id,
            user_message=request.message,
            passage_text=request.passage_text,
            passage_reference=request.passage_reference,
            insight_context=request.insight_context
        )
        
        if not response:
            raise HTTPException(status_code=500, detail="Failed to generate chat response")
        
        return {"response": response}
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/messages/{insight_id}")
async def get_chat_messages(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all chat messages for an insight for the current user."""
    service = ChatService()
    messages = service.get_chat_messages(db, insight_id, current_user.id)
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": int(msg.created_at.timestamp() * 1000) if msg.created_at else None
        }
        for msg in messages
    ]


@router.delete("/chat/messages/{insight_id}")
async def clear_chat_messages(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all chat messages for an insight for the current user."""
    service = ChatService()
    count = service.clear_chat_messages(db, insight_id, current_user.id)
    
    return {"message": f"Cleared {count} chat messages"}


@router.post("/standalone-chat")
async def create_standalone_chat(
    request: StandaloneChatCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new standalone chat session."""
    service = ChatService()
    
    try:
        chat_id = await service.create_standalone_chat(
            db=db,
            user_id=current_user.id,
            user_message=request.message,
            passage_text=request.passage_text,
            passage_reference=request.passage_reference
        )
        
        if not chat_id:
            raise HTTPException(status_code=500, detail="Failed to create chat")
        
        # Get the messages for the new chat
        messages = service.get_standalone_chat_messages(db, chat_id, current_user.id)
        
        return {
            "chat_id": chat_id,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": int(msg.created_at.timestamp() * 1000) if msg.created_at else None
                }
                for msg in messages
            ]
        }
    except Exception as e:
        print(f"Error in create standalone chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/standalone-chat/message")
async def send_standalone_chat_message(
    request: StandaloneChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a message in a standalone chat."""
    service = ChatService()
    
    try:
        response = await service.send_standalone_message(
            db=db,
            chat_id=request.chat_id,
            user_id=current_user.id,
            user_message=request.message
        )
        
        if not response:
            raise HTTPException(status_code=500, detail="Failed to send message")
        
        return {"response": response}
    except Exception as e:
        print(f"Error in standalone chat message endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/standalone-chat")
async def get_standalone_chats(
    limit: int = Query(50, description="Maximum number of chats to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all standalone chat sessions for the current user."""
    service = ChatService()
    chats = service.get_standalone_chats(db, current_user.id, limit=limit)
    
    return [
        {
            "id": chat.id,
            "title": chat.title,
            "passage_reference": chat.passage_reference,
            "passage_text": chat.passage_text,
            "created_at": int(chat.created_at.timestamp() * 1000) if chat.created_at else None,
            "updated_at": int(chat.updated_at.timestamp() * 1000) if chat.updated_at else None
        }
        for chat in chats
    ]


@router.get("/standalone-chat/{chat_id}/messages")
async def get_standalone_chat_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all messages for a standalone chat for the current user."""
    service = ChatService()
    messages = service.get_standalone_chat_messages(db, chat_id, current_user.id)
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": int(msg.created_at.timestamp() * 1000) if msg.created_at else None
        }
        for msg in messages
    ]


@router.delete("/standalone-chat/{chat_id}")
async def delete_standalone_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a standalone chat session."""
    service = ChatService()
    success = service.delete_standalone_chat(db, chat_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {"message": "Chat deleted successfully"}


class ImportDataRequest(BaseModel):
    """Request model for importing user data."""
    data: Dict[str, Any]


@router.get("/user/session")
async def get_user_session(
    current_user: User = Depends(get_current_user)
):
    """Get the current user session information."""
    return {
        "anonymous_id": current_user.anonymous_id,
        "created_at": int(current_user.created_at.timestamp() * 1000) if current_user.created_at else None
    }


@router.delete("/user/data")
async def clear_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all data for the current user."""
    service = UserService()
    counts = service.clear_user_data(db, current_user.id)
    
    return {
        "message": "User data cleared successfully",
        "deleted": counts
    }


@router.get("/user/export")
async def export_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export all data for the current user as JSON."""
    service = UserService()
    data = service.export_user_data(db, current_user.id)
    
    return data


@router.post("/user/import")
async def import_user_data(
    request: ImportDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import user data from JSON."""
    service = UserService()
    try:
        counts = service.import_user_data(db, current_user.id, request.data)
        return {
            "message": "User data imported successfully",
            "imported": counts
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
