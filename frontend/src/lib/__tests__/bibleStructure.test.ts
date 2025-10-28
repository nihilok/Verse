import { describe, it, expect } from "vitest";
import { clampChapterForBook, getBookMaxChapters } from "../bibleStructure";

describe("bibleStructure helpers", () => {
  it("returns max chapters for John and clamps correctly", () => {
    const max = getBookMaxChapters("John");
    expect(max).toBe(21);
    expect(clampChapterForBook("John", 100)).toBe(21);
    expect(clampChapterForBook("John", 0)).toBe(1);
    expect(clampChapterForBook("UnknownBook", 5)).toBe(5);
  });
});
