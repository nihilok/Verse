# RAG Integration Guide

This guide shows how to integrate the RAG (Retrieval-Augmented Generation) context retrieval into your AI prompts.

## Current State

The RAG infrastructure is in place:
- ✅ Vector embeddings are generated and stored for all messages
- ✅ `_get_relevant_context()` method exists to retrieve similar messages
- ❌ **BUT:** The retrieved context is not yet used in AI prompts

## Integration Options

There are three main approaches to integrate RAG context:

### Option 1: Add to System Prompt (Recommended)

**Pros:**
- Simple implementation
- Clear separation of RAG context from conversation history
- Good for providing background context

**Cons:**
- All RAG context counts toward system message tokens
- Less flexible for very large contexts

**Implementation:**

```python
# In chat_service.py - modify send_message method

async def send_message(
    self,
    db: Session,
    insight_id: int,
    user_id: int,
    user_message: str,
    passage_text: str,
    passage_reference: str,
    insight_context: dict
) -> Optional[str]:
    # Get previous chat history for this user
    chat_history = self.get_chat_messages(db, insight_id, user_id)

    # NEW: Get relevant RAG context
    rag_context = []
    if self.embedding_client:
        try:
            rag_context = await self._get_relevant_context(db, user_id, user_message)
        except Exception as e:
            logger.warning(f"Failed to retrieve RAG context: {e}")
            # Continue without RAG context

    # Generate AI response with context
    ai_response = await self.client.generate_chat_response(
        user_message=user_message,
        passage_text=passage_text,
        passage_reference=passage_reference,
        insight_context=insight_context,
        chat_history=chat_history,
        rag_context=rag_context  # NEW parameter
    )
    # ... rest of method unchanged
```

Then modify `claude_client.py`:

```python
# In claude_client.py - modify generate_chat_response signature and system prompt

async def generate_chat_response(
    self,
    user_message: str,
    passage_text: str,
    passage_reference: str,
    insight_context: dict,
    chat_history: List,
    rag_context: List = None  # NEW parameter
) -> Optional[str]:
    try:
        # Truncate passage text if too long
        truncated_passage = passage_text[:self.MAX_PASSAGE_TEXT_LENGTH] + (
            "..." if len(passage_text) > self.MAX_PASSAGE_TEXT_LENGTH else ""
        )
        truncated_reference = passage_reference[:self.MAX_REFERENCE_LENGTH]

        # NEW: Format RAG context if provided
        rag_context_text = ""
        if rag_context and len(rag_context) > 0:
            context_items = []
            for msg in rag_context:
                # Format each retrieved message
                context_items.append(f"- {msg.role}: {msg.content[:200]}...")  # Limit each to 200 chars
            rag_context_text = "\n\nRelevant context from previous conversations:\n" + "\n".join(context_items)

        # Build the system message with context
        system_prompt = f"""You are a knowledgeable biblical scholar and theologian having a conversation about a Bible passage.

Passage Reference: {truncated_reference}
Passage Text: {truncated_passage}

You previously provided these insights:
- Historical Context: {insight_context.get('historical_context', '')[:self.MAX_CONTEXT_LENGTH]}
- Theological Significance: {insight_context.get('theological_significance', '')[:self.MAX_CONTEXT_LENGTH]}
- Practical Application: {insight_context.get('practical_application', '')[:self.MAX_CONTEXT_LENGTH]}
{rag_context_text}

Continue the conversation by answering the user's questions thoughtfully and in depth. Draw from biblical scholarship, theology, and practical wisdom. Keep your responses focused and relevant to the passage and previous insights."""

        # Rest of method unchanged...
        messages = []
        for msg in chat_history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_message})

        response = self.client.messages.create(
            model=self.MODEL_NAME,
            max_tokens=self.MAX_TOKENS_CHAT,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text
    except Exception as e:
        logger.error(f"Error generating chat response: {e}", exc_info=True)
        return None
```

### Option 2: Prepend to Chat History

**Pros:**
- RAG messages appear in natural conversation flow
- More intuitive for the AI model

**Cons:**
- Harder to distinguish between current conversation and retrieved context
- May confuse the model about conversation continuity

**Implementation:**

```python
# In chat_service.py

async def send_message(self, ...):
    # Get current conversation history
    chat_history = self.get_chat_messages(db, insight_id, user_id)

    # Get RAG context and prepend to history
    if self.embedding_client:
        try:
            rag_messages = await self._get_relevant_context(db, user_id, user_message)
            # Prepend RAG context to chat history
            chat_history = list(rag_messages) + chat_history
        except Exception as e:
            logger.warning(f"Failed to retrieve RAG context: {e}")

    # Generate AI response (no change to claude_client needed)
    ai_response = await self.client.generate_chat_response(...)
```

### Option 3: Hybrid Approach (Best for Production)

Combine both: Add a brief summary to system prompt and optionally include full messages in history.

```python
# In chat_service.py

async def send_message(self, ...):
    chat_history = self.get_chat_messages(db, insight_id, user_id)

    rag_summary = None
    rag_messages = []

    if self.embedding_client:
        try:
            rag_messages = await self._get_relevant_context(db, user_id, user_message, limit=3)

            # Create a brief summary for system prompt
            if rag_messages:
                topics = [msg.content[:100] for msg in rag_messages]
                rag_summary = f"Previously discussed: {', '.join(topics)}"
        except Exception as e:
            logger.warning(f"Failed to retrieve RAG context: {e}")

    ai_response = await self.client.generate_chat_response(
        user_message=user_message,
        passage_text=passage_text,
        passage_reference=passage_reference,
        insight_context=insight_context,
        chat_history=chat_history,
        rag_summary=rag_summary  # Brief summary in system prompt
    )
```

## Configuration Recommendations

### RAG Context Limit

The `RAG_CONTEXT_LIMIT` constant (currently 5) controls how many similar messages to retrieve. Consider making this configurable:

```python
# In backend/app/core/config.py

class Settings(BaseSettings):
    # ... existing settings ...

    # RAG Configuration
    rag_enabled: bool = True  # Master switch for RAG
    rag_context_limit: int = 5  # Number of similar messages to retrieve
    rag_similarity_threshold: float = 0.7  # Minimum similarity score (0-1)
```

Then use in `chat_service.py`:

```python
class ChatService:
    def __init__(self, embedding_client: Optional[EmbeddingClient] = None):
        self.client = ClaudeAIClient()
        settings = get_settings()

        # RAG configuration
        self.rag_enabled = settings.rag_enabled
        self.rag_context_limit = settings.rag_context_limit

        # Embedding client setup
        if embedding_client:
            self.embedding_client = embedding_client
        elif settings.openai_api_key and settings.rag_enabled:
            self.embedding_client = OpenAIEmbeddingClient(settings.openai_api_key)
        else:
            self.embedding_client = None
            if settings.rag_enabled:
                logger.warning("RAG enabled but no OpenAI API key configured")
```

### Standalone Chats

Don't forget to add the same RAG integration to standalone chats:

```python
async def send_standalone_message(
    self,
    db: Session,
    chat_id: int,
    user_id: int,
    user_message: str
) -> Optional[str]:
    chat = db.query(StandaloneChat).filter(
        StandaloneChat.id == chat_id,
        StandaloneChat.user_id == user_id
    ).first()
    if not chat:
        return None

    chat_history = self.get_standalone_chat_messages(db, chat_id, user_id)

    # NEW: Get relevant RAG context from ALL user's standalone chats
    rag_context = []
    if self.embedding_client and self.rag_enabled:
        try:
            rag_context = await self._get_relevant_standalone_context(db, user_id, user_message)
        except Exception as e:
            logger.warning(f"Failed to retrieve RAG context: {e}")

    ai_response = await self.client.generate_standalone_chat_response(
        user_message=user_message,
        passage_text=chat.passage_text,
        passage_reference=chat.passage_reference,
        chat_history=chat_history,
        rag_context=rag_context  # NEW
    )
    # ... rest unchanged
```

## Testing RAG Integration

After integrating RAG, test it works:

### 1. Verify Context Retrieval

```python
# Add to chat_service.py temporarily for testing

async def send_message(self, ...):
    # ... existing code ...

    rag_context = await self._get_relevant_context(db, user_id, user_message)

    # TEMPORARY: Log retrieved context for debugging
    if rag_context:
        logger.info(f"Retrieved {len(rag_context)} RAG contexts:")
        for msg in rag_context:
            logger.info(f"  - {msg.role}: {msg.content[:100]}...")

    # ... continue with AI response ...
```

### 2. Test Scenarios

1. **Test 1: No History**
   - Send a message with no previous conversations
   - Verify RAG context is empty

2. **Test 2: Relevant History**
   - Have a conversation about "prayer"
   - In a new chat, ask "Tell me more about prayer"
   - Check logs to verify relevant previous messages were retrieved

3. **Test 3: User Isolation**
   - User A discusses "baptism"
   - User B asks about "baptism"
   - Verify User B does NOT receive User A's context

### 3. Monitor Performance

```sql
-- Check vector search performance
EXPLAIN ANALYZE
SELECT id, content, created_at
FROM chat_messages
WHERE user_id = 1
  AND embedding IS NOT NULL
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector(1536)
LIMIT 5;
```

Should show:
- "Index Scan using idx_chat_messages_embedding_user"
- Execution time < 100ms

## Rollout Strategy

### Phase 1: Dark Launch (Recommended First Step)
1. Integrate RAG retrieval but don't use in prompts
2. Just log what would be retrieved
3. Monitor performance and relevance

```python
rag_context = await self._get_relevant_context(db, user_id, user_message)
logger.info(f"[RAG Dark Launch] Would retrieve {len(rag_context)} messages")
# Don't actually pass to AI yet
```

### Phase 2: A/B Test
1. Add a feature flag
2. Enable for 10% of users
3. Compare response quality

```python
settings = get_settings()
if settings.rag_enabled and user_id % 10 == 0:  # 10% of users
    rag_context = await self._get_relevant_context(db, user_id, user_message)
else:
    rag_context = []
```

### Phase 3: Full Rollout
1. Enable for all users
2. Monitor OpenAI embedding API costs
3. Watch for user feedback

## Cost Considerations

RAG adds minimal cost because:
- ✅ Embeddings are generated once when messages are saved
- ✅ Vector search is local (PostgreSQL), no API calls
- ✅ Only the final prompt tokens count toward Claude API costs

**Extra tokens per request:**
- ~50-200 tokens for RAG context (5 retrieved messages × 10-40 tokens each)
- Cost: ~$0.00015 - $0.0006 per chat message (negligible)

## Monitoring

Add metrics to track RAG effectiveness:

```python
# In chat_service.py

async def send_message(self, ...):
    rag_start = time.time()
    rag_context = await self._get_relevant_context(db, user_id, user_message)
    rag_duration = time.time() - rag_start

    logger.info(
        f"RAG retrieval: {len(rag_context)} results in {rag_duration:.3f}s "
        f"(user={user_id}, query_len={len(user_message)})"
    )
```

## Summary

**To integrate RAG into your prompts:**

1. **Minimal change (Option 1):** Modify `send_message()` to call `_get_relevant_context()` and pass result to `generate_chat_response()` as a new parameter
2. **Update Claude client:** Format RAG context into system prompt
3. **Test thoroughly:** Verify retrieval works and user isolation is enforced
4. **Monitor costs:** Track token usage and OpenAI API costs
5. **Iterate:** Adjust `RAG_CONTEXT_LIMIT` and similarity thresholds based on results

The infrastructure is ready - you just need to connect the retrieved context to the AI prompts!
