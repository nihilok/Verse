# Quick Fix: Enable SSE Streaming in Production

## The Problem
Chat responses load all at once after a long delay instead of streaming token-by-token.

## The Fix
Add these 5 lines to your nginx config `/api` location block:

```nginx
# Add after proxy_http_version 1.1;
proxy_buffering off;
proxy_cache off;
proxy_request_buffering off;
proxy_set_header Connection '';
proxy_set_header X-Accel-Buffering no;
```

And change this line:
```nginx
# Change from:
proxy_read_timeout 90;

# To:
proxy_read_timeout 3600;  # 1 hour for long conversations
```

## Complete /api Block
Your production `/api` location block on `verse.jarv.dev` should look like:

```nginx
location /api {
    proxy_pass http://localhost:7776;
    proxy_http_version 1.1;

    # CRITICAL: Disable buffering for SSE streaming
    proxy_buffering off;
    proxy_cache off;
    proxy_request_buffering off;

    # SSE-specific headers
    proxy_set_header Connection '';
    proxy_set_header X-Accel-Buffering no;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_read_timeout 3600;  # Changed from 90
    proxy_connect_timeout 90;
    proxy_send_timeout 90;
}
```

## Deploy
```bash
# On your Raspberry Pi:
sudo nano /etc/nginx/sites-available/verse  # Edit your config
sudo nginx -t                               # Test config
sudo nginx -s reload                        # Apply changes (zero downtime)
```

## Verify
Open browser DevTools → Network tab → Send a chat message. You should see tokens arriving in real-time instead of all at once.

---

**See [SSE_STREAMING_PRODUCTION.md](./SSE_STREAMING_PRODUCTION.md) for full technical details.**
