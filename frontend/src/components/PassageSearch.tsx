import React, { useState } from 'react';
import { BookOpen, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
  onSearch: (book: string, chapter: number, verseStart: number, verseEnd?: number, translation?: string) => void;
}

const PassageSearch: React.FC<PassageSearchProps> = ({ onSearch }) => {
  const [book, setBook] = useState('John');
  const [chapter, setChapter] = useState('3');
  const [verseStart, setVerseStart] = useState('16');
  const [verseEnd, setVerseEnd] = useState('');
  const [translation, setTranslation] = useState('WEB');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const chapterNum = parseInt(chapter);
    const verseStartNum = parseInt(verseStart);
    const verseEndNum = verseEnd ? parseInt(verseEnd) : undefined;

    if (isNaN(chapterNum) || isNaN(verseStartNum)) {
      alert('Please enter valid numbers for chapter and verse');
      return;
    }

    onSearch(book, chapterNum, verseStartNum, verseEndNum, translation);
  };

  return (
    <Card>
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
              <SelectContent>
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
            <Label htmlFor="verseStart">Verse Start</Label>
            <Input
              id="verseStart"
              type="number"
              value={verseStart}
              onChange={(e) => setVerseStart(e.target.value)}
              min="1"
              required
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
    </Card>
  );
};

export default PassageSearch;
