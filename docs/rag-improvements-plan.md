# RAG Memory Improvements + Refactoring Plan

## Overview

Enhance RAG context formatting to feel more like "memory" by adding conversation summaries, temporal context, and surrounding messages. Additionally, refactor the codebase to eliminate ~577 lines of duplication and improve adherence to DRY and Single Responsibility principles.

## Current State

- RAG retrieves top 5 similar messages using pgvector cosine similarity
- Context shown as numbered list with 500-char previews
- No conversation summaries, timestamps, or surrounding messages
- Significant code duplication across RAG retrieval, message saving, and prompt building

## Proposed Changes

### Part 1: RAG Memory Enhancement

#### 1. Enhanced Context Retrieval

**What:** For each RAG-matched message, retrieve surrounding messages (before/after) to provide richer context.

**How:**

- Modify RAG retrieval to get N messages before and after each match
- Use `created_at` timestamp ordering within same conversation
- Group by conversation (insight_id or chat_id)

**Configuration:**

- Messages before/after: **2 each** (5 total messages per excerpt including the match)
- Hardcoded constant: `RAG_SURROUNDING_MESSAGES = 2`

#### 2. Conversation Summarization

**What:** Generate concise summaries of entire conversations using Haiku model.

**How:**

- For each unique conversation containing RAG results, fetch all messages
- Use Claude Haiku to generate 1-2 sentence summary
- Include summary header before each excerpt

**Caching Strategy:** Cache with TTL/invalidation

- Add `conversation_summaries` table with columns:
  - `id`, `conversation_type` (insight/standalone), `conversation_id`, `summary_text`, `created_at`, `updated_at`
  - Composite unique index on (conversation_type, conversation_id)
- Invalidate when new messages added to conversation
- Check cache before generating summary
- Store conversation message count to detect changes

#### 3. Enhanced Formatting

**What:** Format RAG context as structured excerpts with summaries and timestamps.

**Format:**

```
[Summary of Conversation from {date}: {summary_text}]
---excerpt---
[Message from User at {timestamp}: {message_text}]
[Message from Agent at {timestamp}: {message_text}]
[Message from User at {timestamp}: {message_text}] <-- Retrieved via semantic search
[Message from Agent at {timestamp}: {message_text}]
---end excerpt---
```

**Implementation:**

- Extract to new method (e.g., `_format_enhanced_rag_context()`)
- Replace current `_format_rag_context()` usage
- Include full timestamps from `created_at` field

### Part 2: Code Refactoring (DRY + SRP)

#### High Priority Refactoring

**1. Extract Message Persistence Logic**

- **Issue:** Message saving duplicated 6 times across streaming/non-streaming methods
- **Solution:** Create `_save_message_pair()` helper
- **Impact:** Eliminates ~200 lines

**2. Unify RAG Context Retrieval**

- **Issue:** `_get_relevant_context()` and `_get_relevant_standalone_context()` are 95% identical
- **Solution:** Create generic `_get_relevant_context_generic()` accepting model class, filters
- **Impact:** Eliminates ~60 lines

**3. Consolidate System Prompt Building**

- **Issue:** Prompt construction duplicated 4 times (streaming/non-streaming × insight/standalone)
- **Solution:** Extract `_build_system_prompt()` helper
- **Impact:** Eliminates ~80 lines

**4. Fix Conversation Message Building**

- **Issue:** Helper exists but not used consistently in non-streaming methods
- **Solution:** Use existing `_build_conversation_messages()` everywhere
- **Impact:** Eliminates ~30 lines, improves consistency

#### Medium Priority Refactoring

**5. Extract RAG Retrieval Pattern**

- **Issue:** RAG fetching with error handling duplicated 4 times
- **Solution:** Create `_get_rag_context_safe()` wrapper
- **Impact:** Eliminates ~32 lines

**6. Consolidate Streaming Pattern**

- **Issue:** Streaming logic duplicated 3 times
- **Solution:** Extract generic streaming handler
- **Impact:** Eliminates ~150 lines

## Implementation Strategy: Incremental Approach

**Chosen Strategy:** Refactor RAG code first, add features to clean foundation, then finish remaining refactoring.

### Phase 1: Extract RagService & Refactor RAG Code

1. Create `backend/app/services/rag_service.py`
2. Extract RAG retrieval logic from ChatService to RagService
3. Unify `_get_relevant_context()` and `_get_relevant_standalone_context()` into generic method
4. Add summary caching infrastructure

### Phase 2: Implement RAG Memory Features

5. Add conversation summary generation using Haiku
6. Implement surrounding message retrieval (2 before, 2 after)
7. Create enhanced formatting with timestamps and excerpts
8. Integrate with existing ChatService methods

### Phase 3: Finish Remaining Refactoring

9. Extract message persistence logic
10. Consolidate system prompt building
11. Fix conversation message building inconsistencies
12. Extract streaming patterns

## Files to Modify

### Core Changes

- `backend/app/services/chat_service.py` - RAG retrieval, message saving, streaming
- `backend/app/clients/claude_client.py` - Prompt building, formatting
- `backend/app/clients/anthropic_client.py` (if exists) - Haiku client for summaries

### New Files

- `backend/app/services/rag_service.py` - **Required** - RAG logic extraction
- `backend/app/models/models.py` - **Modified** - Add ConversationSummary model

### Testing

- `backend/tests/test_rag_service.py` - **New** - Test RagService methods
- `backend/tests/test_chat_service.py` - Update tests for refactored methods
- Mock embedding client and AI client in tests
- Test summary caching and invalidation
- Test surrounding message retrieval
- Test enhanced formatting output

## Detailed Implementation Plan

### Phase 1: Extract RagService & Refactor RAG Code

#### Step 1.1: Create RagService Class

**File:** `backend/app/services/rag_service.py`

**Class structure:**

```python
class RagService:
    def __init__(self, embedding_client: Optional[OpenAIEmbeddingClient]):
        self.embedding_client = embedding_client

    async def get_enhanced_rag_context(
        self,
        db: Session,
        user_id: int,
        query: str,
        conversation_type: str,  # "insight" or "standalone"
        current_conversation_id: Optional[int] = None,
        limit: int = RAG_CONTEXT_LIMIT
    ) -> List[EnhancedRagContext]:
        """Retrieve RAG context with summaries and surrounding messages."""

    async def _get_relevant_messages(
        self,
        db: Session,
        model_class: Type,
        user_id: int,
        query: str,
        exclude_filter: Optional[tuple],
        join_model: Optional[Type],
        limit: int
    ) -> List:
        """Generic RAG retrieval for any message model."""

    async def _get_surrounding_messages(
        self,
        db: Session,
        model_class: Type,
        message: Any,
        conversation_id_field: str,
        before: int = 2,
        after: int = 2
    ) -> Dict[str, List]:
        """Get messages before and after a specific message."""

    async def _get_or_create_conversation_summary(
        self,
        db: Session,
        conversation_type: str,
        conversation_id: int,
        ai_client: AIClient
    ) -> str:
        """Get cached summary or generate new one using Haiku."""

    def _format_enhanced_context(
        self,
        enhanced_contexts: List[EnhancedRagContext]
    ) -> str:
        """Format contexts as structured excerpts with summaries."""
```

**Data classes:**

```python
@dataclass
class EnhancedRagContext:
    conversation_id: int
    conversation_type: str
    summary: str
    matched_message: Any
    messages_before: List[Any]
    messages_after: List[Any]
```

#### Step 1.2: Add ConversationSummary Model

**File:** `backend/app/models/models.py`

**Add new table:**

```python
class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"

    id = Column(Integer, primary_key=True, index=True)
    conversation_type = Column(String(20), nullable=False)  # 'insight' or 'standalone'
    conversation_id = Column(Integer, nullable=False)
    summary_text = Column(Text, nullable=False)
    message_count = Column(Integer, nullable=False)  # For invalidation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_conversation_lookup', 'conversation_type', 'conversation_id', unique=True),
    )
```

**Migration:** Create table on first app startup (SQLAlchemy creates all tables automatically)

#### Step 1.3: Implement Generic RAG Retrieval

**Consolidates:** `_get_relevant_context()` and `_get_relevant_standalone_context()`

**Logic:**

- Accept model class (ChatMessage or StandaloneChatMessage)
- Handle joins dynamically based on join_model parameter
- Use same vector search logic for both types
- Return consistent format

#### Step 1.4: Implement Surrounding Message Retrieval

**Algorithm:**

1. Get matched message's `created_at` and conversation ID
2. Query messages with same conversation ID
3. Filter: `created_at < matched.created_at` ORDER BY `created_at DESC` LIMIT 2 (before)
4. Filter: `created_at > matched.created_at` ORDER BY `created_at ASC` LIMIT 2 (after)
5. Return dict with 'before' and 'after' lists

#### Step 1.5: Implement Summary Caching with Invalidation

**Get or Create Summary:**

1. Query `ConversationSummary` by (type, id)
2. If exists: Check if `message_count` matches current conversation message count
3. If match: Return cached summary
4. If mismatch or doesn't exist: Generate new summary
5. Update/insert summary with new message count

**Summary Generation:**

1. Fetch all messages from conversation (limited to last 50 for performance)
2. Format as conversation history
3. Call Haiku with prompt: "Summarize this conversation in 1-2 sentences focusing on the main topics discussed"
4. Store result with current message count

**Invalidation happens implicitly:** When message count changes, cache is stale and regenerated

#### Step 1.6: Implement Enhanced Formatting

**Format:**

```
RELEVANT CONTEXT FROM PAST CONVERSATIONS:

[Summary of conversation from {first_message_date}: {summary_text}]
---excerpt---
User ({timestamp}): {message_text}
You ({timestamp}): {message_text}
User ({timestamp}): {message_text}  ← Retrieved via semantic search
You ({timestamp}): {message_text}
---end excerpt---

[Summary of conversation from {date}: {summary_text}]
---excerpt---
...
---end excerpt---
```

**Timestamp format:** `2024-03-15 14:30` (human-readable)

#### Step 1.7: Integrate RagService into ChatService

**Changes to `chat_service.py`:**

1. Add `rag_service: RagService` to constructor
2. Replace RAG retrieval calls with `rag_service.get_enhanced_rag_context()`
3. Pass RagService to routes via dependency injection
4. Update all 4 locations where RAG context is retrieved

---

### Phase 2: Implement RAG Memory Features

#### Step 2.1: Update ClaudeAIClient

**File:** `backend/app/clients/claude_client.py`

**Changes:**

- Update `_format_rag_context()` to handle new enhanced format (or remove if RagService handles formatting)
- Ensure system prompt injection works with new multiline format
- No changes needed if RagService returns formatted string

#### Step 2.2: Add Haiku Summary Method to AIClient

**Option A:** Add to existing `ClaudeAIClient`

```python
async def generate_conversation_summary(
    self,
    messages: List[Dict[str, str]]
) -> Optional[str]:
    """Generate conversation summary using Haiku (cheap, fast)."""
    # Use claude-3-haiku-20240307
    # Max 500 tokens
    # Simple prompt
```

**Option B:** Create separate client

- Create `HaikuSummaryClient` for cost optimization
- Cleaner separation but more complexity

**Recommendation:** Option A (simpler, same infrastructure)

#### Step 2.3: Testing Integration

**Test scenarios:**

1. RAG with single conversation - summary generated once, cached
2. RAG with multiple conversations - multiple summaries
3. Cache hit - no Haiku call
4. Cache invalidation - new message added, summary regenerated
5. Surrounding messages - correct before/after retrieval
6. Timestamps formatted correctly
7. Graceful degradation if summary fails

---

### Phase 3: Finish Remaining Refactoring

#### Step 3.1: Extract Message Persistence Logic

**Create:** `_save_message_pair()` helper in ChatService

**Signature:**

```python
async def _save_message_pair(
    self,
    db: Session,
    model_class: Type,
    context_id_field: str,
    context_id: int,
    user_id: Optional[int],
    user_message: str,
    ai_response: str,
    stop_reason: Optional[str] = None
) -> Tuple[Any, Any]:
    """Save user and AI messages with embeddings."""
```

**Replace in 6 locations:**

- `send_message()` - line 226
- `create_standalone_chat()` - line 342
- `create_standalone_chat_stream()` - line 436
- `send_standalone_message()` - line 532
- `send_message_stream()` - line 684
- `send_standalone_message_stream()` - line 788

#### Step 3.2: Consolidate System Prompt Building

**Create:** `_build_chat_system_prompt()` helper in ClaudeAIClient

**Signature:**

```python
def _build_chat_system_prompt(
    self,
    prompt_type: str,  # "insight" or "standalone"
    passage_text: Optional[str],
    passage_reference: Optional[str],
    insight_context: Optional[dict],
    rag_context_text: str
) -> str:
```

**Replace in 4 locations:**

- `generate_chat_response()` - line 270
- `generate_standalone_chat_response()` - line 341
- `generate_chat_response_stream()` - line 425
- `generate_standalone_chat_response_stream()` - line 493

#### Step 3.3: Fix Conversation Message Building

**Current issue:** Non-streaming methods duplicate `_build_conversation_messages()` logic

**Fix:**

- Use existing helper in `generate_chat_response()` (lines 284-297)
- Use existing helper in `generate_standalone_chat_response()` (lines 361-374)

#### Step 3.4: Extract Streaming Pattern (Optional)

**Lower priority** - Can be done later if time permits

**Create:** `_stream_response()` generic handler

---

### Phase 4: Database Schema Updates

#### New Table: conversation_summaries

```sql
CREATE TABLE conversation_summaries (
    id SERIAL PRIMARY KEY,
    conversation_type VARCHAR(20) NOT NULL,
    conversation_id INTEGER NOT NULL,
    summary_text TEXT NOT NULL,
    message_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_conversation_lookup
ON conversation_summaries(conversation_type, conversation_id);
```

**Note:** No foreign keys since conversation_id can point to two different tables
**Cleanup:** Manual cleanup needed if conversations deleted (add to deletion logic)

---

### Phase 5: Configuration Constants

**Add to `chat_service.py`:**

```python
RAG_CONTEXT_LIMIT = 5  # Existing
RAG_SURROUNDING_MESSAGES = 2  # New - messages before/after
RAG_SUMMARY_MAX_MESSAGES = 50  # New - limit conversation length for summaries
```

**Add to `claude_client.py`:**

```python
MAX_TOKENS_SUMMARY = 500  # New - for Haiku summaries
HAIKU_MODEL = "claude-3-haiku-20240307"  # New - model for summaries
```

## Performance Considerations

**Token Usage:**

- Enhanced RAG format will increase system prompt size
- Summaries add ~50-100 tokens per conversation
- Surrounding messages add ~100-300 tokens per excerpt
- Estimate: 2-5x current RAG token usage

**Database Queries:**

- Retrieving surrounding messages: Additional queries per RAG result
- Fetching full conversations for summaries: More expensive queries
- Mitigation: Use efficient joins, limit conversation length

**API Costs:**

- Haiku calls for summaries: ~$0.00025 per summary (cheap)
- Cached summaries reduce repeat costs
- Trade-off: Storage vs compute

**Latency:**

- Summary generation adds 200-500ms per unique conversation
- Parallel summary generation possible
- Cached summaries eliminate latency on repeat requests

## Implementation Order (Step-by-Step)

1. **Create ConversationSummary model** - Add to models.py, test table creation
2. **Create RagService skeleton** - Empty class with method stubs
3. **Implement generic RAG retrieval** - Unify two methods into one
4. **Implement surrounding message retrieval** - Query before/after messages
5. **Implement summary generation with Haiku** - Add method to ClaudeAIClient
6. **Implement summary caching** - Cache get/set with invalidation
7. **Implement enhanced formatting** - Format excerpts with timestamps
8. **Wire up RagService** - Integrate into ChatService, update 4 call sites
9. **Test RAG enhancements** - Write comprehensive tests
10. **Extract message persistence** - Create `_save_message_pair()`, replace 6 usages
11. **Consolidate prompt building** - Create `_build_chat_system_prompt()`, replace 4 usages
12. **Fix message building** - Use existing helper consistently
13. **Final testing** - Full integration test, verify duplication eliminated

## Success Criteria

✅ RAG context includes conversation summaries generated by Haiku
✅ Summaries cached in database with invalidation on new messages
✅ Each RAG match shows 2 messages before and 2 after (5 total per excerpt)
✅ Timestamps visible in format "YYYY-MM-DD HH:MM"
✅ Context formatted as structured excerpts with clear delimiters
✅ RagService extracted from ChatService (separation of concerns)
✅ Code duplication reduced by ~500+ lines
✅ All existing tests pass
✅ New tests cover RAG memory features and caching

## Risk Mitigation

**Risk:** Summary generation increases latency

- **Mitigation:** Cache aggressively, use fast Haiku model, generate in parallel

**Risk:** Database schema change without migrations

- **Mitigation:** SQLAlchemy auto-creates tables, document manual cleanup needed

**Risk:** Token usage increases significantly

- **Mitigation:** Monitor and adjust surrounding message count if needed, truncate summaries

**Risk:** Breaking existing RAG functionality

- **Mitigation:** Incremental approach, test at each step, feature flag if needed

**Risk:** Summary cache grows unbounded

- **Mitigation:** Add periodic cleanup job (future work), TTL-based deletion (optional)
