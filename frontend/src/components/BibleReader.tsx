import React, { useEffect, useRef, useState } from 'react';
import { BiblePassage } from '../types';

interface BibleReaderProps {
  passage: BiblePassage | null;
  onTextSelected: (text: string, reference: string) => void;
}

const BibleReader: React.FC<BibleReaderProps> = ({ passage, onTextSelected }) => {
  const [selectedText, setSelectedText] = useState('');
  const readerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();
      
      if (text && text.length > 0 && readerRef.current?.contains(selection.anchorNode)) {
        setSelectedText(text);
      }
    };

    document.addEventListener('mouseup', handleSelection);
    document.addEventListener('touchend', handleSelection);

    return () => {
      document.removeEventListener('mouseup', handleSelection);
      document.removeEventListener('touchend', handleSelection);
    };
  }, []);

  const handleGetInsights = () => {
    if (selectedText && passage) {
      onTextSelected(selectedText, passage.reference);
      setSelectedText('');
      window.getSelection()?.removeAllRanges();
    }
  };

  if (!passage) {
    return (
      <div className="bible-reader empty">
        <p>Search for a passage to begin reading</p>
      </div>
    );
  }

  return (
    <div className="bible-reader">
      <div className="passage-header">
        <h2>{passage.reference}</h2>
        <span className="translation-badge">{passage.translation}</span>
      </div>
      
      <div className="passage-content" ref={readerRef}>
        {passage.verses.map((verse) => (
          <p key={`${verse.chapter}:${verse.verse}`} className="verse">
            <span className="verse-number">{verse.verse}</span>
            <span className="verse-text">{verse.text}</span>
          </p>
        ))}
      </div>

      {selectedText && (
        <div className="selection-toolbar">
          <button onClick={handleGetInsights} className="insights-button">
            Get AI Insights on Selected Text
          </button>
        </div>
      )}
    </div>
  );
};

export default BibleReader;
