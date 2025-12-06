# Usage Limits

This document describes the usage limits feature for the Verse application.

## Overview

Verse implements a daily usage limit system for AI-powered features:
- **Free users**: Limited to 10 LLM calls per day
- **Pro users**: Unlimited LLM calls

An LLM call is counted for:
- Generating insights for a Bible passage
- Generating word definitions
- Sending chat messages (both insight-based and standalone chats)

## Database Schema

### User Model
Added `pro_subscription` field (Boolean, default False) to track pro status.

### UsageTracking Model
Tracks daily LLM usage per user:
- `user_id`: Foreign key to users table
- `date`: Date of usage (UTC, start of day)
- `llm_calls`: Count of LLM calls made on this date
- Unique constraint on (user_id, date)

## Managing Pro Subscriptions

Use the `manage_pro_users.py` script to manage pro subscriptions:

### Add a User to Pro

```bash
python manage_pro_users.py add <anonymous_id>
```

Example:
```bash
python manage_pro_users.py add abc123-def456-ghi789
```

This will:
1. Find the user by their anonymous_id
2. Set their `pro_subscription` to True
3. Display information about the user and their linked devices

### Remove a User from Pro

```bash
python manage_pro_users.py remove <anonymous_id>
```

Example:
```bash
python manage_pro_users.py remove abc123-def456-ghi789
```

### List All Pro Users

```bash
python manage_pro_users.py list
```

This displays:
- Anonymous ID
- User ID
- Creation date
- Number of linked devices
- Device details (name, type, last active)

### Check User Status

```bash
python manage_pro_users.py status <anonymous_id>
```

This shows:
- User information
- Pro subscription status
- Linked devices
- Today's usage (LLM calls made and remaining)

## Finding a User's Anonymous ID

Users can find their anonymous ID:
1. Open the Verse app
2. Go to Settings (gear icon in sidebar)
3. The anonymous ID is displayed in the User Session section

Alternatively, check the database:
```sql
SELECT id, anonymous_id, pro_subscription, created_at 
FROM users 
ORDER BY created_at DESC;
```

## API Endpoints

### Get User Session with Usage Info

```
GET /api/user/session
```

Response includes usage information:
```json
{
  "anonymous_id": "abc123-def456-ghi789",
  "created_at": 1234567890000,
  "usage": {
    "is_pro": false,
    "daily_limit": 10,
    "calls_today": 3,
    "remaining": 7
  }
}
```

For pro users:
```json
{
  "usage": {
    "is_pro": true,
    "daily_limit": 0,
    "calls_today": 0,
    "remaining": -1
  }
}
```

Note: `daily_limit: 0` and `remaining: -1` indicate unlimited usage.

### Error Response When Limit Reached

When a free user exceeds their daily limit, API endpoints return 429 status:

```json
{
  "detail": {
    "message": "Daily limit of 10 AI requests reached. Please try again tomorrow or upgrade to pro.",
    "current_usage": 10,
    "limit": 10,
    "is_pro": false
  }
}
```

## Frontend Handling

The frontend displays user-friendly error messages when the limit is reached:
- For insights: Alert banner with error message
- For definitions: Alert banner with error message
- For chat: Error message in chat interface

Users see: "Daily limit of 10 AI requests reached. Please try again tomorrow or upgrade to pro."

## Usage Reset

Usage counters reset automatically at the start of each day (UTC 00:00).

## Cleanup

Old usage records can be cleaned up periodically:

```python
from app.services.usage_service import UsageService
from app.core.database import get_db

async with get_db() as db:
    usage_service = UsageService()
    deleted_count = await usage_service.cleanup_old_usage_records(db, days_to_keep=30)
```

This can be added to a scheduled task or cron job.

## Implementation Details

### Backend
- `UsageService` in `app/services/usage_service.py` handles all usage tracking logic
- API routes check usage before processing LLM requests
- Tracking happens after successful LLM call completion
- Pro users bypass all checks

### Frontend
- Error handling in `App.tsx` checks for 429 status code
- Custom error messages displayed for usage limits
- Regular errors still show generic "Failed to..." messages

## Testing

Run usage tracking tests:
```bash
cd backend
python -m pytest tests/test_usage_tracking.py -v
```

Tests cover:
- New user can make calls
- Pro users have unlimited access
- Tracking LLM calls
- Reaching usage limit
- Setting pro subscription
- Cleanup of old records
- Unique constraint enforcement
