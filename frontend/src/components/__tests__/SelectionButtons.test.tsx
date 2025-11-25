import { render, screen, fireEvent, act, cleanup } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import SelectionButtons from "../SelectionButtons";

describe("SelectionButtons", () => {
  const mockOnGetInsights = vi.fn();
  const mockOnAskQuestion = vi.fn();
  const mockOnClear = vi.fn();

  // Store original getBoundingClientRect
  const originalGetBoundingClientRect =
    Element.prototype.getBoundingClientRect;

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset viewport width to default
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1024,
    });
    // Restore original getBoundingClientRect before each test
    Element.prototype.getBoundingClientRect = originalGetBoundingClientRect;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    // Ensure getBoundingClientRect is restored
    Element.prototype.getBoundingClientRect = originalGetBoundingClientRect;
  });

  const renderComponent = (position: { x: number; y: number }) => {
    return render(
      <SelectionButtons
        position={position}
        onGetInsights={mockOnGetInsights}
        onAskQuestion={mockOnAskQuestion}
        onClear={mockOnClear}
      />
    );
  };

  // Helper to mock getBoundingClientRect with specific width
  const mockBoundingClientRect = (width: number) => {
    Element.prototype.getBoundingClientRect = vi.fn().mockReturnValue({
      width,
      height: 80,
      top: 0,
      left: 0,
      right: width,
      bottom: 80,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });
  };

  describe("viewport boundary detection", () => {
    it("maintains position when tooltip fits within viewport", () => {
      // Mock a 200px wide tooltip
      mockBoundingClientRect(200);

      // Position in the middle of a 1024px wide viewport
      // halfWidth = 100, position.x = 512
      // 512 + 100 = 612 < 1024 (fits right)
      // 512 - 100 = 412 > 0 (fits left)
      const position = { x: 512, y: 100 };
      renderComponent(position);

      const tooltip = screen.getByTestId("selection-tooltip");
      expect(tooltip).toBeTruthy();

      // The tooltip should be positioned at the original x position
      expect(tooltip.style.left).toBe("512px");
      expect(tooltip.style.top).toBe("100px");
    });

    it("adjusts position when tooltip would overflow right edge", () => {
      // Mock a 200px wide tooltip (halfWidth = 100)
      mockBoundingClientRect(200);

      // Set viewport width to 1024
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 1024,
      });

      // Position near the right edge
      // position.x = 970, halfWidth = 100
      // 970 + 100 = 1070 > 1024 (overflows right)
      // Expected adjustment: viewportWidth - halfWidth - padding = 1024 - 100 - 8 = 916
      const position = { x: 970, y: 100 };
      renderComponent(position);

      const tooltip = screen.getByTestId("selection-tooltip");
      expect(tooltip).toBeTruthy();

      // After adjustment, the tooltip's left position should be adjusted
      const leftValue = parseFloat(tooltip.style.left || "0");
      // The adjusted position should be 916 (viewportWidth - halfWidth - padding)
      expect(leftValue).toBe(916);
    });

    it("adjusts position when tooltip would overflow left edge", () => {
      // Mock a 200px wide tooltip (halfWidth = 100)
      mockBoundingClientRect(200);

      // Position near the left edge
      // position.x = 50, halfWidth = 100
      // 50 - 100 = -50 < 0 (overflows left)
      // Expected adjustment: halfWidth + padding = 100 + 8 = 108
      const position = { x: 50, y: 100 };
      renderComponent(position);

      const tooltip = screen.getByTestId("selection-tooltip");
      expect(tooltip).toBeTruthy();

      // After adjustment, the tooltip's left position should be adjusted
      const leftValue = parseFloat(tooltip.style.left || "0");
      // The adjusted position should be 108 (halfWidth + padding)
      expect(leftValue).toBe(108);
    });

    it("recalculates position on window resize", () => {
      // Mock a 200px wide tooltip (halfWidth = 100)
      mockBoundingClientRect(200);

      // Start with a wide viewport where position fits
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 1024,
      });

      // Position that fits in wide viewport
      const position = { x: 500, y: 100 };
      renderComponent(position);

      const tooltip = screen.getByTestId("selection-tooltip");
      expect(tooltip).toBeTruthy();

      // Initial position should be maintained
      expect(tooltip.style.left).toBe("500px");

      // Simulate viewport resize to a smaller width that would cause overflow
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 400,
      });

      // Trigger resize event
      act(() => {
        fireEvent(window, new Event("resize"));
      });

      // The tooltip position should be recalculated
      // After resize to 400px viewport, position 500 would overflow right
      // position.x (500) + halfWidth (100) = 600 > 400
      // Expected new position: viewportWidth (400) - halfWidth (100) - padding (8) = 292
      const leftValue = parseFloat(tooltip.style.left || "0");
      expect(leftValue).toBe(292);
    });

    it("adds and removes resize event listener correctly", () => {
      // Mock a 200px wide tooltip
      mockBoundingClientRect(200);

      const addEventListenerSpy = vi.spyOn(window, "addEventListener");
      const removeEventListenerSpy = vi.spyOn(window, "removeEventListener");

      const { unmount } = renderComponent({ x: 512, y: 100 });

      // Check that resize listener was added
      expect(addEventListenerSpy).toHaveBeenCalledWith(
        "resize",
        expect.any(Function)
      );

      // Unmount and check that listener was removed
      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        "resize",
        expect.any(Function)
      );

      addEventListenerSpy.mockRestore();
      removeEventListenerSpy.mockRestore();
    });
  });

  describe("button interactions", () => {
    it("calls onGetInsights when Get Insights button is clicked", () => {
      renderComponent({ x: 512, y: 100 });

      const getInsightsButton = screen.getByRole("button", {
        name: /Get Insights/i,
      });
      fireEvent.click(getInsightsButton);

      expect(mockOnGetInsights).toHaveBeenCalledTimes(1);
    });

    it("calls onAskQuestion when Ask a Question button is clicked", () => {
      renderComponent({ x: 512, y: 100 });

      const askQuestionButton = screen.getByRole("button", {
        name: /Ask a Question/i,
      });
      fireEvent.click(askQuestionButton);

      expect(mockOnAskQuestion).toHaveBeenCalledTimes(1);
    });

    it("calls onClear when close button is clicked", () => {
      renderComponent({ x: 512, y: 100 });

      const closeButton = screen.getByRole("button", { name: /Close/i });
      fireEvent.click(closeButton);

      expect(mockOnClear).toHaveBeenCalledTimes(1);
    });
  });
});
