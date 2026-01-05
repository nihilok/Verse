import React from "react";
import type {
  BibleVerse,
  ChapterContentElement,
  ChapterContentVerse,
} from "@/types";
import type { FontSize, FontFamily } from "@/lib/storage";
import { getFontSizeClass, getFontFamilyClass } from "@/lib/storage";
import { isVerseHighlighted } from "@/lib/urlParser";
import { ProseVerse } from "./ProseVerse";
import { PoetryVerse } from "./PoetryVerse";
import { VerseNumber } from "./VerseNumber";
import { isTextPart } from "./textUtils";

interface ParagraphLayoutProps {
  verses: BibleVerse[];
  chapterContent?: { content: ChapterContentElement[] };
  fontSize: FontSize;
  fontFamily?: FontFamily;
  highlightVerseStart?: number;
  highlightVerseEnd?: number;
}

function hasPoetryFormatting(verse: BibleVerse): boolean {
  const parts = verse.text_parts;
  if (!parts || parts.length === 0) return false;
  return parts.some((p) => isTextPart(p) && p.poem !== undefined);
}

function hasPoetryInVerse(verse: ChapterContentVerse): boolean {
  return verse.content.some(
    (part) =>
      typeof part === "object" && "text" in part && part.poem !== undefined,
  );
}

function renderChapterContentVerse(
  verse: ChapterContentVerse,
  highlighted: boolean,
  isFirstVerse: boolean = false,
): React.ReactNode {
  const elements: React.ReactNode[] = [];
  let verseNumberShown = false;
  const isPoetry = hasPoetryInVerse(verse);

  // Add line break before poetry verses (except the first one) to separate stanzas
  if (isPoetry && !isFirstVerse) {
    elements.push(<br key="stanza-break" />);
  }

  verse.content.forEach((part, i) => {
    if (typeof part === "string") {
      if (!verseNumberShown) {
        elements.push(
          <React.Fragment key={`vn-${i}`}>
            <VerseNumber verse={verse.number} variant="superscript" />
            {part}
          </React.Fragment>,
        );
        verseNumberShown = true;
      } else {
        elements.push(<React.Fragment key={i}>{part}</React.Fragment>);
      }
    } else if ("text" in part) {
      // For poetry, use block display with indentation
      if (isPoetry) {
        const indentStyle: React.CSSProperties = {
          display: "block",
          paddingLeft: part.poem ? `${part.poem}rem` : undefined,
        };
        if (!verseNumberShown) {
          elements.push(
            <span key={`vn-${i}`} style={indentStyle}>
              <VerseNumber verse={verse.number} variant="superscript" />
              {part.text}
            </span>,
          );
          verseNumberShown = true;
        } else {
          elements.push(
            <span key={i} style={indentStyle}>
              {part.text}
            </span>,
          );
        }
      } else {
        // For prose, keep inline
        if (!verseNumberShown) {
          elements.push(
            <React.Fragment key={`vn-${i}`}>
              <VerseNumber verse={verse.number} variant="superscript" />
              {part.text}
            </React.Fragment>,
          );
          verseNumberShown = true;
        } else {
          elements.push(<React.Fragment key={i}>{part.text}</React.Fragment>);
        }
      }
    } else if ("lineBreak" in part) {
      elements.push(<br key={i} />);
    }
  });

  // Fallback if no text content found
  if (!verseNumberShown) {
    elements.unshift(
      <VerseNumber
        key="vn-fallback"
        verse={verse.number}
        variant="superscript"
      />,
    );
  }

  return (
    <span
      id={`verse-${verse.number}`}
      className={
        highlighted
          ? "bg-yellow-100 dark:bg-yellow-900/30 rounded px-0.5 transition-colors duration-300"
          : ""
      }
    >
      {elements}{" "}
    </span>
  );
}

function verseStartsWithPilcrow(verse: ChapterContentVerse): boolean {
  if (verse.content.length === 0) return false;
  const firstPart = verse.content[0];
  if (typeof firstPart === "string") {
    return firstPart.trimStart().startsWith("¶");
  }
  if (typeof firstPart === "object" && "text" in firstPart) {
    return firstPart.text.trimStart().startsWith("¶");
  }
  return false;
}

function stripPilcrowFromVerse(
  verse: ChapterContentVerse,
): ChapterContentVerse {
  if (!verseStartsWithPilcrow(verse)) return verse;

  const newContent = [...verse.content];
  const firstPart = newContent[0];
  if (typeof firstPart === "string") {
    newContent[0] = firstPart.replace(/^\s*¶\s*/, "");
  } else if (typeof firstPart === "object" && "text" in firstPart) {
    newContent[0] = {
      ...firstPart,
      text: firstPart.text.replace(/^\s*¶\s*/, ""),
    };
  }
  return { ...verse, content: newContent };
}

function renderChapterContent(
  content: ChapterContentElement[],
  highlightStart?: number,
  highlightEnd?: number,
): React.ReactNode {
  const elements: React.ReactNode[] = [];
  let currentParagraph: React.ReactNode[] = [];
  let paragraphKey = 0;
  let isFirstVerseInParagraph = true;

  const flushParagraph = () => {
    if (currentParagraph.length > 0) {
      elements.push(
        <p key={`p-${paragraphKey}`} className="mb-4 leading-relaxed">
          {currentParagraph}
        </p>,
      );
      currentParagraph = [];
      paragraphKey++;
      isFirstVerseInParagraph = true;
    }
  };

  content.forEach((item, index) => {
    if (item.type === "heading") {
      flushParagraph();
      elements.push(
        <h3
          key={`h-${index}`}
          className="text-lg font-semibold mt-6 mb-3 text-primary"
        >
          {item.content.join(" ")}
        </h3>,
      );
    } else if (item.type === "line_break") {
      // flushParagraph();
    } else if (item.type === "verse") {
      const hasPilcrow = verseStartsWithPilcrow(item);
      if (hasPilcrow) {
        flushParagraph();
      }

      const highlighted = isVerseHighlighted(
        item.number,
        highlightStart,
        highlightEnd,
      );

      const displayVerse = hasPilcrow ? stripPilcrowFromVerse(item) : item;

      currentParagraph.push(
        <React.Fragment key={`v-${item.number}`}>
          {renderChapterContentVerse(
            displayVerse,
            highlighted,
            isFirstVerseInParagraph,
          )}
        </React.Fragment>,
      );
      isFirstVerseInParagraph = false;
    }
  });

  flushParagraph();

  return <>{elements}</>;
}

export const ParagraphLayout: React.FC<ParagraphLayoutProps> = ({
  verses,
  chapterContent,
  fontSize,
  fontFamily = "inter",
  highlightVerseStart,
  highlightVerseEnd,
}) => {
  const fontClasses = `mt-2 ${getFontSizeClass(fontSize)} ${getFontFamilyClass(fontFamily)}`;

  if (chapterContent) {
    return (
      <div className={fontClasses}>
        {renderChapterContent(
          chapterContent.content,
          highlightVerseStart,
          highlightVerseEnd,
        )}
      </div>
    );
  }

  return (
    <div className={fontClasses}>
      <div className="leading-relaxed">
        {verses.map((verse) => {
          const highlighted = isVerseHighlighted(
            verse.verse,
            highlightVerseStart,
            highlightVerseEnd,
          );
          const isPoetry = hasPoetryFormatting(verse);

          return (
            <React.Fragment key={`${verse.chapter}:${verse.verse}`}>
              {isPoetry ? (
                <PoetryVerse verse={verse} highlighted={highlighted} />
              ) : (
                <ProseVerse verse={verse} highlighted={highlighted} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
