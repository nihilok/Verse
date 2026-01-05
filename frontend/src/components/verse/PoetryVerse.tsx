import React from "react";
import type { BibleVerse } from "@/types";
import { VerseNumber } from "./VerseNumber";
import { isTextPart, isLineBreak, getPoemIndentClass } from "./textUtils";

interface PoetryVerseProps {
  verse: BibleVerse;
  highlighted: boolean;
}

export const PoetryVerse: React.FC<PoetryVerseProps> = ({
  verse,
  highlighted,
}) => {
  const parts = verse.text_parts;
  if (!parts || parts.length === 0) return null;

  const elements: React.ReactNode[] = [];
  let verseNumberShown = false;

  parts.forEach((part, i) => {
    if (typeof part === "string") {
      elements.push(
        <span key={i} className="italic ml-2">
          {!verseNumberShown && (
            <VerseNumber verse={verse.verse} variant="superscript" />
          )}
          {part}
        </span>,
      );
      verseNumberShown = true;
    } else if (isTextPart(part)) {
      const indentClass = getPoemIndentClass(part.poem);
      elements.push(
        <span key={i} className={`block ${indentClass}`}>
          {!verseNumberShown && (
            <VerseNumber verse={verse.verse} variant="superscript" />
          )}
          {part.text}
        </span>,
      );
      verseNumberShown = true;
    } else if (isLineBreak(part)) {
      elements.push(<span key={i} className="block h-2" />);
    }
  });

  return (
    <span
      id={`verse-${verse.verse}`}
      className={`block mb-1 ${
        highlighted
          ? "bg-yellow-100 dark:bg-yellow-900/30 rounded px-1 py-0.5 transition-colors duration-300"
          : ""
      }`}
    >
      {elements}
    </span>
  );
};
