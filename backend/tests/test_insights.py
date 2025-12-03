"""Tests for insights functionality."""

from app.services.insight_service import InsightService


def test_save_and_get_insight_with_same_text(db, test_user):
    """Test that insights are cached based on both reference and text."""
    service = InsightService()

    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # Save an insight
    service.save_insight(
        db,
        passage_reference="John 3",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=test_user.id,
    )

    # Retrieve the same insight
    saved = service.get_saved_insight(
        db, passage_reference="John 3", passage_text="For God so loved the world"
    )

    assert saved is not None
    assert saved.passage_reference == "John 3"
    assert saved.passage_text == "For God so loved the world"
    assert saved.historical_context == "Historical context"


def test_different_text_same_reference_not_cached(db, test_user):
    """Test that different texts with same reference are not cached together."""
    service = InsightService()

    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # Save an insight with one text
    service.save_insight(
        db,
        passage_reference="John 3",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=test_user.id,
    )

    # Try to retrieve with different text but same reference
    saved = service.get_saved_insight(
        db, passage_reference="John 3", passage_text="that he gave his only Son"
    )

    # Should not find a cached result
    assert saved is None


def test_get_all_insights(db, test_user):
    """Test getting all insights for a user."""
    service = InsightService()

    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # Save multiple insights
    service.save_insight(
        db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=test_user.id,
    )

    service.save_insight(
        db,
        passage_reference="John 3:17",
        passage_text="For God did not send his Son into the world",
        insights=MockInsight(),
        user_id=test_user.id,
    )

    # Get all insights for the user
    insights = service.get_user_insights(db, test_user.id, limit=50)

    assert len(insights) == 2


def test_clear_all_insights(db, test_user):
    """Test clearing all insights for a user."""
    service = InsightService()

    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # Save some insights
    service.save_insight(
        db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=test_user.id,
    )

    service.save_insight(
        db,
        passage_reference="John 3:17",
        passage_text="For God did not send his Son into the world",
        insights=MockInsight(),
        user_id=test_user.id,
    )

    # Clear all insights for the user
    count = service.clear_user_insights(db, test_user.id)

    assert count == 2

    # Verify all insights are cleared for the user
    insights = service.get_user_insights(db, test_user.id, limit=50)
    assert len(insights) == 0
