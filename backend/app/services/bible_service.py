from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.bible_client import BibleClient, BiblePassage
from app.clients.helloao_client import HelloAOBibleClient
from app.clients.sqlite_bible_client import SQLiteBibleClient
from app.core.config import get_settings
from app.models.models import SavedPassage, User
from app.schemas.translation import TranslationInfo


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

    async def save_passage(self, db: AsyncSession, passage: BiblePassage) -> SavedPassage:
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
        await db.flush()  # Flush to get ID without committing (commit handled by dependency)
        await db.refresh(db_passage)
        return db_passage

    async def close(self):
        """Close the client."""
        if hasattr(self.client, "close"):
            await self.client.close()

    @staticmethod
    def get_available_translations(is_pro: bool = False) -> list[TranslationInfo]:
        """
        Get list of available translations based on user's subscription status.

        Args:
            is_pro: Whether the user has a pro subscription

        Returns:
            List of available translations with metadata
        """
        # Get all translations from the SQLite client
        all_translations = [
            TranslationInfo(
                code="WEB",
                name="World English Bible",
                requires_pro=False,
            ),
            TranslationInfo(
                code="KJV",
                name="King James Version",
                requires_pro=False,
            ),
            TranslationInfo(
                code="BSB",
                name="Berean Standard Bible",
                requires_pro=False,
            ),
            TranslationInfo(
                code="NRSV",
                name="New Revised Standard Version",
                requires_pro=True,
            ),
            TranslationInfo(
                code="ASV",
                name="American Standard Version",
                requires_pro=False,
            ),
            TranslationInfo(
                code="LSV",
                name="Literal Standard Version",
                requires_pro=False,
            ),
            TranslationInfo(
                code="BST",
                name="Brenton English Septuagint",
                requires_pro=False,
            ),
            TranslationInfo(
                code="LXXSB",
                name="British English Septuagint 2012",
                requires_pro=False,
            ),
            TranslationInfo(
                code="TOJBT",
                name="The Orthodox Jewish Bible",
                requires_pro=False,
            ),
            TranslationInfo(
                code="PEV",
                name="Plain English Version",
                requires_pro=False,
            ),
            TranslationInfo(
                code="RV",
                name="Revised Version",
                requires_pro=False,
            ),
            TranslationInfo(
                code="MSB",
                name="Majority Standard Bible",
                requires_pro=False,
            ),
            TranslationInfo(
                code="YLT",
                name="Young's Literal Translation",
                requires_pro=False,
            ),
            TranslationInfo(
                code="BBE",
                name="Bible in Basic English",
                requires_pro=False,
            ),
            TranslationInfo(
                code="EMTV",
                name="English Majority Text Version",
                requires_pro=False,
            ),
            TranslationInfo(
                code="BES",
                name="La Biblia en Español Sencillo",
                requires_pro=False,
            ),
            TranslationInfo(
                code="SRV",
                name="Santa Biblia - Reina-Valera 1909",
                requires_pro=False,
            ),
        ]

        # Filter translations based on pro status
        if is_pro:
            return all_translations
        else:
            return [t for t in all_translations if not t.requires_pro]

    @staticmethod
    def validate_translation_access(translation: str, user: User) -> None:
        """
        Validate that a user has access to a specific translation.

        Args:
            translation: Translation code
            user: User object

        Raises:
            HTTPException: If user doesn't have access to the translation
        """
        if SQLiteBibleClient.is_pro_translation(translation) and not user.pro_subscription:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": f"The {translation} translation requires a pro subscription.",
                    "translation": translation,
                    "requires_pro": True,
                },
            )
