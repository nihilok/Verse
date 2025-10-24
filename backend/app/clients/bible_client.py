from abc import ABC, abstractmethod
from typing import Optional, List
from pydantic import BaseModel


class BibleVerse(BaseModel):
    """Model for a Bible verse."""
    book: str
    chapter: int
    verse: int
    text: str
    translation: str


class BiblePassage(BaseModel):
    """Model for a Bible passage (multiple verses)."""
    reference: str
    verses: List[BibleVerse]
    translation: str


class BibleClient(ABC):
    """Abstract base class for Bible API clients."""
    
    @abstractmethod
    async def get_verse(
        self, 
        book: str, 
        chapter: int, 
        verse: int, 
        translation: str = "WEB"
    ) -> Optional[BibleVerse]:
        """Get a single verse."""
        pass
    
    @abstractmethod
    async def get_passage(
        self,
        book: str,
        chapter: int,
        verse_start: int,
        verse_end: int,
        translation: str = "WEB"
    ) -> Optional[BiblePassage]:
        """Get a passage (range of verses)."""
        pass
    
    @abstractmethod
    async def get_chapter(
        self,
        book: str,
        chapter: int,
        translation: str = "WEB"
    ) -> Optional[BiblePassage]:
        """Get an entire chapter."""
        pass
