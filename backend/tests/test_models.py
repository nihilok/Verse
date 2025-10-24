"""Tests for client abstractions."""
from app.clients.bible_client import BibleVerse, BiblePassage
from app.clients.ai_client import InsightRequest, InsightResponse


def test_bible_verse_model():
    """Test BibleVerse model creation."""
    verse = BibleVerse(
        book="John",
        chapter=3,
        verse=16,
        text="For God so loved the world...",
        translation="WEB"
    )
    assert verse.book == "John"
    assert verse.chapter == 3
    assert verse.verse == 16


def test_bible_passage_model():
    """Test BiblePassage model creation."""
    verse = BibleVerse(
        book="John",
        chapter=3,
        verse=16,
        text="For God so loved the world...",
        translation="WEB"
    )
    passage = BiblePassage(
        reference="John 3:16",
        verses=[verse],
        translation="WEB"
    )
    assert passage.reference == "John 3:16"
    assert len(passage.verses) == 1


def test_insight_request_model():
    """Test InsightRequest model creation."""
    request = InsightRequest(
        passage_text="Test passage",
        passage_reference="John 3:16"
    )
    assert request.passage_text == "Test passage"
    assert request.passage_reference == "John 3:16"


def test_insight_response_model():
    """Test InsightResponse model creation."""
    response = InsightResponse(
        historical_context="Test context",
        theological_significance="Test significance",
        practical_application="Test application"
    )
    assert response.historical_context == "Test context"
    assert response.theological_significance == "Test significance"
    assert response.practical_application == "Test application"
