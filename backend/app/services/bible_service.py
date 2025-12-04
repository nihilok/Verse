from sqlalchemy.orm import Session

from app.clients.bible_client import BibleClient, BiblePassage
from app.clients.helloao_client import HelloAOBibleClient
from app.clients.sqlite_bible_client import SQLiteBibleClient
from app.core.config import get_settings
from app.models.models import SavedPassage


class BibleService:
    """Service for Bible-related operations."""

    def __init__(self, client: BibleClient | None = None):
        if client:
            self.client = client
        else:
            # Use configured client type
            settings = get_settings()
            if settings.bible_client_type == "sqlite":
                self.client = SQLiteBibleClient()
            else:
                self.client = HelloAOBibleClient()

    async def get_passage(
        self,
        book: str,
        chapter: int,
        verse_start: int,
        verse_end: int | None = None,
        translation: str = "WEB",
    ) -> BiblePassage | None:
        """Get a Bible passage."""
        if verse_end is None or verse_end == verse_start:
            verse = await self.client.get_verse(book, chapter, verse_start, translation)
            if verse:
                return BiblePassage(
                    reference=f"{book} {chapter}:{verse_start}",
                    verses=[verse],
                    translation=translation,
                )
            return None
        else:
            return await self.client.get_passage(book, chapter, verse_start, verse_end, translation)

    async def get_chapter(self, book: str, chapter: int, translation: str = "WEB") -> BiblePassage | None:
        """Get an entire chapter."""
        return await self.client.get_chapter(book, chapter, translation)

    def save_passage(self, db: Session, passage: BiblePassage) -> SavedPassage:
        """Save a passage to the database."""
        # Extract verse range
        verse_start = passage.verses[0].verse if passage.verses else 0
        verse_end = passage.verses[-1].verse if len(passage.verses) > 1 else verse_start

        # Combine all verse texts
        text = " ".join([v.text for v in passage.verses])

        db_passage = SavedPassage(
            reference=passage.reference,
            book=passage.verses[0].book if passage.verses else "",
            chapter=passage.verses[0].chapter if passage.verses else 0,
            verse_start=verse_start,
            verse_end=verse_end if verse_end != verse_start else None,
            translation=passage.translation,
            text=text,
        )
        db.add(db_passage)
        db.commit()
        db.refresh(db_passage)
        return db_passage

    async def close(self):
        """Close the client."""
        if hasattr(self.client, "close"):
            await self.client.close()
