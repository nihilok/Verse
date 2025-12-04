"""Tests for HelloAO Bible client text extraction."""

import pytest

from app.clients.helloao_client import HelloAOBibleClient


@pytest.fixture
def helloao_client():
    """Create a HelloAO Bible client for testing."""
    return HelloAOBibleClient()


def test_extract_verse_text_simple_string(helloao_client):
    """Test extracting text from simple string content."""
    content = ["This is a simple verse."]
    result = helloao_client._extract_verse_text(content)
    assert result == "This is a simple verse."


def test_extract_verse_text_with_note_id(helloao_client):
    """Test extracting text with noteId marker (footnote)."""
    content = [
        "For God so loved the world that He gave His one and only",
        {"noteId": 17},
        "Son, that everyone who believes in Him shall not perish.",
    ]
    result = helloao_client._extract_verse_text(content)
    # Should have space where noteId was
    assert "only Son" in result
    assert "onlySon" not in result
    expected = (
        "For God so loved the world that He gave His one and only Son, "
        "that everyone who believes in Him shall not perish."
    )
    assert result == expected


def test_extract_verse_text_with_line_break(helloao_client):
    """Test extracting text with lineBreak marker."""
    content = [
        "The sons of Noah:",
        {"lineBreak": True},
        "Shem, Ham, and Japheth.",
    ]
    result = helloao_client._extract_verse_text(content)
    # Should have space where lineBreak was
    assert "Noah: Shem" in result
    assert "Noah:Shem" not in result


def test_extract_verse_text_with_multiple_markers(helloao_client):
    """Test extracting text with multiple noteId and lineBreak markers."""
    content = [
        "The sons of Gomer: Ashkenaz, Riphath,",
        {"noteId": 1},
        "and Togarmah.",
        {"lineBreak": True},
        "The sons of Javan:",
        {"noteId": 2},
        "Elishah and Tarshish.",
    ]
    result = helloao_client._extract_verse_text(content)
    # Should have spaces where markers were
    assert "Riphath, and" in result
    assert "Riphath,and" not in result
    assert "Togarmah. The" in result
    assert "Javan: Elishah" in result
    assert "Javan:Elishah" not in result


def test_extract_verse_text_with_text_object(helloao_client):
    """Test extracting text from object with 'text' key (e.g., words of Jesus)."""
    content = [
        {
            "text": "For God so loved the world.",
            "wordsOfJesus": True,
        }
    ]
    result = helloao_client._extract_verse_text(content)
    assert result == "For God so loved the world."


def test_extract_verse_text_mixed_content(helloao_client):
    """Test extracting text with mixed string and object content."""
    content = [
        "In the beginning",
        {"noteId": 1},
        {
            "text": "God created the heavens and the earth.",
            "emphasis": True,
        },
    ]
    result = helloao_client._extract_verse_text(content)
    assert "beginning God" in result
    assert "beginningGod" not in result
    assert "God created" in result


def test_extract_verse_text_strips_whitespace(helloao_client):
    """Test that result is stripped of leading/trailing whitespace."""
    content = [
        "   Some text with spaces   ",
        {"noteId": 1},
        "   and more text.   ",
    ]
    result = helloao_client._extract_verse_text(content)
    # The result should be stripped of leading/trailing whitespace
    assert not result.startswith(" ")
    assert not result.endswith(" ")
    # Internal spacing might have extra spaces where markers were, which is acceptable
    assert "Some text with spaces" in result
    assert "and more text." in result


def test_extract_verse_text_unknown_marker_ignored(helloao_client):
    """Test that unknown marker types are gracefully ignored."""
    content = [
        "Some text",
        {"unknownMarker": "value"},
        "more text.",
    ]
    result = helloao_client._extract_verse_text(content)
    # Unknown markers are skipped, but surrounding text should be joined
    assert "text" in result and "more text" in result


@pytest.mark.asyncio
async def test_real_bsb_verse_with_footnote(helloao_client):
    """Integration test: Fetch a real BSB verse known to have footnotes."""
    try:
        verse = await helloao_client.get_verse("John", 3, 16, "BSB")
        assert verse is not None
        assert "only Son" in verse.text
        assert "onlySon" not in verse.text
    except Exception as e:
        pytest.skip(f"API not available: {e}")
    finally:
        await helloao_client.close()


@pytest.mark.asyncio
async def test_real_bsb_verse_with_linebreak(helloao_client):
    """Integration test: Fetch a real BSB verse known to have line breaks."""
    try:
        verse = await helloao_client.get_verse("1 Chronicles", 1, 4, "BSB")
        assert verse is not None
        # Should have proper spacing after "Noah:"
        assert "Noah:" in verse.text
        # Should not have words joined without space
        assert not any(bad in verse.text for bad in ["Noah:S", "Noah:E", ":Shem"])
    except Exception as e:
        pytest.skip(f"API not available: {e}")
    finally:
        await helloao_client.close()
