# Frequently Asked Questions

Common questions about Verse and their answers.

## General Questions

### What is Verse?

Verse is an interactive Bible reader that combines beautiful text presentation with AI-powered insights from Claude. You can read any Bible passage, highlight text, and get instant analysis of its historical context, theological significance, and practical application.

### Is Verse free to use?

Yes, Verse is open source under the MIT license. However, you'll need your own Anthropic API key to use the AI features, which has associated costs from Anthropic.

### Do I need to create an account?

No! Verse uses anonymous sessions. You can use all features without creating an account or providing any personal information. Your data is linked to a cookie-based anonymous ID.

### Can I export my data?

Yes, you can export all your insights, definitions, and chats through the user export feature. This creates a JSON file you can save and later import into another instance of Verse.

---

## Features

### What Bible translations are supported?

Verse supports multiple translations through the HelloAO Bible API, including:
- WEB (World English Bible) – default
- KJV (King James Version)
- BSB (Berean Standard Bible)
- LSV (Literal Standard Version)
- SRV (Spanish Reina-Valera)
- BES (Bible in Easy Spanish)

Check the [HelloAO API documentation](https://bible.helloao.org) for the complete list.

### What AI model powers the insights?

Verse uses Anthropic's Claude AI (currently Claude 3 Sonnet) to generate insights, definitions, and answer chat questions.

### Are insights cached?

Yes! Insights are cached in the database based on the passage text. If you or another user requests insights for the same passage, it's retrieved from cache instead of making a new AI request. This saves costs and improves speed.

### What's the difference between insights and definitions?

- **Insights** - Analysis of a passage including historical context, theological significance, and practical application
- **Definitions** - Biblical meaning of a specific word, including original language (Hebrew/Greek) information

### Can I chat with the AI about passages?

Yes! After viewing insights, you can ask follow-up questions. You can also start standalone chats to discuss any biblical topic.

### Is my chat history saved?

Yes, chat history is saved and linked to your anonymous user ID. You can view previous chats in the chat history panel.

---

## Technical Questions

### What technologies does Verse use?

**Frontend:**
- React 18 with TypeScript
- Vite (build tool)
- Bun (package manager)

**Backend:**
- Python 3.11+ with FastAPI
- PostgreSQL database
- SQLAlchemy ORM

**Infrastructure:**
- Docker & Docker Compose

### Why use Bun instead of npm?

Bun is significantly faster than npm/yarn for installing packages and running scripts. It also has built-in TypeScript support. However, the project works fine with npm if you prefer it.

### Why use uv instead of pip?

uv is a modern Python package manager that's much faster than pip and provides better dependency resolution. It also manages virtual environments automatically.

### Can I run Verse without Docker?

Yes! See the [Development Guide](guides/development.md) for instructions on running the backend and frontend locally without Docker.

### Does Verse work offline?

No, Verse requires internet connection to:
- Fetch Bible text from the HelloAO API
- Generate AI insights from Claude API
- Access the backend API

However, cached insights work offline if you've already viewed them.

---

## Setup and Configuration

### Where do I get an Anthropic API key?

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new key
5. Copy it to your `.env` file

### How much does the Anthropic API cost?

Pricing varies by model. Check [Anthropic's pricing page](https://www.anthropic.com/pricing) for current rates. Claude 3 Sonnet (the model Verse uses) is currently $3 per million input tokens and $15 per million output tokens.

**Cost-saving features:**
- Verse caches insights to avoid duplicate API calls
- Rate limiting prevents accidental excessive usage

### What are the system requirements?

**For Docker deployment:**
- Docker and Docker Compose
- 2GB+ RAM
- 5GB+ disk space

**For local development:**
- Python 3.11+
- Bun (or Node.js 18+)
- PostgreSQL 15+
- 2GB+ RAM

### Can I use SQLite instead of PostgreSQL?

Yes, but it's not recommended for production. SQLite is supported for testing. Change the `DATABASE_URL` in `.env`:

```env
DATABASE_URL=sqlite:///./verse.db
```

### What ports does Verse use?

- **Frontend:** 5173 (development)
- **Backend:** 8000
- **Database:** 5432 (PostgreSQL)

You can change these in `docker-compose.yml`.

---

## Usage Questions

### Why am I getting rate limit errors?

Verse implements rate limiting to prevent abuse:
- **Insights/Definitions:** 10 requests per minute
- **Chat:** 20 requests per minute

Wait for the limit to reset (check the `X-RateLimit-Reset` header) or adjust limits in your `.env` file for development.

### Can I increase the rate limits?

Yes, in your `.env` file:

```env
AI_ENDPOINT_LIMIT=20/minute
CHAT_ENDPOINT_LIMIT=40/minute
```

However, keep in mind this affects API costs and server load.

### Why are my insights taking so long?

AI generation can take 5-30 seconds depending on:
- Passage length
- Anthropic API response time
- Network latency

If it's consistently slow:
1. Check [status.anthropic.com](https://status.anthropic.com/)
2. Increase timeout in `.env`: `ANTHROPIC_API_TIMEOUT=90`
3. Check your network connection

### Can I use Verse on mobile?

Yes! The frontend is fully responsive and works on mobile browsers. However, there's no native mobile app yet.

---

## Privacy and Security

### What data does Verse collect?

Verse stores:
- Anonymous user ID (UUID in a cookie)
- Bible passages you've viewed
- Insights and definitions you've generated
- Chat history

Verse does NOT store:
- Email addresses
- Names
- Passwords
- IP addresses (beyond normal web server logs)

### Is my data private?

Your data is linked to an anonymous ID and not shared with third parties. However:
- Insights are cached globally (shared across all users)
- Your passages and chats are private to your anonymous ID

### Can others see my insights?

Cached insights are shared (no ownership), but your personal history (which insights YOU saved) is private to your anonymous ID.

### How secure is Verse?

Verse implements several security measures:
- HTTPS in production (recommended)
- Secure cookies (HttpOnly, SameSite)
- Rate limiting
- Security headers (HSTS, CSP, etc.)
- Input validation
- SQL injection protection
- CORS protection

See [Security Documentation](architecture/security.md) for details.

---

## Troubleshooting

### Verse won't start - what do I do?

1. Check Docker is running: `docker --version`
2. Check your `.env` file exists and has `ANTHROPIC_API_KEY`
3. Check logs: `docker compose logs`
4. See [Troubleshooting Guide](guides/troubleshooting.md)

### I see "CORS error" in browser console

This usually means:
1. Backend isn't running - check `docker compose logs backend`
2. CORS origins misconfigured - check `backend/app/main.py`
3. Frontend is on wrong port - should be 5173

### Database connection failed

Wait a few seconds for PostgreSQL to start, then:

```bash
docker compose restart backend
```

### Where can I find more help?

1. Check the [Troubleshooting Guide](guides/troubleshooting.md)
2. Review the [Documentation](README.md)
3. Search [GitHub Issues](https://github.com/nihilok/Verse/issues)
4. Create a new issue if your problem isn't listed

---

## Development

### How do I contribute?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

Quick steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

### How do I run tests?

**Backend:**
```bash
cd backend
uv run pytest
```

**Frontend:**
```bash
cd frontend
bun test
```

### Can I add a new Bible API provider?

Yes! Verse uses an abstraction layer. You just need to:
1. Create a new client implementing `BibleClient`
2. Update `BibleService` to use your client

Backend development documentation is planned and will be added soon.

### Can I add a new AI provider?

Yes! Same as Bible API:
1. Create a new client implementing `AIClient`
2. Update `InsightService` and `ChatService`

---

## Deployment

### Can I deploy Verse to production?

Yes! Verse is production-ready. See the planned Production Guide for deployment instructions.

**Key considerations:**
- Use HTTPS (Let's Encrypt recommended)
- Set `ENVIRONMENT=production` in `.env`
- Use strong PostgreSQL password
- Configure `ALLOWED_ORIGINS` for your domain
- Consider using a reverse proxy (nginx)
- Set up monitoring and backups

### What hosting providers work with Verse?

Verse can be deployed to any platform that supports Docker:
- AWS (ECS, EC2)
- Google Cloud (Cloud Run, GKE)
- Azure (Container Instances, AKS)
- DigitalOcean (App Platform, Droplets)
- Heroku
- Fly.io
- Railway

### How do I handle database backups?

```bash
# Backup
docker compose exec db pg_dump -U verse_user verse_db > backup.sql

# Restore
cat backup.sql | docker compose exec -T db psql -U verse_user verse_db
```

For production, set up automated backups using your hosting provider's tools.

---

## Feature Requests

### Will there be user authentication in the future?

It's being considered! Authentication would enable:
- Syncing across devices
- Social features
- Password-protected data

### Will there be a mobile app?

A React Native mobile app is on the roadmap but not currently in development.

### Can you add feature X?

Check existing [GitHub Issues](https://github.com/nihilok/Verse/issues) to see if it's already requested. If not, create a new feature request with:
- Clear description
- Use case
- Why it would be valuable

---

## Related Documentation

- [Getting Started](getting-started.md) - Quick start guide
- User Guide (planned) - Feature guide coming soon
- [Development Guide](guides/development.md) - Development setup
- [Troubleshooting](guides/troubleshooting.md) - Common issues
- [API Reference](reference/api.md) - API documentation
