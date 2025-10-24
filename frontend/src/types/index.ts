export interface BibleVerse {
  book: string;
  chapter: number;
  verse: number;
  text: string;
  translation: string;
}

export interface BiblePassage {
  reference: string;
  verses: BibleVerse[];
  translation: string;
}

export interface Insight {
  historical_context: string;
  theological_significance: string;
  practical_application: string;
  cached?: boolean;
}

export interface PassageQuery {
  book: string;
  chapter: number;
  verse_start: number;
  verse_end?: number;
  translation?: string;
}
