import React, { useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Sparkles, X } from 'lucide-react';
import type { BiblePassage } from '../types';
import { CardHeader, CardTitle, CardContent } from '@/components/ui/card';

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
    let selectionTimeout: ReturnType<typeof setTimeout>;
    
    const handleSelection = () => {
      // Clear any pending timeout
      if (selectionTimeout) {
        clearTimeout(selectionTimeout);
      }
      
      // Delay the selection capture slightly on mobile to allow selection to complete
      selectionTimeout = setTimeout(() => {
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
            y: rect.bottom - containerRect.top + 5
          });
        }
      }, 50); // 50ms delay to allow selection to stabilize on mobile
    };

    document.addEventListener('mouseup', handleSelection);
    document.addEventListener('touchend', handleSelection);

    return () => {
      if (selectionTimeout) {
        clearTimeout(selectionTimeout);
      }
      document.removeEventListener('mouseup', handleSelection);
      document.removeEventListener('touchend', handleSelection);
    };
  }, []);

  const handleGetInsights = (e: React.MouseEvent | React.TouchEvent) => {
    // Prevent the event from bubbling up and triggering document handlers
    e.preventDefault();
    e.stopPropagation();
    
    if (selectedText && passage) {
      // Store the text before clearing
      const textToSend = selectedText;
      const referenceToSend = passage.reference;
      
      // Clear the UI immediately
      setSelectedText('');
      setSelectionPosition(null);
      
      // Send the text after clearing the selection
      onTextSelected(textToSend, referenceToSend);
      
      // Clear the browser selection after a brief delay to ensure click is processed
      setTimeout(() => {
        window.getSelection()?.removeAllRanges();
      }, 100);
    }
  };

  const clearSelection = () => {
    setSelectedText('');
    setSelectionPosition(null);
    window.getSelection()?.removeAllRanges();
  };

  if (!passage) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-muted-foreground">
        <p>Search for a passage to begin reading</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full" ref={readerRef}>
      <CardHeader className="flex flex-row items-center gap-2 pb-4 border-b">
        <CardTitle className="text-lg">{passage.reference}</CardTitle>
        <span className="ml-auto bg-secondary text-secondary-foreground px-3 py-1 rounded text-xs font-semibold">{passage.translation}</span>
      </CardHeader>
      <CardContent className="flex-1 relative">
        {passage.verses.map((verse) => (
          <div key={`${verse.chapter}:${verse.verse}`} className="mb-4 flex items-start gap-2">
            <span className="text-primary font-bold min-w-[30px]">{verse.verse}</span>
            <span className="text-base">{verse.text}</span>
          </div>
        ))}

        {/* Selection Tooltip */}
        {selectionPosition && selectedText && (
          <div
            className="absolute bg-popover border border-border rounded-md shadow-lg p-2 flex gap-2 z-50"
            style={{
              left: `${selectionPosition.x}px`,
              top: `${selectionPosition.y}px`,
              transform: 'translate(-50%, 0)'
            }}
          >
            <button 
              onClick={handleGetInsights}
              onTouchEnd={handleGetInsights}
              className="tooltip-button"
            >
              <Sparkles size={16} />
              Get Insight
            </button>
            <button onClick={clearSelection} className="tooltip-button close">
              <X size={16} />
            </button>
          </div>
        )}
      </CardContent>

      {/* Navigation Controls */}
      {onNavigate && (
        <div className="flex justify-between p-4 border-t">
          <button onClick={() => onNavigate('prev')} className="flex items-center text-sm text-muted-foreground">
            <ChevronLeft size={16} className="mr-1" />
            Previous Chapter
          </button>
          <button onClick={() => onNavigate('next')} className="flex items-center text-sm text-muted-foreground">
            Next Chapter
            <ChevronRight size={16} className="ml-1" />
          </button>
        </div>
      )}
    </div>
  );
};

export default BibleReader;
