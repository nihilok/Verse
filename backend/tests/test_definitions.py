"""Tests for definitions functionality."""

import pytest

from app.services.definition_service import DefinitionService


@pytest.mark.asyncio
async def test_save_and_get_definition_with_same_word(async_db, async_test_user):
    """Test that definitions are cached based on word, reference, and verse text."""
    service = DefinitionService()

    # Create a mock definition response
    class MockDefinition:
        definition = "The definition of love"
        biblical_usage = "How love is used in the Bible"
        original_language = "Greek: agape"

    # Save a definition
    await service.save_definition(
        async_db,
        word="love",
        passage_reference="John 3:16",
        verse_text="For God so loved the world",
        definition=MockDefinition(),
        user_id=async_test_user.id,
    )

    # Retrieve the same definition
    saved = await service.get_saved_definition(
        async_db,
        word="love",
        passage_reference="John 3:16",
        verse_text="For God so loved the world",
    )

    assert saved is not None
    assert saved.word == "love"
    assert saved.passage_reference == "John 3:16"
    assert saved.verse_text == "For God so loved the world"
    assert saved.definition == "The definition of love"
    assert saved.biblical_usage == "How love is used in the Bible"
    assert saved.original_language == "Greek: agape"


@pytest.mark.asyncio
async def test_different_word_same_verse_not_cached(async_db, async_test_user):
    """Test that different words with same verse are not cached together."""
    service = DefinitionService()

    # Create a mock definition response
    class MockDefinition:
        definition = "The definition of love"
        biblical_usage = "How love is used in the Bible"
        original_language = "Greek: agape"

    # Save a definition for one word
    await service.save_definition(
        async_db,
        word="love",
        passage_reference="John 3:16",
        verse_text="For God so loved the world",
        definition=MockDefinition(),
        user_id=async_test_user.id,
    )

    # Try to retrieve with different word but same verse
    saved = await service.get_saved_definition(
        async_db,
        word="world",
        passage_reference="John 3:16",
        verse_text="For God so loved the world",
    )

    # Should not find a cached result
    assert saved is None


@pytest.mark.asyncio
async def test_get_all_definitions(async_db, async_test_user):
    """Test getting all definitions for a user."""
    service = DefinitionService()

    class MockDefinition:
        definition = "A definition"
        biblical_usage = "Biblical usage"
        original_language = "Original language"

    # Save multiple definitions
    await service.save_definition(
        async_db,
        word="love",
        passage_reference="John 3:16",
        verse_text="For God so loved the world",
        definition=MockDefinition(),
        user_id=async_test_user.id,
    )

    await service.save_definition(
        async_db,
        word="world",
        passage_reference="John 3:16",
        verse_text="For God so loved the world",
        definition=MockDefinition(),
        user_id=async_test_user.id,
    )

    # Get all definitions for the user
    definitions = await service.get_user_definitions(async_db, async_test_user.id, limit=50)

    assert len(definitions) == 2


@pytest.mark.asyncio
async def test_clear_all_definitions(async_db, async_test_user):
    """Test clearing all definitions for a user."""
    service = DefinitionService()

    class MockDefinition:
        definition = "A definition"
        biblical_usage = "Biblical usage"
        original_language = "Original language"

    # Save some definitions
    await service.save_definition(
        async_db,
        word="love",
        passage_reference="John 3:16",
        verse_text="For God so loved the world",
        definition=MockDefinition(),
        user_id=async_test_user.id,
    )

    await service.save_definition(
        async_db,
        word="world",
        passage_reference="John 3:16",
        verse_text="For God so loved the world",
        definition=MockDefinition(),
        user_id=async_test_user.id,
    )

    # Clear all definitions for the user
    count = await service.clear_user_definitions(async_db, async_test_user.id)

    assert count == 2

    # Verify all definitions are cleared for the user
    definitions = await service.get_user_definitions(async_db, async_test_user.id, limit=50)
    assert len(definitions) == 0


def test_strip_whitespace_on_request():
    """Test that whitespace is stripped from word and verse_text in the request model."""
    from app.api.routes import DefinitionRequestModel

    # Test with leading and trailing whitespace
    request = DefinitionRequestModel(
        word="  love  ",
        verse_text="  For God so loved the world  ",
        passage_reference="John 3:16",
        save=True,
    )

    assert request.word == "love"
    assert request.verse_text == "For God so loved the world"


def test_strip_whitespace_on_insight_request():
    """Test that whitespace is stripped from passage_text in the insight request model."""
    from app.api.routes import InsightRequestModel

    # Test with leading and trailing whitespace
    request = InsightRequestModel(
        passage_text="  For God so loved the world  ",
        passage_reference="John 3:16",
        save=True,
    )

    assert request.passage_text == "For God so loved the world"
