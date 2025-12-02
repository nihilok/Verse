import { describe, it, expect } from "vitest";
import {
  formatReferenceWithTranslation,
  parseReferenceWithTranslation,
} from "../index";

describe("Translation Reference Helpers", () => {
  describe("formatReferenceWithTranslation", () => {
    it("should add translation in parentheses to reference", () => {
      expect(formatReferenceWithTranslation("John 3:16", "KJV")).toBe(
        "John 3:16 (KJV)",
      );
      expect(formatReferenceWithTranslation("Romans 8:28", "WEB")).toBe(
        "Romans 8:28 (WEB)",
      );
      expect(formatReferenceWithTranslation("Genesis 1:1", "ASV")).toBe(
        "Genesis 1:1 (ASV)",
      );
    });

    it("should not add translation if already present", () => {
      expect(formatReferenceWithTranslation("John 3:16 (KJV)", "WEB")).toBe(
        "John 3:16 (KJV)",
      );
      expect(formatReferenceWithTranslation("Romans 8:28 (ASV)", "BSB")).toBe(
        "Romans 8:28 (ASV)",
      );
    });

    it("should handle references with ranges", () => {
      expect(formatReferenceWithTranslation("John 3:16-17", "KJV")).toBe(
        "John 3:16-17 (KJV)",
      );
      expect(formatReferenceWithTranslation("Matthew 5:1-12", "WEB")).toBe(
        "Matthew 5:1-12 (WEB)",
      );
    });

    it("should handle chapter-only references", () => {
      expect(formatReferenceWithTranslation("John 3", "KJV")).toBe(
        "John 3 (KJV)",
      );
      expect(formatReferenceWithTranslation("Psalm 23", "WEB")).toBe(
        "Psalm 23 (WEB)",
      );
    });
  });

  describe("parseReferenceWithTranslation", () => {
    it("should extract reference and translation from formatted reference", () => {
      expect(parseReferenceWithTranslation("John 3:16 (KJV)")).toEqual({
        reference: "John 3:16",
        translation: "KJV",
      });
      expect(parseReferenceWithTranslation("Romans 8:28 (WEB)")).toEqual({
        reference: "Romans 8:28",
        translation: "WEB",
      });
    });

    it("should handle reference without translation", () => {
      expect(parseReferenceWithTranslation("John 3:16")).toEqual({
        reference: "John 3:16",
        translation: null,
      });
      expect(parseReferenceWithTranslation("Romans 8:28")).toEqual({
        reference: "Romans 8:28",
        translation: null,
      });
    });

    it("should handle references with ranges", () => {
      expect(parseReferenceWithTranslation("John 3:16-17 (KJV)")).toEqual({
        reference: "John 3:16-17",
        translation: "KJV",
      });
    });

    it("should trim whitespace", () => {
      expect(parseReferenceWithTranslation("  John 3:16 (KJV)  ")).toEqual({
        reference: "John 3:16",
        translation: "KJV",
      });
      expect(parseReferenceWithTranslation("John 3:16  (  WEB  )")).toEqual({
        reference: "John 3:16",
        translation: "WEB",
      });
    });
  });
});
