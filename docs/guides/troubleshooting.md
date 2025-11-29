# Troubleshooting Guide

Common issues and their solutions when working with Verse.

## Table of Contents

- [Installation Issues](#installation-issues)
- [API Issues](#api-issues)
- [Database Issues](#database-issues)
- [Docker Issues](#docker-issues)
- [Frontend Issues](#frontend-issues)
- [Backend Issues](#backend-issues)

---

## Installation Issues

### Port Already in Use

**Problem:** Error message: "port is already allocated" or "address already in use"

**Common Ports:**
- 5173 (Frontend)
- 8000 (Backend)
- 5432 (PostgreSQL)

**Solution 1: Stop conflicting services**

```bash
# Find what's using the port
lsof -i :5173  # macOS/Linux
netstat -ano | findstr :5173  # Windows

# Kill the process (macOS/Linux)
kill -9 <PID>

# Kill the process (Windows)
taskkill /PID <PID> /F
```

**Solution 2: Change ports in docker-compose.yml**

```yaml
services:
  frontend:
    ports:
      - "3000:5173"  # Changed from 5173:5173
```

---

### Missing .env File

**Problem:** Application fails to start with "ANTHROPIC_API_KEY is required"

**Solution:**

```bash
# Create .env file from example
cp .env.example .env

# Edit and add your API key
# ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

---

### Invalid API Key

**Problem:** "Invalid API key" or "Authentication failed" errors

**Solution:**

1. Verify your key at [console.anthropic.com](https://console.anthropic.com/)
2. Check for extra spaces or newlines in .env file
3. Ensure key starts with `sk-ant-api03-`
4. Generate a new key if necessary

---

## API Issues

### Rate Limit Exceeded

**Problem:** HTTP 429 error: "Rate limit exceeded"

**Limits:**
- Insights/Definitions: 10 requests per minute
- Chat: 20 requests per minute

**Solution:**

Wait for the rate limit to reset. Check response headers:

```
X-RateLimit-Reset: 1638360000  # Unix timestamp
```

To adjust limits (development only):

```env
# In .env
AI_ENDPOINT_LIMIT=20/minute
CHAT_ENDPOINT_LIMIT=40/minute
```

---

### CORS Errors

**Problem:** Browser console shows "CORS policy" errors

**Solution:**

1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify allowed origins in backend:**
   ```python
   # backend/app/main.py
   ALLOWED_ORIGINS = [
       "http://localhost:5173",
       "http://localhost:3000"
   ]
   ```

3. **Check browser console for actual error**

4. **Restart backend after config changes:**
   ```bash
   docker compose restart backend
   ```

---

### Timeout Errors

**Problem:** "Request timeout" or "Connection timeout" errors

**Solution:**

Increase timeout values in .env:

```env
BIBLE_API_TIMEOUT=15
ANTHROPIC_API_TIMEOUT=90
```

Check network connectivity:

```bash
# Test Bible API
curl https://bible.helloao.org

# Test Anthropic API (with your key)
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY"
```

---

## Database Issues

### Connection Failed

**Problem:** "Could not connect to database" or "Connection refused"

**Solution 1: Wait for database to start**

PostgreSQL takes a few seconds to initialize:

```bash
# Check database logs
docker compose logs db

# Wait for this message:
# "database system is ready to accept connections"
```

**Solution 2: Restart backend**

```bash
docker compose restart backend
```

**Solution 3: Check DATABASE_URL**

```env
# Correct format
DATABASE_URL=postgresql://user:password@host:5432/database

# For Docker Compose, host is service name
DATABASE_URL=postgresql://verse_user:verse_password@db:5432/verse_db
```

---

### Tables Not Created

**Problem:** "Table does not exist" errors

**Solution:**

Tables are created automatically on startup. Check backend logs:

```bash
docker compose logs backend | grep -i "table"
```

To manually create tables:

```bash
# Enter backend container
docker compose exec backend bash

# Run Python
python
```

```python
from app.core.database import engine, Base
from app.models.models import *

Base.metadata.create_all(bind=engine)
```

---

### Migration Errors

**Problem:** Alembic migration failures

**Solution:**

```bash
cd backend

# Check migration history
alembic history

# Check current version
alembic current

# Downgrade to previous version
alembic downgrade -1

# Re-apply migrations
alembic upgrade head

# If all else fails, reset database (DATA LOSS!)
docker compose down -v
docker compose up --build
```

---

## Docker Issues

### Build Failures

**Problem:** "Error building image" or similar

**Solution:**

```bash
# Clean build (no cache)
docker compose build --no-cache

# Remove all containers and volumes
docker compose down -v

# Prune unused Docker resources
docker system prune -a

# Rebuild
docker compose up --build
```

---

### Container Exits Immediately

**Problem:** Container starts then immediately stops

**Solution:**

```bash
# View container logs
docker compose logs backend
docker compose logs frontend

# Look for error messages in logs

# Common causes:
# - Missing environment variables
# - Syntax errors in code
# - Port conflicts
# - Dependency issues
```

---

### Out of Disk Space

**Problem:** "No space left on device"

**Solution:**

```bash
# Check Docker disk usage
docker system df

# Remove unused containers, images, volumes
docker system prune -a --volumes

# Remove specific volumes
docker volume ls
docker volume rm <volume_name>
```

---

## Frontend Issues

### Blank Page

**Problem:** Frontend loads but shows blank page

**Solution:**

1. **Check browser console for errors:**
   - Open DevTools (F12)
   - Look for red errors in Console tab

2. **Check frontend is running:**
   ```bash
   docker compose logs frontend
   ```

3. **Verify API connection:**
   - Open Network tab in DevTools
   - Look for failed API calls
   - Check if backend is responding

4. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)
   - Clear site data in DevTools

---

### API Calls Failing

**Problem:** Frontend loads but API calls return errors

**Solution:**

1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify CORS configuration**

3. **Check network tab in browser:**
   - See what error code is returned
   - Look at request/response headers

4. **Check backend logs:**
   ```bash
   docker compose logs backend
   ```

---

### Build Errors

**Problem:** `bun run build` fails

**Solution:**

```bash
# Clean node_modules
rm -rf node_modules
rm bun.lockb

# Reinstall
bun install

# Check for TypeScript errors
tsc --noEmit

# Try building again
bun run build
```

---

## Backend Issues

### Import Errors

**Problem:** "ModuleNotFoundError" or import errors

**Solution:**

```bash
cd backend

# Reinstall dependencies
uv sync --reinstall

# Check Python version
python --version  # Should be 3.11+

# Verify virtual environment is activated
which python  # Should point to .venv/bin/python
```

---

### Database Model Errors

**Problem:** "Table has no column named..." errors

**Solution:**

This means database schema doesn't match models.

```bash
# Create migration
alembic revision --autogenerate -m "Update schema"

# Apply migration
alembic upgrade head

# Or reset database (DATA LOSS!)
docker compose down -v
docker compose up --build
```

---

### Slow AI Responses

**Problem:** AI endpoints taking very long to respond

**Possible Causes:**

1. **Anthropic API is slow** - Check [status.anthropic.com](https://status.anthropic.com/)
2. **Network issues** - Test connectivity
3. **Large requests** - Reduce passage text size

**Solution:**

```bash
# Check Anthropic API status
curl -I https://api.anthropic.com/v1/messages

# Increase timeout if needed
ANTHROPIC_API_TIMEOUT=120
```

---

## General Tips

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend

# Follow in real-time
docker compose logs -f --tail=100 backend
```

### Restarting Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend

# Full restart (rebuild)
docker compose down
docker compose up --build
```

### Entering Containers

```bash
# Backend
docker compose exec backend bash

# Frontend
docker compose exec frontend sh

# Database
docker compose exec db psql -U verse_user -d verse_db
```

### Checking Service Health

```bash
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:5173

# Database
docker compose exec db pg_isready -U verse_user
```

---

## Still Having Issues?

1. **Check the documentation:**
   - [Getting Started Guide](../getting-started.md)
   - [Development Guide](development.md)
   - [API Reference](../reference/api.md)

2. **Search existing issues:**
   - [GitHub Issues](https://github.com/nihilok/Verse/issues)

3. **Ask for help:**
   - Create a new [GitHub Issue](https://github.com/nihilok/Verse/issues/new)
   - Include:
     - Error message (full text)
     - Steps to reproduce
     - Environment (OS, Docker version, etc.)
     - Relevant logs

---

## Related Documentation

- [Getting Started](../getting-started.md)
- [Development Setup](development.md)
- [Configuration Reference](../reference/configuration.md)
