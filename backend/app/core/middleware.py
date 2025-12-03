from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import get_settings

# Cookie configuration constants
COOKIE_NAME = "verse_user_id"
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365 * 10  # 10 years


class AnonymousUserMiddleware(BaseHTTPMiddleware):
    """Middleware to handle anonymous user authentication via cookies."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next):
        """Process request and ensure user has anonymous ID cookie."""
        # Get anonymous_id from cookie
        anonymous_id = request.cookies.get(COOKIE_NAME)

        # Use the database session that will be provided by the dependency
        # We'll get or create the user lazily when needed in routes
        # For now, just mark that we need to handle the user
        request.state.anonymous_id = anonymous_id
        request.state.user = None  # Will be set by get_current_user dependency
        request.state.user_anonymous_id = None  # Will store the ID for cookie setting

        # Process the request
        response: Response = await call_next(request)

        # If a user was created during the request, set the cookie
        # Use the stored anonymous_id instead of accessing the detached user object
        if hasattr(request.state, "user_anonymous_id") and request.state.user_anonymous_id:
            user_anonymous_id = request.state.user_anonymous_id
            if not anonymous_id or anonymous_id != user_anonymous_id:
                response.set_cookie(
                    key=COOKIE_NAME,
                    value=user_anonymous_id,
                    max_age=COOKIE_MAX_AGE_SECONDS,
                    httponly=True,
                    samesite="lax",
                    secure=self.settings.cookie_secure,
                )

        return response
