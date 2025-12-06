import React, { useEffect, useRef, useState, useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { BiblePassage } from "../types";
import { formatReferenceWithTranslation } from "../types";
import { CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import SelectionButtons from "./SelectionButtons";
import TranslationDropdown from "./TranslationDropdown";
import { isVerseHighlighted } from "@/lib/urlParser";

// Selection timing constants
const SELECTION_CHANGE_DELAY = 100; // ms to wait after selection change before capturing
const POINTER_UP_DELAY = 50; // ms to wait after pointer/touch up before capturing
const SELECTION_TOOLTIP_OFFSET = 32;

// Swipe constants
const SWIPE_THRESHOLD = 50; // minimum distance for swipe
const SWIPE_MAX_VERTICAL = 100; // maximum vertical movement allowed for horizontal swipe

interface BibleReaderProps {
  passage: BiblePassage | null;
  onTextSelected: (
    text: string,
    reference: string,
    isSingleWord: boolean,
    verseText?: string,
    verseStart?: number,
    verseEnd?: number,
  ) => void;
  onAskQuestion: (
    text: string,
    reference: string,
    verseStart?: number,
    verseEnd?: number,
  ) => void;
  onNavigate?: (direction: "prev" | "next") => void;
  onTranslationChange?: (translation: string) => void;
  loading?: boolean;
  highlightVerseStart?: number;
  highlightVerseEnd?: number;
}

const BibleReader: React.FC<BibleReaderProps> = ({
  passage,
  onTextSelected,
  onAskQuestion,
  onNavigate,
  onTranslationChange,
  loading = false,
  highlightVerseStart,
  highlightVerseEnd,
}) => {
  const [selectedText, setSelectedText] = useState("");
  const [selectionPosition, setSelectionPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const readerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const innerDivRef = useRef<HTMLDivElement>(null);

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

        // The SelectionButtons component is absolutely positioned relative to innerDivRef
        // We need to calculate position relative to that inner div
        const innerDiv = innerDivRef.current;
        if (!innerDiv) return;

        const innerDivRect = innerDiv.getBoundingClientRect();

        // Calculate position relative to the inner div
        // Both rect and innerDivRect are in viewport coordinates
        // Subtracting them gives us position relative to the inner div
        setSelectionPosition({
          x: rect.left - innerDivRect.left + rect.width / 2,
          y: rect.bottom - innerDivRect.top + SELECTION_TOOLTIP_OFFSET,
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

  // Scroll to highlighted verse when passage loads or highlight changes
  useEffect(() => {
    if (!passage || !highlightVerseStart || loading) {
      return;
    }

    // Wait for the passage to render before scrolling
    const scrollTimeout = setTimeout(() => {
      const highlightedElement = document.getElementById(
        `verse-${highlightVerseStart}`,
      );
      if (highlightedElement) {
        // Scroll the element into view with smooth behavior
        highlightedElement.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }
    }, 100);

    return () => clearTimeout(scrollTimeout);
  }, [passage, highlightVerseStart, loading]);

  // Helper function to check if text is a single word
  const isSingleWord = (text: string): boolean => {
    const trimmed = text.trim();
    // A single word contains no whitespace
    return trimmed.length > 0 && !/\s/.test(trimmed);
  };

  // Helper function to find the verse containing the selected text
  const findContainingVerse = (
    text: string,
  ): { verseText: string; verseReference: string } | null => {
    if (!passage) return null;

    // Create a regex with word boundaries for exact word matching, case-insensitive
    const escapedText = text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const wordRegex = new RegExp(`\\b${escapedText}\\b`, "i");
    for (const verse of passage.verses) {
      if (wordRegex.test(verse.text)) {
        // Create the specific verse reference (e.g., "John 3:16")
        const verseReference = `${verse.book} ${verse.chapter}:${verse.verse}`;
        return { verseText: verse.text, verseReference };
      }
    }
    return null;
  };

  // Helper function to get verse range from current selection
  const getVerseRangeFromSelection = (): {
    start?: number;
    end?: number;
  } => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return {};

    const range = selection.getRangeAt(0);
    const container = readerRef.current;
    if (!container || !container.contains(range.commonAncestorContainer)) {
      return {};
    }

    // Find all verse elements in the selection using a Set to avoid duplicates
    const verseElementSet = new Set<Element>();
    const walker = document.createTreeWalker(
      range.commonAncestorContainer,
      NodeFilter.SHOW_ELEMENT,
      {
        acceptNode: (node: Node) => {
          if (
            node instanceof Element &&
            node.id &&
            node.id.startsWith("verse-")
          ) {
            return NodeFilter.FILTER_ACCEPT;
          }
          return NodeFilter.FILTER_SKIP;
        },
      },
    );

    let node = walker.nextNode();
    while (node) {
      if (range.intersectsNode(node)) {
        verseElementSet.add(node as Element);
      }
      node = walker.nextNode();
    }

    // Also check start and end containers for verse parents
    const startVerse =
      range.startContainer.parentElement?.closest('[id^="verse-"]');
    const endVerse =
      range.endContainer.parentElement?.closest('[id^="verse-"]');

    if (startVerse) verseElementSet.add(startVerse);
    if (endVerse) verseElementSet.add(endVerse);

    const verseElements = Array.from(verseElementSet);

    if (verseElements.length === 0) return {};

    // Extract verse numbers from IDs
    const verseNumbers = verseElements
      .map((el) => {
        const match = el.id.match(/^verse-(\d+)$/);
        return match ? parseInt(match[1]) : null;
      })
      .filter((n): n is number => n !== null)
      .sort((a, b) => a - b);

    if (verseNumbers.length === 0) return {};

    return {
      start: verseNumbers[0],
      end: verseNumbers[verseNumbers.length - 1],
    };
  };

  // Memoize whether the current selection is a single word
  const isSelectedSingleWord = useMemo(() => {
    return isSingleWord(selectedText);
  }, [selectedText]);

  const handleGetInsights = (e: React.MouseEvent | React.TouchEvent) => {
    // Prevent the event from bubbling up and triggering document handlers
    e.preventDefault();
    e.stopPropagation();

    if (selectedText && passage) {
      // Store the text before clearing
      const textToSend = selectedText.trim();
      const isSingleWordSelection = isSingleWord(textToSend);

      // Get verse range from selection
      const verseRange = getVerseRangeFromSelection();

      // For single word selections, find the verse containing the word
      const verseInfo = isSingleWordSelection
        ? findContainingVerse(textToSend)
        : null;
      const baseReference = verseInfo?.verseReference || passage.reference;
      // Include translation in reference
      const referenceToSend = formatReferenceWithTranslation(
        baseReference,
        passage.translation,
      );
      const verseTextToSend = verseInfo?.verseText;

      // Clear the UI immediately
      setSelectedText("");
      setSelectionPosition(null);

      // Send the text after clearing the selection
      onTextSelected(
        textToSend,
        referenceToSend,
        isSingleWordSelection,
        verseTextToSend,
        verseRange.start,
        verseRange.end,
      );

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

      // Get verse range from selection
      const verseRange = getVerseRangeFromSelection();

      // Include translation in reference
      const referenceToSend = formatReferenceWithTranslation(
        passage.reference,
        passage.translation,
      );

      // Clear the UI immediately
      setSelectedText("");
      setSelectionPosition(null);

      // Send the text after clearing the selection
      onAskQuestion(
        textToSend,
        referenceToSend,
        verseRange.start,
        verseRange.end,
      );

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
        <div className="ml-auto">
          {passage && onTranslationChange ? (
            <TranslationDropdown
              value={passage.translation}
              onChange={onTranslationChange}
              disabled={loading}
            />
          ) : passage ? (
            <span className="bg-accent/80 text-accent-foreground px-3 py-1.5 rounded-full text-xs font-semibold tracking-wide">
              {passage.translation}
            </span>
          ) : null}
        </div>
      </CardHeader>
      <CardContent
        ref={contentRef}
        key={passage && !loading ? passage.reference : "loading"}
        className="flex-1 relative overflow-y-auto min-h-0 pt-6 px-4 sm:px-6 scrollbar-thin"
        onTouchStart={isTouchDevice ? handleTouchStart : undefined}
        onTouchMove={isTouchDevice ? handleTouchMove : undefined}
        onTouchEnd={isTouchDevice ? handleTouchEnd : undefined}
      >
        <div
          ref={innerDivRef}
          className="relative max-w-2xl min-h-full mx-auto"
        >
          {loading ? (
            <div className="space-y-3 mt-2 pl-4">
              {Array.from({ length: 9 }).map((_, index) => (
                <div key={index} className="flex gap-2 mb-4">
                  <Skeleton className="h-5 w-5 min-w-[24px] flex-shrink-0" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-5 w-full" />
                    <Skeleton
                      className="h-5"
                      style={{ width: `${Math.random() * 40 + 50}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : passage ? (
            passage.verses.map((verse, index) => {
              const highlighted = isVerseHighlighted(
                verse.verse,
                highlightVerseStart,
                highlightVerseEnd,
              );
              return (
                <div
                  key={`${verse.chapter}:${verse.verse}`}
                  id={`verse-${verse.verse}`}
                  className={`mb-3 flex items-start gap-2 group ${index === 0 ? "mt-2" : ""} ${
                    highlighted
                      ? "bg-yellow-100 dark:bg-yellow-900/30 -mx-2 px-2 py-2 rounded-md transition-colors duration-300"
                      : ""
                  }`}
                >
                  <span className="verse-number text-primary/70 font-semibold min-w-[28px] text-right select-none">
                    {verse.verse}
                  </span>
                  <span className="text-base leading-relaxed">
                    {verse.text}
                  </span>
                </div>
              );
            })
          ) : null}

          {/* Selection Tooltip */}
          {selectionPosition && selectedText && !loading && (
            <SelectionButtons
              position={selectionPosition}
              onGetInsights={handleGetInsights}
              onAskQuestion={handleAskQuestion}
              onClear={clearSelection}
              isSingleWord={isSelectedSingleWord}
            />
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
