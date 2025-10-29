import React, { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Loader2, Sparkles, X, MessageCircle } from "lucide-react";
import type { BiblePassage } from "../types";
import { CardHeader, CardTitle, CardContent } from "@/components/ui/card";

// Selection timing constants
const SELECTION_CHANGE_DELAY = 100; // ms to wait after selection change before capturing
const POINTER_UP_DELAY = 50; // ms to wait after pointer/touch up before capturing
const SELECTION_TOOLTIP_OFFSET = 32;

// Swipe constants
const SWIPE_THRESHOLD = 50; // minimum distance for swipe
const SWIPE_MAX_VERTICAL = 100; // maximum vertical movement allowed for horizontal swipe

interface BibleReaderProps {
  passage: BiblePassage | null;
  onTextSelected: (text: string, reference: string) => void;
  onAskQuestion: (text: string, reference: string) => void;
  onNavigate?: (direction: "prev" | "next") => void;
  loading?: boolean;
}

const BibleReader: React.FC<BibleReaderProps> = ({
  passage,
  onTextSelected,
  onAskQuestion,
  onNavigate,
  loading = false,
}) => {
  const [selectedText, setSelectedText] = useState("");
  const [selectionPosition, setSelectionPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const readerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // Swipe state
  const [touchStart, setTouchStart] = useState<{ x: number; y: number } | null>(
    null,
  );
  const [touchEnd, setTouchEnd] = useState<{ x: number; y: number } | null>(
    null,
  );

  useEffect(() => {
    let selectionTimeout: ReturnType<typeof setTimeout>;

    const updateSelection = () => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();

      if (
        text &&
        text.length > 0 &&
        selection &&
        selection.rangeCount > 0 &&
        readerRef.current?.contains(selection.anchorNode)
      ) {
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
          y:
            rect.bottom -
            containerRect.top +
            scrollTop +
            SELECTION_TOOLTIP_OFFSET,
        });
      } else if (!text) {
        // Clear selection if no text is selected
        setSelectedText("");
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
    document.addEventListener("selectionchange", handleSelectionChange);

    // Also listen to mouse/touch events for initial selection
    document.addEventListener("mouseup", handlePointerUp);
    document.addEventListener("touchend", handlePointerUp);

    return () => {
      if (selectionTimeout) {
        clearTimeout(selectionTimeout);
      }
      document.removeEventListener("selectionchange", handleSelectionChange);
      document.removeEventListener("mouseup", handlePointerUp);
      document.removeEventListener("touchend", handlePointerUp);
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
      setSelectedText("");
      setSelectionPosition(null);

      // Send the text after clearing the selection
      onTextSelected(textToSend, referenceToSend);

      // Clear the browser selection after a brief delay to ensure click is processed
      setTimeout(() => {
        window.getSelection()?.removeAllRanges();
      }, 100);
    }
  };

  const handleAskQuestion = (e: React.MouseEvent | React.TouchEvent) => {
    // Prevent the event from bubbling up and triggering document handlers
    e.preventDefault();
    e.stopPropagation();

    if (selectedText && passage) {
      // Store the text before clearing
      const textToSend = selectedText;
      const referenceToSend = passage.reference;

      // Clear the UI immediately
      setSelectedText("");
      setSelectionPosition(null);

      // Send the text after clearing the selection
      onAskQuestion(textToSend, referenceToSend);

      // Clear the browser selection after a brief delay to ensure click is processed
      setTimeout(() => {
        window.getSelection()?.removeAllRanges();
      }, 100);
    }
  };

  const clearSelection = () => {
    setSelectedText("");
    setSelectionPosition(null);
    window.getSelection()?.removeAllRanges();
  };

  // Swipe handling functions
  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null); // Reset touch end
    setTouchStart({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY,
    });
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    setTouchEnd({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY,
    });
  };

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd || !onNavigate || loading) return;

    const distanceX = touchStart.x - touchEnd.x;
    const distanceY = touchStart.y - touchEnd.y;
    const isLeftSwipe = distanceX > SWIPE_THRESHOLD;
    const isRightSwipe = distanceX < -SWIPE_THRESHOLD;
    const isVerticalSwipe = Math.abs(distanceY) > SWIPE_MAX_VERTICAL;

    // Only trigger swipe if it's horizontal and not too vertical
    if ((isLeftSwipe || isRightSwipe) && !isVerticalSwipe) {
      // Check if there's any selected text - if so, don't treat as swipe
      const selection = window.getSelection();
      const hasSelection = selection && selection.toString().trim().length > 0;

      if (!hasSelection) {
        if (isLeftSwipe) {
          onNavigate("next");
        } else if (isRightSwipe) {
          onNavigate("prev");
        }
      }
    }
  };

  // Check if device supports touch (mobile)
  const isTouchDevice =
    "ontouchstart" in window || navigator.maxTouchPoints > 0;

  if (!passage && !loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-muted-foreground">
        <p>Search for a passage to begin reading</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full" ref={readerRef}>
      <CardHeader className="flex flex-row items-center gap-2 pb-4 border-b flex-shrink-0 bg-muted/30 rounded-t-none lg:rounded-t-lg px-4 lg:px-6">
        <CardTitle className="text-xl font-semibold tracking-tight">
          {passage ? (
            passage.reference
          ) : (
            <span className="opacity-60">Loading...</span>
          )}
        </CardTitle>
        <span className="ml-auto bg-accent/80 text-accent-foreground px-3 py-1.5 rounded-full text-xs font-semibold tracking-wide">
          {passage ? passage.translation : null}
        </span>
      </CardHeader>
      <CardContent
        ref={contentRef}
        className="flex-1 relative overflow-y-auto min-h-0 pt-6 px-4 sm:px-6 scrollbar-thin"
        onTouchStart={isTouchDevice ? handleTouchStart : undefined}
        onTouchMove={isTouchDevice ? handleTouchMove : undefined}
        onTouchEnd={isTouchDevice ? handleTouchEnd : undefined}
      >
        <div className="relative max-w-2xl min-h-full mx-auto">
          {loading ? (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-muted-foreground fade-in-loading">
              <Loader2 size={48} className="animate-spin mb-4 text-primary" />
              <p>Loading passage...</p>
            </div>
          ) : passage ? (
            passage.verses.map((verse, index) => (
              <div
                key={`${verse.chapter}:${verse.verse}`}
                className={`mb-3 flex items-start gap-2 group ${index === 0 ? "mt-2" : ""}`}
              >
                <span className="verse-number text-primary/70 font-semibold min-w-[28px] text-right select-none">
                  {verse.verse}
                </span>
                <span className="text-base leading-relaxed">{verse.text}</span>
              </div>
            ))
          ) : null}

          {/* Selection Tooltip */}
          {selectionPosition && selectedText && !loading && (
            <div
              className="absolute bg-popover border-2 border-primary/20 rounded-lg shadow-xl p-1.5 flex flex-col gap-1.5 z-50"
              style={{
                left: `${selectionPosition.x}px`,
                top: `${selectionPosition.y}px`,
                transform: "translate(-50%, 0)",
              }}
            >
              <div className="flex gap-1.5">
                <button
                  onClick={handleGetInsights}
                  className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-all text-sm font-semibold whitespace-nowrap shadow-sm"
                >
                  <Sparkles size={16} />
                  Get Insights
                </button>
                <button
                  onClick={clearSelection}
                  className="flex items-center justify-center p-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
                  aria-label="Close"
                >
                  <X size={16} />
                </button>
              </div>
              <button
                onClick={handleAskQuestion}
                className="flex items-center gap-2 px-3.5 py-2 rounded-md bg-accent text-accent-foreground hover:bg-accent/80 transition-all text-sm font-semibold whitespace-nowrap shadow-sm"
              >
                <MessageCircle size={16} />
                Ask a Question
              </button>
            </div>
          )}
        </div>
      </CardContent>
      {/* Navigation Controls */}
      {onNavigate && (
        <div className="flex justify-between p-4 border-t bg-muted/20 gap-4 flex-shrink-0 sticky lg:relative bottom-0 left-0 right-0 z-10">
          <button
            onClick={() => onNavigate("prev")}
            className="flex-1 flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-medium text-foreground bg-background hover:bg-accent hover:text-accent-foreground rounded-lg transition-all border border-border shadow-sm hover:shadow disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loading}
          >
            <ChevronLeft size={16} />
            Previous Chapter
          </button>
          <button
            onClick={() => onNavigate("next")}
            className="flex-1 flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-medium text-foreground bg-background hover:bg-accent hover:text-accent-foreground rounded-lg transition-all border border-border shadow-sm hover:shadow disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loading}
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
