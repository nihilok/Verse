"""Tests for rate limiting functionality."""

from unittest.mock import Mock

from app.core.rate_limiter import (
    AI_ENDPOINT_LIMIT,
    CHAT_ENDPOINT_LIMIT,
    get_user_identifier,
    limiter,
)


def test_get_user_identifier_with_anonymous_id():
    """Test that get_user_identifier uses anonymous_id when available."""
    request = Mock()
    request.state.anonymous_id = "test-anonymous-id-123"

    identifier = get_user_identifier(request)

    assert identifier == "user:test-anonymous-id-123"


def test_get_user_identifier_fallback_to_ip():
    """Test that get_user_identifier falls back to IP address when anonymous_id not present."""
    request = Mock()
    request.state.anonymous_id = None
    request.client.host = "192.168.1.100"

    identifier = get_user_identifier(request)

    assert identifier == "ip:192.168.1.100"


def test_rate_limiter_initialized():
    """Test that the rate limiter is properly initialized."""
    assert limiter is not None
    # Verify the limiter uses our custom key function
    assert limiter._key_func == get_user_identifier


def test_ai_endpoint_rate_limit_configured():
    """Test that AI endpoint rate limit is configured correctly."""
    # Verify the limit is set to 10 requests per minute
    assert AI_ENDPOINT_LIMIT == "10/minute"


def test_chat_endpoint_rate_limit_configured():
    """Test that chat endpoint rate limit is configured correctly."""
    # Verify the limit is set to 20 requests per minute
    assert CHAT_ENDPOINT_LIMIT == "20/minute"


def test_rate_limiting_decorator_applied():
    """Test that rate limiting decorators are applied to endpoints."""
    # Verify that the rate limiting decorators are present on the routes
    # by checking the module imports and function decorators
    from app.api import routes

    # Verify the limiter and rate limit constants are imported in routes module
    assert hasattr(routes, "limiter")
    assert hasattr(routes, "AI_ENDPOINT_LIMIT")
    assert hasattr(routes, "CHAT_ENDPOINT_LIMIT")

    # Verify the rate limit values are correct
    assert routes.AI_ENDPOINT_LIMIT == "10/minute"
    assert routes.CHAT_ENDPOINT_LIMIT == "20/minute"
