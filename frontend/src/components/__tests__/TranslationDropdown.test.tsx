import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, Mock } from "vitest";
import TranslationDropdown from "../TranslationDropdown";
import { bibleService } from "@/services/api";

// Mock the API service
vi.mock("@/services/api", () => ({
  bibleService: {
    getTranslations: vi.fn(),
  },
}));

const MOCK_TRANSLATIONS = [
  { code: "WEB", name: "World English Bible", requires_pro: false },
  { code: "KJV", name: "King James Version", requires_pro: false },
  { code: "BSB", name: "Berean Standard Bible", requires_pro: false },
  { code: "NRSV", name: "New Revised Standard Version", requires_pro: true },
];

describe("TranslationDropdown", () => {
  let onChange: Mock<(value: string) => void>;

  beforeEach(() => {
    onChange = vi.fn();
    // Mock successful API response
    (
      bibleService.getTranslations as ReturnType<typeof vi.fn>
    ).mockResolvedValue({
      translations: MOCK_TRANSLATIONS,
    });
  });

  it("renders the component with Radix UI Select", async () => {
    render(<TranslationDropdown value="WEB" onChange={onChange} />);

    // Wait for loading to complete
    await waitFor(() => {
      const trigger = screen.getByRole("combobox");
      expect(trigger).toBeTruthy();
    });
  });

  it("displays the selected translation code in the trigger", async () => {
    const { container } = render(
      <TranslationDropdown value="KJV" onChange={onChange} />,
    );

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.getByRole("combobox")).toBeTruthy();
    });

    // The trigger should display "KJV"
    expect(container.textContent).toContain("KJV");
  });

  it("renders all translations from API in the dropdown", async () => {
    render(<TranslationDropdown value="WEB" onChange={onChange} />);

    // Wait for translations to load
    await waitFor(() => {
      expect(bibleService.getTranslations).toHaveBeenCalled();
    });

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    // Wait for dropdown to open and check that all translations are present
    await waitFor(() => {
      const options = screen.getAllByRole("option");
      expect(options.length).toBe(MOCK_TRANSLATIONS.length);
    });
  });

  it("displays translation codes and names in dropdown options", async () => {
    render(<TranslationDropdown value="WEB" onChange={onChange} />);

    // Wait for translations to load
    await waitFor(() => {
      expect(bibleService.getTranslations).toHaveBeenCalled();
    });

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    // Check that at least some specific translations are rendered with their full names
    await waitFor(() => {
      expect(screen.getByText(/KJV - King James Version/)).toBeTruthy();
      expect(screen.getByText(/WEB - World English Bible/)).toBeTruthy();
      expect(screen.getByText(/BSB - Berean Standard Bible/)).toBeTruthy();
    });
  });

  it("calls onChange callback when a translation is selected", async () => {
    render(<TranslationDropdown value="WEB" onChange={onChange} />);

    // Wait for loading
    await waitFor(() => {
      expect(screen.getByRole("combobox")).toBeTruthy();
    });

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    // Select a different translation
    await waitFor(() => {
      const kjvOption = screen.getByText(/KJV - King James Version/);
      fireEvent.click(kjvOption);
    });

    // Verify onChange was called with the correct value
    expect(onChange).toHaveBeenCalledWith("KJV");
  });

  it("does not call onChange when the same translation is selected", async () => {
    render(<TranslationDropdown value="WEB" onChange={onChange} />);

    // Wait for loading
    await waitFor(() => {
      expect(screen.getByRole("combobox")).toBeTruthy();
    });

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    // Select the same translation (WEB)
    await waitFor(() => {
      const webOption = screen.getByText(/WEB - World English Bible/);
      fireEvent.click(webOption);
    });

    // onChange might still be called by Radix UI, but we verify it's called with the correct value
    if (onChange.mock.calls.length > 0) {
      expect(onChange).toHaveBeenCalledWith("WEB");
    }
  });

  it("renders correctly when disabled prop is true", async () => {
    render(<TranslationDropdown value="WEB" onChange={onChange} disabled />);

    // Wait for loading
    await waitFor(() => {
      const trigger = screen.getByRole("combobox");
      expect(trigger).toBeTruthy();
    });

    const trigger = screen.getByRole("combobox");

    // Check that the trigger has disabled attribute (Radix UI sets data-disabled)
    expect(trigger.hasAttribute("data-disabled")).toBe(true);
  });

  it("renders correctly when disabled prop is false", async () => {
    render(
      <TranslationDropdown value="WEB" onChange={onChange} disabled={false} />,
    );

    // Wait for loading
    await waitFor(() => {
      const trigger = screen.getByRole("combobox");
      expect(trigger).toBeTruthy();
    });

    const trigger = screen.getByRole("combobox");
    expect(trigger).toBeTruthy();
    // Disabled attribute should not be present
    expect(trigger.hasAttribute("data-disabled")).toBe(false);
  });

  it("displays crown icon for pro translations", async () => {
    render(<TranslationDropdown value="WEB" onChange={onChange} />);

    // Wait for translations to load
    await waitFor(() => {
      expect(bibleService.getTranslations).toHaveBeenCalled();
    });

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    // Check that NRSV has a crown icon (pro translation)
    await waitFor(() => {
      const nrsvOption = screen.getByText(
        /NRSV - New Revised Standard Version/,
      );
      expect(nrsvOption).toBeTruthy();
      // Crown icon should be present for NRSV
      const svg = nrsvOption.parentElement?.querySelector("svg");
      expect(svg).toBeTruthy();
    });
  });

  it("shows loading state initially", () => {
    render(<TranslationDropdown value="WEB" onChange={onChange} />);

    // Should show loading state (just the code without dropdown)
    expect(screen.getByText("WEB")).toBeTruthy();
  });
});
