import { describe, it, expect, beforeAll } from "vitest";
import {
  createPassageLink,
  createMarkdownPassageLink,
  formatPassageReference,
  parsePassageReference,
} from "../passageLinks";

describe("passageLinks", () => {
  beforeAll(() => {
    // Mock window.location.origin for all tests
    if (typeof window !== "undefined") {
      Object.defineProperty(window, "location", {
        value: { origin: "http://localhost:5173" },
        writable: true,
        configurable: true,
      });
    }
  });

  describe("createPassageLink", () => {
    const baseUrl = "http://localhost:5173";

    it("should create a link for a single verse", () => {
      const link = createPassageLink(
        {
          book: "John",
          chapter: 3,
          verseStart: 16,
        },
        baseUrl,
      );
      expect(link).toBe("http://localhost:5173?book=John&chapter=3&verse=16");
    });

    it("should create a link for a verse range", () => {
      const link = createPassageLink(
        {
          book: "John",
          chapter: 3,
          verseStart: 16,
          verseEnd: 17,
        },
        baseUrl,
      );
      expect(link).toBe(
        "http://localhost:5173?book=John&chapter=3&verseStart=16&verseEnd=17",
      );
    });

    it("should create a link with translation", () => {
      const link = createPassageLink(
        {
          book: "John",
          chapter: 3,
          verseStart: 16,
          translation: "KJV",
        },
        baseUrl,
      );
      expect(link).toBe(
        "http://localhost:5173?book=John&chapter=3&verse=16&translation=KJV",
      );
    });

    it("should use custom base URL if provided", () => {
      const link = createPassageLink(
        {
          book: "John",
          chapter: 3,
          verseStart: 16,
        },
        "https://example.com",
      );
      expect(link).toBe("https://example.com?book=John&chapter=3&verse=16");
    });
  });

  describe("createMarkdownPassageLink", () => {
    const baseUrl = "http://localhost:5173";

    it("should create a markdown link with custom text", () => {
      const mdLink = createMarkdownPassageLink(
        { book: "John", chapter: 3, verseStart: 16 },
        "Read John 3:16",
        baseUrl,
      );
      expect(mdLink).toBe(
        "[Read John 3:16](http://localhost:5173?book=John&chapter=3&verse=16)",
      );
    });

    it("should create a markdown link with auto-generated text", () => {
      const mdLink = createMarkdownPassageLink(
        {
          book: "John",
          chapter: 3,
          verseStart: 16,
        },
        undefined,
        baseUrl,
      );
      expect(mdLink).toBe(
        "[John 3:16](http://localhost:5173?book=John&chapter=3&verse=16)",
      );
    });

    it("should create a markdown link for a verse range", () => {
      const mdLink = createMarkdownPassageLink(
        {
          book: "John",
          chapter: 3,
          verseStart: 16,
          verseEnd: 17,
        },
        undefined,
        baseUrl,
      );
      expect(mdLink).toBe(
        "[John 3:16-17](http://localhost:5173?book=John&chapter=3&verseStart=16&verseEnd=17)",
      );
    });
  });

  describe("formatPassageReference", () => {
    it("should format a chapter reference", () => {
      const ref = formatPassageReference({ book: "John", chapter: 3 });
      expect(ref).toBe("John 3");
    });

    it("should format a single verse reference", () => {
      const ref = formatPassageReference({
        book: "John",
        chapter: 3,
        verseStart: 16,
      });
      expect(ref).toBe("John 3:16");
    });

    it("should format a verse range reference", () => {
      const ref = formatPassageReference({
        book: "John",
        chapter: 3,
        verseStart: 16,
        verseEnd: 17,
      });
      expect(ref).toBe("John 3:16-17");
    });

    it("should include translation in parentheses", () => {
      const ref = formatPassageReference({
        book: "John",
        chapter: 3,
        verseStart: 16,
        translation: "KJV",
      });
      expect(ref).toBe("John 3:16 (KJV)");
    });

    it("should handle book names with numbers", () => {
      const ref = formatPassageReference({
        book: "1 Corinthians",
        chapter: 13,
        verseStart: 4,
      });
      expect(ref).toBe("1 Corinthians 13:4");
    });
  });

  describe("parsePassageReference", () => {
    it("should parse a chapter reference", () => {
      const result = parsePassageReference("John 3");
      expect(result).toEqual({ book: "John", chapter: 3 });
    });

    it("should parse a single verse reference", () => {
      const result = parsePassageReference("John 3:16");
      expect(result).toEqual({ book: "John", chapter: 3, verseStart: 16 });
    });

    it("should parse a verse range reference", () => {
      const result = parsePassageReference("John 3:16-17");
      expect(result).toEqual({
        book: "John",
        chapter: 3,
        verseStart: 16,
        verseEnd: 17,
      });
    });

    it("should parse book names with numbers", () => {
      const result = parsePassageReference("1 Corinthians 13:4");
      expect(result).toEqual({
        book: "1 Corinthians",
        chapter: 13,
        verseStart: 4,
      });
    });

    it("should parse book names with multiple words", () => {
      const result = parsePassageReference("Song of Solomon 2:1");
      expect(result).toEqual({
        book: "Song of Solomon",
        chapter: 2,
        verseStart: 1,
      });
    });

    it("should handle extra whitespace", () => {
      const result = parsePassageReference("  John   3:16  ");
      expect(result).toEqual({ book: "John", chapter: 3, verseStart: 16 });
    });

    it("should return null for invalid format", () => {
      expect(parsePassageReference("invalid")).toBeNull();
      expect(parsePassageReference("John")).toBeNull();
    });
  });
});
