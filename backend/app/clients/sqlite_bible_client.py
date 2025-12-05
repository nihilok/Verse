import logging
from pathlib import Path

import aiosqlite

from app.clients.bible_client import BibleClient, BiblePassage, BibleVerse

logger = logging.getLogger(__name__)


class SQLiteBibleClient(BibleClient):
    """Implementation of BibleClient using local SQLite database."""

    # Default database path relative to backend directory
    DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "bible.eng.db"

    # Map user-friendly translation names to database translation IDs
    TRANSLATION_IDS = {
        "WEB": "ENGWEBP",  # World English Bible
        "KJV": "eng_kjv",  # King James Version
        "BSB": "BSB",  # Berean Standard Bible
        "ASV": "eng_asv",  # American Standard Version (1901)
        "LSV": "eng_lsv",  # Literal Standard Version
        "BST": "eng_bre",  # Brenton English Septuagint
        "LXXSB": "eng_lxu",  # British English Septuagint 2012
        "LXXSA": "eng_lxx",  # American English Septuagint 2012
        "UBES": "eng_boy",  # Updated Brenton English Septuagint
        "TOJBT": "eng_ojb",  # The Orthodox Jewish Bible Translation
        "PEV": "eng_pev",  # Plain English Version
        "RV": "eng_rv5",  # Revised Version
        "MSB": "eng_msb",  # Majority Standard Bible
        "YLT": "eng_ylt",  # Young's Literal Translation
        "BBE": "eng_bbe",  # Bible in Basic English
        "EMTV": "eng_emtv",  # English Majority Text Version
        # Jewish/Hebrew-focused translations
        "JPSTN": "eng_jps",  # JPS TaNaKH 1917
        "ILT": "eng_lee",  # Isaac Leeser Tanakh
        "TOE": "eng_oke",  # Targum Onkelos Etheridge
        "WMB": "eng_wmb",  # World Messianic Bible
        # Scholarly translations
        "NETB": "eng_net",  # NET Bible
        "DBY": "eng_dby",  # Darby Translation
    }

    BOOK_IDS = {
        "Genesis": "GEN",
        "Exodus": "EXO",
        "Leviticus": "LEV",
        "Numbers": "NUM",
        "Deuteronomy": "DEU",
        "Joshua": "JOS",
        "Judges": "JDG",
        "Ruth": "RUT",
        "1 Samuel": "1SA",
        "2 Samuel": "2SA",
        "1 Kings": "1KI",
        "2 Kings": "2KI",
        "1 Chronicles": "1CH",
        "2 Chronicles": "2CH",
        "Ezra": "EZR",
        "Nehemiah": "NEH",
        "Esther": "EST",
        "Job": "JOB",
        "Psalms": "PSA",
        "Proverbs": "PRO",
        "Ecclesiastes": "ECC",
        "Song of Solomon": "SNG",
        "Isaiah": "ISA",
        "Jeremiah": "JER",
        "Lamentations": "LAM",
        "Ezekiel": "EZE",
        "Daniel": "DAN",
        "Hosea": "HOS",
        "Joel": "JOL",
        "Amos": "AMO",
        "Obadiah": "OBA",
        "Jonah": "JON",
        "Micah": "MIC",
        "Nahum": "NAM",
        "Habakkuk": "HAB",
        "Zephaniah": "ZEP",
        "Haggai": "HAG",
        "Zechariah": "ZEC",
        "Malachi": "MAL",
        "Matthew": "MAT",
        "Mark": "MRK",
        "Luke": "LUK",
        "John": "JHN",
        "Acts": "ACT",
        "Romans": "ROM",
        "1 Corinthians": "1CO",
        "2 Corinthians": "2CO",
        "Galatians": "GAL",
        "Ephesians": "EPH",
        "Philippians": "PHP",
        "Colossians": "COL",
        "1 Thessalonians": "1TH",
        "2 Thessalonians": "2TH",
        "1 Timothy": "1TI",
        "2 Timothy": "2TI",
        "Titus": "TIT",
        "Philemon": "PHM",
        "Hebrews": "HEB",
        "James": "JAS",
        "1 Peter": "1PE",
        "2 Peter": "2PE",
        "1 John": "1JN",
        "2 John": "2JN",
        "3 John": "3JN",
        "Jude": "JUD",
        "Revelation": "REV",
    }

    def __init__(self, db_path: str | Path | None = None):
        """Initialize the SQLite Bible client.

        Args:
            db_path: Path to the SQLite database file. If None, uses default path.
        """
        self.db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

    def _normalize_book_name(self, book: str) -> str:
        """Normalize book names to database book IDs."""
        return self.BOOK_IDS.get(book, self.BOOK_IDS.get(book.title(), book.upper()))

    def _normalize_translation(self, translation: str) -> str:
        """Normalize translation name to database translation ID."""
        return self.TRANSLATION_IDS.get(translation, translation)

    async def get_verse(
        self, book: str, chapter: int, verse: int, translation: str = "WEB"
    ) -> BibleVerse | None:
        """Get a single verse from the SQLite database."""
        try:
            book_id = self._normalize_book_name(book)
            translation_id = self._normalize_translation(translation)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT number, chapterNumber, text
                    FROM ChapterVerse
                    WHERE bookId = ? AND chapterNumber = ? AND number = ? AND translationId = ?
                    """,
                    (book_id, chapter, verse, translation_id),
                )
                row = await cursor.fetchone()

                if row:
                    return BibleVerse(
                        book=book,
                        chapter=chapter,
                        verse=row[0],
                        text=row[2],
                        translation=translation,
                    )
                return None
        except Exception as e:
            logger.error(
                f"Error fetching verse {book} {chapter}:{verse} ({translation}): {e}",
                exc_info=True,
            )
            return None

    async def get_passage(
        self,
        book: str,
        chapter: int,
        verse_start: int,
        verse_end: int,
        translation: str = "WEB",
    ) -> BiblePassage | None:
        """Get a passage (range of verses) from the SQLite database."""
        try:
            book_id = self._normalize_book_name(book)
            translation_id = self._normalize_translation(translation)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT number, chapterNumber, text
                    FROM ChapterVerse
                    WHERE bookId = ? AND chapterNumber = ? AND number BETWEEN ? AND ? AND translationId = ?
                    ORDER BY number
                    """,
                    (book_id, chapter, verse_start, verse_end, translation_id),
                )
                rows = await cursor.fetchall()

                if rows:
                    verses = [
                        BibleVerse(
                            book=book,
                            chapter=chapter,
                            verse=row[0],
                            text=row[2],
                            translation=translation,
                        )
                        for row in rows
                    ]
                    reference = f"{book} {chapter}:{verse_start}-{verse_end}"
                    return BiblePassage(reference=reference, verses=verses, translation=translation)
                return None
        except Exception as e:
            logger.error(
                f"Error fetching passage {book} {chapter}:{verse_start}-{verse_end} ({translation}): {e}",
                exc_info=True,
            )
            return None

    async def get_chapter(self, book: str, chapter: int, translation: str = "WEB") -> BiblePassage | None:
        """Get an entire chapter from the SQLite database."""
        try:
            book_id = self._normalize_book_name(book)
            translation_id = self._normalize_translation(translation)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT number, chapterNumber, text
                    FROM ChapterVerse
                    WHERE bookId = ? AND chapterNumber = ? AND translationId = ?
                    ORDER BY number
                    """,
                    (book_id, chapter, translation_id),
                )
                rows = await cursor.fetchall()

                if rows:
                    verses = [
                        BibleVerse(
                            book=book,
                            chapter=chapter,
                            verse=row[0],
                            text=row[2],
                            translation=translation,
                        )
                        for row in rows
                    ]
                    reference = f"{book} {chapter}"
                    return BiblePassage(reference=reference, verses=verses, translation=translation)
                return None
        except Exception as e:
            logger.error(
                f"Error fetching chapter {book} {chapter} ({translation}): {e}",
                exc_info=True,
            )
            return None
