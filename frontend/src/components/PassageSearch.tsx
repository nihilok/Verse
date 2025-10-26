import React, { useState, useEffect, useMemo, useRef } from 'react';
import { BookOpen, Search } from 'lucide-react';
import { CardHeader, CardContent, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { loadPassageSearch, savePassageSearch } from '@/lib/storage';

const BIBLE_BOOKS = [
  'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth',
  '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra',
  'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs', 'Ecclesiastes', 'Song of Solomon',
  'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos',
  'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah',
  'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians',
  '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians',
  '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James',
  '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation'
];

const TRANSLATIONS = [
  { code: 'WEB', name: 'World English Bible' },
  { code: 'KJV', name: 'King James Version' },
  { code: 'OEB', name: 'Open English Bible' }
];

interface PassageSearchProps {
  onSearch: (book: string, chapter: number, verseStart?: number, verseEnd?: number, translation?: string) => void;
}

const PassageSearch: React.FC<PassageSearchProps> = ({ onSearch }) => {
  // Load saved values from localStorage once during initialization
  // useMemo with empty deps ensures this only runs once
  const savedState = useMemo(() => loadPassageSearch(), []);
  
  const [book, setBook] = useState(savedState?.book || 'John');
  const [chapter, setChapter] = useState(savedState?.chapter || '3');
  const [verseStart, setVerseStart] = useState(savedState?.verseStart || '');
  const [verseEnd, setVerseEnd] = useState(savedState?.verseEnd || '');
  const [translation, setTranslation] = useState(savedState?.translation || 'WEB');

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
      alert('Please enter a valid number for chapter');
      return;
    }

    if (verseStart && verseStartNum === undefined) {
      alert('Please enter a valid number for verse start');
      return;
    }

    onSearch(book, chapterNum, verseStartNum, verseEndNum, translation);
  };

  return (
    <>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BookOpen size={24} />
          Bible Passage
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="book">Book</Label>
            <Select value={book} onValueChange={setBook}>
              <SelectTrigger id="book">
                <SelectValue placeholder="Select a book" />
              </SelectTrigger>
              <SelectContent className="max-h-60 overflow-y-auto border border-border">
                {BIBLE_BOOKS.map(bookName => (
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
              onChange={(e) => setChapter(e.target.value)}
              min="1"
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
              placeholder="Optional - leave blank for full chapter"
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
            <Select value={translation} onValueChange={setTranslation}>
              <SelectTrigger id="translation">
                <SelectValue placeholder="Select translation" />
              </SelectTrigger>
              <SelectContent>
                {TRANSLATIONS.map(trans => (
                  <SelectItem key={trans.code} value={trans.code}>
                    {trans.name}
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
