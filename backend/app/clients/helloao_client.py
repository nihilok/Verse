import httpx
from typing import Optional, List
from app.clients.bible_client import BibleClient, BibleVerse, BiblePassage


class HelloAOBibleClient(BibleClient):
    """Implementation of BibleClient using bible.helloao.org API."""
    
    BASE_URL = "https://bible.helloao.org/api"
    
    # Map user-friendly translation names to HelloAO API IDs
    TRANSLATION_IDS = {
        "WEB": "ENGWEBP",  # World English Bible
        "KJV": "eng_kjv",   # King James Version
        "BSB": "BSB",   # Berean Standard Bible
        "LSV": "eng_lsv",   # Literal Standard Version
        "SRV": "spa_r09",  # Spanish Reina-Valera 1909
        "BES": "spa_bes"  # Spanish Biblia en Español Sencillo
    }

    BOOK_IDS = {
    "Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV", "Numbers": "NUM", "Deuteronomy": "DEU",
    "Joshua": "JOS", "Judges": "JDG", "Ruth": "RUT", "1 Samuel": "1SA", "2 Samuel": "2SA",
    "1 Kings": "1KI", "2 Kings": "2KI", "1 Chronicles": "1CH", "2 Chronicles": "2CH",
    "Ezra": "EZR", "Nehemiah": "NEH", "Esther": "EST", "Job": "JOB", "Psalms": "PSA",
    "Proverbs": "PRO", "Ecclesiastes": "ECC", "Song of Solomon": "SNG", "Isaiah": "ISA",
    "Jeremiah": "JER", "Lamentations": "LAM", "Ezekiel": "EZE", "Daniel": "DAN",
    "Hosea": "HOS", "Joel": "JOL", "Amos": "AMO", "Obadiah": "OBA", "Jonah": "JON",
    "Micah": "MIC", "Nahum": "NAM", "Habakkuk": "HAB", "Zephaniah": "ZEP", "Haggai": "HAG",
    "Zechariah": "ZEC", "Malachi": "MAL", "Matthew": "MAT", "Mark": "MRK", "Luke": "LUK",
    "John": "JHN", "Acts": "ACT", "Romans": "ROM", "1 Corinthians": "1CO", "2 Corinthians": "2CO",
    "Galatians": "GAL", "Ephesians": "EPH", "Philippians": "PHP", "Colossians": "COL",
    "1 Thessalonians": "1TH", "2 Thessalonians": "2TH", "1 Timothy": "1TI", "2 Timothy": "2TI",
    "Titus": "TIT", "Philemon": "PHM", "Hebrews": "HEB", "James": "JAS", "1 Peter": "1PE",
    "2 Peter": "2PE", "1 John": "1JN", "2 John": "2JN", "3 John": "3JN", "Jude": "JUD",
    "Revelation": "REV"
}

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _normalize_book_name(self, book: str) -> str:
        """Normalize book names to API book IDs."""
        return self.BOOK_IDS.get(book, self.BOOK_IDS.get(book.title(), book.replace(" ", "").upper()))

    async def _get_chapter_data(self, book: str, chapter: int, translation: str = "WEB") -> Optional[dict]:
        try:
            book_id = self._normalize_book_name(book)
            # Map translation name to HelloAO API ID
            api_translation = self.TRANSLATION_IDS.get(translation, translation)
            url = f"{self.BASE_URL}/{api_translation}/{book_id}/{chapter}.json"
            print(f"Fetching from URL: {url}")  # Debug log
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching chapter data: {e}")
            return None

    def _extract_verse_text(self, content: List) -> str:
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict):
                # Handle footnotes and other non-text dictionaries by adding a space
                # to prevent words from being concatenated together
                if 'text' in item:
                    text_parts.append(item['text'])
                elif 'noteId' in item:
                    # Footnote marker - add a space to separate surrounding words
                    text_parts.append(' ')
        return ''.join(text_parts).strip()

    async def get_verse(
        self, 
        book: str, 
        chapter: int, 
        verse: int, 
        translation: str = "WEB"
    ) -> Optional[BibleVerse]:
        """Get a single verse from HelloAO API."""
        data = await self._get_chapter_data(book, chapter, translation)
        if not data:
            return None
        chapter_content = data.get('chapter', {}).get('content', [])
        for item in chapter_content:
            if item.get('type') == 'verse' and item.get('number') == verse:
                text = self._extract_verse_text(item.get('content', []))
                return BibleVerse(
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    text=text,
                    translation=translation
                )
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
        data = await self._get_chapter_data(book, chapter, translation)
        if not data:
            return None
        chapter_content = data.get('chapter', {}).get('content', [])
        verses = []
        for item in chapter_content:
            if item.get('type') == 'verse':
                verse_num = item.get('number')
                if verse_start <= verse_num <= verse_end:
                    text = self._extract_verse_text(item.get('content', []))
                    verses.append(BibleVerse(
                        book=book,
                        chapter=chapter,
                        verse=verse_num,
                        text=text,
                        translation=translation
                    ))
        if verses:
            reference = f"{book} {chapter}:{verse_start}-{verse_end}"
            return BiblePassage(
                reference=reference,
                verses=verses,
                translation=translation
            )
        return None

    async def get_chapter(
        self,
        book: str,
        chapter: int,
        translation: str = "WEB"
    ) -> Optional[BiblePassage]:
        """Get an entire chapter from HelloAO API."""
        data = await self._get_chapter_data(book, chapter, translation)
        if not data:
            return None
        chapter_content = data.get('chapter', {}).get('content', [])
        verses = []
        for item in chapter_content:
            if item.get('type') == 'verse':
                verse_num = item.get('number')
                text = self._extract_verse_text(item.get('content', []))
                verses.append(BibleVerse(
                    book=book,
                    chapter=chapter,
                    verse=verse_num,
                    text=text,
                    translation=translation
                ))
        if verses:
            reference = f"{book} {chapter}"
            return BiblePassage(
                reference=reference,
                verses=verses,
                translation=translation
            )
        return None
