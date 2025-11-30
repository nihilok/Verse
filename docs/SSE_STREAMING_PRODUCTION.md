# SSE Streaming in Production

## Problem

When deploying the Verse application to production (Raspberry Pi 5), SSE (Server-Sent Events) streaming for chat responses was not working properly:
- Responses appeared all at once after a long delay instead of streaming token-by-token
- The user experience was degraded compared to local development

## Root Cause

**Nginx reverse proxy buffering** was preventing real-time streaming. By default, nginx buffers responses before sending them to clients, which defeats the purpose of SSE streaming.

### Technical Details

1. **Default nginx behavior**: `proxy_buffering on` (default) causes nginx to:
   - Wait to receive the entire backend response
   - Buffer it in memory
   - Then send it all at once to the client
   - This completely breaks SSE streaming

2. **Port mismatch**: The nginx config was proxying to `localhost:8000`, but the production backend runs on port `7776` (configured in `docker-compose.prod.yml`)

## Solution

### 1. Add These Lines to Your Production Nginx Config

In your `/api` location block, add the following lines **immediately after `proxy_http_version 1.1;`**:

```nginx
# CRITICAL: Disable buffering for Server-Sent Events (SSE) streaming
# Without these, chat responses will appear all at once instead of streaming
proxy_buffering off;
proxy_cache off;
proxy_request_buffering off;

# SSE-specific headers
proxy_set_header Connection '';
proxy_set_header X-Accel-Buffering no;
```

And change the `proxy_read_timeout` from `90` to `3600`:
```nginx
proxy_read_timeout 3600;  # 1 hour for long conversations
```

### 2. Complete Example

Your production `/api` block should look like this:

```nginx
location /api {
    proxy_pass http://localhost:7776;
    proxy_http_version 1.1;

    # CRITICAL: Disable buffering for Server-Sent Events (SSE) streaming
    proxy_buffering off;
    proxy_cache off;
    proxy_request_buffering off;

    # SSE-specific headers
    proxy_set_header Connection '';
    proxy_set_header X-Accel-Buffering no;

    # Standard proxy headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Increased timeouts for long-running SSE streams
    proxy_read_timeout 3600;  # 1 hour for long conversations
    proxy_connect_timeout 90;
    proxy_send_timeout 90;
}
```

### 3. Key Configuration Explained

- **`proxy_buffering off;`** - Disables response buffering (critical!)
- **`proxy_cache off;`** - Disables caching of responses
- **`proxy_request_buffering off;`** - Disables request buffering for immediate flushing
- **`Connection ''`** - Prevents "Connection: close" header
- **`X-Accel-Buffering no`** - Nginx-specific header to disable buffering
- **`proxy_read_timeout 3600;`** - Extended timeout for long conversations (1 hour)
- **Port updated to `7776`** - Matches production backend port

## Deployment

After updating `nginx-verse.conf` on your Raspberry Pi:

```bash
# Test nginx configuration
sudo nginx -t

# Reload nginx (zero-downtime)
sudo nginx -s reload

# Or restart nginx
sudo systemctl restart nginx
```

## Verification

To verify streaming is working:

1. **Browser DevTools**:
   - Open Network tab
   - Send a chat message
   - Look for `/api/chat/message` or `/api/standalone-chat` request
   - Check that "Type" shows `eventsource`
   - Watch the response stream in real-time

2. **curl test**:
   ```bash
   curl -N -H "Cookie: your-session-cookie" \
     -H "Content-Type: application/json" \
     -d '{"message":"test","insight_id":1,...}' \
     http://your-pi-ip/api/chat/message
   ```
   You should see tokens arriving incrementally.

## Architecture

```
Client (Browser)
    ↓
External Nginx (nginx-verse.conf) - Port 80
    ↓ /api → localhost:7776 (buffering OFF)
    ↓
Backend Container (FastAPI + uvicorn) - Port 7776
    ↓
Claude API (Anthropic) - Streaming responses
```

## Common Issues

### Issue: Streaming still doesn't work after nginx changes

**Possible causes**:
1. Nginx config not reloaded: `sudo nginx -s reload`
2. Browser cache: Hard refresh (Ctrl+Shift+R)
3. CDN/proxy in front of nginx also buffering
4. ISP transparent proxy (rare, but possible)

### Issue: Connection timeouts during long conversations

**Solution**: Increase `proxy_read_timeout` in nginx config (currently set to 3600 seconds / 1 hour)

### Issue: High memory usage

**Cause**: Buffering is disabled, so nginx doesn't use memory buffers
**Impact**: Minimal - SSE responses are small (few KB)

## Backend Configuration

The backend already has proper SSE headers set in `app/api/routes.py`:

```python
return StreamingResponse(
    event_stream(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"  # Nginx-specific
    }
)
```

These work together with the nginx configuration to ensure streaming works end-to-end.

## References

- [Nginx SSE documentation](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering)
- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
