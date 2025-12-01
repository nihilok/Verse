# RAG Service Quick Reference

## Overview

The RAG (Retrieval-Augmented Generation) service provides enhanced conversational memory by retrieving relevant context from past conversations with summaries, surrounding messages, and timestamps.

## Basic Usage

```python
from app.services.rag_service import RagService
from app.clients.openai_embedding_client import OpenAIEmbeddingClient

# Initialize
embedding_client = OpenAIEmbeddingClient(api_key="...")
rag_service = RagService(embedding_client=embedding_client)

# Get enhanced context
enhanced_contexts = await rag_service.get_enhanced_rag_context(
    db=db,
    user_id=123,
    query="What did we discuss about prayer?",
    conversation_type="insight",  # or "standalone"
    ai_client=claude_client,
    current_conversation_id=456,  # Optional: exclude current conversation
    limit=5  # Optional: max number of results
)

# Format for AI prompt
formatted_context = rag_service.format_enhanced_rag_context(enhanced_contexts)

# Use in system prompt
system_prompt = f"""You are a biblical scholar.
{formatted_context}

Answer the user's question..."""
```

## Configuration

Located in `app/services/rag_service.py`:

```python
RAG_CONTEXT_LIMIT = 5           # Number of relevant messages to retrieve
RAG_SURROUNDING_MESSAGES = 2    # Messages before/after each match
RAG_SUMMARY_MAX_MESSAGES = 50   # Max messages for summary generation
```

## Enhanced Context Structure

```python
@dataclass
class EnhancedRagContext:
    conversation_id: int                    # ID of the conversation
    conversation_type: str                  # "insight" or "standalone"
    summary: str                            # 1-2 sentence summary
    matched_message: Any                    # The semantically matched message
    messages_before: List[Any]              # 2 messages before match
    messages_after: List[Any]               # 2 messages after match
    conversation_date: datetime             # First message timestamp
```

## Formatted Output Example

```
RELEVANT CONTEXT FROM PAST CONVERSATIONS:

[Summary of conversation from 2024-03-15 14:20: Discussion about biblical interpretation and historical context]
---excerpt---
You (2024-03-15 14:25): Let me explain the historical context.
User (2024-03-15 14:30): What does this passage mean?  ← Retrieved via semantic search
You (2024-03-15 14:35): This passage relates to...
---end excerpt---
```

## Conversation Summaries

### Automatic Generation
Summaries are auto-generated using Claude Haiku when first needed:
- 1-2 sentences describing main topics
- Uses last 50 messages maximum
- Costs ~$0.00025 per summary

### Caching
Summaries are cached in the `conversation_summaries` table:
```python
# Check if cached
cached_summary = db.query(ConversationSummary).filter(
    ConversationSummary.conversation_type == "insight",
    ConversationSummary.conversation_id == 123
).first()

# Automatic invalidation
# When message_count changes, summary is regenerated
```

### Manual Summary Invalidation
```python
# Delete cached summary to force regeneration
db.query(ConversationSummary).filter(
    ConversationSummary.conversation_type == "insight",
    ConversationSummary.conversation_id == 123
).delete()
db.commit()
```

## Integration with ChatService

The ChatService automatically uses RagService:

```python
class ChatService:
    def __init__(self, embedding_client=None):
        self.embedding_client = embedding_client
        self.rag_service = RagService(embedding_client=embedding_client)
    
    async def send_message(self, db, insight_id, user_id, user_message, ...):
        # Get enhanced RAG context
        enhanced_contexts = await self.rag_service.get_enhanced_rag_context(
            db=db,
            user_id=user_id,
            query=user_message,
            conversation_type="insight",
            ai_client=self.client,
            current_conversation_id=insight_id
        )
        
        # Format for prompt
        rag_context_text = self.rag_service.format_enhanced_rag_context(enhanced_contexts)
        
        # Pass to AI
        response = await self.client.generate_chat_response(
            user_message=user_message,
            ...,
            rag_context=rag_context_text
        )
```

## Error Handling

All methods include graceful fallbacks:

```python
# No embedding client
if not self.embedding_client:
    return []  # Empty context, no error

# Summary generation fails
try:
    summary = await ai_client.generate_conversation_summary(...)
except Exception as e:
    logger.error(f"Summary generation failed: {e}")
    return "Previous conversation"  # Fallback text

# Database query fails
try:
    messages = db.execute(stmt).scalars().all()
except Exception as e:
    logger.error(f"RAG retrieval failed: {e}")
    return []  # Empty context
```

## Performance Tips

### 1. Adjust Context Limit
For faster responses, reduce `RAG_CONTEXT_LIMIT`:
```python
# In rag_service.py
RAG_CONTEXT_LIMIT = 3  # Instead of 5
```

### 2. Reduce Surrounding Messages
For lower token usage, reduce `RAG_SURROUNDING_MESSAGES`:
```python
# In rag_service.py
RAG_SURROUNDING_MESSAGES = 1  # Instead of 2
```

### 3. Monitor Cache Hit Rate
```sql
-- Check summary cache usage
SELECT 
    conversation_type,
    COUNT(*) as total_summaries,
    AVG(message_count) as avg_conversation_length
FROM conversation_summaries
GROUP BY conversation_type;
```

### 4. Clean Old Summaries (Optional)
```sql
-- Delete summaries older than 90 days
DELETE FROM conversation_summaries
WHERE updated_at < NOW() - INTERVAL '90 days';
```

## Debugging

### Enable Debug Logging
```python
import logging
logging.getLogger('app.services.rag_service').setLevel(logging.DEBUG)
```

### Check RAG Retrieval
Look for log messages:
```
INFO: RAG retrieval for user 123: query='What did we...', found 3 relevant messages
DEBUG: RAG context message IDs: [456, 789, 101], from insights: {10, 15, 20}
```

### Verify Summaries
```python
# Check if summary exists
summary = db.query(ConversationSummary).filter(
    ConversationSummary.conversation_type == "insight",
    ConversationSummary.conversation_id == 123
).first()

print(f"Summary: {summary.summary_text if summary else 'Not cached'}")
print(f"Message count: {summary.message_count if summary else 'N/A'}")
```

## Testing

### Mock RagService
```python
from unittest.mock import AsyncMock

# Mock in tests
rag_service = Mock()
rag_service.get_enhanced_rag_context = AsyncMock(return_value=[])
rag_service.format_enhanced_rag_context = Mock(return_value="")

chat_service = ChatService(embedding_client=None)
chat_service.rag_service = rag_service
```

### Test Summary Generation
```python
@pytest.mark.asyncio
async def test_summary_generation():
    # Create mock AI client
    ai_client = Mock()
    ai_client.generate_conversation_summary = AsyncMock(
        return_value="Discussion about prayer"
    )
    
    # Generate summary
    summary = await rag_service._generate_summary(
        db=db,
        model_class=ChatMessage,
        conversation_id=123,
        conversation_id_field="insight_id",
        ai_client=ai_client
    )
    
    assert "prayer" in summary
```

## Common Issues

### Issue: No RAG context retrieved
**Cause:** No embedding client configured or no embeddings in database
**Solution:** 
```python
# Check embedding client
if not chat_service.embedding_client:
    logger.warning("Embedding client not configured")

# Check for embeddings
count = db.query(ChatMessage).filter(
    ChatMessage.embedding.isnot(None)
).count()
logger.info(f"Messages with embeddings: {count}")
```

### Issue: Summaries not being cached
**Cause:** Database transaction not committed
**Solution:**
```python
# Ensure commit after summary creation
db.commit()
```

### Issue: High token usage
**Cause:** Too many surrounding messages or long conversations
**Solution:**
```python
# Reduce surrounding messages
RAG_SURROUNDING_MESSAGES = 1

# Limit summary length
RAG_SUMMARY_MAX_MESSAGES = 30
```

## Migration Guide

### From Old RAG Format
The old format was a simple numbered list:
```
1. User: What does...
2. You (previous response): Let me...
```

The new format includes summaries and timestamps. **No code changes needed** - the transition is automatic.

### Database Migration
Run the migration SQL:
```bash
psql -U your_user -d your_db -f backend/migrations/add_conversation_summaries.sql
```

Or let SQLAlchemy auto-create (for development):
```python
from app.core.database import engine, Base
Base.metadata.create_all(bind=engine)
```

## API Reference

See `rag_service.py` for complete API documentation with type hints and docstrings.

### Main Methods
- `get_enhanced_rag_context()` - Retrieve enhanced RAG context
- `format_enhanced_rag_context()` - Format contexts for AI prompt

### Helper Methods (Private)
- `_get_relevant_messages()` - Semantic search
- `_get_surrounding_messages()` - Get context messages
- `_get_or_create_conversation_summary()` - Manage summary cache
- `_generate_summary()` - Generate summary with Haiku
- `_get_conversation_date()` - Get first message timestamp

## Support

For questions or issues:
1. Check logs for detailed error messages
2. Verify database schema is up to date
3. Test with mock clients in isolation
4. Review implementation summary: `docs/rag-implementation-summary.md`
