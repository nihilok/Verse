import httpx
from typing import Optional, List
from app.clients.bible_client import BibleClient, BibleVerse, BiblePassage


class HelloAOBibleClient(BibleClient):
    """Implementation of BibleClient using bible.helloao.org API."""
    
    BASE_URL = "https://bible.helloao.org/api"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _normalize_book_name(self, book: str) -> str:
        """Normalize book names for the API."""
        # Remove spaces and convert to lowercase
        return book.replace(" ", "").lower()
    
    async def get_verse(
        self, 
        book: str, 
        chapter: int, 
        verse: int, 
        translation: str = "WEB"
    ) -> Optional[BibleVerse]:
        """Get a single verse from HelloAO API."""
        try:
            book_normalized = self._normalize_book_name(book)
            url = f"{self.BASE_URL}/{translation}/{book_normalized}/{chapter}:{verse}.json"
            
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # HelloAO API returns verses in a specific format
            if data and len(data) > 0:
                verse_data = data[0]
                return BibleVerse(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    text=verse_data.get("text", ""),
                    translation=translation
                )
            return None
        except Exception as e:
            print(f"Error fetching verse: {e}")
            return None
    
    async def get_passage(
        self,
        book: str,
        chapter: int,
        verse_start: int,
        verse_end: int,
        translation: str = "WEB"
    ) -> Optional[BiblePassage]:
        """Get a passage (range of verses) from HelloAO API."""
        try:
            book_normalized = self._normalize_book_name(book)
            url = f"{self.BASE_URL}/{translation}/{book_normalized}/{chapter}:{verse_start}-{verse_end}.json"
            
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            verses = []
            for verse_data in data:
                verses.append(BibleVerse(
                    book=book,
                    chapter=chapter,
                    verse=verse_data.get("verse", 0),
                    text=verse_data.get("text", ""),
                    translation=translation
                ))
            
            reference = f"{book} {chapter}:{verse_start}-{verse_end}"
            return BiblePassage(
                reference=reference,
                verses=verses,
                translation=translation
            )
        except Exception as e:
            print(f"Error fetching passage: {e}")
            return None
    
    async def get_chapter(
        self,
        book: str,
        chapter: int,
        translation: str = "WEB"
    ) -> Optional[BiblePassage]:
        """Get an entire chapter from HelloAO API."""
        try:
            book_normalized = self._normalize_book_name(book)
            url = f"{self.BASE_URL}/{translation}/{book_normalized}/{chapter}.json"
            
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            verses = []
            for verse_data in data:
                verses.append(BibleVerse(
                    book=book,
                    chapter=chapter,
                    verse=verse_data.get("verse", 0),
                    text=verse_data.get("text", ""),
                    translation=translation
                ))
            
            reference = f"{book} {chapter}"
            return BiblePassage(
                reference=reference,
                verses=verses,
                translation=translation
            )
        except Exception as e:
            print(f"Error fetching chapter: {e}")
            return None
