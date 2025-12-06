import { describe, it, expect } from "vitest";
import {
  parsePassageFromURL,
  generatePassageURL,
  isVerseHighlighted,
} from "../urlParser";

describe("urlParser", () => {
  describe("parsePassageFromURL", () => {
    it("should parse basic book and chapter", () => {
      const params = new URLSearchParams("book=John&chapter=3");
      const result = parsePassageFromURL(params);
      expect(result).toEqual({
        book: "John",
        chapter: 3,
      });
    });

    it("should parse single verse with verse parameter", () => {
      const params = new URLSearchParams("book=John&chapter=3&verse=16");
      const result = parsePassageFromURL(params);
      expect(result).toEqual({
        book: "John",
        chapter: 3,
        verseStart: 16,
        verseEnd: 16,
      });
    });

    it("should parse verse range with verseStart and verseEnd", () => {
      const params = new URLSearchParams(
        "book=John&chapter=3&verseStart=16&verseEnd=17"
      );
      const result = parsePassageFromURL(params);
      expect(result).toEqual({
        book: "John",
        chapter: 3,
        verseStart: 16,
        verseEnd: 17,
      });
    });

    it("should parse translation", () => {
      const params = new URLSearchParams(
        "book=John&chapter=3&verse=16&translation=KJV"
      );
      const result = parsePassageFromURL(params);
      expect(result).toEqual({
        book: "John",
        chapter: 3,
        verseStart: 16,
        verseEnd: 16,
        translation: "KJV",
      });
    });

    it("should handle book names with spaces", () => {
      const params = new URLSearchParams("book=1 Corinthians&chapter=13");
      const result = parsePassageFromURL(params);
      expect(result).toEqual({
        book: "1 Corinthians",
        chapter: 13,
      });
    });

    it("should return null if book is missing", () => {
      const params = new URLSearchParams("chapter=3");
      const result = parsePassageFromURL(params);
      expect(result).toBeNull();
    });

    it("should return null if chapter is missing", () => {
      const params = new URLSearchParams("book=John");
      const result = parsePassageFromURL(params);
      expect(result).toBeNull();
    });

    it("should return null if chapter is not a number", () => {
      const params = new URLSearchParams("book=John&chapter=invalid");
      const result = parsePassageFromURL(params);
      expect(result).toBeNull();
    });

    it("should prioritize verse parameter over verseStart/verseEnd", () => {
      const params = new URLSearchParams(
        "book=John&chapter=3&verse=16&verseStart=20&verseEnd=22"
      );
      const result = parsePassageFromURL(params);
      expect(result).toEqual({
        book: "John",
        chapter: 3,
        verseStart: 16,
        verseEnd: 16,
      });
    });
  });

  describe("generatePassageURL", () => {
    it("should generate URL for book and chapter", () => {
      const url = generatePassageURL({
        book: "John",
        chapter: 3,
      });
      expect(url).toBe("?book=John&chapter=3");
    });

    it("should generate URL with single verse", () => {
      const url = generatePassageURL({
        book: "John",
        chapter: 3,
        verseStart: 16,
      });
      expect(url).toBe("?book=John&chapter=3&verse=16");
    });

    it("should generate URL with single verse when start and end are same", () => {
      const url = generatePassageURL({
        book: "John",
        chapter: 3,
        verseStart: 16,
        verseEnd: 16,
      });
      expect(url).toBe("?book=John&chapter=3&verse=16");
    });

    it("should generate URL with verse range", () => {
      const url = generatePassageURL({
        book: "John",
        chapter: 3,
        verseStart: 16,
        verseEnd: 17,
      });
      expect(url).toBe("?book=John&chapter=3&verseStart=16&verseEnd=17");
    });

    it("should generate URL with translation", () => {
      const url = generatePassageURL({
        book: "John",
        chapter: 3,
        verseStart: 16,
        translation: "KJV",
      });
      expect(url).toBe("?book=John&chapter=3&verse=16&translation=KJV");
    });

    it("should handle book names with spaces", () => {
      const url = generatePassageURL({
        book: "1 Corinthians",
        chapter: 13,
      });
      expect(url).toBe("?book=1+Corinthians&chapter=13");
    });
  });

  describe("isVerseHighlighted", () => {
    it("should return false when no highlight range is provided", () => {
      expect(isVerseHighlighted(16)).toBe(false);
      expect(isVerseHighlighted(16, undefined, undefined)).toBe(false);
    });

    it("should return true for verse in single-verse highlight", () => {
      expect(isVerseHighlighted(16, 16)).toBe(true);
      expect(isVerseHighlighted(16, 16, 16)).toBe(true);
    });

    it("should return false for verse outside single-verse highlight", () => {
      expect(isVerseHighlighted(15, 16)).toBe(false);
      expect(isVerseHighlighted(17, 16)).toBe(false);
    });

    it("should return true for verse in range highlight", () => {
      expect(isVerseHighlighted(16, 15, 17)).toBe(true);
      expect(isVerseHighlighted(15, 15, 17)).toBe(true);
      expect(isVerseHighlighted(17, 15, 17)).toBe(true);
    });

    it("should return false for verse outside range highlight", () => {
      expect(isVerseHighlighted(14, 15, 17)).toBe(false);
      expect(isVerseHighlighted(18, 15, 17)).toBe(false);
    });
  });
});
