from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.services.user_service import UserService


class AnonymousUserMiddleware(BaseHTTPMiddleware):
    """Middleware to handle anonymous user authentication via cookies."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Process request and ensure user has anonymous ID cookie."""
        # Get anonymous_id from cookie
        anonymous_id = request.cookies.get("verse_user_id")
        
        # Use the database session that will be provided by the dependency
        # We'll get or create the user lazily when needed in routes
        # For now, just mark that we need to handle the user
        request.state.anonymous_id = anonymous_id
        request.state.user = None  # Will be set by get_current_user dependency
        
        # Process the request
        response: Response = await call_next(request)
        
        # If a user was created during the request, set the cookie
        if hasattr(request.state, 'user') and request.state.user:
            user = request.state.user
            if not anonymous_id or anonymous_id != user.anonymous_id:
                response.set_cookie(
                    key="verse_user_id",
                    value=user.anonymous_id,
                    max_age=60 * 60 * 24 * 365 * 10,  # 10 years
                    httponly=True,
                    samesite="lax",
                    secure=False  # Set to True in production with HTTPS
                )
        
        return response
