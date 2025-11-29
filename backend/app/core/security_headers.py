"""Security headers middleware for application hardening."""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import get_settings

settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Implements recommended security headers to protect against common web vulnerabilities:
    - Content-Security-Policy: Mitigate XSS attacks
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - Strict-Transport-Security: Force HTTPS (production only)
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Restrict browser features

    Note: CSP directive includes 'unsafe-inline' for styles to support React app.
    Consider using a nonce-based approach for production if stricter CSP is needed.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)

        # Content Security Policy - Mitigate XSS attacks
        # 'self' allows resources from same origin
        # 'unsafe-inline' for styles is needed for React inline styles
        # Consider using nonce-based CSP for stricter security
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.anthropic.com https://api.helloao.org; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # X-Frame-Options - Prevent clickjacking
        # DENY prevents the page from being displayed in a frame
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options - Prevent MIME sniffing
        # nosniff prevents browsers from MIME-sniffing responses
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Strict-Transport-Security (HSTS) - Force HTTPS
        # Only enable in production with HTTPS
        # max-age=31536000: Cache for 1 year
        # includeSubDomains: Apply to all subdomains
        # preload: Allow inclusion in browser preload lists
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Referrer-Policy - Control referrer information
        # strict-origin-when-cross-origin: Send full URL for same-origin,
        # origin only for cross-origin, nothing for downgrade (HTTPS -> HTTP)
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (formerly Feature-Policy)
        # Restrict browser features to minimize attack surface
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # X-XSS-Protection - Legacy XSS protection (for older browsers)
        # Modern browsers use CSP instead, but this provides defense in depth
        # 1; mode=block: Enable XSS filter and block rendering if attack detected
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response
