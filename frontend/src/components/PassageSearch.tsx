import React, { useState } from 'react';

interface PassageSearchProps {
  onSearch: (book: string, chapter: number, verseStart: number, verseEnd?: number) => void;
}

const PassageSearch: React.FC<PassageSearchProps> = ({ onSearch }) => {
  const [book, setBook] = useState('John');
  const [chapter, setChapter] = useState('3');
  const [verseStart, setVerseStart] = useState('16');
  const [verseEnd, setVerseEnd] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const chapterNum = parseInt(chapter);
    const verseStartNum = parseInt(verseStart);
    const verseEndNum = verseEnd ? parseInt(verseEnd) : undefined;

    if (isNaN(chapterNum) || isNaN(verseStartNum)) {
      alert('Please enter valid numbers for chapter and verse');
      return;
    }

    onSearch(book, chapterNum, verseStartNum, verseEndNum);
  };

  return (
    <div className="search-container">
      <h2>Search Bible Passage</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="book">Book:</label>
          <input
            id="book"
            type="text"
            value={book}
            onChange={(e) => setBook(e.target.value)}
            placeholder="e.g., John, Genesis, Romans"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="chapter">Chapter:</label>
          <input
            id="chapter"
            type="number"
            value={chapter}
            onChange={(e) => setChapter(e.target.value)}
            min="1"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="verseStart">Verse Start:</label>
          <input
            id="verseStart"
            type="number"
            value={verseStart}
            onChange={(e) => setVerseStart(e.target.value)}
            min="1"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="verseEnd">Verse End (optional):</label>
          <input
            id="verseEnd"
            type="number"
            value={verseEnd}
            onChange={(e) => setVerseEnd(e.target.value)}
            min="1"
          />
        </div>
        <button type="submit" className="search-button">
          Load Passage
        </button>
      </form>
    </div>
  );
};

export default PassageSearch;
