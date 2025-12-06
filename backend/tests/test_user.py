"""Tests for user functionality."""

import pytest

from app.models.models import StandaloneChat
from app.services.chat_service import ChatService
from app.services.insight_service import InsightService
from app.services.user_service import UserService


def test_create_anonymous_user(db):
    """Test creating an anonymous user."""
    service = UserService()
    user = service.get_or_create_user(db)

    assert user is not None
    assert user.anonymous_id is not None
    assert user.id is not None


def test_get_existing_user(db):
    """Test getting an existing user by anonymous_id."""
    service = UserService()

    # Create a user
    user1 = service.get_or_create_user(db)
    anonymous_id = user1.anonymous_id

    # Get the same user
    user2 = service.get_or_create_user(db, anonymous_id)

    assert user1.id == user2.id
    assert user1.anonymous_id == user2.anonymous_id


@pytest.mark.asyncio
async def test_clear_user_data(async_db, async_test_user):
    user_service = UserService()
    """Test clearing all data for a user."""
    insight_service = InsightService()

    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # Add some insights for the user
    await insight_service.save_insight(
        async_db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=async_test_user.id,
    )

    await insight_service.save_insight(
        async_db,
        passage_reference="John 3:17",
        passage_text="For God did not send his Son",
        insights=MockInsight(),
        user_id=async_test_user.id,
    )

    # Clear user data
    counts = await user_service.clear_user_data(async_db, async_test_user.id)

    assert counts["insights"] == 2

    # Verify insights are cleared for the user
    user_insights = await insight_service.get_user_insights(async_db, async_test_user.id)
    assert len(user_insights) == 0


@pytest.mark.asyncio
async def test_export_user_data(async_db, async_test_user):
    """Test exporting user data as JSON."""
    user_service = UserService()
    insight_service = InsightService()

    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # Add some insights for the user
    await insight_service.save_insight(
        async_db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=async_test_user.id,
    )

    # Export user data
    data = await user_service.export_user_data(async_db, async_test_user.id)

    assert "user" in data
    assert "insights" in data
    assert "standalone_chats" in data

    assert data["user"]["anonymous_id"] == async_test_user.anonymous_id
    assert len(data["insights"]) == 1
    assert data["insights"][0]["passage_reference"] == "John 3:16"
    assert "chat_messages" in data["insights"][0]


@pytest.mark.asyncio
async def test_import_user_data(async_db, async_test_user):
    """Test importing user data from JSON."""
    user_service = UserService()

    # Create mock data to import
    data = {
        "user": {
            "anonymous_id": async_test_user.anonymous_id,
            "created_at": "2024-01-01T00:00:00",
        },
        "insights": [
            {
                "passage_reference": "Romans 8:28",
                "passage_text": "And we know that in all things God works",
                "historical_context": "Historical context",
                "theological_significance": "Theological significance",
                "practical_application": "Practical application",
                "chat_messages": [],
            }
        ],
        "standalone_chats": [],
    }

    # Import data
    counts = await user_service.import_user_data(async_db, async_test_user.id, data)

    assert counts["insights"] == 1

    # Verify insights were imported
    insight_service = InsightService()
    user_insights = await insight_service.get_user_insights(async_db, async_test_user.id)
    assert len(user_insights) == 1
    assert user_insights[0].passage_reference == "Romans 8:28"


@pytest.mark.asyncio
async def test_user_data_segregation_insights(async_db):
    """Test that users can only see their own insights."""
    insight_service = InsightService()

    # Create two users
    from tests.conftest import create_test_user

    user1 = await create_test_user(async_db)
    user2 = await create_test_user(async_db)

    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # User 1 saves an insight
    await insight_service.save_insight(
        async_db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=user1.id,
    )

    # User 2 saves a different insight
    await insight_service.save_insight(
        async_db,
        passage_reference="Romans 8:28",
        passage_text="And we know that in all things",
        insights=MockInsight(),
        user_id=user2.id,
    )

    # Verify each user only sees their own insights
    user1_insights = await insight_service.get_user_insights(async_db, user1.id)
    user2_insights = await insight_service.get_user_insights(async_db, user2.id)

    assert len(user1_insights) == 1
    assert len(user2_insights) == 1
    assert user1_insights[0].passage_reference == "John 3:16"
    assert user2_insights[0].passage_reference == "Romans 8:28"


@pytest.mark.asyncio
async def test_user_data_segregation_chats(async_db):
    """Test that users can only see their own standalone chats."""

    # Create two users
    from tests.conftest import create_test_user

    user1 = await create_test_user(async_db)
    user2 = await create_test_user(async_db)

    # Create standalone chats for each user
    chat1 = StandaloneChat(user_id=user1.id, title="User 1 Chat", passage_text="Some text")
    async_db.add(chat1)

    chat2 = StandaloneChat(user_id=user2.id, title="User 2 Chat", passage_text="Some other text")
    async_db.add(chat2)
    await async_db.flush()

    # Verify each user only sees their own chats
    chat_service = ChatService()
    user1_chats = await chat_service.get_standalone_chats(async_db, user1.id)
    user2_chats = await chat_service.get_standalone_chats(async_db, user2.id)

    assert len(user1_chats) == 1
    assert len(user2_chats) == 1
    assert user1_chats[0].title == "User 1 Chat"
    assert user2_chats[0].title == "User 2 Chat"


@pytest.mark.asyncio
async def test_insight_caching_across_users(async_db):
    """Test that insights are cached across users (many-to-many)."""
    insight_service = InsightService()

    # Create two users
    from tests.conftest import create_test_user

    user1 = await create_test_user(async_db)
    user2 = await create_test_user(async_db)

    # Create a mock insight response
    class MockInsight:
        historical_context = "Historical context"
        theological_significance = "Theological significance"
        practical_application = "Practical application"

    # User 1 generates and saves an insight
    saved_insight = await insight_service.save_insight(
        async_db,
        passage_reference="John 3:16",
        passage_text="For God so loved the world",
        insights=MockInsight(),
        user_id=user1.id,
    )

    # User 2 requests the same passage - should link to existing insight
    existing_insight = await insight_service.get_saved_insight(
        async_db, passage_reference="John 3:16", passage_text="For God so loved the world"
    )

    assert existing_insight is not None
    assert existing_insight.id == saved_insight.id

    # Link the insight to user 2
    await insight_service.link_insight_to_user(async_db, existing_insight.id, user2.id)

    # Both users should see the same insight
    user1_insights = await insight_service.get_user_insights(async_db, user1.id)
    user2_insights = await insight_service.get_user_insights(async_db, user2.id)

    assert len(user1_insights) == 1
    assert len(user2_insights) == 1
    assert user1_insights[0].id == user2_insights[0].id
