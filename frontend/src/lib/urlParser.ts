/**
 * Utilities for parsing and generating passage URLs
 */

export interface PassageParams {
  book: string;
  chapter: number;
  verseStart?: number;
  verseEnd?: number;
  translation?: string;
}

/**
 * Parse URL search parameters into passage parameters
 * Expected format: ?book=John&chapter=3&verse=16 or ?book=John&chapter=3&verseStart=16&verseEnd=17
 */
export function parsePassageFromURL(searchParams: URLSearchParams): PassageParams | null {
  const book = searchParams.get('book');
  const chapterStr = searchParams.get('chapter');
  const verseStr = searchParams.get('verse');
  const verseStartStr = searchParams.get('verseStart');
  const verseEndStr = searchParams.get('verseEnd');
  const translation = searchParams.get('translation');

  if (!book || !chapterStr) {
    return null;
  }

  const chapter = parseInt(chapterStr);
  if (isNaN(chapter)) {
    return null;
  }

  const result: PassageParams = {
    book,
    chapter,
  };

  // Handle single verse parameter (verse=16)
  if (verseStr) {
    const verse = parseInt(verseStr);
    if (!isNaN(verse)) {
      result.verseStart = verse;
      result.verseEnd = verse;
    }
  }

  // Handle verse range parameters (verseStart=16&verseEnd=17)
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

  if (translation) {
    result.translation = translation;
  }

  return result;
}

/**
 * Generate URL search parameters from passage parameters
 */
export function generatePassageURL(params: PassageParams): string {
  const searchParams = new URLSearchParams();
  searchParams.set('book', params.book);
  searchParams.set('chapter', params.chapter.toString());

  if (params.verseStart !== undefined) {
    // If verseStart and verseEnd are the same, use single verse param
    if (params.verseEnd === params.verseStart || params.verseEnd === undefined) {
      searchParams.set('verse', params.verseStart.toString());
    } else {
      searchParams.set('verseStart', params.verseStart.toString());
      searchParams.set('verseEnd', params.verseEnd.toString());
    }
  }

  if (params.translation) {
    searchParams.set('translation', params.translation);
  }

  return `?${searchParams.toString()}`;
}

/**
 * Check if a verse number is within the highlighted range
 */
export function isVerseHighlighted(
  verseNumber: number,
  highlightStart?: number,
  highlightEnd?: number
): boolean {
  if (highlightStart === undefined) {
    return false;
  }

  const end = highlightEnd ?? highlightStart;
  return verseNumber >= highlightStart && verseNumber <= end;
}
