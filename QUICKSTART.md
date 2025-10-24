# Quick Reference Guide

## Essential Commands

### Start the Application

```bash
# Using the helper script
./start.sh

# Or manually with Docker Compose
docker compose up --build
```

### Stop the Application

```bash
docker compose down
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

### Access Points

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432 (connection details in docker-compose.yml)

## Development Workflows

### Backend Development (without Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload
```

### Frontend Development (without Docker)

```bash
cd frontend
bun install  # or npm install
bun run dev  # or npm run dev
```

### Run Backend Tests

```bash
cd backend
pip install -r requirements-test.txt
pytest
```

## API Quick Reference

### Get a Passage

```bash
curl "http://localhost:8000/api/passage?book=John&chapter=3&verse_start=16&verse_end=17"
```

### Get a Chapter

```bash
curl "http://localhost:8000/api/chapter?book=Psalm&chapter=23"
```

### Generate Insights

```bash
curl -X POST http://localhost:8000/api/insights \
  -H "Content-Type: application/json" \
  -d '{
    "passage_text": "For God so loved the world...",
    "passage_reference": "John 3:16",
    "save": true
  }'
```

## Common Issues & Solutions

### Issue: API Key Error

**Solution**: Ensure your `.env` file has the correct `ANTHROPIC_API_KEY`.

```bash
cp .env.example .env
# Edit .env and add your key
```

### Issue: Port Already in Use

**Solution**: Change ports in `docker-compose.yml` or stop the conflicting service.

```bash
# Check what's using the port
lsof -i :5173  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # Database
```

### Issue: Database Connection Failed

**Solution**: Wait for the database to be ready.

```bash
# Check database logs
docker compose logs db

# Restart services
docker compose restart backend
```

### Issue: Frontend Can't Connect to Backend

**Solution**: Ensure backend is running and CORS is configured.

```bash
# Check backend logs
docker compose logs backend

# Verify backend is accessible
curl http://localhost:8000/health
```

## File Locations

### Configuration Files

- Environment: `.env` (create from `.env.example`)
- Docker: `docker-compose.yml`
- Backend config: `backend/app/core/config.py`
- Frontend config: `frontend/vite.config.ts`

### Source Code

- Backend API: `backend/app/api/routes.py`
- Backend services: `backend/app/services/`
- Backend clients: `backend/app/clients/`
- Frontend components: `frontend/src/components/`
- Frontend services: `frontend/src/services/`

### Documentation

- Main README: `README.md`
- API docs: `API.md`
- Architecture: `ARCHITECTURE.md`
- Development: `DEVELOPMENT.md`
- Contributing: `CONTRIBUTING.md`

## Environment Variables

### Required

- `ANTHROPIC_API_KEY`: Your Claude API key from Anthropic

### Optional

- `DATABASE_URL`: PostgreSQL connection string (defaults provided)
- `ENVIRONMENT`: development or production
- `DEBUG`: Enable debug mode (true/false)

## Useful Docker Commands

```bash
# Rebuild specific service
docker compose build backend

# Run without cache
docker compose build --no-cache

# Remove all containers and volumes
docker compose down -v

# Execute command in container
docker compose exec backend bash
docker compose exec frontend sh

# View container resource usage
docker compose stats
```

## Database Commands

```bash
# Connect to PostgreSQL
docker compose exec db psql -U verse_user -d verse_db

# Backup database
docker compose exec db pg_dump -U verse_user verse_db > backup.sql

# Restore database
cat backup.sql | docker compose exec -T db psql -U verse_user verse_db
```

## Production Deployment

```bash
# Use production compose file
docker compose -f docker-compose.prod.yml up --build -d

# Set production environment variables
export ANTHROPIC_API_KEY=your_key
export POSTGRES_PASSWORD=secure_password

# Check status
docker compose -f docker-compose.prod.yml ps
```

## Monitoring

```bash
# Check application health
curl http://localhost:8000/health

# View recent logs
docker compose logs --tail=100 backend

# Follow logs in real-time
docker compose logs -f backend
```

## Need Help?

1. Check the documentation in the repo
2. Review the [DEVELOPMENT.md](DEVELOPMENT.md) guide
3. Look at [ARCHITECTURE.md](ARCHITECTURE.md) for system design
4. Check [API.md](API.md) for API details
5. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
