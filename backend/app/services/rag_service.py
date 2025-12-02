"""
RAG (Retrieval-Augmented Generation) Service

This service handles semantic search, conversation summarization, and context formatting
for enhancing AI responses with relevant historical conversation data.
"""

import logging
from typing import Optional, List, Dict, Type, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.clients.embedding_client import EmbeddingClient
from app.clients.ai_client import AIClient
from app.models.models import (
    ChatMessage, 
    StandaloneChatMessage, 
    StandaloneChat,
    ConversationSummary
)

logger = logging.getLogger(__name__)


# Configuration Constants
RAG_CONTEXT_LIMIT = 5  # Number of relevant messages to retrieve
RAG_SURROUNDING_MESSAGES = 2  # Messages before/after each match
RAG_SUMMARY_MAX_MESSAGES = 50  # Max conversation length for summaries


@dataclass
class EnhancedRagContext:
    """Container for RAG context with surrounding messages and summary."""
    conversation_id: int
    conversation_type: str  # 'insight' or 'standalone'
    summary: str
    matched_message: Any  # ChatMessage or StandaloneChatMessage
    messages_before: List[Any]
    messages_after: List[Any]
    conversation_date: datetime  # Date of first message in conversation


@dataclass
class MergedRagContext:
    """
    Container for merged RAG context with multiple matches from same conversation.

    When multiple messages from the same conversation are retrieved via semantic search,
    they are merged into a single excerpt to eliminate redundancy while preserving
    all matched content and context.
    """
    conversation_id: int
    conversation_type: str  # 'insight' or 'standalone'
    summary: str
    matched_messages: List[Any]  # Multiple matched messages (sorted chronologically)
    messages_before: List[Any]  # Messages before earliest match
    messages_between: List[Any]  # Messages between earliest and latest match
    messages_after: List[Any]  # Messages after latest match
    conversation_date: datetime  # Date of first message in conversation


class RagService:
    """Service for RAG operations with enhanced context."""

    def __init__(self, embedding_client: Optional[EmbeddingClient] = None):
        self.embedding_client = embedding_client

    async def get_enhanced_rag_context(
        self,
        db: Session,
        user_id: int,
        query: str,
        conversation_type: str,  # "insight" or "standalone"
        ai_client: AIClient,
        current_conversation_id: Optional[int] = None,
        limit: int = RAG_CONTEXT_LIMIT
    ) -> List[MergedRagContext]:
        """
        Retrieve RAG context with deduplication and merged surrounding messages.

        When multiple messages from the same conversation are retrieved, they are merged
        into a single context to eliminate redundancy (duplicate summaries, overlapping
        surrounding messages) while preserving all matched content.

        Args:
            db: Database session
            user_id: User ID to filter messages
            query: Query text for semantic search
            conversation_type: Type of conversation ('insight' or 'standalone')
            ai_client: AI client for generating summaries
            current_conversation_id: ID to exclude from search
            limit: Max number of relevant messages to retrieve

        Returns:
            List of MergedRagContext objects with deduplicated summaries and merged context
        """
        if not self.embedding_client:
            logger.debug(f"No embedding client configured - RAG disabled for user {user_id}")
            return []

        # Determine which model to use based on conversation type
        if conversation_type == "insight":
            model_class = ChatMessage
            join_model = None  # ChatMessage has direct user_id
            conversation_id_field = "insight_id"
            exclude_filter = ("insight_id", current_conversation_id)
        elif conversation_type == "standalone":
            model_class = StandaloneChatMessage
            join_model = StandaloneChat
            conversation_id_field = "chat_id"
            exclude_filter = ("chat_id", current_conversation_id)
        else:
            raise ValueError(f"Invalid conversation_type: {conversation_type}")

        # Get relevant messages using semantic search
        relevant_messages = await self._get_relevant_messages(
            db=db,
            model_class=model_class,
            user_id=user_id,
            query=query,
            exclude_filter=exclude_filter if current_conversation_id else None,
            join_model=join_model,
            limit=limit
        )

        if not relevant_messages:
            return []

        # Group messages by conversation to detect and merge duplicates
        grouped_messages = self._group_by_conversation(
            relevant_messages=relevant_messages,
            conversation_id_field=conversation_id_field
        )

        logger.info(
            f"RAG retrieved {len(relevant_messages)} messages from "
            f"{len(grouped_messages)} unique conversations for user {user_id}"
        )

        # Build merged contexts with deduplication
        merged_contexts = []
        for conversation_id, conv_messages in grouped_messages.items():
            # Get or create conversation summary (only ONCE per conversation)
            summary = await self._get_or_create_conversation_summary(
                db=db,
                conversation_type=conversation_type,
                conversation_id=conversation_id,
                ai_client=ai_client,
                conversation_id_field=conversation_id_field,
                model_class=model_class
            )

            # Get conversation date (only ONCE per conversation)
            conversation_date = await self._get_conversation_date(
                db=db,
                model_class=model_class,
                conversation_id=conversation_id,
                conversation_id_field=conversation_id_field
            )

            # Get merged surrounding messages for all matches in this conversation
            merged_surrounding = await self._get_merged_surrounding_messages(
                db=db,
                model_class=model_class,
                messages=conv_messages,
                conversation_id_field=conversation_id_field,
                conversation_id=conversation_id,
                before=RAG_SURROUNDING_MESSAGES,
                after=RAG_SURROUNDING_MESSAGES
            )

            # Create merged context (one per conversation instead of one per message)
            merged_contexts.append(MergedRagContext(
                conversation_id=conversation_id,
                conversation_type=conversation_type,
                summary=summary,
                matched_messages=merged_surrounding['matched'],
                messages_before=merged_surrounding['before'],
                messages_between=merged_surrounding.get('between', []),
                messages_after=merged_surrounding['after'],
                conversation_date=conversation_date
            ))

        return merged_contexts

    def _group_by_conversation(
        self,
        relevant_messages: List,
        conversation_id_field: str
    ) -> Dict[int, List]:
        """
        Group retrieved messages by conversation_id to detect duplicates.

        When semantic search retrieves multiple messages from the same conversation,
        this method groups them together so they can be merged into a single excerpt
        instead of creating redundant separate excerpts.

        Args:
            relevant_messages: List of messages from semantic search
            conversation_id_field: Field name for conversation ID ('insight_id' or 'standalone_chat_id')

        Returns:
            Dict mapping conversation_id to list of messages from that conversation
        """
        from collections import defaultdict
        grouped = defaultdict(list)
        for msg in relevant_messages:
            conv_id = getattr(msg, conversation_id_field)
            grouped[conv_id].append(msg)
        return dict(grouped)

    async def _get_merged_surrounding_messages(
        self,
        db: Session,
        model_class: Type,
        messages: List[Any],
        conversation_id_field: str,
        conversation_id: int,
        before: int = RAG_SURROUNDING_MESSAGES,
        after: int = RAG_SURROUNDING_MESSAGES
    ) -> Dict[str, List]:
        """
        Get surrounding messages for multiple matched messages with merged ranges.

        When multiple messages from same conversation are matched, merge their
        time ranges to avoid duplicate surrounding messages in output.

        Args:
            db: Database session
            model_class: Message model class (ChatMessage or StandaloneChatMessage)
            messages: List of matched messages from same conversation
            conversation_id_field: Field name for conversation ID
            conversation_id: The conversation ID
            before: Number of messages before merged range
            after: Number of messages after merged range

        Returns:
            Dict with:
              - 'before': Messages before the earliest match
              - 'matched': All matched messages (sorted chronologically)
              - 'between': Messages between earliest and latest match
              - 'after': Messages after the latest match
        """
        try:
            # Sort matches chronologically
            sorted_matches = sorted(messages, key=lambda m: m.created_at)
            earliest_match = sorted_matches[0]
            latest_match = sorted_matches[-1]

            # Get messages before earliest match
            stmt_before = (
                select(model_class)
                .filter(
                    getattr(model_class, conversation_id_field) == conversation_id,
                    model_class.created_at < earliest_match.created_at
                )
                .order_by(model_class.created_at.desc())
                .limit(before)
            )
            result_before = db.execute(stmt_before)
            messages_before = list(reversed(result_before.scalars().all()))  # Oldest first

            # Get messages after latest match
            stmt_after = (
                select(model_class)
                .filter(
                    getattr(model_class, conversation_id_field) == conversation_id,
                    model_class.created_at > latest_match.created_at
                )
                .order_by(model_class.created_at.asc())
                .limit(after)
            )
            result_after = db.execute(stmt_after)
            messages_after = list(result_after.scalars().all())

            # Get any messages BETWEEN matches (if there are gaps)
            # These should be included in the merged excerpt
            messages_between = []
            if len(sorted_matches) > 1:
                stmt_between = (
                    select(model_class)
                    .filter(
                        getattr(model_class, conversation_id_field) == conversation_id,
                        model_class.created_at > earliest_match.created_at,
                        model_class.created_at < latest_match.created_at
                    )
                    .order_by(model_class.created_at.asc())
                )
                result_between = db.execute(stmt_between)
                messages_between = list(result_between.scalars().all())

            return {
                'before': messages_before,
                'matched': sorted_matches,
                'between': messages_between,
                'after': messages_after
            }

        except Exception as e:
            logger.error(f"Error getting merged surrounding messages: {e}", exc_info=True)
            # Fallback: return at least the matched messages
            return {
                'before': [],
                'matched': sorted(messages, key=lambda m: m.created_at),
                'between': [],
                'after': []
            }

    async def _get_relevant_messages(
        self,
        db: Session,
        model_class: Type,
        user_id: int,
        query: str,
        exclude_filter: Optional[Tuple[str, int]],
        join_model: Optional[Type],
        limit: int
    ) -> List:
        """
        Generic RAG retrieval for any message model.
        
        Args:
            db: Database session
            model_class: ChatMessage or StandaloneChatMessage
            user_id: User ID to filter by
            query: Query text for semantic search
            exclude_filter: Tuple of (field_name, value) to exclude
            join_model: Model to join for user filtering (None if direct)
            limit: Max results
            
        Returns:
            List of message objects ordered by relevance
        """
        if not self.embedding_client:
            return []

        try:
            # Generate embedding for the query
            query_vector = await self.embedding_client.get_embedding(query)
            
            # Build query
            stmt = select(model_class).filter(
                model_class.embedding.isnot(None)
            )
            
            # Add user filter - direct or via join
            if join_model:
                stmt = stmt.join(join_model).filter(join_model.user_id == user_id)
            else:
                stmt = stmt.filter(model_class.user_id == user_id)
            
            # Exclude current conversation if specified
            if exclude_filter:
                field_name, value = exclude_filter
                if value is not None:
                    stmt = stmt.filter(getattr(model_class, field_name) != value)
            
            # Order by semantic similarity
            stmt = stmt.order_by(
                model_class.embedding.cosine_distance(query_vector)
            ).limit(limit)
            
            result = db.execute(stmt)
            messages = result.scalars().all()
            
            logger.info(
                f"RAG retrieval for user {user_id}: "
                f"query='{query[:50]}...', found {len(messages)} relevant messages"
            )
            
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving relevant messages for user {user_id}: {e}", exc_info=True)
            return []

    async def _get_surrounding_messages(
        self,
        db: Session,
        model_class: Type,
        message: Any,
        conversation_id_field: str,
        before: int = 2,
        after: int = 2
    ) -> Dict[str, List]:
        """
        Get messages before and after a specific message.
        
        Args:
            db: Database session
            model_class: Message model class
            message: The matched message
            conversation_id_field: Field name for conversation ID
            before: Number of messages before
            after: Number of messages after
            
        Returns:
            Dict with 'before' and 'after' lists of messages
        """
        try:
            conversation_id = getattr(message, conversation_id_field)
            message_time = message.created_at
            
            # Get messages before (older)
            stmt_before = (
                select(model_class)
                .filter(
                    getattr(model_class, conversation_id_field) == conversation_id,
                    model_class.created_at < message_time
                )
                .order_by(model_class.created_at.desc())
                .limit(before)
            )
            result_before = db.execute(stmt_before)
            messages_before = list(reversed(result_before.scalars().all()))  # Oldest first
            
            # Get messages after (newer)
            stmt_after = (
                select(model_class)
                .filter(
                    getattr(model_class, conversation_id_field) == conversation_id,
                    model_class.created_at > message_time
                )
                .order_by(model_class.created_at.asc())
                .limit(after)
            )
            result_after = db.execute(stmt_after)
            messages_after = result_after.scalars().all()
            
            return {
                'before': messages_before,
                'after': messages_after
            }
            
        except Exception as e:
            logger.error(f"Error getting surrounding messages: {e}", exc_info=True)
            return {'before': [], 'after': []}

    async def _get_or_create_conversation_summary(
        self,
        db: Session,
        conversation_type: str,
        conversation_id: int,
        ai_client: AIClient,
        conversation_id_field: str,
        model_class: Type
    ) -> str:
        """
        Get cached summary or generate new one using AI.
        
        Args:
            db: Database session
            conversation_type: 'insight' or 'standalone'
            conversation_id: ID of the conversation
            ai_client: AI client for generating summaries
            conversation_id_field: Field name for conversation ID
            model_class: Message model class
            
        Returns:
            Summary text (1-2 sentences)
        """
        try:
            # Get current message count for this conversation
            current_count = db.query(model_class).filter(
                getattr(model_class, conversation_id_field) == conversation_id
            ).count()
            
            # Check cache
            cached = db.query(ConversationSummary).filter(
                and_(
                    ConversationSummary.conversation_type == conversation_type,
                    ConversationSummary.conversation_id == conversation_id
                )
            ).first()
            
            # Return cached if valid (message count matches)
            if cached and cached.message_count == current_count:
                logger.debug(f"Using cached summary for {conversation_type} {conversation_id}")
                return cached.summary_text
            
            # Generate new summary
            logger.info(f"Generating new summary for {conversation_type} {conversation_id}")
            summary = await self._generate_summary(
                db=db,
                model_class=model_class,
                conversation_id=conversation_id,
                conversation_id_field=conversation_id_field,
                ai_client=ai_client
            )
            
            # Update or create cache entry
            if cached:
                cached.summary_text = summary
                cached.message_count = current_count
                cached.updated_at = datetime.utcnow()
            else:
                cached = ConversationSummary(
                    conversation_type=conversation_type,
                    conversation_id=conversation_id,
                    summary_text=summary,
                    message_count=current_count
                )
                db.add(cached)
            
            db.commit()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting/creating conversation summary: {e}", exc_info=True)
            return "Previous conversation"  # Fallback

    async def _generate_summary(
        self,
        db: Session,
        model_class: Type,
        conversation_id: int,
        conversation_id_field: str,
        ai_client: AIClient
    ) -> str:
        """
        Generate conversation summary using AI.
        
        Args:
            db: Database session
            model_class: Message model class
            conversation_id: ID of the conversation
            conversation_id_field: Field name for conversation ID
            ai_client: AI client for generation
            
        Returns:
            Summary text
        """
        try:
            # Fetch last N messages from conversation
            messages = db.query(model_class).filter(
                getattr(model_class, conversation_id_field) == conversation_id
            ).order_by(model_class.created_at.desc()).limit(RAG_SUMMARY_MAX_MESSAGES).all()
            
            messages = list(reversed(messages))  # Chronological order
            
            if not messages:
                return "Empty conversation"
            
            # Format conversation for summarization
            conversation_text = "\n".join([
                f"{msg.role.capitalize()}: {msg.content[:200]}"
                for msg in messages
            ])
            
            # Use AI client to generate summary (using Haiku for cost efficiency)
            summary = await ai_client.generate_conversation_summary(conversation_text)
            
            if summary:
                return summary
            else:
                return "Discussion about biblical topics"  # Fallback
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            return "Previous conversation"

    async def _get_conversation_date(
        self,
        db: Session,
        model_class: Type,
        conversation_id: int,
        conversation_id_field: str
    ) -> datetime:
        """
        Get the date of the first message in a conversation.
        
        Args:
            db: Database session
            model_class: Message model class
            conversation_id: ID of the conversation
            conversation_id_field: Field name for conversation ID
            
        Returns:
            Datetime of first message
        """
        try:
            first_message = db.query(model_class).filter(
                getattr(model_class, conversation_id_field) == conversation_id
            ).order_by(model_class.created_at.asc()).first()
            
            if first_message:
                return first_message.created_at
            else:
                return datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error getting conversation date: {e}", exc_info=True)
            return datetime.utcnow()

    def format_enhanced_rag_context(
        self,
        enhanced_contexts: List[MergedRagContext]
    ) -> str:
        """
        Format merged RAG contexts as structured excerpts.

        Each context represents one conversation with potentially multiple
        matched messages merged together to eliminate redundancy.

        Args:
            enhanced_contexts: List of MergedRagContext objects

        Returns:
            Formatted string for system prompt injection
        """
        if not enhanced_contexts:
            return ""

        formatted_parts = ["RELEVANT CONTEXT FROM PAST CONVERSATIONS:\n"]

        for ctx in enhanced_contexts:
            # Format date
            date_str = ctx.conversation_date.strftime("%Y-%m-%d %H:%M")

            # Add summary header (ONCE per conversation, not per message)
            formatted_parts.append(
                f"\n[Summary of conversation from {date_str}: {ctx.summary}]"
            )
            formatted_parts.append("---excerpt---")

            # Add messages before earliest match
            for msg in ctx.messages_before:
                role_label = "User" if msg.role == "user" else "You"
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
                formatted_parts.append(f"{role_label} ({timestamp}): {msg.content}")

            # Add matched messages with markers
            # If multiple matches, mark each one
            for i, matched_msg in enumerate(ctx.matched_messages):
                role_label = "User" if matched_msg.role == "user" else "You"
                timestamp = matched_msg.created_at.strftime("%Y-%m-%d %H:%M")

                # Mark matched messages
                marker = "← Retrieved via semantic search"
                if len(ctx.matched_messages) > 1:
                    marker = f"← Match {i+1}/{len(ctx.matched_messages)} via semantic search"

                formatted_parts.append(
                    f"{role_label} ({timestamp}): {matched_msg.content}  {marker}"
                )

                # Add messages between matches (if this isn't the last match)
                if i < len(ctx.matched_messages) - 1:
                    # Find messages between this match and the next
                    next_match = ctx.matched_messages[i + 1]
                    between_for_this_gap = [
                        msg for msg in ctx.messages_between
                        if matched_msg.created_at < msg.created_at < next_match.created_at
                    ]
                    for between_msg in between_for_this_gap:
                        role_label = "User" if between_msg.role == "user" else "You"
                        timestamp = between_msg.created_at.strftime("%Y-%m-%d %H:%M")
                        formatted_parts.append(f"{role_label} ({timestamp}): {between_msg.content}")

            # Add messages after latest match
            for msg in ctx.messages_after:
                role_label = "User" if msg.role == "user" else "You"
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
                formatted_parts.append(f"{role_label} ({timestamp}): {msg.content}")

            formatted_parts.append("---end excerpt---\n")

        return "\n".join(formatted_parts)
