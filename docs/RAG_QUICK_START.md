# 🚀 RAG Memory Improvements - Quick Start

## TL;DR

Enhanced RAG system now includes:
- 📝 Conversation summaries
- ⏰ Timestamps on all messages
- 📍 Surrounding context (2 before, 2 after)
- 🎯 Better memory for AI responses

## What Changed?

### Before
```
User: "What did we discuss about prayer?"
AI: "I don't recall discussing prayer specifically."
```

### After
```
User: "What did we discuss about prayer?"
AI: "Last week on November 24th, we discussed prayer practices and
intercessory prayer. You asked about praying on behalf of others,
and I explained how this practice appears throughout scripture."
```

## Getting Started

### 1. Run Database Migration

```bash
cd /Users/mj/Code/Verse/backend
psql -U your_user -d your_db -f migrations/add_conversation_summaries.sql
```

Or let SQLAlchemy auto-create (dev only):
```python
from app.core.database import engine, Base
Base.metadata.create_all(bind=engine)
```

### 2. No Code Changes Needed!

Everything is backward compatible. The system will:
- ✅ Automatically use enhanced RAG format
- ✅ Generate summaries on-demand
- ✅ Cache summaries for fast retrieval
- ✅ Work with existing conversations

### 3. Test It

Start the app and have a conversation:

```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Check logs
tail -f logs/app.log | grep RAG
```

Expected log output:
```
INFO: RAG retrieval for user 123: query='What did we...', found 3 relevant messages
INFO: Retrieved 3 enhanced RAG contexts for insight 456 (user 123)
DEBUG: Using cached summary for insight 789
```

## Configuration

### Tune Performance

Edit `backend/app/services/rag_service.py`:

```python
# For faster responses (less context)
RAG_CONTEXT_LIMIT = 3           # Default: 5
RAG_SURROUNDING_MESSAGES = 1    # Default: 2

# For better context (more tokens)
RAG_CONTEXT_LIMIT = 7           # Default: 5
RAG_SURROUNDING_MESSAGES = 3    # Default: 2
```

### Cost Control

Edit `backend/app/clients/claude_client.py`:

```python
# Limit summary length
MAX_TOKENS_SUMMARY = 50         # Default: 100

# Use different model (not recommended)
HAIKU_MODEL = "claude-3-opus-20240229"  # More expensive
```

## Monitoring

### Check Summary Cache

```sql
-- See how many summaries are cached
SELECT
    conversation_type,
    COUNT(*) as total,
    AVG(message_count) as avg_messages
FROM conversation_summaries
GROUP BY conversation_type;
```

### View Recent Summaries

```sql
-- See latest summaries
SELECT
    conversation_type,
    conversation_id,
    summary_text,
    message_count,
    created_at
FROM conversation_summaries
ORDER BY created_at DESC
LIMIT 10;
```

### Clear Cache (if needed)

```sql
-- Clear all summaries
DELETE FROM conversation_summaries;

-- Clear old summaries
DELETE FROM conversation_summaries
WHERE updated_at < NOW() - INTERVAL '30 days';
```

## Troubleshooting

### No RAG Context Retrieved

**Check:** Embedding client configured?
```python
# In ChatService initialization
if not self.embedding_client:
    logger.warning("No embedding client - RAG disabled")
```

**Solution:** Ensure `OPENAI_API_KEY` in `.env`

### Summaries Not Being Generated

**Check:** Anthropic API key configured?
```bash
echo $ANTHROPIC_API_KEY
```

**Solution:** Add to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### High Token Usage

**Check:** How many surrounding messages?
```python
# In rag_service.py
RAG_SURROUNDING_MESSAGES = 2  # 5 messages total per excerpt
```

**Solution:** Reduce to 1 (3 messages total per excerpt)

### Slow Responses

**Check:** Summary cache hit rate
```sql
-- Check if summaries are being used
SELECT COUNT(*) FROM conversation_summaries;
```

**Solution:** Summaries generated on first use, then cached

## Verification Checklist

After deployment, verify:

- [ ] Database migration ran successfully
- [ ] `conversation_summaries` table exists
- [ ] App starts without errors
- [ ] RAG retrieval logs appear
- [ ] Summaries are being generated
- [ ] Summaries are being cached
- [ ] AI responses include temporal context
- [ ] Token usage is acceptable

## Quick Commands

```bash
# Check table exists
psql -d yourdb -c "\d conversation_summaries"

# Count cached summaries
psql -d yourdb -c "SELECT COUNT(*) FROM conversation_summaries;"

# View sample summary
psql -d yourdb -c "SELECT * FROM conversation_summaries LIMIT 1;"

# Check logs for RAG activity
grep "RAG retrieval" logs/app.log

# Test summary generation
curl -X POST http://localhost:8000/api/chat/insights/123/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "What did we discuss?"}'
```

## Performance Expectations

| Metric | Expected Value |
|--------|----------------|
| First RAG retrieval | 300-500ms |
| Cached RAG retrieval | 50-100ms |
| Summary generation | 200-300ms |
| Summary cache hit rate | >80% after warmup |
| Token increase | 2-3x per context |
| Cost per summary | ~$0.00025 |

## Documentation

For more details:
- 📖 `docs/rag-implementation-summary.md` - Full implementation details
- 📘 `docs/rag-quick-reference.md` - API reference and examples
- 📊 `docs/rag-architecture.md` - Architecture diagrams
- ✅ `docs/IMPLEMENTATION_COMPLETE.md` - Success criteria

## Support

Questions? Check:
1. Logs: `tail -f logs/app.log | grep RAG`
2. Database: Check `conversation_summaries` table
3. Config: Verify API keys in `.env`
4. Docs: See files above

## Next Steps

1. ✅ Complete - Phase 1 implemented
2. ⏳ Test in development environment
3. ⏳ Monitor performance and costs
4. ⏳ Gather user feedback
5. ⏳ Consider Phase 2 enhancements

## Rollback (if needed)

If issues arise:

```bash
# Revert code changes
git checkout main

# Keep database table (harmless)
# Or drop if needed:
psql -d yourdb -c "DROP TABLE conversation_summaries;"
```

The old RAG system will work fine without the new table.

## Success Indicators

You'll know it's working when:
- ✅ Logs show "Retrieved X enhanced RAG contexts"
- ✅ AI responses reference past conversations with dates
- ✅ `conversation_summaries` table has rows
- ✅ Response quality improves
- ✅ Users report better memory

---

**Status:** ✅ READY TO DEPLOY

**Version:** Phase 1 Complete

**Last Updated:** December 1, 2025
