/**
 * Utilities for safe localStorage operations with error handling
 */

const STORAGE_KEYS = {
  PASSAGE_SEARCH: "verse_passage_search",
  LAST_PASSAGE: "verse_last_passage",
  WAKE_LOCK_TIMEOUT: "verse_wake_lock_timeout",
  FONT_SIZE: "verse_font_size",
  FONT_FAMILY: "verse_font_family",
} as const;

// Font size types
export type FontSize = "small" | "medium" | "large" | "extra-large";

// Font family types
export type FontFamily = "inter" | "serif" | "open-dyslexic" | "atkinson";

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
  verse_start?: number;
  verse_end?: number;
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

// Wake lock timeout persistence (in minutes)
const DEFAULT_WAKE_LOCK_TIMEOUT_MINUTES = 5;

export function saveWakeLockTimeout(timeoutMinutes: number): void {
  setStorageItem(STORAGE_KEYS.WAKE_LOCK_TIMEOUT, timeoutMinutes);
}

export function loadWakeLockTimeout(): number {
  return getStorageItem<number>(
    STORAGE_KEYS.WAKE_LOCK_TIMEOUT,
    DEFAULT_WAKE_LOCK_TIMEOUT_MINUTES,
  );
}

// Font size persistence
const DEFAULT_FONT_SIZE: FontSize = "medium";

export function saveFontSize(fontSize: FontSize): void {
  setStorageItem(STORAGE_KEYS.FONT_SIZE, fontSize);
}

export function loadFontSize(): FontSize {
  return getStorageItem<FontSize>(STORAGE_KEYS.FONT_SIZE, DEFAULT_FONT_SIZE);
}

// Font size CSS class mapping
export function getFontSizeClass(fontSize: FontSize): string {
  const sizeMap: Record<FontSize, string> = {
    small: "text-sm",
    medium: "text-base",
    large: "text-lg",
    "extra-large": "text-xl",
  };
  return sizeMap[fontSize];
}

// Font family persistence
const DEFAULT_FONT_FAMILY: FontFamily = "inter";

export function saveFontFamily(fontFamily: FontFamily): void {
  setStorageItem(STORAGE_KEYS.FONT_FAMILY, fontFamily);
}

export function loadFontFamily(): FontFamily {
  return getStorageItem<FontFamily>(
    STORAGE_KEYS.FONT_FAMILY,
    DEFAULT_FONT_FAMILY,
  );
}

// Font family CSS class mapping
export function getFontFamilyClass(fontFamily: FontFamily): string {
  const familyMap: Record<FontFamily, string> = {
    inter: "font-sans",
    serif: "font-serif",
    "open-dyslexic": "font-dyslexic",
    atkinson: "font-atkinson",
  };
  return familyMap[fontFamily];
}
