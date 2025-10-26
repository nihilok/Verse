import React, { useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Sparkles, X } from 'lucide-react';
import type { BiblePassage } from '../types';
import { CardHeader, CardTitle, CardContent } from '@/components/ui/card';

// Selection timing constants
const SELECTION_CHANGE_DELAY = 100; // ms to wait after selection change before capturing
const POINTER_UP_DELAY = 50; // ms to wait after pointer/touch up before capturing

interface BibleReaderProps {
  passage: BiblePassage | null;
  onTextSelected: (text: string, reference: string) => void;
  onNavigate?: (direction: 'prev' | 'next') => void;
}

const BibleReader: React.FC<BibleReaderProps> = ({ passage, onTextSelected, onNavigate }) => {
  const [selectedText, setSelectedText] = useState('');
  const [selectionPosition, setSelectionPosition] = useState<{ x: number; y: number } | null>(null);
  const readerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let selectionTimeout: ReturnType<typeof setTimeout>;
    
    const updateSelection = () => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();
      
      if (text && text.length > 0 && selection && selection.rangeCount > 0 && readerRef.current?.contains(selection.anchorNode)) {
        setSelectedText(text);

        // Get selection position for tooltip (below selection to avoid native menu)
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        // Find the scrolling container (CardContent)
        const scrollingContainer = contentRef.current;
        if (!scrollingContainer) return;

        const containerRect = scrollingContainer.getBoundingClientRect();

        // Calculate position relative to the container, accounting for scroll
        // Use the scrolling container's scroll position to ensure correct positioning
        // even when content is scrolled
        const scrollTop = scrollingContainer.scrollTop || 0;
        const scrollLeft = scrollingContainer.scrollLeft || 0;

        setSelectionPosition({
          x: rect.left - containerRect.left + scrollLeft + rect.width / 2,
          y: rect.bottom - containerRect.top + scrollTop + 32
        });
      } else if (!text) {
        // Clear selection if no text is selected
        setSelectedText('');
        setSelectionPosition(null);
      }
    };
    
    const handleSelectionChange = () => {
      // Clear any pending timeout
      if (selectionTimeout) {
        clearTimeout(selectionTimeout);
      }
      
      // Delay the selection capture slightly to allow selection to complete
      // This is especially important on mobile when using selection handles
      selectionTimeout = setTimeout(updateSelection, SELECTION_CHANGE_DELAY);
    };
    
    const handlePointerUp = () => {
      // Immediate update on pointer/touch release
      if (selectionTimeout) {
        clearTimeout(selectionTimeout);
      }
      selectionTimeout = setTimeout(updateSelection, POINTER_UP_DELAY);
    };

    // Listen to selectionchange for when user modifies selection (e.g., dragging handles on mobile)
    document.addEventListener('selectionchange', handleSelectionChange);
    
    // Also listen to mouse/touch events for initial selection
    document.addEventListener('mouseup', handlePointerUp);
    document.addEventListener('touchend', handlePointerUp);

    return () => {
      if (selectionTimeout) {
        clearTimeout(selectionTimeout);
      }
      document.removeEventListener('selectionchange', handleSelectionChange);
      document.removeEventListener('mouseup', handlePointerUp);
      document.removeEventListener('touchend', handlePointerUp);
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
      <CardHeader className="flex flex-row items-center gap-2 pb-4 border-b flex-shrink-0">
        <CardTitle className="text-lg">{passage.reference}</CardTitle>
        <span className="ml-auto bg-secondary text-secondary-foreground px-3 py-1 rounded text-xs font-semibold">{passage.translation}</span>
      </CardHeader>
      <CardContent ref={contentRef} className="flex-1 relative overflow-y-auto min-h-0">
        <div className="relative">
          {passage.verses.map((verse) => (
            <div key={`${verse.chapter}:${verse.verse}`} className="mb-4 flex items-start gap-2">
              <span className="text-primary font-bold min-w-[30px]">{verse.verse}</span>
              <span className="text-base">{verse.text}</span>
            </div>
          ))}

          {/* Selection Tooltip */}
          {selectionPosition && selectedText && (
            <div
              className="absolute bg-popover border border-border rounded-md shadow-lg p-1 flex gap-1 z-50"
              style={{
                left: `${selectionPosition.x}px`,
                top: `${selectionPosition.y}px`,
                transform: 'translate(-50%, 0)'
              }}
            >
              <button
                onClick={handleGetInsights}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors text-sm font-medium whitespace-nowrap"
              >
                <Sparkles size={14} />
                Get Insight
              </button>
              <button
                onClick={clearSelection}
                className="flex items-center justify-center p-1.5 rounded hover:bg-accent hover:text-accent-foreground transition-colors"
                aria-label="Close"
              >
                <X size={14} />
              </button>
            </div>
          )}
        </div>
      </CardContent>

      {/* Navigation Controls */}
      {onNavigate && (
        <div className="flex justify-between p-4 border-t gap-4 flex-shrink-0">
          <button
            onClick={() => onNavigate('prev')} 
            className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-foreground bg-secondary hover:bg-secondary/80 rounded-md transition-colors border border-border"
          >
            <ChevronLeft size={16} />
            Previous Chapter
          </button>
          <button 
            onClick={() => onNavigate('next')} 
            className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-foreground bg-secondary hover:bg-secondary/80 rounded-md transition-colors border border-border"
          >
            Next Chapter
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
};

export default BibleReader;
