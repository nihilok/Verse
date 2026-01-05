import { vi } from "vitest";

// Mock scrollIntoView for jsdom compatibility (used by Radix UI)
Element.prototype.scrollIntoView = vi.fn();

// Mock HTMLElement pointer capture methods for Radix UI
HTMLElement.prototype.hasPointerCapture = vi.fn();
HTMLElement.prototype.setPointerCapture = vi.fn();
HTMLElement.prototype.releasePointerCapture = vi.fn();
