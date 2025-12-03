# RAG System Architecture

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Request                             │
│                  "What did we discuss about...?"                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Routes                                  │
│                   (routes.py)                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ChatService                                   │
│  • send_message()                                                │
│  • send_standalone_message()                                     │
│  • send_message_stream()                                         │
│  • send_standalone_message_stream()                              │
└────────────┬──────────────────────────────┬─────────────────────┘
             │                              │
             │ Uses                         │ Uses
             ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────────────┐
│     RagService          │    │     ClaudeAIClient              │
│  (NEW)                  │    │  • generate_chat_response()     │
│                         │    │  • generate_conversation_       │
│  • get_enhanced_rag_    │    │    summary() (NEW)              │
│    context()            │    └─────────────────────────────────┘
│  • format_enhanced_     │
│    rag_context()        │
│  • _get_relevant_       │
│    messages()           │
│  • _get_surrounding_    │
│    messages()           │
│  • _get_or_create_      │
│    conversation_        │
│    summary()            │
└────────┬────────────────┘
         │
         │ Queries
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database                                    │
│                                                                  │
│  ┌────────────────────┐  ┌──────────────────────────────────┐  │
│  │   ChatMessage      │  │   StandaloneChatMessage          │  │
│  │  • content         │  │  • content                       │  │
│  │  • embedding       │  │  • embedding                     │  │
│  │  • created_at      │  │  • created_at                    │  │
│  └────────────────────┘  └──────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │   ConversationSummary (NEW)                              │  │
│  │  • conversation_type (insight/standalone)                │  │
│  │  • conversation_id                                       │  │
│  │  • summary_text                                          │  │
│  │  • message_count (for cache invalidation)               │  │
│  │  • created_at, updated_at                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## RAG Flow Diagram

```
User asks question
      │
      ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. ChatService.send_message()                                │
│    • Receives user message                                   │
│    • Gets chat history                                       │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. RagService.get_enhanced_rag_context()                     │
│    • Generate embedding for query                            │
│    • Semantic search for relevant messages                   │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. For each relevant message found:                          │
│    ┌──────────────────────────────────────────────────────┐ │
│    │ a. Get surrounding messages                          │ │
│    │    • 2 messages before                               │ │
│    │    • 2 messages after                                │ │
│    └──────────────────────────────────────────────────────┘ │
│    ┌──────────────────────────────────────────────────────┐ │
│    │ b. Get or create conversation summary               │ │
│    │    • Check cache (conversation_summaries table)     │ │
│    │    • If cached and valid: return                    │ │
│    │    • If not cached or invalid:                      │ │
│    │      → Fetch conversation messages                  │ │
│    │      → Generate summary with Haiku                  │ │
│    │      → Cache result                                 │ │
│    └──────────────────────────────────────────────────────┘ │
│    ┌──────────────────────────────────────────────────────┐ │
│    │ c. Get conversation date                             │ │
│    │    • Query first message timestamp                   │ │
│    └──────────────────────────────────────────────────────┘ │
│    ┌──────────────────────────────────────────────────────┐ │
│    │ d. Build EnhancedRagContext object                   │ │
│    │    • Matched message                                 │ │
│    │    • Surrounding messages                            │ │
│    │    • Summary                                         │ │
│    │    • Date                                            │ │
│    └──────────────────────────────────────────────────────┘ │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. RagService.format_enhanced_rag_context()                  │
│    • Format as structured excerpts                           │
│    • Add summary headers                                     │
│    • Add timestamps to all messages                          │
│    • Mark semantically matched message                       │
└────────────┬─────────────────────────────────────────────────┘
             │
             │ Returns formatted string
             ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. ClaudeAIClient.generate_chat_response()                   │
│    • Inject RAG context into system prompt                   │
│    • Include chat history                                    │
│    • Generate AI response                                    │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. ChatService saves messages                                │
│    • Save user message with embedding                        │
│    • Save AI response with embedding                         │
│    • Commit to database                                      │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
      Return response to user
```

## Data Flow Example

### Input: User Query
```
User: "What did we discuss about prayer last week?"
```

### Step 1: Semantic Search
```
Query Embedding: [0.123, -0.456, 0.789, ...]
                         ↓
                 Vector Search
                         ↓
Top 5 Relevant Messages Found:
  - Message ID 101 from Insight 10 (cosine distance: 0.15)
  - Message ID 234 from Insight 15 (cosine distance: 0.18)
  - Message ID 567 from Standalone 5 (cosine distance: 0.22)
  ...
```

### Step 2: Enrich Each Match
```
For Message ID 101:
├─ Get Surrounding Messages
│  ├─ Message 99 (before)
│  ├─ Message 100 (before)
│  ├─ Message 101 (matched) ← Semantic match
│  ├─ Message 102 (after)
│  └─ Message 103 (after)
│
├─ Get/Create Summary
│  ├─ Check cache: conversation_summaries
│  │  WHERE conversation_type = 'insight'
│  │  AND conversation_id = 10
│  │
│  ├─ If not cached:
│  │  ├─ Fetch all messages from Insight 10
│  │  ├─ Call Haiku: "Summarize this conversation..."
│  │  └─ Cache result with message_count = 50
│  │
│  └─ Return: "Discussion about prayer practices and scripture"
│
└─ Get Conversation Date
   └─ First message: 2024-11-24 10:30
```

### Step 3: Format Output
```
RELEVANT CONTEXT FROM PAST CONVERSATIONS:

[Summary of conversation from 2024-11-24 10:30: Discussion about
prayer practices and scripture]
---excerpt---
You (2024-11-24 10:45): Prayer in scripture has multiple dimensions.
User (2024-11-24 10:47): Can you explain more about intercessory prayer?  ← Retrieved via semantic search
You (2024-11-24 10:50): Intercessory prayer means praying on behalf of others.
You (2024-11-24 10:52): This practice is seen throughout the Bible.
---end excerpt---

[Summary of conversation from 2024-11-20 14:15: Questions about
daily prayer routines]
---excerpt---
...
---end excerpt---
```

## Cache Behavior

### Cache Hit (Fast Path)
```
Request: Summary for Insight 10
              ↓
Query conversation_summaries
WHERE conversation_type = 'insight'
AND conversation_id = 10
              ↓
Found: summary_text = "Discussion about prayer..."
       message_count = 50
              ↓
Count current messages: SELECT COUNT(*) FROM chat_messages
                        WHERE insight_id = 10
              ↓
Current count = 50 (matches!)
              ↓
✓ Return cached summary
              ↓
Total time: ~10ms
```

### Cache Miss or Invalidation (Slow Path)
```
Request: Summary for Insight 10
              ↓
Query conversation_summaries
WHERE conversation_type = 'insight'
AND conversation_id = 10
              ↓
Not found OR message_count doesn't match
              ↓
Fetch messages: SELECT * FROM chat_messages
                WHERE insight_id = 10
                ORDER BY created_at DESC
                LIMIT 50
              ↓
Format conversation text
              ↓
Call Haiku API: "Summarize this conversation..."
              ↓
Receive summary: "Discussion about prayer..."
              ↓
Save to cache: INSERT INTO conversation_summaries
               (conversation_type, conversation_id,
                summary_text, message_count)
               VALUES ('insight', 10, '...', 52)
              ↓
✓ Return new summary
              ↓
Total time: ~300ms (first time only)
```

## Component Responsibilities

### RagService
- ✅ Semantic search coordination
- ✅ Surrounding message retrieval
- ✅ Summary caching management
- ✅ Context formatting
- ❌ NOT responsible for AI generation
- ❌ NOT responsible for message persistence

### ChatService
- ✅ Chat flow orchestration
- ✅ Message persistence
- ✅ Embedding generation
- ✅ Chat history management
- ❌ NOT responsible for RAG logic
- ❌ NOT responsible for formatting

### ClaudeAIClient
- ✅ AI response generation
- ✅ Summary generation (Haiku)
- ✅ Prompt construction
- ❌ NOT responsible for RAG retrieval
- ❌ NOT responsible for caching

## Configuration Points

```python
# app/services/rag_service.py
RAG_CONTEXT_LIMIT = 5           # Tune for relevance vs. cost
RAG_SURROUNDING_MESSAGES = 2    # Tune for context vs. tokens
RAG_SUMMARY_MAX_MESSAGES = 50   # Tune for quality vs. performance

# app/clients/claude_client.py
HAIKU_MODEL = "claude-3-haiku-20240307"  # Fast & cheap
MAX_TOKENS_SUMMARY = 100                  # Keep summaries concise
```

## Performance Characteristics

| Operation | Time (Cached) | Time (Uncached) | Cost |
|-----------|---------------|-----------------|------|
| Semantic Search | ~50ms | ~50ms | Free |
| Get Surrounding Messages | ~10ms | ~10ms | Free |
| Get Summary | ~10ms | ~300ms | $0.00025 |
| Format Context | ~5ms | ~5ms | Free |
| **Total RAG** | **~75ms** | **~365ms** | **~$0.00025** |

*Times are approximate and depend on message count and database performance*

## Error Handling Flow

```
Any step fails
      │
      ▼
Log error with context
      │
      ▼
Return fallback value
      │
      ├─ No embedding client → return []
      ├─ Semantic search fails → return []
      ├─ Surrounding messages fail → return {'before': [], 'after': []}
      ├─ Summary generation fails → return "Previous conversation"
      └─ Format fails → return ""
      │
      ▼
Continue execution
(Graceful degradation)
```

## Database Indexes

Critical indexes for performance:

```sql
-- Existing indexes (already present)
CREATE INDEX idx_chat_messages_embedding_user
ON chat_messages USING hnsw (embedding vector_cosine_ops);

CREATE INDEX idx_chat_messages_user_created
ON chat_messages(user_id, created_at);

-- New index (from migration)
CREATE UNIQUE INDEX idx_conversation_lookup
ON conversation_summaries(conversation_type, conversation_id);
```

## Summary

The new architecture:
- ✅ **Modular:** Clear separation of concerns
- ✅ **Scalable:** Efficient caching and indexes
- ✅ **Maintainable:** Well-documented and tested
- ✅ **Reliable:** Graceful error handling
- ✅ **Performant:** Fast with caching, acceptable without
- ✅ **Cost-effective:** Cheap summaries, cached aggressively
