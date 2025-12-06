"""Tests for SQLite Bible client."""

import pytest

from app.clients.sqlite_bible_client import SQLiteBibleClient

pytestmark = pytest.mark.sqlite


@pytest.fixture
def sqlite_client():
    """Create a SQLite Bible client for testing."""
    try:
        client = SQLiteBibleClient()
        return client
    except FileNotFoundError:
        pytest.skip("Bible database file not found. Run download_bible.sh to download it.")


@pytest.mark.asyncio
async def test_get_verse_web(sqlite_client):
    """Test getting a single verse in WEB translation."""
    verse = await sqlite_client.get_verse("John", 3, 16, "WEB")
    assert verse is not None
    assert verse.book == "John"
    assert verse.chapter == 3
    assert verse.verse == 16
    assert verse.translation == "WEB"
    assert "God so loved the world" in verse.text


@pytest.mark.asyncio
async def test_get_passage(sqlite_client):
    """Test getting a passage (range of verses)."""
    passage = await sqlite_client.get_passage("Genesis", 1, 1, 3, "WEB")
    assert passage is not None
    assert passage.reference == "Genesis 1:1-3"
    assert len(passage.verses) == 3
    assert passage.verses[0].verse == 1
    assert passage.verses[2].verse == 3
    assert "In the beginning" in passage.verses[0].text


@pytest.mark.asyncio
async def test_get_chapter(sqlite_client):
    """Test getting an entire chapter."""
    chapter = await sqlite_client.get_chapter("Psalms", 23, "WEB")
    assert chapter is not None
    assert chapter.reference == "Psalms 23"
    assert len(chapter.verses) > 0
    assert "The LORD is my shepherd" in chapter.verses[0].text


@pytest.mark.asyncio
async def test_book_name_normalization(sqlite_client):
    """Test that book names are normalized correctly."""
    # Test with different book name variations
    verse1 = await sqlite_client.get_verse("1 Samuel", 17, 45, "WEB")
    assert verse1 is not None
    assert verse1.book == "1 Samuel"

    verse2 = await sqlite_client.get_verse("Song of Solomon", 1, 1, "WEB")
    assert verse2 is not None
    assert verse2.book == "Song of Solomon"


@pytest.mark.asyncio
async def test_invalid_reference(sqlite_client):
    """Test that invalid references return None."""
    # Non-existent verse
    verse = await sqlite_client.get_verse("John", 3, 999, "WEB")
    assert verse is None

    # Non-existent chapter
    chapter = await sqlite_client.get_chapter("John", 999, "WEB")
    assert chapter is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "translation,book,chapter,verse_num,expected_word",
    [
        # Standard English translations
        ("WEB", "John", 3, 16, "God"),
        ("KJV", "John", 3, 16, "God"),
        ("BSB", "John", 3, 16, "God"),
        ("ASV", "John", 3, 16, "God"),
        ("LSV", "John", 3, 16, "God"),
        ("PEV", "John", 3, 16, "God"),
        ("RV", "John", 3, 16, "God"),
        ("MSB", "John", 3, 16, "God"),
        ("YLT", "John", 3, 16, "God"),
        ("BBE", "John", 3, 16, "God"),
        ("EMTV", "John", 3, 16, "God"),
        # Septuagint translations (Old Testament only)
        ("BST", "Genesis", 1, 1, "God"),  # Brenton Septuagint
        ("LXXSB", "Genesis", 1, 1, "God"),  # LXX British/International English
        ("LXXSA", "Genesis", 1, 1, "God"),  # LXX American English
        ("UBES", "Genesis", 1, 1, "God"),  # Updated Brenton Septuagint
        # Jewish/Hebrew-focused translations
        ("TOJBT", "John", 3, 16, "Hashem"),  # Orthodox Jewish Bible Translation - uses Hebrew names
        ("JPSTN", "Genesis", 1, 1, "God"),  # JPS TaNaKH - Old Testament only
        ("ILT", "Genesis", 1, 1, "God"),  # Isaac Leeser Tanakh - Old Testament only
        ("TOE", "Genesis", 1, 1, "Lord"),  # Targum Onkelos - Torah only
        ("WMB", "John", 3, 16, "God"),  # World Messianic Bible
        # Scholarly translations
        ("NETB", "John", 3, 16, "God"),  # NET Bible
        ("DBY", "John", 3, 16, "God"),  # Darby Translation
    ],
)
async def test_all_supported_translations(
    sqlite_client, translation, book, chapter, verse_num, expected_word
):
    """Test that all supported translations work correctly.

    This test verifies that each translation in TRANSLATION_IDS can successfully
    retrieve a verse, ensuring the database contains all advertised translations.
    Note: Septuagint translations (BST, LXXSB) only contain Old Testament books.
    """
    verse = await sqlite_client.get_verse(book, chapter, verse_num, translation)
    assert verse is not None, f"Failed to fetch {book} {chapter}:{verse_num} in {translation} translation"
    assert verse.book == book
    assert verse.chapter == chapter
    assert verse.verse == verse_num
    assert verse.translation == translation
    assert len(verse.text) > 0, f"Empty text for {translation} translation"
    # Verify the expected word appears in the text
    text_lower = verse.text.lower()
    expected_word_lower = expected_word.lower()
    assert (
        expected_word_lower in text_lower
    ), f"Expected '{expected_word}' in {translation} but got: {verse.text}"


@pytest.mark.asyncio
async def test_translation_differences(sqlite_client):
    """Test that different translations return different text."""
    verse_web = await sqlite_client.get_verse("John", 3, 16, "WEB")
    verse_kjv = await sqlite_client.get_verse("John", 3, 16, "KJV")

    assert verse_web is not None
    assert verse_kjv is not None
    # The translations should be different (e.g., "only born" vs "only begotten")
    assert verse_web.text != verse_kjv.text


@pytest.mark.asyncio
async def test_passage_verse_order(sqlite_client):
    """Test that verses in a passage are returned in correct order."""
    passage = await sqlite_client.get_passage("Matthew", 5, 3, 10, "WEB")
    assert passage is not None
    assert len(passage.verses) == 8

    # Verify verses are in sequential order
    for i, verse in enumerate(passage.verses):
        expected_verse_num = 3 + i
        assert verse.verse == expected_verse_num


@pytest.mark.asyncio
async def test_chapter_completeness(sqlite_client):
    """Test that a chapter contains all expected verses."""
    # Psalm 117 is the shortest chapter (2 verses)
    chapter = await sqlite_client.get_chapter("Psalms", 117, "WEB")
    assert chapter is not None
    assert len(chapter.verses) == 2
    assert chapter.verses[0].verse == 1
    assert chapter.verses[1].verse == 2


@pytest.mark.asyncio
async def test_database_path_validation():
    """Test that SQLiteBibleClient raises error for non-existent database."""
    with pytest.raises(FileNotFoundError):
        SQLiteBibleClient(db_path="/non/existent/path/bible.db")


@pytest.mark.asyncio
async def test_multiple_translations_same_client(sqlite_client):
    """Test that the same client can handle multiple translation requests."""
    translations_to_test = ["WEB", "KJV", "BSB"]

    for translation in translations_to_test:
        verse = await sqlite_client.get_verse("Romans", 8, 28, translation)
        assert verse is not None
        assert verse.translation == translation
        assert len(verse.text) > 0
