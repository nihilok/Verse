import { useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { bibleService } from "../services/api";
import { BiblePassage } from "../types";
import { loadLastPassage, saveLastPassage } from "../lib/storage";
import { BIBLE_BOOKS, getBookIndex } from "../lib/bibleStructure";
import { parsePassageFromURL, generatePassageURL } from "../lib/urlParser";

export function useBiblePassage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [passage, setPassage] = useState<BiblePassage | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentBook, setCurrentBook] = useState("John");
  const [currentChapter, setCurrentChapter] = useState(3);
  const [currentTranslation, setCurrentTranslation] = useState("WEB");
  const [highlightVerseStart, setHighlightVerseStart] = useState<
    number | undefined
  >(undefined);
  const [highlightVerseEnd, setHighlightVerseEnd] = useState<
    number | undefined
  >(undefined);

  const handleSearch = useCallback(
    async (
      book: string,
      chapter: number,
      verseStart?: number,
      verseEnd?: number,
      translation: string = "WEB",
    ) => {
      setLoading(true);
      setCurrentBook(book);
      setCurrentChapter(chapter);
      setCurrentTranslation(translation);
      setHighlightVerseStart(verseStart);
      setHighlightVerseEnd(verseEnd);

      const newUrl = generatePassageURL({
        book,
        chapter,
        verseStart,
        verseEnd,
        translation,
      });
      setSearchParams(newUrl.slice(1));

      try {
        const result = await bibleService.getChapter(
          book,
          chapter,
          translation,
        );
        setPassage(result);

        saveLastPassage({
          book,
          chapter,
          verse_start: verseStart,
          verse_end: verseEnd,
          translation,
        });

        return result;
      } catch (err) {
        console.error("Error loading passage:", err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [setSearchParams],
  );

  const handleNavigate = useCallback(
    async (direction: "prev" | "next") => {
      const bookIdx = getBookIndex(currentBook);
      if (bookIdx === -1) return;
      const currentBookInfo = BIBLE_BOOKS[bookIdx];
      let newBook = currentBook;
      let newChapter = currentChapter;

      if (direction === "next") {
        if (currentChapter < currentBookInfo.chapters) {
          newChapter = currentChapter + 1;
        } else if (bookIdx < BIBLE_BOOKS.length - 1) {
          newBook = BIBLE_BOOKS[bookIdx + 1].name;
          newChapter = 1;
        } else {
          return;
        }
      } else if (direction === "prev") {
        if (currentChapter > 1) {
          newChapter = currentChapter - 1;
        } else if (bookIdx > 0) {
          newBook = BIBLE_BOOKS[bookIdx - 1].name;
          newChapter = BIBLE_BOOKS[bookIdx - 1].chapters;
        } else {
          return;
        }
      }

      await handleSearch(
        newBook,
        newChapter,
        undefined,
        undefined,
        currentTranslation,
      );
    },
    [currentBook, currentChapter, currentTranslation, handleSearch],
  );

  const handleTranslationChange = useCallback(
    async (newTranslation: string) => {
      await handleSearch(
        currentBook,
        currentChapter,
        highlightVerseStart,
        highlightVerseEnd,
        newTranslation,
      );
    },
    [
      currentBook,
      currentChapter,
      highlightVerseStart,
      highlightVerseEnd,
      handleSearch,
    ],
  );

  const loadFromURL = useCallback(() => {
    const urlParams = parsePassageFromURL(searchParams);
    if (urlParams) {
      handleSearch(
        urlParams.book,
        urlParams.chapter,
        urlParams.verseStart,
        urlParams.verseEnd,
        urlParams.translation || "WEB",
      );
      return true;
    }
    return false;
  }, [searchParams, handleSearch]);

  const loadLastViewedPassage = useCallback(() => {
    const lastPassage = loadLastPassage();
    if (lastPassage) {
      handleSearch(
        lastPassage.book,
        lastPassage.chapter,
        lastPassage.verse_start,
        lastPassage.verse_end,
        lastPassage.translation,
      );
      return true;
    }
    return false;
  }, [handleSearch]);

  return {
    passage,
    loading,
    currentBook,
    currentChapter,
    currentTranslation,
    highlightVerseStart,
    highlightVerseEnd,
    handleSearch,
    handleNavigate,
    handleTranslationChange,
    loadFromURL,
    loadLastViewedPassage,
  };
}
