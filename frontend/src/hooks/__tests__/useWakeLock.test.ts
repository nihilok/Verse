/**
 * @vitest-environment jsdom
 */
import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { useWakeLock } from "../useWakeLock";

// Mock wake lock API
class MockWakeLockSentinel {
  released = false;
  type = "screen" as const;
  private releaseHandler: (() => void) | null = null;

  addEventListener(_event: string, handler: () => void) {
    this.releaseHandler = handler;
  }

  removeEventListener() {
    this.releaseHandler = null;
  }

  async release() {
    if (!this.released) {
      this.released = true;
      if (this.releaseHandler) {
        this.releaseHandler();
      }
    }
  }
}

const mockWakeLockRequest = vi.fn();

describe("useWakeLock", () => {
  beforeEach(() => {
    // Mock navigator.wakeLock
    Object.defineProperty(navigator, "wakeLock", {
      value: {
        request: mockWakeLockRequest,
      },
      writable: true,
      configurable: true,
    });

    // Reset mock
    mockWakeLockRequest.mockReset();
    mockWakeLockRequest.mockResolvedValue(new MockWakeLockSentinel());
  });

  afterEach(() => {
    if (vi.isFakeTimers()) {
      vi.clearAllTimers();
      vi.useRealTimers();
    }
  });

  it("should expose refreshWakeLock, releaseWakeLock, and isSupported", () => {
    const { result } = renderHook(() => useWakeLock());

    expect(result.current).toHaveProperty("refreshWakeLock");
    expect(result.current).toHaveProperty("releaseWakeLock");
    expect(result.current).toHaveProperty("isSupported");
    expect(typeof result.current.refreshWakeLock).toBe("function");
    expect(typeof result.current.releaseWakeLock).toBe("function");
    expect(typeof result.current.isSupported).toBe("boolean");
  });

  it("should indicate Wake Lock API is supported when available", () => {
    const { result } = renderHook(() => useWakeLock());

    expect(result.current.isSupported).toBe(true);
  });

  it("should request wake lock when refreshWakeLock is called", async () => {
    const { result } = renderHook(() => useWakeLock());

    await act(async () => {
      await result.current.refreshWakeLock();
    });

    expect(mockWakeLockRequest).toHaveBeenCalledWith("screen");
    expect(mockWakeLockRequest).toHaveBeenCalledTimes(1);
  });

  it("should release wake lock after timeout", async () => {
    vi.useFakeTimers();
    const timeout = 1000; // 1 second
    const { result } = renderHook(() => useWakeLock({ timeout }));

    let sentinel: MockWakeLockSentinel | null = null;
    mockWakeLockRequest.mockImplementation(async () => {
      sentinel = new MockWakeLockSentinel();
      return sentinel;
    });

    await act(async () => {
      await result.current.refreshWakeLock();
    });

    expect(sentinel).not.toBeNull();
    expect(sentinel!.released).toBe(false);

    // Fast-forward time by timeout
    await act(async () => {
      vi.advanceTimersByTime(timeout);
      // Allow promises to resolve
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(sentinel!.released).toBe(true);
    });

    vi.useRealTimers();
  });

  it("should reset timeout when refreshWakeLock is called again", async () => {
    vi.useFakeTimers();
    const timeout = 2000;
    const { result } = renderHook(() => useWakeLock({ timeout }));

    let sentinel: MockWakeLockSentinel | null = null;
    mockWakeLockRequest.mockImplementation(async () => {
      sentinel = new MockWakeLockSentinel();
      return sentinel;
    });

    // First refresh
    await act(async () => {
      await result.current.refreshWakeLock();
    });

    expect(sentinel).not.toBeNull();
    expect(sentinel!.released).toBe(false);

    // Advance time by half the timeout
    await act(async () => {
      vi.advanceTimersByTime(timeout / 2);
    });

    // Second refresh should reset the timer
    await act(async () => {
      await result.current.refreshWakeLock();
    });

    // Advance time by half the timeout again
    await act(async () => {
      vi.advanceTimersByTime(timeout / 2);
    });

    // Should still be active since we reset the timer
    expect(sentinel!.released).toBe(false);

    // Advance the remaining time
    await act(async () => {
      vi.advanceTimersByTime(timeout / 2);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(sentinel!.released).toBe(true);
    });

    vi.useRealTimers();
  });

  it("should manually release wake lock when releaseWakeLock is called", async () => {
    const { result } = renderHook(() => useWakeLock());

    let sentinel: MockWakeLockSentinel | null = null;
    mockWakeLockRequest.mockImplementation(async () => {
      sentinel = new MockWakeLockSentinel();
      return sentinel;
    });

    await act(async () => {
      await result.current.refreshWakeLock();
    });

    expect(sentinel).not.toBeNull();
    expect(sentinel!.released).toBe(false);

    await act(async () => {
      await result.current.releaseWakeLock();
    });

    expect(sentinel!.released).toBe(true);
  });

  it("should use default timeout when not specified", async () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useWakeLock());

    let sentinel: MockWakeLockSentinel | null = null;
    mockWakeLockRequest.mockImplementation(async () => {
      sentinel = new MockWakeLockSentinel();
      return sentinel;
    });

    await act(async () => {
      await result.current.refreshWakeLock();
    });

    expect(sentinel).not.toBeNull();
    expect(sentinel!.released).toBe(false);

    // Default timeout is 5 minutes (300000ms)
    await act(async () => {
      vi.advanceTimersByTime(300000);
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(sentinel!.released).toBe(true);
    });

    vi.useRealTimers();
  });

  it("should handle unsupported Wake Lock API gracefully", async () => {
    // Remove wake lock support
    Object.defineProperty(navigator, "wakeLock", {
      value: undefined,
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useWakeLock());

    expect(result.current.isSupported).toBe(false);

    // Should not throw when calling refreshWakeLock
    await act(async () => {
      await result.current.refreshWakeLock();
    });

    expect(mockWakeLockRequest).not.toHaveBeenCalled();
  });

  it("should handle wake lock request failures gracefully", async () => {
    mockWakeLockRequest.mockRejectedValue(new Error("Permission denied"));

    const { result } = renderHook(() => useWakeLock());

    // Should not throw
    await act(async () => {
      await result.current.refreshWakeLock();
    });

    expect(mockWakeLockRequest).toHaveBeenCalled();
  });

  it("should not request wake lock when timeout is 0 (disabled)", async () => {
    const { result } = renderHook(() => useWakeLock({ timeout: 0 }));

    // Try to refresh wake lock
    await act(async () => {
      await result.current.refreshWakeLock();
    });

    // Should not have requested wake lock
    expect(mockWakeLockRequest).not.toHaveBeenCalled();
  });

  it("should not reacquire wake lock on visibility change when timeout is 0", async () => {
    renderHook(() => useWakeLock({ timeout: 0 }));

    mockWakeLockRequest.mockImplementation(async () => {
      return new MockWakeLockSentinel();
    });

    // Simulate visibility change to hidden then visible
    await act(async () => {
      Object.defineProperty(document, "visibilityState", {
        value: "hidden",
        writable: true,
        configurable: true,
      });
      document.dispatchEvent(new Event("visibilitychange"));
    });

    await act(async () => {
      Object.defineProperty(document, "visibilityState", {
        value: "visible",
        writable: true,
        configurable: true,
      });
      document.dispatchEvent(new Event("visibilitychange"));
    });

    // Wait for any async operations
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 100));
    });

    // Should not have requested wake lock when disabled (timeout is 0)
    expect(mockWakeLockRequest).not.toHaveBeenCalled();
  });
});
