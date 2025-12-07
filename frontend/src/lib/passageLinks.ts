/**
 * Helper functions for creating passage links that can be used in the application
 * These functions generate URLs that will automatically navigate to and highlight passages
 */

import { generatePassageURL } from "./urlParser";

export interface PassageLinkParams {
  book: string;
  chapter: number;
  verseStart?: number;
  verseEnd?: number;
  translation?: string;
}

/**
 * Create a full URL for a passage link
 * This can be used to generate links in markdown, emails, or other contexts
 *
 * @example
 * ```ts
 * // Single verse
 * const link = createPassageLink({ book: "John", chapter: 3, verseStart: 16 });
 * // Result: "http://localhost:5173?book=John&chapter=3&verse=16"
 *
 * // Verse range
 * const link = createPassageLink({
 *   book: "John",
 *   chapter: 3,
 *   verseStart: 16,
 *   verseEnd: 17,
 *   translation: "KJV"
 * });
 * // Result: "http://localhost:5173?book=John&chapter=3&verseStart=16&verseEnd=17&translation=KJV"
 * ```
 */
export function createPassageLink(
  params: PassageLinkParams,
  baseUrl?: string,
): string {
  const base =
    baseUrl || (typeof window !== "undefined" ? window.location.origin : "");
  const queryString = generatePassageURL(params);
  return `${base}${queryString}`;
}

/**
 * Create a markdown link for a passage
 * Useful for generating links in chat responses or documentation
 *
 * @example
 * ```ts
 * const mdLink = createMarkdownPassageLink(
 *   { book: "John", chapter: 3, verseStart: 16 },
 *   "Read John 3:16"
 * );
 * // Result: "[Read John 3:16](http://localhost:5173?book=John&chapter=3&verse=16)"
 * ```
 */
export function createMarkdownPassageLink(
  params: PassageLinkParams,
  linkText?: string,
  baseUrl?: string,
): string {
  const url = createPassageLink(params, baseUrl);
  const text = linkText || formatPassageReference(params);
  return `[${text}](${url})`;
}

/**
 * Format a passage reference as a human-readable string
 *
 * @example
 * ```ts
 * formatPassageReference({ book: "John", chapter: 3, verseStart: 16 })
 * // Result: "John 3:16"
 *
 * formatPassageReference({ book: "John", chapter: 3, verseStart: 16, verseEnd: 17 })
 * // Result: "John 3:16-17"
 *
 * formatPassageReference({ book: "John", chapter: 3 })
 * // Result: "John 3"
 * ```
 */
export function formatPassageReference(params: PassageLinkParams): string {
  let reference = `${params.book} ${params.chapter}`;

  if (params.verseStart !== undefined) {
    reference += `:${params.verseStart}`;

    if (
      params.verseEnd !== undefined &&
      params.verseEnd !== params.verseStart
    ) {
      reference += `-${params.verseEnd}`;
    }
  }

  if (params.translation) {
    reference += ` (${params.translation})`;
  }

  return reference;
}

/**
 * Parse a passage reference string into components
 * This is useful for converting user input into link parameters
 *
 * @example
 * ```ts
 * parsePassageReference("John 3:16")
 * // Result: { book: "John", chapter: 3, verseStart: 16 }
 *
 * parsePassageReference("John 3:16-17")
 * // Result: { book: "John", chapter: 3, verseStart: 16, verseEnd: 17 }
 *
 * parsePassageReference("John 3")
 * // Result: { book: "John", chapter: 3 }
 *
 * parsePassageReference("1 Corinthians 13:4-7")
 * // Result: { book: "1 Corinthians", chapter: 13, verseStart: 4, verseEnd: 7 }
 * ```
 */
export function parsePassageReference(
  reference: string,
): PassageLinkParams | null {
  // Pattern: "Book Chapter:Verse-Verse" or "Book Chapter:Verse" or "Book Chapter"
  // Examples: "John 3:16-17", "John 3:16", "John 3", "1 Corinthians 13:4"
  const pattern = /^(.+?)\s+(\d+)(?::(\d+)(?:-(\d+))?)?$/;
  const match = reference.trim().match(pattern);

  if (!match) {
    return null;
  }

  const [, book, chapterStr, verseStartStr, verseEndStr] = match;
  const chapter = parseInt(chapterStr);

  if (isNaN(chapter)) {
    return null;
  }

  const result: PassageLinkParams = {
    book: book.trim(),
    chapter,
  };

  if (verseStartStr) {
    const verseStart = parseInt(verseStartStr);
    if (!isNaN(verseStart)) {
      result.verseStart = verseStart;
    }
  }

  if (verseEndStr) {
    const verseEnd = parseInt(verseEndStr);
    if (!isNaN(verseEnd)) {
      result.verseEnd = verseEnd;
    }
  }

  return result;
}
