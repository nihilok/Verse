import React, { useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Sparkles, X } from 'lucide-react';
import { BiblePassage } from '../types';

interface BibleReaderProps {
  passage: BiblePassage | null;
  onTextSelected: (text: string, reference: string) => void;
  onNavigate?: (direction: 'prev' | 'next') => void;
}

const BibleReader: React.FC<BibleReaderProps> = ({ passage, onTextSelected, onNavigate }) => {
  const [selectedText, setSelectedText] = useState('');
  const [selectionPosition, setSelectionPosition] = useState<{ x: number; y: number } | null>(null);
  const readerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();
      
      if (text && text.length > 0 && selection && readerRef.current?.contains(selection.anchorNode)) {
        setSelectedText(text);

        // Get selection position for tooltip (below selection to avoid native menu)
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        const containerRect = readerRef.current.getBoundingClientRect();

        setSelectionPosition({
          x: rect.left + rect.width / 2 - containerRect.left,
          y: rect.bottom - containerRect.top + 10
        });
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
      clearSelection();
    }
  };

  const clearSelection = () => {
    setSelectedText('');
    setSelectionPosition(null);
    window.getSelection()?.removeAllRanges();
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

        {/* Selection Tooltip */}
        {selectionPosition && selectedText && (
          <div
            className="selection-tooltip"
            style={{
              left: `${selectionPosition.x}px`,
              top: `${selectionPosition.y}px`
            }}
          >
            <button onClick={handleGetInsights} className="tooltip-button">
              <Sparkles size={16} />
              Get Insight
            </button>
            <button onClick={clearSelection} className="tooltip-button close">
              <X size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Navigation Controls */}
      {onNavigate && (
        <div className="navigation-controls">
          <button onClick={() => onNavigate('prev')} className="nav-button">
            <ChevronLeft size={20} />
            <span>Previous Chapter</span>
          </button>
          <button onClick={() => onNavigate('next')} className="nav-button">
            <span>Next Chapter</span>
            <ChevronRight size={20} />
          </button>
        </div>
      )}
    </div>
  );
};

export default BibleReader;
