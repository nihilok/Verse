import React from "react";
import type { BibleVerse } from "@/types";
import type { FontSize, FontFamily } from "@/lib/storage";
import { getFontSizeClass, getFontFamilyClass } from "@/lib/storage";
import { isVerseHighlighted } from "@/lib/urlParser";
import { VerseNumber } from "./VerseNumber";

interface VerseByVerseLayoutProps {
  verses: BibleVerse[];
  fontSize: FontSize;
  fontFamily?: FontFamily;
  highlightVerseStart?: number;
  highlightVerseEnd?: number;
}

export const VerseByVerseLayout: React.FC<VerseByVerseLayoutProps> = ({
  verses,
  fontSize,
  fontFamily = "inter",
  highlightVerseStart,
  highlightVerseEnd,
}) => {
  return (
    <div className={`mt-2 ${getFontSizeClass(fontSize)} ${getFontFamilyClass(fontFamily)}`}>
      {verses.map((verse, index) => {
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
            <VerseNumber verse={verse.verse} variant="block" />
            <span className={`${getFontSizeClass(fontSize)} leading-relaxed`}>
              {verse.text}
            </span>
          </div>
        );
      })}
    </div>
  );
};
