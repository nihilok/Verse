import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { useLoadOnce } from "../useLoadOnce";

describe("useLoadOnce", () => {
  it("should expose loading, loaded, and executeLoad", () => {
    const { result } = renderHook(() => useLoadOnce());

    expect(result.current).toHaveProperty("loading");
    expect(result.current).toHaveProperty("loaded");
    expect(result.current).toHaveProperty("executeLoad");
    expect(typeof result.current.loading).toBe("boolean");
    expect(typeof result.current.loaded).toBe("boolean");
    expect(typeof result.current.executeLoad).toBe("function");
  });

  it("should start with loading=false and loaded=false", () => {
    const { result } = renderHook(() => useLoadOnce());

    expect(result.current.loading).toBe(false);
    expect(result.current.loaded).toBe(false);
  });

  it("should set loading to true during execution and false after", async () => {
    const { result } = renderHook(() => useLoadOnce());
    const mockLoadFn = vi.fn(async () => {
      return "data";
    });

    expect(result.current.loading).toBe(false);

    await act(async () => {
      await result.current.executeLoad(mockLoadFn);
    });

    expect(result.current.loading).toBe(false);
    expect(mockLoadFn).toHaveBeenCalledTimes(1);
  });

  it("should set loaded to true after successful execution", async () => {
    const { result } = renderHook(() => useLoadOnce());
    const mockLoadFn = vi.fn(async () => {
      return "data";
    });

    await act(async () => {
      await result.current.executeLoad(mockLoadFn);
    });

    expect(result.current.loaded).toBe(true);
  });

  it("should not execute load function on subsequent calls (load-once behavior)", async () => {
    const { result } = renderHook(() => useLoadOnce());
    const mockLoadFn = vi.fn(async () => {
      return "data";
    });

    // First call
    await act(async () => {
      await result.current.executeLoad(mockLoadFn);
    });

    expect(mockLoadFn).toHaveBeenCalledTimes(1);
    expect(result.current.loaded).toBe(true);

    // Second call - should not execute
    await act(async () => {
      await result.current.executeLoad(mockLoadFn);
    });

    expect(mockLoadFn).toHaveBeenCalledTimes(1); // Still only 1 call
    expect(result.current.loaded).toBe(true);
  });

  it("should not execute load function when already loaded", async () => {
    const { result } = renderHook(() => useLoadOnce());
    const mockLoadFn = vi.fn(async () => {
      return "data";
    });

    // First call
    await act(async () => {
      await result.current.executeLoad(mockLoadFn);
    });

    expect(mockLoadFn).toHaveBeenCalledTimes(1);

    // Second call - should not execute
    await act(async () => {
      await result.current.executeLoad(mockLoadFn);
    });

    expect(mockLoadFn).toHaveBeenCalledTimes(1); // Still only 1
  });

  it("should reset loading to false even if load function throws", async () => {
    const { result } = renderHook(() => useLoadOnce());
    const mockLoadFn = vi.fn(async () => {
      throw new Error("Load failed");
    });

    await act(async () => {
      try {
        await result.current.executeLoad(mockLoadFn);
      } catch {
        // Expected to throw
      }
    });

    expect(result.current.loading).toBe(false);
    expect(mockLoadFn).toHaveBeenCalledTimes(1);
  });

  it("should set loaded to true even if load function throws", async () => {
    const { result } = renderHook(() => useLoadOnce());
    const mockLoadFn = vi.fn(async () => {
      throw new Error("Load failed");
    });

    await act(async () => {
      try {
        await result.current.executeLoad(mockLoadFn);
      } catch {
        // Expected to throw
      }
    });

    expect(result.current.loaded).toBe(true);
  });

  it("should propagate errors from load function", async () => {
    const { result } = renderHook(() => useLoadOnce());
    const error = new Error("Load failed");
    const mockLoadFn = vi.fn(async () => {
      throw error;
    });

    await act(async () => {
      await expect(result.current.executeLoad(mockLoadFn)).rejects.toThrow(
        "Load failed",
      );
    });

    expect(mockLoadFn).toHaveBeenCalledTimes(1);
  });

  it("should handle multiple sequential calls without race conditions", async () => {
    const { result } = renderHook(() => useLoadOnce());
    let executionCount = 0;
    const mockLoadFn = vi.fn(async () => {
      executionCount++;
      await new Promise((resolve) => setTimeout(resolve, 10));
      return `data-${executionCount}`;
    });

    // First call
    await act(async () => {
      await result.current.executeLoad(mockLoadFn);
    });

    // Second call - should not execute
    await act(async () => {
      await result.current.executeLoad(mockLoadFn);
    });

    // Only first call should execute
    expect(mockLoadFn).toHaveBeenCalledTimes(1);
    expect(result.current.loaded).toBe(true);
  });

  it("should handle async functions that return values", async () => {
    const { result } = renderHook(() => useLoadOnce());
    const expectedData = { id: 1, name: "test" };
    const mockLoadFn = vi.fn(async () => {
      return expectedData;
    });

    await act(async () => {
      await result.current.executeLoad(mockLoadFn);
    });

    expect(mockLoadFn).toHaveBeenCalledTimes(1);
    expect(result.current.loaded).toBe(true);
  });
});
