import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limiter import AI_ENDPOINT_LIMIT, CHAT_ENDPOINT_LIMIT, limiter
from app.models.models import User
from app.services.bible_service import BibleService
from app.services.chat_service import CHAT_ID_MARKER, ChatService
from app.services.definition_service import DefinitionService
from app.services.device_link_service import DeviceLinkService
from app.services.insight_service import InsightService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Dependency to get or create the current user."""
    # Check if user is already in request state
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user

    # Get anonymous_id from request state (set by middleware)
    anonymous_id = getattr(request.state, "anonymous_id", None)

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
    verse_end: int | None = None
    translation: str = "WEB"


class InsightRequestModel(BaseModel):
    """Request model for generating insights."""

    passage_text: str
    passage_reference: str
    save: bool = False

    @field_validator("passage_text")
    @classmethod
    def strip_passage_text(cls, v: str) -> str:
        """Strip whitespace from passage text for consistent caching."""
        return v.strip() if v else v


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
    passage_text: str | None = None
    passage_reference: str | None = None


class StandaloneChatMessageRequest(BaseModel):
    """Request model for sending a message in a standalone chat."""

    chat_id: int
    message: str


class DefinitionRequestModel(BaseModel):
    """Request model for generating a word definition."""

    word: str
    verse_text: str
    passage_reference: str
    save: bool = False

    @field_validator("word")
    @classmethod
    def strip_word(cls, v: str) -> str:
        """Strip whitespace from word for consistent caching."""
        return v.strip() if v else v

    @field_validator("verse_text")
    @classmethod
    def strip_verse_text(cls, v: str) -> str:
        """Strip whitespace from verse text for consistent caching."""
        return v.strip() if v else v


@router.get("/passage")
async def get_passage(
    book: str = Query(..., description="Book name (e.g., 'John', 'Genesis')"),
    chapter: int = Query(..., description="Chapter number"),
    verse_start: int = Query(..., description="Starting verse number"),
    verse_end: int | None = Query(None, description="Ending verse number (optional)"),
    translation: str = Query("WEB", description="Bible translation (default: WEB)"),
    save: bool = Query(False, description="Save passage to database"),
    db: AsyncSession = Depends(get_db),
):
    """Get a Bible passage."""
    service = BibleService()
    try:
        passage = await service.get_passage(
            book=book,
            chapter=chapter,
            verse_start=verse_start,
            verse_end=verse_end,
            translation=translation,
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
    db: AsyncSession = Depends(get_db),
):
    """Get an entire chapter."""
    service = BibleService()
    try:
        passage = await service.get_chapter(book=book, chapter=chapter, translation=translation)

        if not passage:
            raise HTTPException(status_code=404, detail="Chapter not found")

        if save:
            service.save_passage(db, passage)

        return passage
    finally:
        await service.close()


@router.post("/insights")
@limiter.limit(AI_ENDPOINT_LIMIT)
async def generate_insights(
    request: Request,
    insight_request: InsightRequestModel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate AI insights for a passage."""
    service = InsightService()

    # Check if we already have insights for this passage
    if insight_request.save:
        existing = service.get_saved_insight(
            db, insight_request.passage_reference, insight_request.passage_text
        )
        if existing:
            # Link the insight to the user if not already linked
            service.link_insight_to_user(db, existing.id, current_user.id)
            return {
                "id": existing.id,
                "historical_context": existing.historical_context,
                "theological_significance": existing.theological_significance,
                "practical_application": existing.practical_application,
                "cached": True,
            }

    # Generate new insights
    insights = await service.generate_insights(
        passage_text=insight_request.passage_text,
        passage_reference=insight_request.passage_reference,
    )

    if not insights:
        raise HTTPException(status_code=500, detail="Failed to generate insights")

    # Save if requested
    insight_id = None
    if insight_request.save:
        saved_insight = service.save_insight(
            db,
            insight_request.passage_reference,
            insight_request.passage_text,
            insights,
            current_user.id,
        )
        insight_id = saved_insight.id

    return {
        "id": insight_id,
        "historical_context": insights.historical_context,
        "theological_significance": insights.theological_significance,
        "practical_application": insights.practical_application,
        "cached": False,
    }


@router.get("/insights/history")
async def get_insights_history(
    limit: int = Query(50, description="Maximum number of insights to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
            "timestamp": int(insight.created_at.timestamp() * 1000),
        }
        for insight in insights
    ]


@router.delete("/insights/history")
async def clear_insights_history(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Clear all insights history from the database for the current user."""
    service = InsightService()
    count = service.clear_user_insights(db, current_user.id)

    return {"message": f"Cleared {count} insights from history"}


@router.post("/definitions")
@limiter.limit(AI_ENDPOINT_LIMIT)
async def generate_definition(
    request: Request,
    definition_request: DefinitionRequestModel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate AI definition for a word in context."""
    service = DefinitionService()

    # Check if we already have a definition for this word in this context
    if definition_request.save:
        existing = await service.get_saved_definition(
            db,
            definition_request.word,
            definition_request.passage_reference,
            definition_request.verse_text,
        )
        if existing:
            # Link the definition to the user if not already linked
            await service.link_definition_to_user(db, existing.id, current_user.id)
            return {
                "id": existing.id,
                "word": existing.word,
                "definition": existing.definition,
                "biblical_usage": existing.biblical_usage,
                "original_language": existing.original_language,
                "cached": True,
            }

    # Generate new definition
    definition = await service.generate_definition(
        word=definition_request.word,
        verse_text=definition_request.verse_text,
        passage_reference=definition_request.passage_reference,
    )

    if not definition:
        raise HTTPException(status_code=500, detail="Failed to generate definition")

    # Save if requested
    definition_id = None
    if definition_request.save:
        saved_definition = await service.save_definition(
            db,
            definition_request.word,
            definition_request.passage_reference,
            definition_request.verse_text,
            definition,
            current_user.id,
        )
        definition_id = saved_definition.id

    return {
        "id": definition_id,
        "word": definition_request.word,
        "definition": definition.definition,
        "biblical_usage": definition.biblical_usage,
        "original_language": definition.original_language,
        "cached": False,
    }


@router.get("/definitions/history")
async def get_definitions_history(
    limit: int = Query(50, description="Maximum number of definitions to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get definitions history from the database for the current user."""
    service = DefinitionService()
    definitions = service.get_user_definitions(db, current_user.id, limit=limit)

    return [
        {
            "id": str(definition.id),
            "word": definition.word,
            "passage_reference": definition.passage_reference,
            "verse_text": definition.verse_text,
            "definition": {
                "definition": definition.definition,
                "biblical_usage": definition.biblical_usage,
                "original_language": definition.original_language,
            },
            "timestamp": int(definition.created_at.timestamp() * 1000),
        }
        for definition in definitions
    ]


@router.delete("/definitions/history")
async def clear_definitions_history(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Clear all definitions history from the database for the current user."""
    service = DefinitionService()
    count = service.clear_user_definitions(db, current_user.id)

    return {"message": f"Cleared {count} definitions from history"}


@router.post("/chat/message")
@limiter.limit(CHAT_ENDPOINT_LIMIT)
async def send_chat_message(
    request: Request,
    chat_request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream chat message response via SSE."""
    service = ChatService()

    async def event_stream():
        stop_reason = None
        try:
            async for chunk, chunk_stop_reason in service.send_message_stream(
                db=db,
                insight_id=chat_request.insight_id,
                user_id=current_user.id,
                user_message=chat_request.message,
                passage_text=chat_request.passage_text,
                passage_reference=chat_request.passage_reference,
                insight_context=chat_request.insight_context,
            ):
                if chunk:  # Send non-empty content chunks
                    yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"
                if chunk_stop_reason:  # Capture stop_reason
                    stop_reason = chunk_stop_reason

            # Send completion event with stop_reason
            yield f"event: done\ndata: {json.dumps({'status': 'complete', 'stop_reason': stop_reason})}\n\n"
        except Exception as e:
            logger.error(f"Error streaming chat: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/messages/{insight_id}")
async def get_chat_messages(
    insight_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all chat messages for an insight for the current user."""
    service = ChatService()
    messages = service.get_chat_messages(db, insight_id, current_user.id)

    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": int(msg.created_at.timestamp() * 1000) if msg.created_at else None,
        }
        for msg in messages
    ]


@router.delete("/chat/messages/{insight_id}")
async def clear_chat_messages(
    insight_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clear all chat messages for an insight for the current user."""
    service = ChatService()
    count = service.clear_chat_messages(db, insight_id, current_user.id)

    return {"message": f"Cleared {count} chat messages"}


@router.post("/standalone-chat")
@limiter.limit(CHAT_ENDPOINT_LIMIT)
async def create_standalone_chat(
    request: Request,
    chat_create_request: StandaloneChatCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new standalone chat session and stream the first response via SSE."""
    service = ChatService()

    async def event_stream():
        chat_id = None
        stop_reason = None
        try:
            async for chunk, chunk_stop_reason in service.create_standalone_chat_stream(
                db=db,
                user_id=current_user.id,
                user_message=chat_create_request.message,
                passage_text=chat_create_request.passage_text,
                passage_reference=chat_create_request.passage_reference,
            ):
                # Check if this is the chat_id marker
                if chunk.startswith(CHAT_ID_MARKER):
                    chat_id = int(chunk.split(":", 1)[1])
                    # Send chat_id event
                    yield f"event: chat_id\ndata: {json.dumps({'chat_id': chat_id})}\n\n"
                elif chunk:  # Send non-empty content chunks
                    # Send token as SSE event
                    yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"

                if chunk_stop_reason:  # Capture stop_reason
                    stop_reason = chunk_stop_reason

            # Send completion event with stop_reason
            yield f"event: done\ndata: {json.dumps({'status': 'complete', 'stop_reason': stop_reason})}\n\n"
        except Exception as e:
            logger.error(f"Error streaming standalone chat creation: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/standalone-chat/message")
@limiter.limit(CHAT_ENDPOINT_LIMIT)
async def send_standalone_chat_message(
    request: Request,
    chat_message_request: StandaloneChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream standalone chat message response via SSE."""
    service = ChatService()

    async def event_stream():
        stop_reason = None
        try:
            async for (
                chunk,
                chunk_stop_reason,
            ) in service.send_standalone_message_stream(
                db=db,
                chat_id=chat_message_request.chat_id,
                user_id=current_user.id,
                user_message=chat_message_request.message,
            ):
                if chunk:  # Send non-empty content chunks
                    yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"
                if chunk_stop_reason:  # Capture stop_reason
                    stop_reason = chunk_stop_reason

            # Send completion event with stop_reason
            yield f"event: done\ndata: {json.dumps({'status': 'complete', 'stop_reason': stop_reason})}\n\n"
        except Exception as e:
            logger.error(f"Error streaming standalone chat: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/standalone-chat")
async def get_standalone_chats(
    limit: int = Query(50, description="Maximum number of chats to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
            "updated_at": int(chat.updated_at.timestamp() * 1000) if chat.updated_at else None,
        }
        for chat in chats
    ]


@router.get("/standalone-chat/{chat_id}/messages")
async def get_standalone_chat_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all messages for a standalone chat for the current user."""
    service = ChatService()
    messages = service.get_standalone_chat_messages(db, chat_id, current_user.id)

    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": int(msg.created_at.timestamp() * 1000) if msg.created_at else None,
        }
        for msg in messages
    ]


@router.delete("/standalone-chat/{chat_id}")
async def delete_standalone_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a standalone chat session."""
    service = ChatService()
    success = service.delete_standalone_chat(db, chat_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")

    return {"message": "Chat deleted successfully"}


class ImportDataRequest(BaseModel):
    """Request model for importing user data."""

    data: dict[str, Any]


class AcceptLinkCodeRequest(BaseModel):
    """Request model for accepting a device link code."""

    code: str
    device_name: str | None = None
    device_type: str | None = None


@router.get("/user/session")
async def get_user_session(current_user: User = Depends(get_current_user)):
    """Get the current user session information."""
    return {
        "anonymous_id": current_user.anonymous_id,
        "created_at": int(current_user.created_at.timestamp() * 1000) if current_user.created_at else None,
    }


@router.delete("/user/data")
async def clear_user_data(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Clear all data for the current user."""
    service = UserService()
    counts = service.clear_user_data(db, current_user.id)

    return {"message": "User data cleared successfully", "deleted": counts}


@router.get("/user/export")
async def export_user_data(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Export all data for the current user as JSON."""
    service = UserService()
    data = service.export_user_data(db, current_user.id)

    return data


@router.post("/user/import")
async def import_user_data(
    request: ImportDataRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import user data from JSON."""
    service = UserService()
    try:
        counts = service.import_user_data(db, current_user.id, request.data)
        return {"message": "User data imported successfully", "imported": counts}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# Device Linking Endpoints


@router.post("/user/link/generate")
async def generate_link_code(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a new device linking code with QR data."""
    service = DeviceLinkService()

    # Extract device info from request
    user_agent = request.headers.get("user-agent", "")

    # Create or update device record
    device = service.create_or_update_device(db=db, user_id=current_user.id, user_agent=user_agent)

    try:
        result = service.generate_link_code(db, current_user.id, device.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/user/link/accept")
async def accept_link_code(
    link_request: AcceptLinkCodeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a linking code and merge accounts."""
    service = DeviceLinkService()

    # Extract device info from request
    user_agent = request.headers.get("user-agent", "")

    # Create or update device record
    device = service.create_or_update_device(
        db=db,
        user_id=current_user.id,
        device_name=link_request.device_name,
        device_type=link_request.device_type,
        user_agent=user_agent,
    )

    try:
        result = service.validate_and_use_code(
            db=db,
            display_code=link_request.code,
            target_user_id=current_user.id,
            target_device_id=device.id,
        )

        # Update request state so middleware updates the cookie
        request.state.user_anonymous_id = result["new_anonymous_id"]

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/user/devices")
async def get_user_devices(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get all devices linked to current user."""
    service = DeviceLinkService()
    devices = service.get_user_devices(db, current_user.id)
    return devices


@router.delete("/user/devices/{device_id}")
async def unlink_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unlink a specific device."""
    service = DeviceLinkService()
    try:
        result = service.unlink_device(db, device_id, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/user/link/codes")
async def revoke_link_codes(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Revoke all pending link codes for user."""
    service = DeviceLinkService()
    count = service.revoke_user_codes(db, current_user.id)
    return {"message": f"Revoked {count} pending link codes", "count": count}


# Debug endpoints - only available in development
def register_debug_routes():
    """Register debug endpoints only in development environment."""
    from app.core.config import get_settings

    settings = get_settings()

    if settings.environment != "development":
        return

    @router.get("/debug/rag-status")
    async def get_rag_status(
        db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
    ):
        """
        Debug endpoint to check RAG configuration and message embeddings.
        Returns information about:
        - Whether embedding client is configured
        - Number of messages with/without embeddings
        - Sample messages to verify RAG retrieval
        """
        from sqlalchemy import func as sql_func

        from app.core.config import get_settings
        from app.models.models import ChatMessage, StandaloneChat, StandaloneChatMessage

        chat_service = ChatService()

        # Check embedding client
        has_embedding_client = chat_service.embedding_client is not None
        openai_api_key_configured = bool(get_settings().openai_api_key)

        # Count ALL messages in database (for debugging)
        total_all_standalone_msgs = db.query(sql_func.count(StandaloneChatMessage.id)).scalar()
        total_all_standalone_with_embeddings = (
            db.query(sql_func.count(StandaloneChatMessage.id))
            .filter(StandaloneChatMessage.embedding.isnot(None))
            .scalar()
        )

        total_all_insight_msgs = db.query(sql_func.count(ChatMessage.id)).scalar()
        total_all_insight_with_embeddings = (
            db.query(sql_func.count(ChatMessage.id)).filter(ChatMessage.embedding.isnot(None)).scalar()
        )

        # Count ALL chats in database
        total_all_standalone_chats = db.query(sql_func.count(StandaloneChat.id)).scalar()

        # Count messages for CURRENT USER
        total_standalone_msgs = (
            db.query(sql_func.count(StandaloneChatMessage.id))
            .join(StandaloneChat)
            .filter(StandaloneChat.user_id == current_user.id)
            .scalar()
        )

        standalone_msgs_with_embeddings = (
            db.query(sql_func.count(StandaloneChatMessage.id))
            .join(StandaloneChat)
            .filter(
                StandaloneChat.user_id == current_user.id,
                StandaloneChatMessage.embedding.isnot(None),
            )
            .scalar()
        )

        # Count insight chat messages
        total_insight_msgs = (
            db.query(sql_func.count(ChatMessage.id)).filter(ChatMessage.user_id == current_user.id).scalar()
        )

        insight_msgs_with_embeddings = (
            db.query(sql_func.count(ChatMessage.id))
            .filter(
                ChatMessage.user_id == current_user.id,
                ChatMessage.embedding.isnot(None),
            )
            .scalar()
        )

        # Get sample messages for current user
        sample_standalone = (
            db.query(StandaloneChatMessage)
            .join(StandaloneChat)
            .filter(StandaloneChat.user_id == current_user.id)
            .limit(3)
            .all()
        )

        sample_insight = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).limit(3).all()

        # Get sample messages from ALL users (for debugging)
        sample_all_standalone = db.query(StandaloneChatMessage).limit(3).all()
        sample_all_insight = db.query(ChatMessage).limit(3).all()

        # Get list of all user IDs with chats
        users_with_standalone_chats = db.query(StandaloneChat.user_id).distinct().all()
        users_with_insight_chats = db.query(ChatMessage.user_id).distinct().all()

        return {
            "current_user": {
                "id": current_user.id,
                "anonymous_id": current_user.anonymous_id if hasattr(current_user, "anonymous_id") else None,
            },
            "embedding_client_configured": has_embedding_client,
            "openai_api_key_configured": openai_api_key_configured,
            "database_totals": {
                "all_standalone_chats": total_all_standalone_chats,
                "all_standalone_messages": total_all_standalone_msgs,
                "all_standalone_with_embeddings": total_all_standalone_with_embeddings,
                "all_insight_messages": total_all_insight_msgs,
                "all_insight_with_embeddings": total_all_insight_with_embeddings,
                "users_with_standalone_chats": [uid[0] for uid in users_with_standalone_chats],
                "users_with_insight_chats": [uid[0] for uid in users_with_insight_chats],
            },
            "standalone_chats": {
                "total_messages": total_standalone_msgs,
                "messages_with_embeddings": standalone_msgs_with_embeddings,
                "percentage_embedded": round(100 * standalone_msgs_with_embeddings / total_standalone_msgs, 1)
                if total_standalone_msgs > 0
                else 0,
                "sample_messages": [
                    {
                        "id": msg.id,
                        "chat_id": msg.chat_id,
                        "role": msg.role,
                        "content_preview": msg.content[:100] + "..."
                        if len(msg.content) > 100
                        else msg.content,
                        "has_embedding": msg.embedding is not None and len(msg.embedding) > 0
                        if msg.embedding is not None
                        else False,
                        "embedding_dimensions": len(msg.embedding) if msg.embedding is not None else 0,
                    }
                    for msg in sample_standalone
                ],
            },
            "insight_chats": {
                "total_messages": total_insight_msgs,
                "messages_with_embeddings": insight_msgs_with_embeddings,
                "percentage_embedded": round(100 * insight_msgs_with_embeddings / total_insight_msgs, 1)
                if total_insight_msgs > 0
                else 0,
                "sample_messages": [
                    {
                        "id": msg.id,
                        "insight_id": msg.insight_id,
                        "role": msg.role,
                        "content_preview": msg.content[:100] + "..."
                        if len(msg.content) > 100
                        else msg.content,
                        "has_embedding": msg.embedding is not None and len(msg.embedding) > 0
                        if msg.embedding is not None
                        else False,
                        "embedding_dimensions": len(msg.embedding) if msg.embedding is not None else 0,
                    }
                    for msg in sample_insight
                ],
            },
            "debug_all_messages": {
                "sample_standalone_messages": [
                    {
                        "id": msg.id,
                        "chat_id": msg.chat_id,
                        "role": msg.role,
                        "content_preview": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
                        "has_embedding": msg.embedding is not None and len(msg.embedding) > 0
                        if msg.embedding is not None
                        else False,
                    }
                    for msg in sample_all_standalone
                ],
                "sample_insight_messages": [
                    {
                        "id": msg.id,
                        "insight_id": msg.insight_id,
                        "user_id": msg.user_id,
                        "role": msg.role,
                        "content_preview": msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
                        "has_embedding": msg.embedding is not None and len(msg.embedding) > 0
                        if msg.embedding is not None
                        else False,
                    }
                    for msg in sample_all_insight
                ],
            },
        }

    @router.get("/debug/test-rag")
    async def test_rag_retrieval(
        query: str = Query(..., description="Test query to search for"),
        chat_id: int | None = Query(None, description="Chat ID to exclude from results"),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        """
        Test endpoint to manually check RAG retrieval.

        Usage: /api/debug/test-rag?query=What+kings+have+we+discussed&chat_id=2

        This will show:
        - What messages RAG finds for the query
        - The actual content of those messages
        - Whether they would be passed to Claude
        """
        from app.services.chat_service import ChatService

        chat_service = ChatService()

        try:
            # Test RAG retrieval
            rag_messages = await chat_service._get_relevant_standalone_context(
                db=db,
                user_id=current_user.id,
                query=query,
                current_chat_id=chat_id,
                limit=5,
            )

            # Format the results
            results = []
            for msg in rag_messages:
                results.append(
                    {
                        "message_id": msg.id,
                        "chat_id": msg.chat_id,
                        "role": msg.role,
                        "content": msg.content,
                        "has_embedding": msg.embedding is not None and len(msg.embedding) > 0
                        if msg.embedding is not None
                        else False,
                        "embedding_dimensions": len(msg.embedding) if msg.embedding is not None else 0,
                    }
                )

            # Also format what would be sent to Claude
            formatted_context = chat_service.client._format_rag_context(rag_messages) if rag_messages else ""

            return {
                "query": query,
                "current_user_id": current_user.id,
                "excluded_chat_id": chat_id,
                "messages_found": len(rag_messages),
                "rag_messages": results,
                "formatted_context_for_claude": formatted_context,
                "interpretation": {
                    "rag_enabled": chat_service.embedding_client is not None,
                    "messages_retrieved": len(rag_messages),
                    "would_claude_see_context": len(rag_messages) > 0,
                    "note": "If messages_found is 0, RAG won't help. If > 0, Claude should see this context.",
                },
            }
        except Exception as e:
            import traceback

            return {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "query": query,
                "current_user_id": current_user.id,
            }


# Register debug routes (only in development)
register_debug_routes()
