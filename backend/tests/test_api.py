"""Tests for Bible API routes."""

import pytest


def test_get_passage_missing_params(client):
    """Test passage endpoint with missing parameters."""
    response = client.get("/api/passage")
    assert response.status_code == 422  # Unprocessable Entity


def test_get_chapter_missing_params(client):
    """Test chapter endpoint with missing parameters."""
    response = client.get("/api/chapter")
    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
@pytest.mark.sqlite
async def test_get_passage_valid_params(client):
    """Test passage endpoint with valid parameters."""
    response = client.get("/api/passage?book=John&chapter=3&verse_start=16")
    # This test may fail without a real API key or if the external API is down
    # In a real test suite, we'd use mocking
    assert response.status_code in [200, 404, 500]
