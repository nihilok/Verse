/**
 * Utilities for safe localStorage operations with error handling
 */

const STORAGE_KEYS = {
  PASSAGE_SEARCH: "verse_passage_search",
  LAST_PASSAGE: "verse_last_passage",
} as const;

/**
 * Safely get an item from localStorage with error handling
 */
export function getStorageItem<T>(key: string, defaultValue: T): T {
  try {
    const item = localStorage.getItem(key);
    if (item === null) {
      return defaultValue;
    }
    return JSON.parse(item) as T;
  } catch (error) {
    console.error(`Error reading from localStorage (${key}):`, error);
    return defaultValue;
  }
}

/**
 * Safely set an item in localStorage with error handling
 */
export function setStorageItem<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error writing to localStorage (${key}):`, error);
  }
}

/**
 * Safely remove an item from localStorage with error handling
 */
export function removeStorageItem(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error(`Error removing from localStorage (${key}):`, error);
  }
}

// Passage search persistence
export interface PassageSearchState {
  book: string;
  chapter: string;
  verseStart: string;
  verseEnd: string;
  translation: string;
}

export function savePassageSearch(state: PassageSearchState): void {
  setStorageItem(STORAGE_KEYS.PASSAGE_SEARCH, state);
}

export function loadPassageSearch(): PassageSearchState | null {
  return getStorageItem<PassageSearchState | null>(
    STORAGE_KEYS.PASSAGE_SEARCH,
    null,
  );
}

// Last passage persistence
export interface LastPassageState {
  book: string;
  chapter: number;
  translation: string;
}

export function saveLastPassage(state: LastPassageState): void {
  setStorageItem(STORAGE_KEYS.LAST_PASSAGE, state);
}

export function loadLastPassage(): LastPassageState | null {
  return getStorageItem<LastPassageState | null>(
    STORAGE_KEYS.LAST_PASSAGE,
    null,
  );
}
