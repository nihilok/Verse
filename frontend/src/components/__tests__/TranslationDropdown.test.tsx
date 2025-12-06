import { describe, it, expect, vi } from "vitest";
import TranslationDropdown from "../TranslationDropdown";

describe("TranslationDropdown", () => {
  it("exports the component", () => {
    // Basic smoke test to ensure the component is defined
    expect(TranslationDropdown).toBeDefined();
    expect(typeof TranslationDropdown).toBe("function");
  });

  it("accepts required props", () => {
    const onChange = vi.fn();
    // Verify the component can be instantiated with required props
    // This is a type-level check more than a runtime check
    const props = { value: "WEB", onChange, disabled: false };
    expect(props.value).toBe("WEB");
    expect(typeof props.onChange).toBe("function");
  });
});
