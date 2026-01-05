import React from "react";
import type { BibleVerse } from "@/types";
import { VerseNumber } from "./VerseNumber";
import {
  isTextPart,
  isLineBreak,
  containsPilcrow,
  removePilcrow,
} from "./textUtils";

interface ProseVerseProps {
  verse: BibleVerse;
  highlighted: boolean;
}

export const ProseVerse: React.FC<ProseVerseProps> = ({
  verse,
  highlighted,
}) => {
  const parts = verse.text_parts;

  const textContent =
    parts && parts.length > 0
      ? parts
          .map((part) => {
            if (typeof part === "string") return part;
            if (isTextPart(part)) return part.text;
            return "";
          })
          .join("")
      : verse.text;

  const hasPilcrow = containsPilcrow(textContent);

  return (
    <span
      id={`verse-${verse.verse}`}
      className={
        highlighted
          ? "bg-yellow-100 dark:bg-yellow-900/30 rounded px-0.5 transition-colors duration-300"
          : ""
      }
    >
      {hasPilcrow && <span className="block h-3" />}
      <VerseNumber verse={verse.verse} variant="inline" />
      {parts && parts.length > 0
        ? parts.map((part, i) => {
            if (typeof part === "string") {
              return <span key={i}>{removePilcrow(part)} </span>;
            }
            if (isTextPart(part)) {
              return <span key={i}>{removePilcrow(part.text)} </span>;
            }
            if (isLineBreak(part)) {
              return <br key={i} />;
            }
            return null;
          })
        : removePilcrow(verse.text)}{" "}
    </span>
  );
};
