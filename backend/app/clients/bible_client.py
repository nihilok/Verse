from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BibleVerse(BaseModel):
    """Model for a Bible verse."""

    book: str
    chapter: int
    verse: int
    text: str
    translation: str
    text_parts: list[Any] | None = None  # Rich formatting data (poem indentation, line breaks)


class BiblePassage(BaseModel):
    """Model for a Bible passage (multiple verses)."""

    reference: str
    verses: list[BibleVerse]
    translation: str


class ChapterContent(BaseModel):
    """Model for rich chapter content with formatting."""

    book: str
    chapter: int
    translation: str
    reference: str
    content: list[dict[str, Any]]  # Array of verse, heading, line_break elements


class BibleClient(ABC):
    """Abstract base class for Bible API clients."""

    @abstractmethod
    async def get_verse(
        self, book: str, chapter: int, verse: int, translation: str = "WEB"
    ) -> BibleVerse | None:
        """Get a single verse."""
        pass

    @abstractmethod
    async def get_passage(
        self,
        book: str,
        chapter: int,
        verse_start: int,
        verse_end: int,
        translation: str = "WEB",
    ) -> BiblePassage | None:
        """Get a passage (range of verses)."""
        pass

    @abstractmethod
    async def get_chapter(self, book: str, chapter: int, translation: str = "WEB") -> BiblePassage | None:
        """Get an entire chapter."""
        pass

    async def get_chapter_content(
        self, book: str, chapter: int, translation: str = "WEB"
    ) -> ChapterContent | None:
        """Get rich chapter content with formatting (optional - not all clients support this)."""
        return None
