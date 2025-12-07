import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

// Cleanup after each test case
afterEach(() => {
  cleanup();
});

// Mock scrollIntoView which is not implemented in jsdom
Element.prototype.scrollIntoView = () => {};

// Polyfill for PointerEvent if not available
if (typeof PointerEvent === "undefined") {
  class MockPointerEvent extends Event {
    button: number;
    ctrlKey: boolean;
    pointerType: string;

    constructor(
      type: string,
      props: {
        button?: number;
        ctrlKey?: boolean;
        pointerType?: string;
      } = {},
    ) {
      super(type, props);
      this.button = props.button || 0;
      this.ctrlKey = props.ctrlKey || false;
      this.pointerType = props.pointerType || "mouse";
    }
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (globalThis as any).PointerEvent = MockPointerEvent;
}
