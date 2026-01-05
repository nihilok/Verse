// Keep storage mocked globally to avoid localStorage access during imports
import { vi, Mock } from "vitest";

vi.mock("@/lib/storage", () => ({
  __esModule: true,
  loadPassageSearch: () => ({
    book: "John",
    chapter: "3",
    verseStart: "",
    verseEnd: "",
    translation: "WEB",
  }),
  savePassageSearch: () => {},
}));

import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach } from "vitest";

// Tests will mock or unmock toast per-case and dynamically import PassageSearch after resetModules

describe("PassageSearch (tests)", () => {
  beforeEach(() => {
    // Ensure clean DOM between tests
    cleanup();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it("clamps chapter to book max and calls onSearch (toast mocked)", async () => {
    // Reset module registry so mocks apply correctly
    await vi.resetModules();

    // Mock toast for this test
    vi.mock("@/lib/toast", () => ({
      __esModule: true,
      default: vi.fn(),
    }));

    const { default: PassageSearch } = await import("../PassageSearch");

    const onSearch: Mock<(book: string, chapter: number) => void> = vi.fn();
    render(<PassageSearch onSearch={onSearch} />);

    const chapterInput = screen.getByLabelText(/Chapter/i) as HTMLInputElement;
    expect(chapterInput).toBeTruthy();

    fireEvent.change(chapterInput, { target: { value: "100" } });

    const submit = screen.getByRole("button", { name: /Load Passage/i });
    fireEvent.click(submit);

    expect(onSearch).toHaveBeenCalled();
    const calledWith = onSearch.mock.calls[0];
    expect(calledWith[0]).toBe("John");
    expect(calledWith[1]).toBe(21);
  });

  it("real toast implementation appends a DOM node when called", async () => {
    // Ensure modules are fresh and toast is unmocked
    vi.resetModules();
    try {
      vi.unmock("@/lib/toast");
    } catch {
      // ignore
    }

    const toastModule = await import("@/lib/toast");
    const toast = toastModule.default;

    // Call toast directly
    toast({ title: "Test Toast", description: "This is a test" });

    const toastEl = document.querySelector(".verse-toast-wrapper");
    expect(toastEl).toBeTruthy();
  });
});
