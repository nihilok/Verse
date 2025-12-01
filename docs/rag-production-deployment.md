# RAG Production Deployment Guide

This guide covers deploying the RAG (Retrieval-Augmented Generation) feature to production safely, with zero downtime and data preservation.

## Prerequisites

- Production PostgreSQL database (version 16+)
- Access to production database (with superuser or appropriate permissions to install extensions)
- OpenAI API key
- Ability to deploy new backend code
- Backup of production database (always!)

## Deployment Strategy Overview

The RAG implementation is designed for **zero-downtime deployment** with these safety features:

1. **Nullable embedding columns** - New columns are optional, so existing code continues working
2. **Graceful degradation** - If OpenAI API key is missing, RAG is disabled but chat still works
3. **Backward compatible** - Old messages without embeddings work fine
4. **Progressive rollout** - Can backfill embeddings gradually after deployment

## Step-by-Step Production Deployment

### Phase 1: Pre-Deployment (Backup & Preparation)

#### 1.1 Backup Your Database

```bash
# Create a full database backup before any changes
pg_dump $PRODUCTION_DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### 1.2 Verify PostgreSQL Version

```bash
# Connect to production database
psql $PRODUCTION_DATABASE_URL -c "SELECT version();"
```

**Required:** PostgreSQL 16 or higher for optimal pgvector support. If using PostgreSQL 15 or earlier, pgvector will still work but with fewer optimisation options.

### Phase 2: Database Migration (Enable pgvector)

#### 2.1 Enable pgvector Extension

**Option A: Using Migration Script (Recommended)**

```bash
# If you have SSH/kubectl access to backend in production:
# Deploy the new code first, then run:
<production-command> uv run python -m migrations.enable_vector

# Example for Kubernetes:
kubectl exec -it <backend-pod> -- uv run python -m migrations.enable_vector

# Example for Docker:
docker exec -it <backend-container> uv run python -m migrations.enable_vector
```

**Option B: Direct Database Access**

```bash
# Connect to production database
psql $PRODUCTION_DATABASE_URL

# Enable the extension
CREATE EXTENSION IF NOT EXISTS vector;

# Verify installation
\dx vector
```

Expected output:
```
Name   | Version | Schema |              Description
-------+---------+--------+---------------------------------------
vector | 0.7.0+  | public | vector data type and ivfflat/hnsw access methods
```

#### 2.2 Verify Extension Installation

```bash
psql $PRODUCTION_DATABASE_URL -c "\dx vector"
```

### Phase 3: Code Deployment

#### 3.1 Set Environment Variables

Add to your production environment (Kubernetes secrets, Docker env, etc.):

```bash
OPENAI_API_KEY=sk-...your-production-key...
```

**Important:** Keep this secret secure! Use secret management tools (Kubernetes Secrets, AWS Secrets Manager, etc.)

#### 3.2 Deploy New Backend Code

Deploy the feature branch or merge to main first:

```bash
# Option 1: Merge PR and deploy main
git checkout main
git pull origin main
# Deploy main branch to production

# Option 2: Deploy feature branch directly for testing
# Deploy feature/rag-implementation to production
```

**Container Image Updates:**
If using Docker in production, ensure your base image or docker-compose configuration points to a PostgreSQL image with pgvector support, or ensure the extension is installed on your managed database service.

#### 3.3 Verify Backend Startup

Check backend logs for successful startup:

```bash
# The backend should start without errors
# Look for these log lines:
# - "INFO: Application startup complete."
# - No errors about pgvector or vector columns

# If OPENAI_API_KEY is not set, you should see:
# - "WARNING: No OpenAI API key configured - RAG functionality will be disabled"
```

#### 3.4 Verify Database Schema

Connect to production database and verify the new columns and indexes were created:

```bash
psql $PRODUCTION_DATABASE_URL << 'EOF'
-- Check chat_messages table
\d chat_messages

-- Verify embedding column exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'chat_messages'
AND column_name = 'embedding';

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'chat_messages'
AND indexname LIKE '%embedding%';
EOF
```

Expected:
- `embedding` column of type `vector(1536)`, nullable
- `idx_chat_messages_embedding_user` HNSW index

### Phase 4: Validation & Testing

#### 4.1 Test New Messages

1. Send a test chat message through your application
2. Verify it's saved with an embedding:

```sql
SELECT
    id,
    role,
    content,
    embedding IS NOT NULL as has_embedding,
    created_at
FROM chat_messages
ORDER BY created_at DESC
LIMIT 5;
```

3. Verify the embedding has correct dimensions:

```sql
SELECT
    id,
    array_length(embedding::text::float[], 1) as embedding_dimensions
FROM chat_messages
WHERE embedding IS NOT NULL
LIMIT 1;
```

Expected: `embedding_dimensions = 1536`

#### 4.2 Test RAG Retrieval (if implemented)

If you've integrated the `_get_relevant_context()` method into your prompts:

1. Send multiple related messages
2. Ask a follow-up question
3. Verify the AI response shows contextual awareness

#### 4.3 Monitor Errors

Watch application logs for any errors:

```bash
# Look for these error patterns:
# - "Error generating embeddings"
# - "Error retrieving relevant context"
# - Database connection errors
# - OpenAI API errors
```

### Phase 5: Backfill Existing Data (Optional)

**When to backfill:**
- If you want RAG to work with historical conversations
- Can be done days/weeks after deployment
- Non-urgent, can be scheduled during low-traffic periods

**Cost Estimate Before Running:**

```python
# Calculate estimated cost
import psycopg2

conn = psycopg2.connect(os.environ['PRODUCTION_DATABASE_URL'])
cursor = conn.cursor()

# Count messages without embeddings
cursor.execute("""
    SELECT COUNT(*) FROM chat_messages WHERE embedding IS NULL
    UNION ALL
    SELECT COUNT(*) FROM standalone_chat_messages WHERE embedding IS NULL
""")

counts = cursor.fetchall()
total = sum(row[0] for row in counts)

# OpenAI text-embedding-3-small pricing: ~$0.00002 per 1K tokens
# Average message: ~100 tokens
estimated_tokens = total * 100
estimated_cost = (estimated_tokens / 1000) * 0.00002

print(f"Messages to backfill: {total:,}")
print(f"Estimated tokens: {estimated_tokens:,}")
print(f"Estimated cost: ${estimated_cost:.2f}")
```

#### 5.1 Run Backfill Script

**Important:** This will make many API calls to OpenAI. Monitor costs!

```bash
# Run backfill in production environment
<production-command> uv run python -m migrations.backfill_embeddings

# Example for Kubernetes:
kubectl exec -it <backend-pod> -- uv run python -m migrations.backfill_embeddings

# Example for Docker:
docker exec -it <backend-container> uv run python -m migrations.backfill_embeddings
```

The script:
- Processes messages in batches of 100
- Has built-in rate limiting (1 second between batches)
- Can be safely interrupted and rerun (only processes messages without embeddings)
- Logs progress for each batch

#### 5.2 Monitor Backfill Progress

```bash
# Check progress in real-time
psql $PRODUCTION_DATABASE_URL << 'EOF'
SELECT
    'chat_messages' as table_name,
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as with_embeddings,
    COUNT(*) FILTER (WHERE embedding IS NULL) as without_embeddings,
    ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as percent_complete
FROM chat_messages
UNION ALL
SELECT
    'standalone_chat_messages',
    COUNT(*) FILTER (WHERE embedding IS NOT NULL),
    COUNT(*) FILTER (WHERE embedding IS NULL),
    ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2)
FROM standalone_chat_messages;
EOF
```

#### 5.3 Resume Interrupted Backfill

If the backfill is interrupted, simply run it again:

```bash
# The script only processes messages without embeddings
<production-command> uv run python -m migrations.backfill_embeddings
```

### Phase 6: Monitoring & Optimization

#### 6.1 Monitor OpenAI API Costs

Track your OpenAI API usage:
- Dashboard: https://platform.openai.com/usage
- Set up billing alerts in OpenAI dashboard
- Monitor cost per message

#### 6.2 Monitor Database Performance

Watch for query performance:

```sql
-- Check HNSW index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE indexname LIKE '%embedding%';

-- Check table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as total_size
FROM pg_tables
WHERE tablename IN ('chat_messages', 'standalone_chat_messages');
```

#### 6.3 Query Performance Testing

Test vector similarity search performance:

```sql
-- Example query (replace with actual user_id and message)
EXPLAIN ANALYZE
SELECT id, content, created_at
FROM chat_messages
WHERE user_id = 1
  AND embedding IS NOT NULL
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector(1536)
LIMIT 5;
```

Look for:
- "Index Scan using idx_chat_messages_embedding_user" (good - using HNSW index)
- Execution time < 100ms for typical queries

## Rollback Strategy

If you need to rollback the deployment:

### Option 1: Disable RAG (Keep Code, Remove API Key)

```bash
# Remove OPENAI_API_KEY from production environment
# RAG will be disabled but code continues working
# No database changes needed
```

### Option 2: Full Rollback (Revert Code & Database)

```bash
# 1. Deploy previous version of backend code

# 2. (Optional) Remove embedding columns and extension
psql $PRODUCTION_DATABASE_URL << 'EOF'
-- Remove indexes first
DROP INDEX IF EXISTS idx_chat_messages_embedding_user;
DROP INDEX IF EXISTS idx_standalone_messages_embedding;

-- Remove columns
ALTER TABLE chat_messages DROP COLUMN IF EXISTS embedding;
ALTER TABLE standalone_chat_messages DROP COLUMN IF EXISTS embedding;

-- (Optional) Remove extension if not needed
DROP EXTENSION IF EXISTS vector;
EOF

# 3. Restore from backup if needed
psql $PRODUCTION_DATABASE_URL < backup_file.sql
```

## Managed Database Services

### AWS RDS PostgreSQL

```sql
-- Install pgvector extension (requires rds_superuser role)
CREATE EXTENSION vector;
```

**Note:** Ensure your RDS instance is PostgreSQL 15+ for pgvector support. You may need to add `pgvector` to your parameter group's `shared_preload_libraries`.

### Google Cloud SQL PostgreSQL

```sql
-- Enable pgvector extension
CREATE EXTENSION vector;
```

**Note:** pgvector is available on Cloud SQL for PostgreSQL 14+. Check Google Cloud documentation for specific version support.

### Azure Database for PostgreSQL

```sql
-- Enable pgvector extension
CREATE EXTENSION vector;
```

**Note:** You may need to add `vector` to the `shared_preload_libraries` parameter and restart the server.

### Heroku Postgres

```bash
# Connect to Heroku database
heroku pg:psql -a your-app-name

# Enable extension
CREATE EXTENSION vector;
```

**Note:** Available on Standard plans and higher.

### Supabase

pgvector is pre-installed on all Supabase projects. Just enable it:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Troubleshooting

### Problem: "extension 'vector' does not exist"

**Solution:** Install pgvector on your PostgreSQL server:
```bash
# For managed services, check their documentation
# For self-hosted, install pgvector package
# Ubuntu/Debian:
apt-get install postgresql-15-pgvector

# Then restart PostgreSQL and run:
CREATE EXTENSION vector;
```

### Problem: "permission denied to create extension"

**Solution:** You need superuser privileges or `rds_superuser` role:
```sql
-- Grant privileges (run as superuser)
GRANT ALL PRIVILEGES ON DATABASE verse_db TO verse_user;

-- Or for RDS:
-- Ensure your user has rds_superuser role
```

### Problem: Backend won't start after deployment

**Solution:** Check logs for specific errors:
```bash
# Common issues:
# 1. Missing OPENAI_API_KEY - This is OK, RAG will be disabled
# 2. Database connection issues - Check DATABASE_URL
# 3. pgvector not installed - Run migration script
```

### Problem: Backfill script running out of memory

**Solution:** The script processes in batches, but for very large datasets:
```python
# Modify BATCH_SIZE in backend/migrations/backfill_embeddings.py
BATCH_SIZE = 50  # Reduce from 100 to 50
```

### Problem: High OpenAI API costs

**Solutions:**
1. **Don't backfill old data** - Only new messages get embeddings
2. **Reduce context limit** - Lower `RAG_CONTEXT_LIMIT` in ChatService
3. **Implement caching** - Cache embeddings for frequently accessed messages
4. **Rate limiting** - Add delays between embedding generation calls

## Security Considerations

1. **API Key Security:**
   - Store `OPENAI_API_KEY` in secure secret management system
   - Never commit API keys to version control
   - Rotate keys periodically
   - Use separate keys for dev/staging/production

2. **Data Privacy:**
   - OpenAI embeddings API doesn't retain your data (as of Dec 2024)
   - Embeddings are stored in your database, ensure proper access controls
   - User isolation is enforced via `user_id` filtering in queries

3. **Database Access:**
   - Use least-privilege database users
   - Enable SSL/TLS for database connections
   - Regular database backups

## Performance Optimization

### For High-Volume Production

If you're processing thousands of messages per day:

1. **Batch Embedding Generation:**
```python
# Use get_embeddings_batch() instead of individual get_embedding() calls
# Already implemented in ChatService but ensure you're using it
```

2. **Async Processing:**
```python
# Consider moving embedding generation to background workers
# Use Celery, RQ, or similar job queue
```

3. **Index Tuning:**
```sql
-- For very large datasets, tune HNSW parameters
DROP INDEX idx_chat_messages_embedding_user;
CREATE INDEX idx_chat_messages_embedding_user
ON chat_messages
USING hnsw (embedding vector_cosine_ops)
WITH (m = 32, ef_construction = 128);  -- Higher values = better accuracy, slower build
```

4. **Connection Pooling:**
Ensure your database connection pool is sized appropriately for the additional embedding write load.

## Success Criteria

✅ **Deployment is successful when:**

1. Backend starts without errors
2. pgvector extension is installed and active
3. New chat messages are saved with embeddings
4. Existing functionality (chat without RAG) still works
5. No errors in application logs
6. Database query performance is acceptable
7. OpenAI API costs are within budget

## Support & Resources

- **pgvector documentation:** https://github.com/pgvector/pgvector
- **OpenAI embeddings guide:** https://platform.openai.com/docs/guides/embeddings
- **Migration scripts:** `backend/migrations/`
- **Internal documentation:** `backend/migrations/README.md`

## Post-Deployment Checklist

- [ ] Database backup created
- [ ] pgvector extension enabled
- [ ] Environment variables configured (OPENAI_API_KEY)
- [ ] New backend code deployed
- [ ] Database schema verified (embedding columns exist)
- [ ] Test messages sent successfully
- [ ] Embeddings being generated and stored
- [ ] No errors in application logs
- [ ] (Optional) Historical data backfilled
- [ ] Monitoring and alerts configured
- [ ] OpenAI API usage tracking enabled
- [ ] Documentation updated with production details
