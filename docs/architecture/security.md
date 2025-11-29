# Security Features

Verse implements multiple layers of security to protect users and prevent abuse.

## Security Overview

- **Anonymous User Sessions** - Privacy-preserving user tracking
- **Rate Limiting** - Prevents API abuse
- **Security Headers** - Protects against common web vulnerabilities
- **CORS Protection** - Prevents unauthorized cross-origin requests
- **SQL Injection Protection** - Parameterized queries via SQLAlchemy
- **Input Validation** - Pydantic models validate all inputs

## Anonymous User System

### How It Works

1. **First Visit:**
   - User visits the site
   - Middleware generates a UUID
   - UUID stored in secure cookie
   - User record created in database

2. **Subsequent Visits:**
   - Cookie sent with request
   - Middleware retrieves user from database
   - User ID attached to request

3. **Benefits:**
   - No authentication required
   - User data still tracked
   - Can be linked to authenticated account later
   - Privacy-friendly (no email/name required)

### Implementation

**Middleware:** `backend/app/core/middleware.py`

```python
class AnonymousUserMiddleware:
    async def __call__(self, request, call_next):
        # Get or create anonymous_id
        anonymous_id = request.cookies.get('anonymous_id')
        if not anonymous_id:
            anonymous_id = str(uuid.uuid4())

        # Store in request state
        request.state.anonymous_id = anonymous_id

        # Process request
        response = await call_next(request)

        # Set cookie if new
        if 'anonymous_id' not in request.cookies:
            response.set_cookie(
                key='anonymous_id',
                value=anonymous_id,
                httponly=True,
                secure=cookie_secure,
                samesite='lax'
            )

        return response
```

### Cookie Security

**HttpOnly:** Prevents JavaScript access to cookie (XSS protection)

**Secure:** Cookie only sent over HTTPS in production

**SameSite=Lax:** Protects against CSRF attacks

**Max-Age:** 1 year (can be configured)

---

## Rate Limiting

### Purpose

Prevents abuse of expensive AI endpoints and protects against:
- Denial of Service (DoS) attacks
- API cost abuse
- Excessive Claude API usage

### Limits

**AI Endpoints (Insights, Definitions):**
- Limit: 10 requests per minute per user
- Applies to: `/api/insights`, `/api/definitions`

**Chat Endpoints:**
- Limit: 20 requests per minute per user
- Applies to: `/api/chat/*`

### Implementation

**Middleware:** `backend/app/core/rate_limiter.py`

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_anonymous_id)

@router.post("/api/insights")
@limiter.limit("10/minute")
async def generate_insights(...):
    # Implementation
```

### Rate Limit Headers

Responses include rate limit information:

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1638360000
```

### Handling Rate Limits

**Frontend:**

```typescript
try {
  const response = await api.generateInsights(data);
} catch (error) {
  if (error.response?.status === 429) {
    // Show user-friendly message
    alert('Too many requests. Please wait a moment.');
  }
}
```

**Response:**

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "detail": "Rate limit exceeded: 10 per minute"
}
```

---

## Security Headers

### Headers Set

**Strict-Transport-Security (HSTS):**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```
- Forces HTTPS for 1 year
- Includes all subdomains

**X-Content-Type-Options:**
```
X-Content-Type-Options: nosniff
```
- Prevents MIME type sniffing
- Reduces XSS attack surface

**X-Frame-Options:**
```
X-Frame-Options: DENY
```
- Prevents clickjacking attacks
- Disallows embedding in iframes

**Content-Security-Policy:**
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'
```
- Controls resource loading
- Mitigates XSS attacks
- Allows inline scripts/styles (for React)

**X-XSS-Protection:**
```
X-XSS-Protection: 1; mode=block
```
- Enables browser XSS filter
- Blocks page on XSS detection

### Implementation

**Middleware:** `backend/app/core/security_headers.py`

```python
class SecurityHeadersMiddleware:
    async def __call__(self, request, call_next):
        response = await call_next(request)

        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "default-src 'self'"

        return response
```

---

## CORS Protection

### Configuration

**Development:**
```python
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000"
]
```

**Production:**
```python
ALLOWED_ORIGINS = [
    "https://verse.example.com"
]
```

### Implementation

**File:** `backend/app/main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

### Best Practices

1. **Never use wildcard (`*`)** in production
2. **Specify exact origins** including protocol
3. **No trailing slashes** in origin URLs
4. **Enable credentials** for cookie-based auth
5. **Limit methods** to what you actually use

---

## Input Validation

### Pydantic Models

All API inputs validated using Pydantic:

```python
class InsightRequestModel(BaseModel):
    passage_text: str
    passage_reference: str
    save: bool = False

    @field_validator('passage_text')
    @classmethod
    def strip_passage_text(cls, v: str) -> str:
        return v.strip() if v else v
```

**Benefits:**
- Type validation
- Required field checking
- Custom validators
- Automatic error messages
- Data transformation

### Validation Example

**Invalid Request:**
```json
{
  "passage_text": "",
  "passage_reference": null
}
```

**Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "passage_text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Database Security

### SQL Injection Protection

SQLAlchemy uses parameterized queries:

```python
# Safe - parameterized
user = db.query(User).filter(User.id == user_id).first()

# NEVER do this - vulnerable to SQL injection
# db.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

### CASCADE DELETE

Foreign keys configured with CASCADE DELETE:

```python
class ChatMessage(Base):
    insight_id = Column(
        Integer,
        ForeignKey('saved_insights.id', ondelete='CASCADE')
    )
```

**Benefits:**
- Prevents orphaned records
- Maintains data integrity
- Automatic cleanup

### Database Permissions

**Recommended Production Setup:**

1. **Application user** (verse_user):
   - SELECT, INSERT, UPDATE, DELETE on tables
   - USAGE on sequences
   - No CREATE, DROP, ALTER

2. **Migration user** (verse_admin):
   - All permissions
   - Used only for migrations

```sql
-- Application user (limited permissions)
CREATE USER verse_user WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO verse_user;

-- Migration user (full permissions)
CREATE USER verse_admin WITH PASSWORD 'admin_password';
GRANT ALL PRIVILEGES ON DATABASE verse_db TO verse_admin;
```

---

## API Key Security

### Storage

**DO NOT:**
- Commit API keys to git
- Store in code
- Share in plain text
- Use same key for dev and prod

**DO:**
- Use environment variables
- Use `.env.local` for local keys
- Use secrets manager in production (AWS Secrets Manager, etc.)
- Rotate keys regularly

### Key Validation

Backend validates API key on startup:

```python
if not settings.anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY is required")
```

### Error Handling

Never expose API keys in error messages:

```python
try:
    client = anthropic.Anthropic(api_key=api_key)
except Exception as e:
    logger.error("Failed to initialize Anthropic client")
    raise HTTPException(500, "AI service unavailable")
    # NOT: raise HTTPException(500, f"Invalid API key: {api_key}")
```

---

## Request Timeouts

Prevents hanging requests:

```python
# Bible API client
async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.get(url)

# Anthropic client
client = anthropic.Anthropic(
    api_key=api_key,
    timeout=60.0
)
```

**Benefits:**
- Prevents resource exhaustion
- Better user experience
- Fails fast on errors

---

## HTTPS/TLS

### Production Requirements

1. **Use HTTPS** for all production traffic
2. **Set COOKIE_SECURE=true**
3. **Enable HSTS** (done via security headers)
4. **Use valid SSL certificate** (Let's Encrypt, etc.)

### Database Connections

Use SSL for production database:

```env
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

---

## Security Checklist

### Development

- [ ] `.env` file in `.gitignore`
- [ ] No API keys in code
- [ ] CORS allows localhost only
- [ ] COOKIE_SECURE=false (HTTP)

### Production

- [ ] Unique API keys (not dev keys)
- [ ] HTTPS enabled
- [ ] COOKIE_SECURE=true
- [ ] Strict CORS (exact origins)
- [ ] HSTS enabled
- [ ] Database uses SSL
- [ ] Rate limiting enabled
- [ ] Security headers enabled
- [ ] Regular key rotation
- [ ] Monitoring and alerts

---

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email security concerns to: [security@example.com]
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

---

## Related Documentation

- [Configuration Reference](../reference/configuration.md) - Security settings
- [Architecture Overview](./) - System design

