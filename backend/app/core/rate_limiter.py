"""Rate limiting configuration for API endpoints."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def get_user_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.

    Uses anonymous_id from request state if available (set by middleware),
    otherwise falls back to IP address.

    This approach:
    - Properly rate-limits per user (not per IP for shared networks)
    - Prevents bypass by switching IPs
    - Falls back gracefully to IP for unauthenticated requests
    """
    # Try to get anonymous_id from request state (set by AnonymousUserMiddleware)
    anonymous_id = getattr(request.state, 'anonymous_id', None)
    if anonymous_id:
        return f"user:{anonymous_id}"

    # Fallback to IP address
    return f"ip:{get_remote_address(request)}"


# Configure rate limiter
# Storage: In-memory storage suitable for single-instance deployments
# For multi-instance deployments, consider Redis storage:
#   from slowapi.extension import LimiterExtension
#   from slowapi.util import get_remote_address
#   limiter = Limiter(key_func=get_user_identifier, storage_uri="redis://localhost:6379")
limiter = Limiter(key_func=get_user_identifier)


# Rate limit configurations
# These limits are per user (via anonymous_id) or per IP if user not identified

# AI endpoints (expensive Claude API calls)
AI_ENDPOINT_LIMIT = "10/minute"  # 10 requests per minute for insights/definitions

# Chat endpoints (interactive, but still expensive)
CHAT_ENDPOINT_LIMIT = "20/minute"  # 20 messages per minute

# General API endpoints (less expensive)
GENERAL_ENDPOINT_LIMIT = "100/minute"  # 100 requests per minute for other endpoints
