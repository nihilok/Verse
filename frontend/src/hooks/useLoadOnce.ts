import { useState, useCallback } from "react";

/**
 * A hook that manages loading state for data that should only be loaded once.
 * Tracks both whether data has been loaded and whether it's currently loading.
 *
 * @returns An object containing:
 *   - loading: boolean indicating if data is currently being loaded
 *   - loaded: boolean indicating if data has been loaded at least once
 *   - executeLoad: function to wrap your load function with loading state management
 */
export function useLoadOnce() {
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);

  /**
   * Wraps a load function with loading state management.
   * If already loaded, returns early without calling the load function.
   * Sets loading to true before calling, and false in finally block.
   *
   * @param loadFn The async function to execute
   */
  const executeLoad = useCallback(
    async <T>(loadFn: () => Promise<T>): Promise<T | undefined> => {
      if (loaded) return;
      setLoading(true);
      try {
        const result = await loadFn();
        setLoaded(true);
        return result;
      } finally {
        setLoading(false);
      }
    },
    [loaded],
  );

  return { loading, loaded, executeLoad };
}
