import React, { useState, useEffect, useMemo, useRef } from "react";
import { Search, Crown } from "lucide-react";
import { CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { loadPassageSearch, savePassageSearch } from "@/lib/storage";
import {
  BIBLE_BOOKS,
  getBookIndex,
  clampChapterForBook,
} from "@/lib/bibleStructure";
import { TranslationInfo } from "@/types";
import { bibleService } from "@/services/api";
import toast from "@/lib/toast";

// Derive a simple list of book names from the canonical structure
const BOOK_NAMES = BIBLE_BOOKS.map((b) => b.name);

interface PassageSearchProps {
  onSearch: (
    book: string,
    chapter: number,
    verseStart?: number,
    verseEnd?: number,
    translation?: string,
  ) => void;
}

const PassageSearch: React.FC<PassageSearchProps> = ({ onSearch }) => {
  // Load saved values from localStorage once during initialization
  // useMemo with empty deps ensures this only runs once
  const savedState = useMemo(() => loadPassageSearch(), []);

  const [book, setBook] = useState(savedState?.book || "John");
  const [chapter, setChapter] = useState(savedState?.chapter || "3");
  const [verseStart, setVerseStart] = useState(savedState?.verseStart || "");
  const [verseEnd, setVerseEnd] = useState(savedState?.verseEnd || "");
  const [translation, setTranslation] = useState(
    savedState?.translation || "WEB",
  );
  const [translations, setTranslations] = useState<TranslationInfo[]>([]);
  const [translationsLoading, setTranslationsLoading] = useState(true);

  // Fetch available translations on mount
  useEffect(() => {
    const fetchTranslations = async () => {
      try {
        const response = await bibleService.getTranslations();
        setTranslations(response.translations);
      } catch (error) {
        console.error("Failed to fetch translations:", error);
        toast({
          title: "Error loading translations",
          description: "Using default translation (WEB)",
        });
      } finally {
        setTranslationsLoading(false);
      }
    };

    fetchTranslations();
  }, []);

  // Compute the maximum chapter for the currently selected book
  const currentBookIndex = getBookIndex(book);
  const maxChapters =
    currentBookIndex === -1
      ? undefined
      : BIBLE_BOOKS[currentBookIndex].chapters;

  // If the selected book changes and the current chapter is greater than the
  // book's maximum, clamp it to the last chapter of the book.
  useEffect(() => {
    if (!maxChapters) return;
    const chapterNum = parseInt(chapter);
    if (!isNaN(chapterNum) && chapterNum > maxChapters) {
      setChapter(String(maxChapters));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [book]);

  // Track if this is the first render to avoid saving during initialization
  const isFirstRender = useRef(true);

  // Save to localStorage whenever values change (except on first render)
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    savePassageSearch({
      book,
      chapter,
      verseStart,
      verseEnd,
      translation,
    });
  }, [book, chapter, verseStart, verseEnd, translation]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const chapterNum = parseInt(chapter);
    const verseStartNum = verseStart ? parseInt(verseStart) : undefined;
    const verseEndNum = verseEnd ? parseInt(verseEnd) : undefined;

    if (isNaN(chapterNum)) {
      toast({
        title: "Invalid input",
        description: "Please enter a valid number for chapter",
      });
      return;
    }

    // Enforce maximum chapter for the selected book using helper
    const clamped = clampChapterForBook(book, chapterNum);
    if (clamped !== chapterNum) {
      const bookMax = clamped;
      toast({
        title: "Chapter out of range",
        description: `Requested chapter ${chapterNum} is beyond the last chapter of ${book}. Loading chapter ${bookMax} instead.`,
      });
      onSearch(book, bookMax, verseStartNum, verseEndNum, translation);
      setChapter(String(bookMax));
      return;
    }

    if (verseStart && verseStartNum === undefined) {
      toast({
        title: "Invalid input",
        description: "Please enter a valid number for verse start",
      });
      return;
    }

    onSearch(book, chapterNum, verseStartNum, verseEndNum, translation);
  };

  return (
    <>
      <CardContent className="pt-0 px-4">
        <p className="text-sm text-muted-foreground mb-4">
          Search for any Bible passage by book, chapter, and verse
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="book">Book</Label>
            <Select value={book} onValueChange={setBook}>
              <SelectTrigger id="book">
                <SelectValue placeholder="Select a book" />
              </SelectTrigger>
              <SelectContent className="max-h-60 overflow-y-auto border border-border">
                {BOOK_NAMES.map((bookName) => (
                  <SelectItem key={bookName} value={bookName}>
                    {bookName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="chapter">Chapter</Label>
            <Input
              id="chapter"
              type="number"
              value={chapter}
              onChange={(e) => {
                const v = e.target.value;
                // allow empty while typing but clamp to max if provided
                if (v === "") {
                  setChapter(v);
                  return;
                }
                const num = parseInt(v);
                if (isNaN(num)) {
                  setChapter(v);
                  return;
                }
                if (maxChapters && num > maxChapters) {
                  setChapter(String(maxChapters));
                } else if (num < 1) {
                  setChapter("1");
                } else {
                  setChapter(String(num));
                }
              }}
              min="1"
              max={maxChapters}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="verseStart">Verse Start (optional)</Label>
            <Input
              id="verseStart"
              type="number"
              value={verseStart}
              onChange={(e) => setVerseStart(e.target.value)}
              min="1"
              placeholder="Optional"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="verseEnd">Verse End (optional)</Label>
            <Input
              id="verseEnd"
              type="number"
              value={verseEnd}
              onChange={(e) => setVerseEnd(e.target.value)}
              min="1"
              placeholder="Optional"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="translation">Translation</Label>
            <Select
              value={translation}
              onValueChange={setTranslation}
              disabled={translationsLoading}
            >
              <SelectTrigger id="translation">
                <SelectValue placeholder="Select translation" />
              </SelectTrigger>
              <SelectContent>
                {translations.map((trans) => (
                  <SelectItem key={trans.code} value={trans.code}>
                    <div className="flex items-center gap-2">
                      <span>{trans.name}</span>
                      {trans.requires_pro && (
                        <Crown className="h-3 w-3 text-yellow-500" />
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button type="submit" className="w-full">
            <Search size={18} />
            Load Passage
          </Button>
        </form>
      </CardContent>
    </>
  );
};

export default PassageSearch;
